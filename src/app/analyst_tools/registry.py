"""Analyst tool registry — the deterministic, provider-neutral tool layer the future
LLM analyst will be allowed to call.

Boundaries:
- Tools call Python analytics services DIRECTLY (never HTTP to our own FastAPI).
- Tools are READ ONLY. No SQL, no filesystem, no shell, no write access is exposed.
- Every invocation is audit-logged.
- Outputs are typed Pydantic models (no unrestricted dict[str, Any] for core analytics).
- No LLM/provider-specific schema is produced here (see ANALYST_TOOL_SCHEMAS.json).

The registry exposes: name, description, business_question, input_schema, output_schema,
callable.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Type

from pydantic import BaseModel, Field, ValidationError

from ..services.common import TimeContext, resolve_time_context
from .errors import InvalidPeriod, ToolError, UnsupportedPrototypeDateRange

logger = logging.getLogger("cti.analyst_tools")

# --------------------------------------------------------------------------- audit log


def _audit_log(tool_name: str, input_summary: str, success: bool, duration_ms: int,
               result_count: Optional[int], error_type: Optional[str]) -> None:
    """Structured audit entry. Never logs prompts/secrets — tool parameters only
    (the synthetic prototype contains no sensitive commercial data)."""
    entry = {
        "event": "tool_call",
        "tool": tool_name,
        "input_summary": input_summary,
        "success": success,
        "duration_ms": duration_ms,
        "result_count": result_count,
        "error_type": error_type,
    }
    if success:
        logger.info("analyst_tool_ok %s", entry)
    else:
        logger.warning("analyst_tool_fail %s", entry)


# --------------------------------------------------------------------------- spec + result


@dataclass
class ToolSpec:
    name: str
    description: str
    business_question: str
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]
    func: Callable[[BaseModel, Any, TimeContext], dict]
    input_summary_fn: Optional[Callable[[dict], str]] = None

    def input_summary(self, input_dict: dict) -> str:
        if self.input_summary_fn:
            return self.input_summary_fn(input_dict)
        return str(input_dict)[:200]


class ToolExecutionResult(BaseModel):
    tool_name: str
    success: bool
    data: Any = None
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    error_type: Optional[str] = None


# --------------------------------------------------------------------------- registry


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> ToolSpec:
        if spec.name in self._tools:
            raise ValueError(f"Duplicate tool name: {spec.name}")
        self._tools[spec.name] = spec
        return spec

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def all(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def names(self) -> list[str]:
        return sorted(self._tools)

    # ------------------------------------------------------------------ execution

    def execute(self, tool_name: str, input_dict: dict, conn: Any) -> ToolExecutionResult:
        spec = self.get(tool_name)
        if spec is None:
            return ToolExecutionResult(tool_name=tool_name, success=False,
                                       error=f"Unknown tool '{tool_name}'.", error_type="UnknownTool")

        started = time.perf_counter()
        input_summary = spec.input_summary(input_dict)
        try:
            validated = spec.input_schema.model_validate(input_dict)
        except ValidationError as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            _audit_log(tool_name, input_summary, False, duration_ms, None, "InvalidInput")
            return ToolExecutionResult(tool_name=tool_name, success=False,
                                       error=f"Invalid tool input: {exc.errors()[:3]}",
                                       error_type="InvalidInput")

        try:
            ctx = self._build_context(validated)
            data = spec.func(validated, conn, ctx)
        except ToolError as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            _audit_log(tool_name, input_summary, False, duration_ms, None, exc.code)
            return ToolExecutionResult(tool_name=tool_name, success=False,
                                       error=str(exc), error_type=exc.code)
        except Exception as exc:  # noqa: BLE001 - structured boundary
            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.debug("analyst_tool_stack", exc_info=True)
            _audit_log(tool_name, input_summary, False, duration_ms, None, "UnexpectedError")
            return ToolExecutionResult(tool_name=tool_name, success=False,
                                       error="Internal tool error.", error_type="UnexpectedError")

        duration_ms = int((time.perf_counter() - started) * 1000)
        count = _count(data)
        _audit_log(tool_name, input_summary, True, duration_ms, count, None)
        return ToolExecutionResult(tool_name=tool_name, success=True, data=data,
                                   metadata={"duration_ms": duration_ms, "result_count": count})

    @staticmethod
    def _build_context(validated: BaseModel) -> TimeContext:
        """Build a TimeContext from the optional time fields of any tool input.
        Defaults reproduce the approved prototype dataset."""
        dump = validated.model_dump()
        try:
            return resolve_time_context(
                period_start=dump.get("period_start"),
                period_end=dump.get("period_end"),
                as_of=dump.get("as_of"),
            )
        except ValueError as exc:
            msg = str(exc)
            if "outside the supported synthetic dataset" in msg:
                raise UnsupportedPrototypeDateRange(msg) from exc
            raise InvalidPeriod(msg) from exc

    # ------------------------------------------------------------------ schemas

    def schema_payload(self) -> dict:
        return {
            "tools": [
                {
                    "name": spec.name,
                    "description": spec.description,
                    "business_question": spec.business_question,
                    "input_schema": spec.input_schema.model_json_schema(),
                    "output_schema": spec.output_schema.model_json_schema(),
                }
                for spec in self.all()
            ]
        }

    def write_schemas_file(self, path: str) -> None:
        import json

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.schema_payload(), f, indent=2, ensure_ascii=False)


def _count(data: Any) -> Optional[int]:
    if not isinstance(data, dict):
        return None
    for key in ("batches", "rows", "months", "briefs"):
        v = data.get(key)
        if isinstance(v, list):
            return len(v)
    if "batch" in data:
        return 1
    return None


def make_provenance(ctx: TimeContext) -> dict:
    ps, pe, as_of = ctx.iso()
    return {
        "dataset_type": "synthetic_prototype",
        "period_start": ps,
        "period_end": pe,
        "as_of": as_of,
        "currency": "AUD",
        "weight_unit": "t",
        "prototype": True,
    }


REGISTRY = ToolRegistry()


def tool(name: str, description: str, business_question: str,
         input_schema: Type[BaseModel], output_schema: Type[BaseModel]):
    """Decorator to register a tool implementation (signature: fn(inp, conn, ctx) -> dict)."""
    def deco(func: Callable[[BaseModel, Any, TimeContext], dict]) -> Callable:
        REGISTRY.register(ToolSpec(
            name=name,
            description=description,
            business_question=business_question,
            input_schema=input_schema,
            output_schema=output_schema,
            func=func,
        ))
        return func
    return deco
