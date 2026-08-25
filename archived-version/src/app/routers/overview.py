"""GET /api/v1/overview — North Star, six KPIs, six chart datasets."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..dependencies import get_conn, get_time_context
from ..models.api import OverviewResponse
from ..services.common import TimeContext
from ..services.overview import calculate_overview

router = APIRouter(prefix="/api/v1", tags=["overview"])


@router.get("/overview", response_model=OverviewResponse, summary="Executive overview")
def get_overview(
    conn: sqlite3.Connection = Depends(get_conn),
    ctx: TimeContext = Depends(get_time_context),
) -> OverviewResponse:
    """North Star + the six approved Overview KPIs + the six chart datasets.

    Default request (no parameters) reproduces the approved prototype dataset:
    period 2025-01-01..2025-12-31, snapshot 2025-12-31T18:00:00.
    """
    return OverviewResponse.model_validate(calculate_overview(conn, ctx))
