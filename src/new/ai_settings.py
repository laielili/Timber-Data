"""Workbench AI provider settings — OpenAI-compatible config, server-side secrets.

The API key lives only in ``src/new/.secrets/ai_provider.json`` (git-ignored,
never returned to the frontend). Provider call logic is reused from the
well-tested ``app.ai`` package.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit

import httpx

from .ai_errors import (
    AIProviderAuth,
    AIProviderMalformedResponse,
    AIProviderRateLimit,
    AIProviderTimeout,
    AIProviderUnavailable,
)
from .ai_provider import OpenAICompatibleProvider
from . import config

logger = logging.getLogger("workbench.ai.settings")

SUPPORTED_SCHEMES = ("http", "https")


def _validate_base_url(value: str) -> str:
    v = (value or "").strip()
    if not v:
        raise ValueError("Base URL 不能为空。")
    parts = urlsplit(v)
    if parts.scheme not in SUPPORTED_SCHEMES:
        raise ValueError("Base URL 必须以 http:// 或 https:// 开头。")
    if not parts.hostname:
        raise ValueError("Base URL 必须包含主机名。")
    if parts.fragment:
        raise ValueError("Base URL 不能包含 fragment。")
    return v.rstrip("/")


def _load_local() -> dict[str, Any]:
    try:
        if not config.SETTINGS_FILE.exists():
            return {}
        return json.loads(config.SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write(local: dict[str, Any]) -> None:
    config.SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = config.SETTINGS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(local, indent=2), encoding="utf-8")
    try:
        tmp.replace(config.SETTINGS_FILE)
        # Best-effort permissions where the OS supports them.
        import os
        os.chmod(config.SETTINGS_FILE, 0o600)
    except OSError:
        pass


def effective() -> dict[str, Any]:
    local = _load_local()
    has_local = bool(local)
    enabled = bool(local["enabled"]) if "enabled" in local else config.AI_ENABLED
    base_url = (local.get("base_url") or config.AI_BASE_URL).strip() or config.DEFAULT_BASE_URL
    model = (local.get("model") or config.AI_MODEL).strip()
    api_key = local.get("api_key") or config.AI_API_KEY

    if has_local:
        source = "local_settings"
    elif config.AI_API_KEY or config.AI_MODEL or config.AI_ENABLED:
        source = "environment"
    else:
        source = "defaults"

    return {
        "enabled": enabled,
        "provider": "openai-compatible",
        "base_url": base_url,
        "model": model,
        "api_key": api_key,
        "source": source,
    }


def safe_response() -> dict[str, Any]:
    s = effective()
    return {
        "enabled": s["enabled"],
        "provider": s["provider"],
        "base_url": s["base_url"],
        "model": s["model"],
        "api_key_configured": bool(s["api_key"]),
        "source": s["source"],
    }


def save(update: dict[str, Any]) -> dict[str, Any]:
    base_url = _validate_base_url(update.get("base_url", ""))
    model = (update.get("model") or "").strip()
    enabled = bool(update.get("enabled", False))

    local = _load_local()
    key_changed = False
    if update.get("api_key"):
        local["api_key"] = str(update["api_key"]).strip()
        key_changed = True
    local["enabled"] = enabled
    local["base_url"] = base_url
    local["model"] = model

    _write(local)
    logger.info("ai_settings_saved host=%s model=%s enabled=%s key_changed=%s",
                urlsplit(base_url).hostname, model, enabled, key_changed)
    return safe_response()


def delete_key() -> dict[str, bool]:
    local = _load_local()
    had_key = "api_key" in local
    if had_key:
        del local["api_key"]
        _write(local)
    return {"api_key_configured": False}


def build_provider() -> OpenAICompatibleProvider:
    s = effective()
    if not s["api_key"]:
        raise ValueError("尚未配置 API Key。请在 AI 页的配置面板中填写。")
    if not s["model"]:
        raise ValueError("尚未配置模型名称（model）。")
    return OpenAICompatibleProvider(
        model=s["model"], api_key=s["api_key"], base_url=s["base_url"], timeout=config.AI_REQUEST_TIMEOUT
    )


def _provider_for(base_url: Optional[str], model: Optional[str], api_key: Optional[str]) -> OpenAICompatibleProvider:
    s = effective()
    bu = _validate_base_url(base_url or s["base_url"])
    m = (model or "").strip() or s["model"]
    key = api_key or s["api_key"]
    return OpenAICompatibleProvider(model=m, api_key=key, base_url=bu, timeout=config.AI_REQUEST_TIMEOUT)


async def test_connection(req: dict[str, Any]) -> dict[str, Any]:
    s = effective()
    base_url = req.get("base_url") or s["base_url"]
    model = req.get("model") or s["model"]
    api_key = req.get("api_key") or s["api_key"]

    try:
        _validate_base_url(base_url)
    except ValueError as exc:
        return {"success": False, "code": "invalid_base_url", "message": str(exc)}
    if not api_key:
        return {"success": False, "code": "authentication_failed", "message": "未配置 API Key。"}
    if not model:
        return {"success": False, "code": "model_not_found", "message": "未配置模型名称。"}

    provider = _provider_for(base_url, model, api_key)
    try:
        await provider.chat(
            system="You are a connection checker. Respond with the single word OK.",
            messages=[{"role": "user", "content": "Reply only with OK."}],
            tools=[],
            response_format=None,
            temperature=0.0,
        )
        return {"success": True, "message": "连接成功。", "code": None}
    except AIProviderAuth:
        return {"success": False, "code": "authentication_failed", "message": "API Key 认证失败。"}
    except AIProviderRateLimit:
        return {"success": False, "code": "rate_limited", "message": "请求被限流，请稍后再试。"}
    except AIProviderTimeout:
        return {"success": False, "code": "timeout", "message": "请求超时。"}
    except AIProviderUnavailable:
        return {"success": False, "code": "provider_unavailable", "message": "无法连接模型服务商。"}
    except AIProviderMalformedResponse:
        return {"success": False, "code": "model_not_found", "message": "模型不存在或接口路径不正确。"}
    except Exception:
        return {"success": False, "code": "unknown_provider_error", "message": "连接模型服务商时发生意外错误。"}


async def list_models(req: dict[str, Any]) -> dict[str, Any]:
    s = effective()
    base_url = req.get("base_url") or s["base_url"]
    api_key = req.get("api_key") or s["api_key"]

    try:
        bu = _validate_base_url(base_url)
    except ValueError as exc:
        return {"models": [], "supported": False, "message": str(exc)}
    if not api_key:
        return {"models": [], "supported": False, "message": "未配置 API Key。"}

    try:
        async with httpx.AsyncClient(timeout=config.AI_REQUEST_TIMEOUT) as client:
            r = await client.get(f"{bu}/models", headers={"Authorization": f"Bearer {api_key}"})
            r.raise_for_status()
            data = r.json()
        ids = [m.get("id") for m in data.get("data", []) if isinstance(m, dict) and isinstance(m.get("id"), str)]
        return {"models": ids, "supported": True, "message": "模型列表获取成功。"}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (401, 403):
            return {"models": [], "supported": False, "message": "认证失败。"}
        if exc.response.status_code == 404:
            return {"models": [], "supported": False, "message": "该服务商不支持模型发现，请手动输入模型名称。"}
        return {"models": [], "supported": False, "message": "服务商返回错误。"}
    except (httpx.ConnectError, httpx.TimeoutException):
        return {"models": [], "supported": False, "message": "无法连接服务商。"}
    except Exception:
        return {"models": [], "supported": False, "message": "模型发现失败。"}