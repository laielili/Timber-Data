"""Development-only analyst tool endpoints.

⚠️ DEVELOPMENT PROTOTYPE ENDPOINTS — not production business endpoints.
Used to inspect the tool registry and exercise tools from Swagger while building
the future AI analyst integration.
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Body, Depends

from ..analyst_tools.registry import REGISTRY
from ..dependencies import get_conn

router = APIRouter(prefix="/api/v1/dev", tags=["dev-analyst-tools"])


@router.get("/analyst-tools", summary="List registered analyst tools (development prototype)")
def list_analyst_tools():
    """Registered tool metadata: name, description, business question, input/output schemas."""
    return {
        "development_prototype": True,
        "tool_count": len(REGISTRY.all()),
        "tools": [
            {
                "name": spec.name,
                "description": spec.description,
                "business_question": spec.business_question,
                "input_schema": spec.input_schema.model_json_schema(),
                "output_schema": spec.output_schema.model_json_schema(),
            }
            for spec in REGISTRY.all()
        ],
    }


@router.post("/analyst-tools/{tool_name}/execute", summary="Execute an analyst tool (development prototype)")
def execute_analyst_tool(
    tool_name: str,
    payload: dict = Body(default_factory=dict, description="Tool input as JSON (validated against the tool input schema)"),
    conn: sqlite3.Connection = Depends(get_conn),
):
    """Execute one registered tool with validated input. Returns a structured
    ToolExecutionResult (success, data, error, error_type) — no stack traces."""
    return REGISTRY.execute(tool_name, payload, conn).model_dump()
