"""Typed request/response models for the AI analyst endpoint.

The final `AnalystResponse` is the ONLY shape the frontend renders. It is produced
by the orchestration layer (model synthesis → Pydantic validation) and carries
structured evidence with provenance so the UI never trusts unvalidated model text.
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from ..config import AI_MAX_QUESTION_LEN

# --------------------------------------------------------------------------- request


class AnalystContext(BaseModel):
    """Frontend-supplied context. Helps the analyst interpret deixis ("this batch")
    but is NEVER treated as authoritative numerical evidence. Period fields default
    to the approved prototype dataset when omitted."""

    period_start: Optional[date] = None
    period_end: Optional[date] = None
    as_of: Optional[str] = None
    current_page: Optional[str] = None
    selected_batch_id: Optional[str] = None


class AnalystQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=AI_MAX_QUESTION_LEN)
    context: AnalystContext = Field(default_factory=AnalystContext)
    conversation_id: Optional[str] = None

    @field_validator("question")
    @classmethod
    def _strip(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("question must not be empty")
        return stripped


# --------------------------------------------------------------------------- response


class EvidenceItem(BaseModel):
    """One grounded evidence row. `value`/`unit` should derive from a tool result;
    `source_tool` + `batch_id` link it back to deterministic evidence."""

    label: str
    value: str
    unit: Optional[str] = None
    source_tool: Optional[str] = None
    batch_id: Optional[str] = None
    time_basis: Optional[str] = None


class AnalystResponse(BaseModel):
    """Structured management answer. Maps directly onto the approved Ask Circular
    visual sections (Conclusion / Evidence / Business implication / Suggested
    investigation / Data limitation)."""

    answer_id: str
    question: str
    conclusion: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    business_implication: str
    suggested_investigation: str
    data_limitation: str
    tools_used: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"
    prototype: Literal[True] = True
    conversation_id: str
    model: Optional[str] = None
    provider: Optional[str] = None
    tool_rounds: Optional[int] = None


class AnalystErrorResponse(BaseModel):
    """Clean structured error returned to the frontend when AI analysis fails.

    Never contains API keys, raw HTTP bodies, or stack traces.
    """

    status: Literal["error"] = "error"
    code: str
    message: str
    conversation_id: Optional[str] = None
    prototype: Literal[True] = True
