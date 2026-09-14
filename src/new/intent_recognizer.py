"""Intent recognition — harness step 1.

Loads the preset intent schema (``config/intent_schema.json``) and classifies the
latest user utterance into one of the configured intents. Pure standard library
only (no numpy / sklearn / jieba): local matching uses character bigram + cosine
similarity against each intent's ``examples`` / ``keywords``; when the local score
is below ``local_threshold`` it falls back to the configured LLM (schema-prompted
zero-shot) via the shared :class:`ModelProvider`. If both are unsure the result
falls back to the ``clarify_abstain`` intent so the harness can ask, never guess.

The returned :class:`IntentMatch` carries the routing policy the chat harness uses
to constrain downstream reasoning: which tools to expose, what system constraint to
inject, and what clarification to return when confidence is low.
"""
from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from . import config

# NOTE: ModelProvider is imported lazily inside _llm_classify so this module stays
# importable without httpx (httpx is only needed for the optional LLM fallback path).

logger = logging.getLogger("workbench.ai.intent")

_TOKEN_RE = re.compile(r"\s+")
_N = 2  # character n-gram size


def _normalize(text: str) -> str:
    return _TOKEN_RE.sub("", text or "")


def _char_ngrams(text: str, n: int = _N) -> Counter:
    s = _normalize(text)
    if len(s) == 0:
        return Counter()
    if len(s) < n:
        return Counter([s])
    return Counter(s[i : i + n] for i in range(len(s) - n + 1))


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    if not common:
        return 0.0
    num = sum(a[t] * b[t] for t in common)
    denom = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return num / denom if denom else 0.0


@dataclass
class IntentMatch:
    intent_id: str
    name_zh: str
    name_en: str
    category: str
    needs_data_context: bool
    tool_policy: str
    system_constraint: str
    clarification_prompt: str
    confidence: float
    source: str  # "local" | "llm" | "clarify"

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "name_zh": self.name_zh,
            "category": self.category,
            "needs_data_context": self.needs_data_context,
            "tool_policy": self.tool_policy,
            "confidence": round(self.confidence, 3),
            "source": self.source,
        }


class IntentRecognizer:
    def __init__(self, schema_path: Optional[Path] = None) -> None:
        self.schema_path = schema_path or config.INTENT_SCHEMA_PATH
        self._intents: list[dict[str, Any]] = []
        self._vectors: dict[str, list[Counter]] = {}
        self._local_threshold = 0.25
        self._global_confidence = 0.6
        self._llm_fallback = True
        self.load()

    def load(self) -> None:
        data = json.loads(self.schema_path.read_text(encoding="utf-8"))
        self._intents = data.get("intents", [])
        rec = data.get("recognition", {})
        self._local_threshold = float(rec.get("local_threshold", 0.25))
        self._global_confidence = float(rec.get("global_confidence", 0.6))
        self._llm_fallback = bool(rec.get("llm_fallback", True))
        self._vectors = {}
        for it in self._intents:
            docs = list(it.get("examples", [])) + list(it.get("keywords", []))
            self._vectors[it["id"]] = [_char_ngrams(d) for d in docs if d]

    # ---- local matching -------------------------------------------------
    def _local_best(self, text: str) -> tuple[Optional[dict[str, Any]], float]:
        qv = _char_ngrams(text)
        if not qv:
            return None, 0.0
        best_it, best_score = None, 0.0
        for it in self._intents:
            if it["id"] == "clarify_abstain":
                continue
            score = max((_cosine(qv, v) for v in self._vectors.get(it["id"], [])), default=0.0)
            if score > best_score:
                best_score, best_it = score, it
        return best_it, best_score

    # ---- llm fallback ---------------------------------------------------
    async def _llm_classify(self, text: str, provider: Optional[ModelProvider]) -> tuple[Optional[str], float]:
        if not self._llm_fallback:
            return None, 0.0
        if provider is None:
            try:
                from . import ai_settings

                provider = ai_settings.build_provider()
            except Exception as exc:  # noqa: BLE001 - unconfigured etc.
                logger.info("intent_llm_skip no_provider=%s", exc)
                return None, 0.0
        listing = "\n".join(f"- {i['id']}: {i['name_zh']}（{i['description']}）" for i in self._intents)
        system = (
            "你是意图分类器。根据用户问题，从给定意图列表中选择最匹配的一个，"
            '只返回 JSON：{"intent": "<意图id>", "confidence": <0到1的浮点数>}。不要解释。'
        )
        user = f"可选意图：\n{listing}\n\n用户输入：{text}\n\n返回 JSON。"
        try:
            turn = await provider.chat(
                system=system,
                messages=[{"role": "user", "content": user}],
                tools=[],
                response_format=None,
                temperature=0.0,
            )
        except Exception as exc:  # noqa: BLE001
            logger.info("intent_llm_error %s", exc)
            return None, 0.0
        try:
            obj = json.loads(self._extract_json(turn.content or ""))
        except Exception:
            return None, 0.0
        intent_id = obj.get("intent")
        try:
            confidence = float(obj.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        if not intent_id or intent_id not in {i["id"] for i in self._intents}:
            return None, 0.0
        return intent_id, confidence

    @staticmethod
    def _extract_json(content: str) -> str:
        s = content.find("{")
        e = content.rfind("}")
        if s == -1 or e == -1 or e <= s:
            return content
        return content[s : e + 1]

    # ---- public ---------------------------------------------------------
    def _match_for(self, intent_id: str) -> dict[str, Any]:
        for it in self._intents:
            if it["id"] == intent_id:
                return it
        return self._intents[-1]  # clarify_abstain fallback

    def _build(self, it: dict[str, Any], confidence: float, source: str) -> IntentMatch:
        return IntentMatch(
            intent_id=it["id"],
            name_zh=it.get("name_zh", it["id"]),
            name_en=it.get("name_en", ""),
            category=it.get("category", ""),
            needs_data_context=bool(it.get("needs_data_context", False)),
            tool_policy=it.get("tool_policy", "full"),
            system_constraint=it.get("system_constraint", ""),
            clarification_prompt=it.get("clarification_prompt", ""),
            confidence=confidence,
            source=source,
        )

    async def recognize(self, text: str, provider: Optional[ModelProvider] = None) -> IntentMatch:
        best_it, best_score = self._local_best(text)
        if best_it is not None and best_score >= self._local_threshold:
            return self._build(best_it, best_score, "local")

        llm_id, llm_conf = await self._llm_classify(text, provider)
        if llm_id is not None and llm_conf >= self._global_confidence:
            return self._build(self._match_for(llm_id), llm_conf, "llm")

        clarify = self._match_for("clarify_abstain")
        return self._build(clarify, best_score, "clarify")
