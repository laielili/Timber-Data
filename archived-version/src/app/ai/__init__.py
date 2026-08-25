"""AI Analyst layer — Phase 02.

Real conversational analyst that connects ONE real LLM provider to the approved,
deterministic analyst tool layer.

Architecture (hard boundary — never bypassed):
    User → Ask Circular → AI Analyst → Analyst Tools → Python Analytics → SQLite

The LLM interprets. Python calculates. The model never sees raw SQLite, CSV,
filesystem, or writes. It may only call the 12 registered analyst tools via the
registry, each of which is validated, audited, and read-only.
"""
from __future__ import annotations

from .schemas import (
    AnalystContext,
    AnalystQueryRequest,
    AnalystResponse,
    EvidenceItem,
)
from .service import AnalystService

__all__ = [
    "AnalystContext",
    "AnalystQueryRequest",
    "AnalystResponse",
    "EvidenceItem",
    "AnalystService",
]
