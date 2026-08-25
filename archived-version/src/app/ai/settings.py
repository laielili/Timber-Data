"""Backend-only AI provider settings.

Local prototype storage for an OpenAI-compatible provider configuration. The API key
is a SECRET: it lives only on the server (``backend/.secrets/ai_provider.json``), is
never returned to the frontend, never logged, and is excluded from version control.

Configuration priority (single policy, documented in AI_PROVIDER_SETTINGS.md):

    saved local settings  ->  environment variables  ->  safe defaults

The rest of the system reads provider configuration exclusively through
``AISettingsService`` so there is exactly one source of truth. The analyst router and
the connection-test both obtain the provider via ``AISettingsService`` — never by
reading provider values from scattered files.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, Field

from ..config import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_ENABLED,
    AI_MAX_TOOL_ROUNDS,
    AI_MODEL,
    AI_PROVIDER,
    AI_REQUEST_TIMEOUT,
    AI_TEMPERATURE,
    BACKEND_DIR,
)
from .errors import (
    AIProviderAuth,
    AIProviderError,
    AIProviderMalformedResponse,
    AIProviderRateLimit,
    AIProviderTimeout,
    AIProviderUnavailable,
)
from .provider import OpenAICompatibleProvider

logger = logging.getLogger("cti.ai.settings")

# Backend-only secret storage. Never served statically; git-ignored (.secrets/).
SECRETS_DIR = BACKEND_DIR / ".secrets"
SETTINGS_FILE = SECRETS_DIR / "ai_provider.json"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
SUPPORTED_SCHEMES = ("http", "https")


# --------------------------------------------------------------------------- schemas
class AIProviderSettingsUpdate(BaseModel):
    """Incoming settings payload. ``api_key`` is optional: when omitted/null/empty the
    previously stored key is preserved (never erased accidentally)."""

    enabled: bool
    provider: str = "openai-compatible"
    base_url: str
    model: str
    api_key: Optional[str] = None
    advanced: Optional[dict[str, Any]] = None


class AIProviderSettingsResponse(BaseModel):
    """Safe settings returned to the frontend. CRITICAL: contains NO api_key / secret."""

    enabled: bool
    provider: str
    base_url: str
    model: str
    api_key_configured: bool
    source: str
    advanced: Optional[dict[str, Any]] = None


class AIConnectionTestRequest(BaseModel):
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None


class AIConnectionTestResult(BaseModel):
    success: bool
    provider_reachable: bool = False
    model_available: bool = False
    message: str = ""
    code: Optional[str] = None


class AIModelsRequest(BaseModel):
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None


class AIModelsResponse(BaseModel):
    models: list[str] = Field(default_factory=list)
    supported: bool = True
    message: str = ""


# --------------------------------------------------------------------------- validation
def _validate_base_url(value: str) -> str:
    """Accept http/https only; reject fragments/empty host. Local HTTP servers allowed."""
    v = (value or "").strip()
    if not v:
        raise ValueError("Base URL is required.")
    parts = urlsplit(v)
    if parts.scheme not in SUPPORTED_SCHEMES:
        raise ValueError("Base URL must start with http:// or https://")
    if not parts.hostname:
        raise ValueError("Base URL must include a host.")
    if parts.fragment:
        raise ValueError("Base URL must not contain a fragment.")
    return v.rstrip("/")


# --------------------------------------------------------------------------- runtime model
@dataclass
class AIProviderSettings:
    enabled: bool
    provider: str
    base_url: str
    model: str
    api_key: str
    source: str
    timeout: float
    temperature: float
    max_tool_rounds: int
    advanced: dict[str, Any] = field(default_factory=dict)


class AISettingsService:
    """Single source of truth for AI provider configuration (server-side only)."""

    @staticmethod
    def _load_local() -> dict[str, Any]:
        try:
            if not SETTINGS_FILE.exists():
                return {}
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            # Corrupt/unreadable settings must never crash the app — fall back to env/defaults.
            return {}

    @staticmethod
    def effective() -> AIProviderSettings:
        """Merge saved local settings > environment variables > safe defaults."""
        local = AISettingsService._load_local()
        has_local = bool(local)

        enabled = bool(local["enabled"]) if "enabled" in local else bool(AI_ENABLED)
        provider = (local.get("provider") or AI_PROVIDER).strip() or "openai-compatible"
        base_url = (local.get("base_url") or AI_BASE_URL).strip() or DEFAULT_BASE_URL
        model = (local.get("model") or AI_MODEL).strip()
        api_key = local.get("api_key") or AI_API_KEY

        adv = dict(local.get("advanced") or {})
        timeout = float(adv.get("timeout", AI_REQUEST_TIMEOUT))
        temperature = float(adv.get("temperature", AI_TEMPERATURE))
        max_tool_rounds = int(adv.get("max_tool_rounds", AI_MAX_TOOL_ROUNDS))

        if has_local:
            source = "local_settings"
        elif (
            AI_API_KEY
            or AI_MODEL
            or AI_PROVIDER != "openai-compatible"
            or AI_BASE_URL != DEFAULT_BASE_URL
            or AI_ENABLED
        ):
            source = "environment"
        else:
            source = "defaults"

        return AIProviderSettings(
            enabled=enabled,
            provider=provider,
            base_url=base_url,
            model=model,
            api_key=api_key,
            source=source,
            timeout=timeout,
            temperature=temperature,
            max_tool_rounds=max_tool_rounds,
            advanced=adv,
        )

    # -- persistence --------------------------------------------------------
    @staticmethod
    def _write(local: dict[str, Any]) -> None:
        SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        tmp = SETTINGS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(local, indent=2), encoding="utf-8")
        # Restrict permissions where the OS supports it (secret file + directory).
        try:
            os.chmod(tmp, 0o600)
            tmp.replace(SETTINGS_FILE)
            os.chmod(SETTINGS_FILE, 0o600)
            os.chmod(SECRETS_DIR, 0o700)
        except OSError:
            # Platforms without POSIX perms (e.g. some Windows setups) still write the file.
            tmp.replace(SETTINGS_FILE)

    @staticmethod
    def save(update: AIProviderSettingsUpdate) -> AIProviderSettingsResponse:
        base_url = _validate_base_url(update.base_url)
        provider = (update.provider or "openai-compatible").strip() or "openai-compatible"
        model = (update.model or "").strip()
        enabled = bool(update.enabled)

        local = AISettingsService._load_local()
        key_changed = False
        if update.api_key:
            local["api_key"] = update.api_key.strip()
            key_changed = True
        # else: keep existing saved key untouched.

        adv = dict(local.get("advanced") or {})
        if update.advanced:
            for k in ("timeout", "max_tool_rounds", "temperature"):
                if k in update.advanced:
                    adv[k] = update.advanced[k]
        local["advanced"] = adv
        local["enabled"] = enabled
        local["provider"] = provider
        local["base_url"] = base_url
        local["model"] = model

        AISettingsService._write(local)

        # Log ONLY safe, non-secret metadata.
        logger.info(
            "ai_settings_saved %s",
            {
                "provider": provider,
                "base_url_host": urlsplit(base_url).hostname,
                "model": model,
                "enabled": enabled,
                "api_key_changed": key_changed,
            },
        )
        return AISettingsService.safe_response(advanced=adv)

    @staticmethod
    def delete_key() -> dict[str, bool]:
        local = AISettingsService._load_local()
        had_key = "api_key" in local
        if had_key:
            del local["api_key"]
        if local:
            AISettingsService._write(local)
        logger.info(
            "ai_settings_key_deleted %s",
            {"base_url_host": urlsplit(local.get("base_url", "")).hostname, "had_key": had_key},
        )
        return {"api_key_configured": False}

    @staticmethod
    def safe_response(advanced: Optional[dict[str, Any]] = None) -> AIProviderSettingsResponse:
        s = AISettingsService.effective()
        if advanced is None:
            advanced = {"timeout": s.timeout, "max_tool_rounds": s.max_tool_rounds, "temperature": s.temperature}
        return AIProviderSettingsResponse(
            enabled=s.enabled,
            provider=s.provider,
            base_url=s.base_url,
            model=s.model,
            api_key_configured=bool(s.api_key),
            source=s.source,
            advanced=advanced,
        )

    # -- provider factory ---------------------------------------------------
    @staticmethod
    def build_provider_from_settings() -> OpenAICompatibleProvider:
        """Build the configured provider. Raises (cleanly) when no key is configured."""
        s = AISettingsService.effective()
        if not s.api_key:
            raise AIProviderError("No API key is configured for the AI analyst.")
        return OpenAICompatibleProvider(
            model=s.model, api_key=s.api_key, base_url=s.base_url, timeout=s.timeout
        )

    # -- connection test ----------------------------------------------------
    @staticmethod
    async def test_connection(req: AIConnectionTestRequest) -> AIConnectionTestResult:
        s = AISettingsService.effective()
        base_url = (req.base_url or "").strip() or s.base_url
        model = (req.model or "").strip() or s.model
        api_key = req.api_key or s.api_key

        try:
            bu = _validate_base_url(base_url)
        except ValueError as exc:
            return AIConnectionTestResult(success=False, code="invalid_base_url", message=str(exc))

        if not api_key:
            return AIConnectionTestResult(
                success=False, code="authentication_failed", message="No API key is configured."
            )
        if not model:
            return AIConnectionTestResult(
                success=False, code="model_not_found", message="No model identifier is configured."
            )

        provider = OpenAICompatibleProvider(model=model, api_key=api_key, base_url=bu, timeout=AI_REQUEST_TIMEOUT)
        try:
            await provider.chat(
                system="You are a connection checker. Respond with the single word OK.",
                messages=[{"role": "user", "content": "Reply only with OK."}],
                tools=[],
                response_format=None,
                temperature=0.0,
            )
            return AIConnectionTestResult(
                success=True,
                provider_reachable=True,
                model_available=True,
                message="Connection successful.",
            )
        except AIProviderAuth:
            return AIConnectionTestResult(
                success=False,
                code="authentication_failed",
                message="The provider rejected the API credentials.",
            )
        except AIProviderRateLimit:
            return AIConnectionTestResult(
                success=False, code="rate_limited", message="The provider rate-limited the request."
            )
        except AIProviderTimeout:
            return AIConnectionTestResult(
                success=False, code="timeout", message="The provider request timed out."
            )
        except AIProviderUnavailable:
            return AIConnectionTestResult(
                success=False, code="provider_unavailable", message="Could not reach the model provider."
            )
        except AIProviderMalformedResponse:
            return AIConnectionTestResult(
                success=False,
                code="model_not_found",
                message="The model was not found or the endpoint path is incorrect.",
            )
        except Exception:
            return AIConnectionTestResult(
                success=False,
                code="unknown_provider_error",
                message="An unexpected error occurred while contacting the provider.",
            )

    # -- optional model discovery ------------------------------------------
    @staticmethod
    async def list_models(req: AIModelsRequest) -> AIModelsResponse:
        s = AISettingsService.effective()
        base_url = (req.base_url or "").strip() or s.base_url
        api_key = req.api_key or s.api_key

        try:
            bu = _validate_base_url(base_url)
        except ValueError as exc:
            return AIModelsResponse(models=[], supported=False, message=str(exc))

        if not api_key:
            return AIModelsResponse(models=[], supported=False, message="No API key is configured.")

        try:
            async with httpx.AsyncClient(timeout=AI_REQUEST_TIMEOUT) as client:
                r = await client.get(f"{bu}/models", headers={"Authorization": f"Bearer {api_key}"})
                r.raise_for_status()
                data = r.json()
            ids = [
                m.get("id")
                for m in data.get("data", [])
                if isinstance(m, dict) and isinstance(m.get("id"), str)
            ]
            return AIModelsResponse(models=ids, supported=True, message="Model list retrieved.")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                return AIModelsResponse(models=[], supported=False, message="Authentication failed.")
            if exc.response.status_code == 404:
                return AIModelsResponse(
                    models=[],
                    supported=False,
                    message="Model discovery is not supported by this provider. Enter the model identifier manually.",
                )
            return AIModelsResponse(models=[], supported=False, message="The provider returned an error.")
        except (httpx.ConnectError, httpx.TimeoutException):
            return AIModelsResponse(models=[], supported=False, message="Could not reach the provider.")
        except Exception:
            return AIModelsResponse(models=[], supported=False, message="Model discovery failed.")
