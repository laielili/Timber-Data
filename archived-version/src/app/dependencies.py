"""FastAPI dependencies: read-only DB session + validated time context."""
from __future__ import annotations

import sqlite3
from datetime import date
from typing import Iterator, Optional

from fastapi import HTTPException

from .db import session
from .services.common import TimeContext, resolve_time_context


def get_conn() -> Iterator[sqlite3.Connection]:
    with session() as conn:
        yield conn


def get_time_context(
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    as_of: Optional[str] = None,
) -> TimeContext:
    """Parse/validate period + snapshot query parameters; invalid -> HTTP 422."""
    try:
        return resolve_time_context(period_start, period_end, as_of)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
