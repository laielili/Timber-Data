"""AI analyst error hierarchy.

All errors here are INTERNAL — they are converted to clean structured HTTP
responses at the router boundary. No API key, raw HTTP body, or stack trace is
ever propagated to the frontend.
"""
from __future__ import annotations

from typing import Optional


class AIAnalystError(Exception):
    """Base class for AI analyst errors.

    `status_code` maps to the HTTP status returned to the frontend.
    `code` is a stable machine-readable identifier (never contains secrets).
    """

    status_code: int = 500
    code: str = "ai_analyst_error"

    def __init__(self, message: str, *, code: Optional[str] = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class AIProviderError(AIAnalystError):
    """Base class for upstream model-provider failures."""

    status_code = 502
    code = "ai_provider_error"


class AIProviderTimeout(AIProviderError):
    status_code = 504
    code = "ai_provider_timeout"


class AIProviderRateLimit(AIProviderError):
    status_code = 429
    code = "ai_provider_rate_limit"


class AIProviderAuth(AIProviderError):
    status_code = 502
    code = "ai_provider_auth"


class AIProviderUnavailable(AIProviderError):
    status_code = 503
    code = "ai_provider_unavailable"


class AIProviderMalformedResponse(AIProviderError):
    status_code = 502
    code = "ai_provider_malformed_response"


class InvalidAnalystRequest(AIAnalystError):
    """The user question/context failed request validation (e.g. empty/over-long)."""

    status_code = 422
    code = "invalid_analyst_request"


class UnknownToolRequested(AIAnalystError):
    """The model requested a tool name that is not in the registry."""

    status_code = 502
    code = "unknown_tool_requested"


class ToolExecutionFailed(AIAnalystError):
    """A requested approved tool returned a structured failure."""

    status_code = 502
    code = "tool_execution_failed"


class MaxToolRoundsExceeded(AIAnalystError):
    """The model exceeded the safety cap on sequential tool-call rounds."""

    status_code = 502
    code = "max_tool_rounds_exceeded"


class EvidenceValidationError(AIAnalystError):
    """Final answer evidence could not be grounded in tool outputs."""

    status_code = 502
    code = "evidence_validation_error"
