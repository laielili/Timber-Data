"""AI Analyst — offline tests (no paid/live model).

Driven by `FakeModelProvider` (scripted turns) so the full orchestration, tool
execution, evidence grounding, conversation memory, and error handling can be
exercised deterministically. Live provider tests live under `pytest -m live_ai`.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from pydantic import ValidationError

from app.ai.errors import AIProviderMalformedResponse, AIProviderTimeout
from app.ai.orchestration import MaxToolRoundsExceeded
from app.ai.provider import FakeModelProvider, ScriptedTurn, ToolCall
from app.ai.schemas import AnalystQueryRequest
from app.ai.service import AnalystService
from app.db import connect


# --------------------------------------------------------------------------- helpers


def _conn():
    return connect()


def run(coro):
    return asyncio.run(coro)


def synth(
    conclusion: str,
    evidence: list[dict[str, Any]],
    business_implication: str,
    suggested_investigation: str,
    data_limitation: str,
    entities: list[str] | None = None,
    confidence: str = "high",
) -> str:
    return json.dumps(
        {
            "conclusion": conclusion,
            "evidence": evidence,
            "business_implication": business_implication,
            "suggested_investigation": suggested_investigation,
            "data_limitation": data_limitation,
            "entities": entities or [],
            "confidence": confidence,
        }
    )


def b017_evidence() -> list[dict[str, Any]]:
    return [
        {"label": "Sorting + Inspection Cost", "value": "229.52", "unit": "AUD/t",
         "source_tool": "get_batch_details", "batch_id": "B017", "time_basis": "realised"},
        {"label": "Net sorting benefit", "value": "-6172.24", "unit": "AUD",
         "source_tool": "get_batch_details", "batch_id": "B017", "time_basis": "realised"},
        {"label": "Net recovery value", "value": "-75.22", "unit": "AUD/t",
         "source_tool": "get_batch_details", "batch_id": "B017", "time_basis": "realised"},
        {"label": "Status", "value": "Realised", "source_tool": "get_batch_details", "batch_id": "B017"},
        {"label": "Quadrant", "value": "Review Required", "source_tool": "get_batch_details", "batch_id": "B017"},
    ]


# --------------------------------------------------------------------------- request validation


def test_request_rejects_empty_question():
    with pytest.raises(ValidationError):
        AnalystQueryRequest(question="   ")


def test_request_rejects_overlong_question():
    with pytest.raises(ValidationError):
        AnalystQueryRequest(question="x" * 2001)


def test_request_accepts_normal_question():
    req = AnalystQueryRequest(question="Why is Batch 17 underperforming?")
    assert req.question == "Why is Batch 17 underperforming?"


# --------------------------------------------------------------------------- tool selection


def test_b017_tool_selection_and_grounding():
    provider = FakeModelProvider(
        [
            ScriptedTurn(tool_calls=[ToolCall("c1", "get_batch_details", {"batch_id": "B017"})]),
            ScriptedTurn(
                content=synth(
                    conclusion="Batch 17 has weak realised sorting economics.",
                    evidence=b017_evidence(),
                    business_implication="Detailed sorting cost more than it returned for this completed batch.",
                    suggested_investigation="Compare B017 with B006/B023 and review sorting hours.",
                    data_limitation="Prototype economics only.",
                    entities=["B017", "Residential Demolition"],
                    confidence="high",
                )
            ),
        ]
    )
    req = AnalystQueryRequest(question="Why is Batch 17 underperforming?")
    resp = run(AnalystService().query(req, _conn(), provider_override=provider))

    assert "get_batch_details" in resp.tools_used
    assert resp.prototype is True
    assert resp.confidence in {"high", "medium", "low"}
    assert resp.conversation_id
    # exact grounded numbers survived validation
    values = {e.value for e in resp.evidence}
    assert "229.52" in values
    assert "-6172.24" in values
    assert "-75.22" in values
    assert any(e.batch_id == "B017" and e.value == "Review Required" for e in resp.evidence)


def test_multi_tool_overview_and_source():
    provider = FakeModelProvider(
        [
            ScriptedTurn(
                tool_calls=[
                    ToolCall("c1", "get_overview_metrics", {}),
                    ToolCall("c2", "get_source_performance", {}),
                ]
            ),
            ScriptedTurn(
                content=synth(
                    conclusion="North Star is 85.08 AUD/t; Infrastructure Salvage leads realised recovery.",
                    evidence=[
                        {"label": "North Star", "value": "85.08", "unit": "AUD/t", "source_tool": "get_overview_metrics"},
                        {"label": "Inspection backlog", "value": "104.09", "unit": "t", "source_tool": "get_operational_backlog"},
                    ],
                    business_implication="Recovery is healthy overall but inspection is the bottleneck.",
                    suggested_investigation="Review inspection capacity.",
                    data_limitation="Prototype data.",
                    entities=["Infrastructure Salvage"],
                    confidence="high",
                )
            ),
        ]
    )
    req = AnalystQueryRequest(question="How are we doing overall?")
    resp = run(AnalystService().query(req, _conn(), provider_override=provider))
    assert {"get_overview_metrics", "get_source_performance"}.issubset(set(resp.tools_used))


# --------------------------------------------------------------------------- unknown / failed tools


def test_unknown_tool_is_not_counted_as_used():
    provider = FakeModelProvider(
        [
            ScriptedTurn(
                tool_calls=[
                    ToolCall("c1", "get_batch_details", {"batch_id": "B017"}),
                    ToolCall("c2", "unknown_tool", {}),
                ]
            ),
            ScriptedTurn(
                content=synth(
                    conclusion="B017 underperforms on sorting economics.",
                    evidence=b017_evidence(),
                    business_implication="x", suggested_investigation="x",
                    data_limitation="x", entities=["B017"], confidence="medium",
                )
            ),
        ]
    )
    req = AnalystQueryRequest(question="Why is Batch 17 underperforming?")
    resp = run(AnalystService().query(req, _conn(), provider_override=provider))
    assert "unknown_tool" not in resp.tools_used
    assert "get_batch_details" in resp.tools_used


def test_tool_failure_is_handled_gracefully():
    provider = FakeModelProvider(
        [
            ScriptedTurn(tool_calls=[ToolCall("c1", "get_batch_details", {"batch_id": "B999"})]),
            ScriptedTurn(
                content=synth(
                    conclusion="The requested batch was not found in the dataset.",
                    evidence=[],
                    business_implication="Check the batch id.",
                    suggested_investigation="Re-run with a valid batch id.",
                    data_limitation="Tool returned no data.",
                    entities=["B999"], confidence="low",
                )
            ),
        ]
    )
    req = AnalystQueryRequest(question="Tell me about B999")
    resp = run(AnalystService().query(req, _conn(), provider_override=provider))
    assert resp is not None
    assert "get_batch_details" in resp.tools_used


# --------------------------------------------------------------------------- guardrails


def test_max_tool_rounds_exceeded():
    provider = FakeModelProvider([ScriptedTurn(tool_calls=[ToolCall("c1", "get_batch_details", {"batch_id": "B017"})])] * 10)
    req = AnalystQueryRequest(question="Loop forever")
    with pytest.raises(MaxToolRoundsExceeded):
        run(AnalystService().query(req, _conn(), provider_override=provider))


def test_provider_error_propagates_cleanly():
    class RaisingProvider:
        async def chat(self, *, system, messages, tools, response_format, temperature):
            raise AIProviderTimeout("timed out")

    req = AnalystQueryRequest(question="Anything")
    with pytest.raises(AIProviderTimeout):
        run(AnalystService().query(req, _conn(), provider_override=RaisingProvider()))


# --------------------------------------------------------------------------- evidence validator


def test_evidence_validator_drops_unsupported_claims():
    bad_evidence = b017_evidence() + [
        {"label": "Magic metric", "value": "99999.99", "unit": "AUD/t",
         "source_tool": "get_batch_details", "batch_id": "B017"},
    ]
    provider = FakeModelProvider(
        [
            ScriptedTurn(tool_calls=[ToolCall("c1", "get_batch_details", {"batch_id": "B017"})]),
            ScriptedTurn(
                content=synth(
                    conclusion="B017 underperforms.",
                    evidence=bad_evidence,
                    business_implication="x", suggested_investigation="x",
                    data_limitation="Prototype only.", entities=["B017"], confidence="medium",
                )
            ),
        ]
    )
    req = AnalystQueryRequest(question="Why is Batch 17 underperforming?")
    resp = run(AnalystService().query(req, _conn(), provider_override=provider))
    assert not any("99999.99" in e.value for e in resp.evidence)
    assert "unsupported evidence" in resp.data_limitation.lower()


def test_malformed_synthesis_raises():
    provider = FakeModelProvider(
        [
            ScriptedTurn(tool_calls=[ToolCall("c1", "get_batch_details", {"batch_id": "B017"})]),
            ScriptedTurn(content="this is not json at all"),
        ]
    )
    req = AnalystQueryRequest(question="Why is Batch 17 underperforming?")
    with pytest.raises(AIProviderMalformedResponse):
        run(AnalystService().query(req, _conn(), provider_override=provider))


# --------------------------------------------------------------------------- conversation continuity


def test_conversation_continuity_references_prior_batches():
    provider = FakeModelProvider(
        [
            ScriptedTurn(tool_calls=[ToolCall("c1", "get_batch_details", {"batch_id": "B017"})]),
            ScriptedTurn(
                content=synth(
                    conclusion="B017 underperforms on sorting.",
                    evidence=b017_evidence(),
                    business_implication="x", suggested_investigation="x",
                    data_limitation="x", entities=["B017"], confidence="high",
                )
            ),
            ScriptedTurn(tool_calls=[ToolCall("c2", "compare_batches", {"batch_ids": ["B017", "B022"]})]),
            ScriptedTurn(
                content=synth(
                    conclusion="B017 has higher sorting+inspection cost per tonne than B022.",
                    evidence=[
                        {"label": "B017 S+I/t", "value": "229.52", "unit": "AUD/t", "source_tool": "compare_batches", "batch_id": "B017"},
                        {"label": "B022 S+I/t", "value": "54.54", "unit": "AUD/t", "source_tool": "compare_batches", "batch_id": "B022"},
                    ],
                    business_implication="B022 is far more efficient.",
                    suggested_investigation="Investigate B017 sorting intensity.",
                    data_limitation="Realised comparison only.", entities=["B017", "B022"], confidence="high",
                )
            ),
        ]
    )
    svc = AnalystService()
    req1 = AnalystQueryRequest(question="Why is Batch 17 underperforming?")
    resp1 = run(svc.query(req1, _conn(), provider_override=provider))
    req2 = AnalystQueryRequest(question="Which one had higher inspection cost?", conversation_id=resp1.conversation_id)
    resp2 = run(svc.query(req2, _conn(), provider_override=provider))

    # the follow-up reached the same conversation
    assert resp2.conversation_id == resp1.conversation_id
    assert "compare_batches" in resp2.tools_used
    # the second query's first model call received the prior question in its history
    second_tool_call_messages = provider.calls[2]["messages"]
    joined = " ".join(str(m.get("content", "")) for m in second_tool_call_messages)
    assert "Why is Batch 17 underperforming?" in joined


# --------------------------------------------------------------------------- provisional reasoning (B030)


def test_b030_provisional_not_ranked_as_final():
    provider = FakeModelProvider(
        [
            ScriptedTurn(tool_calls=[ToolCall("c1", "get_batch_details", {"batch_id": "B017"})]),
            ScriptedTurn(tool_calls=[ToolCall("c2", "get_batch_details", {"batch_id": "B030"})]),
            ScriptedTurn(
                content=synth(
                    conclusion=(
                        "B030 has high cost exposure but its economics are PROVISIONAL, so it must not be "
                        "ranked as a final realised loser alongside B017."
                    ),
                    evidence=[
                        {"label": "B017 status", "value": "Realised", "source_tool": "get_batch_details", "batch_id": "B017"},
                        {"label": "B030 status", "value": "Provisional", "source_tool": "get_batch_details", "batch_id": "B030"},
                        {"label": "B030 eligible", "value": "False", "source_tool": "get_batch_details", "batch_id": "B030"},
                    ],
                    business_implication="Compare B030's current exposure separately from realised performance.",
                    suggested_investigation="Resolve B030 records before any economic ranking.",
                    data_limitation="B030 provisional; not a final realised result.",
                    entities=["B017", "B030"], confidence="high",
                )
            ),
        ]
    )
    req = AnalystQueryRequest(question="Is B030 worse than B017?")
    resp = run(AnalystService().query(req, _conn(), provider_override=provider))
    assert "get_batch_details" in resp.tools_used
    assert "provisional" in resp.conclusion.lower()
    assert any(e.batch_id == "B030" and e.value == "Provisional" for e in resp.evidence)
    # B030 must not be assigned a final economic quadrant (it is None in the data)
    assert not any(e.batch_id == "B030" and e.label == "Quadrant" and e.value not in ("", "None", "null") for e in resp.evidence)


@pytest.mark.live_ai
def test_live_provider_end_to_end():
    """Optional live test. Runs only with AI_LIVE_TEST=1 and valid AI_API_KEY.

    Not part of the default suite; validates a real provider round-trip.
    """
    import os

    if os.environ.get("AI_LIVE_TEST") != "1" or not os.environ.get("AI_API_KEY"):
        pytest.skip("Live AI test disabled (set AI_LIVE_TEST=1 and AI_API_KEY).")

    from app.ai.provider import build_provider
    from app.config import AI_BASE_URL, AI_MODEL

    provider = build_provider(model=AI_MODEL, api_key=os.environ["AI_API_KEY"], base_url=AI_BASE_URL)
    req = AnalystQueryRequest(question="How are we doing overall?")
    resp = run(AnalystService().query(req, _conn(), provider_override=provider))
    assert resp.conclusion
    assert resp.prototype is True
