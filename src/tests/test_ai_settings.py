"""AI Provider Settings — backend tests (offline; no live model API).

Covers: safe responses never leak the key, save/preserve/replace/delete key,
invalid base URL rejection, fake-provider connection success, clean auth-error
mapping, and that no secret reaches the frontend. Uses a temp secrets directory
so the real backend/.secrets is never touched.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.ai.errors import AIProviderAuth
from app.ai.provider import ModelTurn
from app.main import app
from app.ai import settings as settings_mod

SECRETS_MODULE = "app.ai.settings"


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Route secret storage to a temp dir and return a TestClient."""
    monkeypatch.setattr(f"{SECRETS_MODULE}.SECRETS_DIR", tmp_path)
    monkeypatch.setattr(f"{SECRETS_MODULE}.SETTINGS_FILE", tmp_path / "ai_provider.json")
    return TestClient(app)


async def _fake_chat_ok(self, *, system, messages, tools, response_format, temperature):
    return ModelTurn(content="OK", tool_calls=[])


def _fake_chat_auth(self, *, system, messages, tools, response_format, temperature):
    raise AIProviderAuth("rejected")


# --------------------------------------------------------------------------- GET safe
def test_get_safe_settings_never_contains_api_key(client):
    r = client.get("/api/v1/settings/ai")
    assert r.status_code == 200
    body = r.json()
    assert "api_key" not in body
    assert body["api_key_configured"] is False
    assert body["source"] == "defaults"
    assert body["provider"] == "openai-compatible"
    assert body["base_url"] == "https://api.openai.com/v1"


# --------------------------------------------------------------------------- save + key
def test_save_stores_key_server_side_and_reports_configured(client):
    r = client.put(
        "/api/v1/settings/ai",
        json={"enabled": True, "provider": "openai-compatible", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "api_key": "sk-SUPER-SECRET"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["api_key_configured"] is True
    assert "api_key" not in body  # never returned

    # The key must exist only in the server-side file, never in any response.
    raw = json.loads((settings_mod.SETTINGS_FILE).read_text())
    assert raw["api_key"] == "sk-SUPER-SECRET"

    # Subsequent GET still never reveals it.
    g = client.get("/api/v1/settings/ai").json()
    assert g["api_key_configured"] is True
    assert "api_key" not in g


def test_update_model_without_key_preserves_saved_key(client):
    client.put(
        "/api/v1/settings/ai",
        json={"enabled": True, "provider": "openai-compatible", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "api_key": "sk-ORIGINAL"},
    )
    # Update only model + enabled, omit api_key.
    r = client.put(
        "/api/v1/settings/ai",
        json={"enabled": True, "provider": "openai-compatible", "base_url": "https://api.openai.com/v1", "model": "gpt-4o"},
    )
    assert r.status_code == 200
    assert r.json()["api_key_configured"] is True

    raw = json.loads((settings_mod.SETTINGS_FILE).read_text())
    assert raw["api_key"] == "sk-ORIGINAL"  # preserved
    assert raw["model"] == "gpt-4o"          # updated


def test_replace_key_works(client):
    client.put(
        "/api/v1/settings/ai",
        json={"enabled": True, "provider": "openai-compatible", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "api_key": "sk-OLD"},
    )
    r = client.put(
        "/api/v1/settings/ai",
        json={"enabled": True, "provider": "openai-compatible", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "api_key": "sk-NEW"},
    )
    assert r.status_code == 200
    raw = json.loads((settings_mod.SETTINGS_FILE).read_text())
    assert raw["api_key"] == "sk-NEW"


def test_delete_key_works(client):
    client.put(
        "/api/v1/settings/ai",
        json={"enabled": True, "provider": "openai-compatible", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "api_key": "sk-TO-DELETE"},
    )
    assert client.get("/api/v1/settings/ai").json()["api_key_configured"] is True

    d = client.delete("/api/v1/settings/ai/key")
    assert d.status_code == 200
    assert d.json() == {"api_key_configured": False}
    assert client.get("/api/v1/settings/ai").json()["api_key_configured"] is False

    raw = json.loads((settings_mod.SETTINGS_FILE).read_text())
    assert "api_key" not in raw


# --------------------------------------------------------------------------- validation
def test_invalid_base_url_rejected(client):
    r = client.put(
        "/api/v1/settings/ai",
        json={"enabled": True, "provider": "openai-compatible", "base_url": "ftp://nope", "model": "gpt-4o-mini", "api_key": "sk-x"},
    )
    assert r.status_code == 422
    assert client.get("/api/v1/settings/ai").json()["api_key_configured"] is False


def test_local_http_base_url_accepted(client):
    r = client.put(
        "/api/v1/settings/ai",
        json={"enabled": True, "provider": "openai-compatible", "base_url": "http://localhost:11434/v1", "model": "llama3", "api_key": "sk-x"},
    )
    assert r.status_code == 200
    assert r.json()["base_url"] == "http://localhost:11434/v1"


# --------------------------------------------------------------------------- test connection
def test_test_connection_success_with_fake_provider(client, monkeypatch):
    monkeypatch.setattr(f"{SECRETS_MODULE}.OpenAICompatibleProvider.chat", _fake_chat_ok)
    r = client.post(
        "/api/v1/settings/ai/test",
        json={"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "api_key": "sk-x"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["provider_reachable"] is True
    assert body["model_available"] is True
    # No secret in the response.
    assert "api_key" not in body
    assert "sk-" not in json.dumps(body)


def test_test_connection_auth_error_mapped_cleanly(client, monkeypatch):
    monkeypatch.setattr(f"{SECRETS_MODULE}.OpenAICompatibleProvider.chat", _fake_chat_auth)
    r = client.post(
        "/api/v1/settings/ai/test",
        json={"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "api_key": "sk-BAD"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["code"] == "authentication_failed"
    assert "api_key" not in body
    assert "sk-" not in json.dumps(body)


def test_test_connection_invalid_base_url(client):
    r = client.post(
        "/api/v1/settings/ai/test",
        json={"base_url": "not-a-url", "model": "gpt-4o-mini", "api_key": "sk-x"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["code"] == "invalid_base_url"


def test_test_connection_missing_key(client):
    r = client.post(
        "/api/v1/settings/ai/test",
        json={"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["code"] == "authentication_failed"


# --------------------------------------------------------------------------- analyst gating
def test_analyst_query_disabled_when_not_configured(client):
    r = client.post(
        "/api/v1/analyst/query",
        json={"question": "How are we doing overall?"},
    )
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "ai_disabled"
    # No key leaked.
    assert "sk-" not in json.dumps(r.json())
