"""Analyst service — ties the provider, orchestration, conversation memory, and audit
log together behind one async `query()` entry point.

Responsibilities:
- resolve the configured provider (server-side only — API key never leaves here);
- run the multi-round orchestration through the approved tool registry;
- ground evidence in tool outputs;
- keep short-lived, in-memory conversation continuity (no vector DB, no persistence);
- emit a separate AI audit log (no secrets, no full questions stored permanently).
"""
from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Any, Optional

from ..config import AI_MAX_HISTORY, AI_MODEL, AI_PROVIDER, AI_TEMPERATURE, AI_MAX_TOOL_ROUNDS
from ..analyst_tools.registry import REGISTRY
from .errors import AIAnalystError, AIProviderError
from .orchestration import (
    OrchestrationSettings,
    ToolExecutionRecord,
    build_response_format,
    orchestrate,
    validate_evidence,
)
from .prompts import SYSTEM_ROLE
from .provider import ModelProvider, build_provider
from .schemas import AnalystContext, AnalystQueryRequest, AnalystResponse

logger = logging.getLogger("cti.ai.service")
audit = logging.getLogger("cti.ai.audit")


class ConversationStore:
    """In-memory, short-lived conversation memory keyed by conversation_id.

    Only compact user/assistant text is retained (no tool JSON, no raw model output),
    capped at `max_messages` to prevent unbounded context growth.
    """

    def __init__(self, max_messages: int = AI_MAX_HISTORY) -> None:
        self._store: dict[str, list[dict[str, str]]] = {}
        self._lock = threading.Lock()
        self.max_messages = max_messages

    def get_or_create(self, conversation_id: Optional[str]) -> str:
        cid = conversation_id or f"conv_{uuid.uuid4().hex}"
        with self._lock:
            self._store.setdefault(cid, [])
        return cid

    def get_messages(self, conversation_id: str) -> list[dict[str, str]]:
        with self._lock:
            return list(self._store.get(conversation_id, []))

    def add_turn(self, conversation_id: str, user_text: str, assistant_summary: str) -> None:
        with self._lock:
            history = self._store.setdefault(conversation_id, [])
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": assistant_summary})
            # keep only the most recent messages
            if len(history) > self.max_messages:
                del history[: len(history) - self.max_messages]


def _assistant_summary(response: AnalystResponse) -> str:
    entities = ", ".join(response.entities[:6]) if response.entities else "—"
    return f"{response.conclusion} [tools: {', '.join(response.tools_used)}; entities: {entities}]"


class AnalystService:
    def __init__(self, provider: Optional[ModelProvider] = None, settings: Optional[OrchestrationSettings] = None) -> None:
        self.provider = provider
        self.settings = settings or OrchestrationSettings(
            max_tool_rounds=AI_MAX_TOOL_ROUNDS,
            temperature=AI_TEMPERATURE,
            max_history=AI_MAX_HISTORY,
            response_format=build_response_format(),
        )
        self.conversations = ConversationStore(max_messages=self.settings.max_history)

    @classmethod
    def from_config(cls) -> "AnalystService":
        provider = build_provider(
            model=AI_MODEL,
            api_key="",  # populated per-request from config in the router; '' when disabled
            base_url="",
        )
        return cls(provider=provider)

    async def query(
        self,
        request: AnalystQueryRequest,
        conn: Any,
        *,
        provider_override: Optional[ModelProvider] = None,
        api_key: str = "",
        base_url: str = "",
        model: str | None = None,
    ) -> AnalystResponse:
        """Run one analyst query. `provider_override` is used by tests; in production the
        provider is built from server configuration."""
        provider = provider_override or self.provider
        if provider is None:
            raise AIProviderError("No model provider is configured.")

        # tests may pass a provider that has no .model attribute; default gracefully
        provider_model = getattr(provider, "model", model or AI_MODEL)
        provider_name = AI_PROVIDER

        conversation_id = self.conversations.get_or_create(request.conversation_id)
        history = self.conversations.get_messages(conversation_id)

        started = time.perf_counter()
        tools_requested: list[str] = []
        records: list[ToolExecutionRecord] = []
        rounds = 0
        answer_status = "ok"
        try:
            parsed, records, rounds, tools_requested = await orchestrate(
                provider=provider,
                system=SYSTEM_ROLE,
                history=history,
                question=request.question,
                context=request.context,
                conn=conn,
                settings=self.settings,
            )
            verified_evidence, dropped = validate_evidence(parsed, records)
            tools_used = sorted({r.name for r in records if REGISTRY.get(r.name) is not None})
            response = self._build_response(
                parsed=parsed,
                verified_evidence=verified_evidence,
                dropped=dropped,
                question=request.question,
                conversation_id=conversation_id,
                tools_used=tools_used,
                rounds=rounds,
                model=provider_model,
                provider=provider_name,
            )
            self.conversations.add_turn(conversation_id, request.question, _assistant_summary(response))
            return response
        except AIAnalystError as exc:
            answer_status = exc.code
            raise
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            executed = [r.name for r in records if r.success]
            failed = [r.name for r in records if not r.success]
            audit.info(
                "analyst_request %s",
                {
                    "event": "analyst_request",
                    "conversation_id": conversation_id,
                    "question_length": len(request.question),
                    "model": provider_model,
                    "provider": provider_name,
                    "tools_requested": tools_requested,
                    "tools_executed": executed,
                    "tools_failed": failed,
                    "tool_rounds": rounds,
                    "duration_ms": duration_ms,
                    "answer_status": answer_status,
                },
            )

    @staticmethod
    def _build_response(
        *,
        parsed: dict[str, Any],
        verified_evidence: list[Any],
        dropped: int,
        question: str,
        conversation_id: str,
        tools_used: list[str],
        rounds: int,
        model: str,
        provider: str,
    ) -> AnalystResponse:
        limitation = str(parsed.get("data_limitation", ""))
        if dropped > 0:
            extra = f" {dropped} unsupported evidence claim(s) were removed because they could not be grounded in tool outputs."
            limitation = (limitation + extra).strip()
        entities = [str(e) for e in (parsed.get("entities") or [])]
        return AnalystResponse(
            answer_id=f"ans_{uuid.uuid4().hex}",
            question=question,
            conclusion=str(parsed.get("conclusion", "")),
            evidence=verified_evidence,
            business_implication=str(parsed.get("business_implication", "")),
            suggested_investigation=str(parsed.get("suggested_investigation", "")),
            data_limitation=limitation,
            tools_used=tools_used,
            entities=entities,
            confidence=str(parsed.get("confidence", "medium")),
            conversation_id=conversation_id,
            model=model or None,
            provider=provider or None,
            tool_rounds=rounds,
        )
