"""AI Analyst endpoint.

POST /api/v1/analyst/query

Connects the Ask Circular frontend to ONE real LLM provider through the approved,
deterministic analyst tool layer. The model never touches SQLite, CSV, or the
filesystem directly — it may only call the 12 registered tools via the registry.

Provider configuration is resolved exclusively through ``AISettingsService`` (saved
local settings > environment > defaults). On any AI/provider failure the endpoint
returns a clean structured error (never an API key, raw HTTP body, or stack trace).
The rest of the dashboard is unaffected.
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Body, Depends, status

from ..ai.errors import AIAnalystError
from ..ai.orchestration import OrchestrationSettings, build_response_format
from ..ai.schemas import AnalystErrorResponse, AnalystQueryRequest, AnalystResponse
from ..ai.service import AnalystService
from ..ai.settings import AISettingsService
from ..config import AI_MAX_HISTORY
from ..dependencies import get_conn

router = APIRouter(prefix="/api/v1/analyst", tags=["analyst"])


def _service() -> AnalystService:
    eff = AISettingsService.effective()
    settings = OrchestrationSettings(
        max_tool_rounds=eff.max_tool_rounds,
        temperature=eff.temperature,
        max_history=AI_MAX_HISTORY,
        response_format=build_response_format(),
    )
    return AnalystService(settings=settings)


@router.post("/query", summary="Ask the Recovery Intelligence Analyst a free-text question")
async def analyst_query(
    payload: AnalystQueryRequest = Body(...),
    conn: sqlite3.Connection = Depends(get_conn),
    service: AnalystService = Depends(_service),
) -> AnalystResponse:
    try:
        eff = AISettingsService.effective()
        if not eff.enabled or not eff.api_key:
            # No silent fallback to fake AI. Surface a clear, clean error.
            raise _DisabledAnalyst("AI analyst is not enabled or not configured on this server.")

        provider = AISettingsService.build_provider_from_settings()
        return await service.query(
            payload, conn, provider_override=provider, model=eff.model
        )
    except AIAnalystError as exc:
        raise _to_http_error(exc) from exc


# --------------------------------------------------------------------------- errors


class _DisabledAnalyst(AIAnalystError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "ai_disabled"


def _to_http_error(exc: AIAnalystError) -> Exception:
    """Convert an internal AI error into a FastAPI HTTPException with a clean body."""
    from fastapi import HTTPException

    return HTTPException(
        status_code=exc.status_code,
        detail=AnalystErrorResponse(
            code=exc.code,
            message=str(exc) or "The analyst could not complete the analysis.",
            prototype=True,
        ).model_dump(),
    )
