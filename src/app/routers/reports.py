"""GET /api/v1/management-report-data — deterministic structured report (no AI text)."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..dependencies import get_conn, get_time_context
from ..models.api import ManagementReportData
from ..services.batches import assign_economic_quadrants, calculate_batch_metrics
from ..services.common import TimeContext
from ..services.monthly import calculate_monthly
from ..services.overview import calculate_overview
from ..services.reports import calculate_report_data
from ..services.sources import calculate_source_performance

router = APIRouter(prefix="/api/v1", tags=["reports"])


@router.get("/management-report-data", response_model=ManagementReportData, summary="Management report data")
def get_management_report_data(
    conn: sqlite3.Connection = Depends(get_conn),
    ctx: TimeContext = Depends(get_time_context),
) -> ManagementReportData:
    """Structured sections for future report generation / AI analyst / portfolio demo."""
    overview = calculate_overview(conn, ctx)
    metrics = calculate_batch_metrics(conn)
    assign_economic_quadrants(metrics)
    monthly = calculate_monthly(conn, ctx)
    realised_src, open_src = calculate_source_performance(conn, ctx, metrics)
    payload = calculate_report_data(conn, ctx, overview, metrics, monthly, realised_src, open_src)
    return ManagementReportData.model_validate(payload)
