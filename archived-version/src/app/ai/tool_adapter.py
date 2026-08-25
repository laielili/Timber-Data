"""Provider-neutral tool adapter.

Converts the REGISTRY metadata (name / description / input_schema) into the selected
provider's tool/function definition format. Definitions are generated at runtime from the
registry — a second hand-maintained list of the 12 tools is never created, so the
Python tool definition always equals the AI-visible tool definition.
"""
from __future__ import annotations

from typing import Any

from ..analyst_tools.registry import REGISTRY


def _resolve_refs(schema: Any, defs: dict[str, Any]) -> Any:
    """Inline `$ref`/`$defs` so the schema is self-contained for providers that do
    not support external references."""
    if isinstance(schema, dict):
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            resolved = defs.get(ref_name, {})
            return _resolve_refs(resolved, defs)
        return {k: _resolve_refs(v, defs) for k, v in schema.items() if k not in ("title", "default")}
    if isinstance(schema, list):
        return [_resolve_refs(item, defs) for item in schema]
    return schema


def _clean_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Remove cosmetic/unsupported keys and inline refs for provider compatibility."""
    defs = schema.get("$defs", {}) or schema.get("definitions", {})
    cleaned = _resolve_refs(schema, defs)
    # ensure top-level object forbids extra properties (keeps tool calls strict)
    if isinstance(cleaned, dict) and cleaned.get("type") == "object":
        cleaned.setdefault("additionalProperties", False)
    cleaned.pop("$defs", None)
    cleaned.pop("definitions", None)
    return cleaned


def registry_to_provider_tools() -> list[dict[str, Any]]:
    """Build provider tool definitions from the live registry."""
    tools: list[dict[str, Any]] = []
    for spec in REGISTRY.all():
        parameters = _clean_schema(spec.input_schema.model_json_schema())
        description = spec.description
        if spec.business_question:
            description = f"{description}\n\nBusiness question: {spec.business_question}"
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": description,
                    "parameters": parameters,
                },
            }
        )
    return tools


def available_tool_names() -> list[str]:
    return REGISTRY.names()
