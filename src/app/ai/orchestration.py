"""Tool-calling orchestration + evidence grounding.

The orchestrator drives the conversation loop:
    user question → model → tool call(s) → REGISTRY.execute → result → model → …
until the model stops calling tools, then forces a structured synthesis into the
typed `AnalystResponse` shape. Numerical evidence in the final answer is validated
against the deterministic tool outputs before delivery.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from ..analyst_tools.registry import REGISTRY, ToolExecutionResult
from ..config import (
    AI_MAX_HISTORY,
    AI_MAX_TOOL_ROUNDS,
    AI_TEMPERATURE,
    DEFAULT_AS_OF,
    DEFAULT_PERIOD_END,
    DEFAULT_PERIOD_START,
)
from .errors import AIProviderMalformedResponse, MaxToolRoundsExceeded
from .provider import ModelProvider, ToolCall
from .tool_adapter import registry_to_provider_tools
from .schemas import AnalystContext, AnalystResponse, EvidenceItem
from .tool_adapter import _clean_schema

logger = logging.getLogger("cti.ai.orchestration")

PERIOD_FIELDS = ("period_start", "period_end", "as_of")


@dataclass
class ToolExecutionRecord:
    name: str
    success: bool
    data: Optional[dict[str, Any]]
    error_type: Optional[str]
    error: Optional[str]


@dataclass
class OrchestrationSettings:
    max_tool_rounds: int = AI_MAX_TOOL_ROUNDS
    temperature: float = AI_TEMPERATURE
    max_history: int = AI_MAX_HISTORY
    response_format: Optional[dict[str, Any]] = None


def build_response_format() -> dict[str, Any]:
    """JSON-schema response_format for the final synthesis call."""
    schema = _clean_schema(AnalystResponse.model_json_schema())
    return {"type": "json_schema", "json_schema": {"name": "analyst_response", "schema": schema}}


def _resolve_defaults(context: AnalystContext) -> dict[str, Any]:
    return {
        "period_start": context.period_start or DEFAULT_PERIOD_START,
        "period_end": context.period_end or DEFAULT_PERIOD_END,
        "as_of": context.as_of or DEFAULT_AS_OF,
    }


def _inject_defaults(arguments: dict[str, Any], allowed: set[str], defaults: dict[str, Any]) -> dict[str, Any]:
    """Add the approved period window to a tool call only when the tool accepts it
    and the model omitted it. Prevents tool-call validation errors from extra keys."""
    out = dict(arguments)
    for key in PERIOD_FIELDS:
        if key in allowed and key not in out:
            out[key] = defaults[key]
    return out


def _tool_result_payload(result: ToolExecutionResult) -> dict[str, Any]:
    return {
        "tool_name": result.tool_name,
        "success": result.success,
        "data": result.data if result.data is not None else None,
        "error": result.error,
        "error_type": result.error_type,
    }


def _parse_synthesis(content: Optional[str]) -> dict[str, Any]:
    if not content:
        raise AIProviderMalformedResponse("Model returned an empty synthesis.")
    text = content.strip()
    # tolerate ```json fences
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        # find first { and last }
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIProviderMalformedResponse("Model synthesis was not valid JSON.") from exc


# --------------------------------------------------------------------------- evidence


def _walk_numbers(obj: Any, acc: list[float]) -> None:
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        acc.append(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            _walk_numbers(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _walk_numbers(v, acc)


def _walk_batch_ids(obj: Any, acc: set[str]) -> None:
    if isinstance(obj, dict):
        bid = obj.get("batch_id")
        if isinstance(bid, str) and bid:
            acc.add(bid)
        for v in obj.values():
            _walk_batch_ids(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _walk_batch_ids(v, acc)


def _extract_number(value: str) -> Optional[float]:
    m = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(m.group(0)) if m else None


def validate_evidence(
    parsed: dict[str, Any], records: list[ToolExecutionRecord]
) -> tuple[list[EvidenceItem], int]:
    """Lightweight grounding check: every evidence row should be traceable to a tool
    output actually executed this turn. Unsupported rows are dropped (not silently
    returned as fact)."""
    tool_numbers: dict[str, list[float]] = {}
    batch_ids: set[str] = set()
    called_tools: set[str] = set()
    for r in records:
        called_tools.add(r.name)
        if r.success and isinstance(r.data, dict):
            nums: list[float] = []
            _walk_numbers(r.data, nums)
            tool_numbers[r.name] = nums
            _walk_batch_ids(r.data, batch_ids)

    verified: list[EvidenceItem] = []
    dropped = 0
    for raw in parsed.get("evidence", []) or []:
        label = str(raw.get("label", ""))
        value = str(raw.get("value", ""))
        source_tool = raw.get("source_tool")
        batch_id = raw.get("batch_id")
        item = EvidenceItem(
            label=label,
            value=value,
            unit=raw.get("unit"),
            source_tool=source_tool,
            batch_id=batch_id,
            time_basis=raw.get("time_basis"),
        )
        ok = True
        if source_tool and source_tool not in called_tools:
            ok = False
        if batch_id and batch_id not in batch_ids:
            ok = False
        num = _extract_number(value)
        if num is not None:
            candidates = tool_numbers.get(source_tool, []) if source_tool else [
                n for ns in tool_numbers.values() for n in ns
            ]
            if not any(abs(num - c) <= max(0.01, 0.01 * abs(c)) for c in candidates):
                ok = False
        if ok:
            verified.append(item)
        else:
            dropped += 1
            logger.info("evidence_dropped label=%s source_tool=%s batch_id=%s", label, source_tool, batch_id)
    return verified, dropped


# --------------------------------------------------------------------------- loop


async def orchestrate(
    provider: ModelProvider,
    system: str,
    history: list[dict[str, Any]],
    question: str,
    context: AnalystContext,
    conn: Any,
    settings: OrchestrationSettings,
) -> tuple[dict[str, Any], list[ToolExecutionRecord], int, list[str]]:
    messages: list[dict[str, Any]] = list(history)
    messages.append({"role": "user", "content": question})

    tools = registry_to_provider_tools()
    defaults = _resolve_defaults(context)

    records: list[ToolExecutionRecord] = []
    tools_requested: list[str] = []
    rounds = 0

    while True:
        turn: Any = await provider.chat(
            system=system,
            messages=messages,
            tools=tools,
            response_format=settings.response_format,
            temperature=settings.temperature,
        )
        if not turn.tool_calls:
            # Model chose to answer rather than call another tool → its content is the
            # structured JSON answer (enforced by response_format). Parse it directly.
            parsed = _parse_synthesis(turn.content)
            return parsed, records, rounds, tools_requested
        if rounds >= settings.max_tool_rounds:
            # Model insists on more tools than the safety cap allows.
            raise MaxToolRoundsExceeded(
                f"Model exceeded the maximum of {settings.max_tool_rounds} tool-call rounds."
            )

        assistant_msg = {
            "role": "assistant",
            "content": turn.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, default=str)},
                }
                for tc in turn.tool_calls
            ],
        }
        messages.append(assistant_msg)

        for tc in turn.tool_calls:
            tools_requested.append(tc.name)
            spec = REGISTRY.get(tc.name)
            if spec is None:
                result = ToolExecutionResult(
                    tool_name=tc.name, success=False, error=f"Unknown tool '{tc.name}'.", error_type="UnknownTool"
                )
            else:
                allowed = set(spec.input_schema.model_fields.keys())
                args = _inject_defaults(tc.arguments, allowed, defaults)
                result = await asyncio.to_thread(REGISTRY.execute, tc.name, args, conn)
            records.append(
                ToolExecutionRecord(
                    name=tc.name, success=result.success, data=result.data, error_type=result.error_type, error=result.error
                )
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(_tool_result_payload(result), default=str),
                }
            )
        rounds += 1
