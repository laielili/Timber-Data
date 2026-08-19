"""Performance endpoints — management brief, source performance, monthly performance."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..dependencies import get_conn, get_time_context
from ..models.api import ManagementBriefResponse, MonthlyPerformanceResponse, SourcePerformanceResponse
from ..services.batches import assign_economic_quadrants, calculate_batch_metrics
from ..services.common import TimeContext, build_meta
from ..services.management_brief import calculate_management_brief
from ..services.monthly import calculate_monthly
from ..services.overview import calculate_overview
from ..services.sources import calculate_source_performance

router = APIRouter(prefix="/api/v1", tags=["performance"])


@router.get("/management-brief", response_model=ManagementBriefResponse, summary="Management brief")
def get_management_brief(
    conn: sqlite3.Connection = Depends(get_conn),
    ctx: TimeContext = Depends(get_time_context),
) -> ManagementBriefResponse:
    """Deterministic attention items (no LLM): B017 sorting economics, inspection backlog
    growth (computed), higher-value recovery vs prototype target."""
    overview = calculate_overview(conn, ctx)
    metrics = calculate_batch_metrics(conn)
    briefs = calculate_management_brief(conn, ctx, overview, metrics)
    return ManagementBriefResponse.model_validate({"meta": build_meta(ctx), "briefs": briefs})


@router.get("/source-performance", response_model=SourcePerformanceResponse, summary="Source performance")
def get_source_performance(
    conn: sqlite3.Connection = Depends(get_conn),
    ctx: TimeContext = Depends(get_time_context),
) -> SourcePerformanceResponse:
    """Two separate layers: realised source performance (completed only) and current
    operational exposure (non-completed only). Never merged into one profitability view."""
    metrics = calculate_batch_metrics(conn)
    realised_src, open_src = calculate_source_performance(conn, ctx, metrics)
    return SourcePerformanceResponse.model_validate({
        "meta": build_meta(ctx),
        "realised_source_performance": realised_src,
        "current_operational_exposure": open_src,
    })


@router.get("/monthly-performance", response_model=MonthlyPerformanceResponse, summary="Monthly performance")
def get_monthly_performance(
    conn: sqlite3.Connection = Depends(get_conn),
    ctx: TimeContext = Depends(get_time_context),
) -> MonthlyPerformanceResponse:
    """Twelve typed monthly rows (contract fields)."""
    months = calculate_monthly(conn, ctx)
    return MonthlyPerformanceResponse.model_validate({"meta": build_meta(ctx), "months": months})
