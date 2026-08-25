"""Analyst tool error types — structured errors the future LLM can consume
(no stack traces)."""
from __future__ import annotations


class ToolError(Exception):
    """Base class for deterministic tool errors."""

    code = "ToolError"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class BatchNotFound(ToolError):
    code = "BatchNotFound"


class InvalidPeriod(ToolError):
    code = "InvalidPeriod"


class UnsupportedPrototypeDateRange(ToolError):
    code = "UnsupportedPrototypeDateRange"


class InsufficientComparableData(ToolError):
    code = "InsufficientComparableData"


class InvalidInput(ToolError):
    code = "InvalidInput"
