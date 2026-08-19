"""AI Provider Settings endpoints (local prototype, server-side secret storage).

All responses are safe: the API key is NEVER returned. The key lives only in
``backend/.secrets/ai_provider.json`` and is used exclusively server-side when
building the provider for the analyst query or the connection test.

Endpoints:
  GET    /api/v1/settings/ai        -> safe settings (no key)
  PUT    /api/v1/settings/ai        -> save settings (key replaced only when supplied)
  DELETE /api/v1/settings/ai/key    -> remove the stored key
  POST   /api/v1/settings/ai/test   -> connectivity check (key stays server-side)
  POST   /api/v1/settings/ai/models -> optional model discovery (key stays server-side)
"""
from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException

from ..ai.settings import (
    AIConnectionTestRequest,
    AIConnectionTestResult,
    AIModelsRequest,
    AIModelsResponse,
    AIProviderSettingsResponse,
    AIProviderSettingsUpdate,
    AISettingsService,
)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("/ai", summary="Get safe AI provider settings (never includes the API key)")
async def get_ai_settings() -> AIProviderSettingsResponse:
    return AISettingsService.safe_response()


@router.put("/ai", summary="Save AI provider settings")
async def put_ai_settings(payload: AIProviderSettingsUpdate = Body(...)) -> AIProviderSettingsResponse:
    try:
        return AISettingsService.save(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/ai/key", summary="Remove the stored API key")
async def delete_ai_key() -> dict:
    return AISettingsService.delete_key()


@router.post("/ai/test", summary="Test connectivity to the configured provider")
async def test_ai_connection(
    payload: AIConnectionTestRequest = Body(default=AIConnectionTestRequest()),
) -> AIConnectionTestResult:
    return await AISettingsService.test_connection(payload)


@router.post("/ai/models", summary="Discover available models (optional)")
async def discover_models(payload: AIModelsRequest = Body(default=AIModelsRequest())) -> AIModelsResponse:
    return await AISettingsService.list_models(payload)
