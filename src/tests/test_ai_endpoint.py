"""AI Analyst endpoint integration tests (HTTP layer).

Covers the POST /api/v1/analyst/query contract: disabled-mode clean error, live-mode
structured answer, and that no API key / stack trace leaks to the client.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.ai.provider import FakeModelProvider, ScriptedTurn, ToolCall
from app.ai.settings import AIProviderSettings, AISettingsService
from app.main import app


def _synth():
    return json.dumps(
        {
            "conclusion": "Batch 17 underperforms on realised sorting economics.",
            "evidence": [
                {"label": "Sorting + Inspection Cost", "value": "229.52", "unit": "AUD/t",
                 "source_tool": "get_batch_details", "batch_id": "B017", "time_basis": "realised"},
                {"label": "Net sorting benefit", "value": "-6172.24", "unit": "AUD",
                 "source_tool": "get_batch_details", "batch_id": "B017", "time_basis": "realised"},
            ],
            "business_implication": "Sorting cost exceeded returned value for this completed batch.",
            "suggested_investigation": "Compare B017 with similar residential-demolition batches.",
            "data_limitation": "Prototype economics only.",
            "entities": ["B017"],
            "confidence": "high",
        }
    )


def _fake_factory(script):
    return lambda: FakeModelProvider(script)


def _settings(enabled: bool) -> AIProviderSettings:
    return AIProviderSettings(
        enabled=enabled,
        provider="openai-compatible",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        api_key="sk-test" if enabled else "",
        source="environment",
        timeout=60.0,
        temperature=0.1,
        max_tool_rounds=6,
    )


def test_disabled_endpoint_returns_clean_error():
    client = TestClient(app)
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(AISettingsService, "effective", staticmethod(lambda: _settings(False)))
        r = client.post("/api/v1/analyst/query", json={"question": "Why is Batch 17 underperforming?"})
    assert r.status_code == 503
    body = r.json()
    assert body["detail"]["code"] == "ai_disabled"
    assert body["detail"]["prototype"] is True
    # no secret leakage
    assert "api_key" not in json.dumps(body).lower()


def test_live_endpoint_returns_structured_answer():
    script = [
        ScriptedTurn(tool_calls=[ToolCall("c1", "get_batch_details", {"batch_id": "B017"})]),
        ScriptedTurn(content=_synth()),
    ]
    client = TestClient(app)
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(AISettingsService, "effective", staticmethod(lambda: _settings(True)))
        mp.setattr(AISettingsService, "build_provider_from_settings", staticmethod(_fake_factory(script)))
        r = client.post("/api/v1/analyst/query", json={"question": "Why is Batch 17 underperforming?"})
    assert r.status_code == 200
    body = r.json()
    assert body["conclusion"]
    assert "get_batch_details" in body["tools_used"]
    assert body["prototype"] is True
    assert body["conversation_id"]


def test_endpoint_rejects_empty_question():
    client = TestClient(app)
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(AISettingsService, "effective", staticmethod(lambda: _settings(True)))
        r = client.post("/api/v1/analyst/query", json={"question": "   "})
    assert r.status_code == 422
