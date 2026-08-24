"""Dashboard endpoints — KPIs + charts with dimension filters."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Query

from .. import dashboard_service
from ..dependencies import get_conn
from ..schemas import FilterParams

router = APIRouter(prefix="/api/new", tags=["dashboard"])


@router.get("/dashboard", summary="数据看板（带维度筛选）")
def get_dashboard(
    conn: sqlite3.Connection = Depends(get_conn),
    period_start: str | None = Query(None, description="起始日期 YYYY-MM-DD"),
    period_end: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    source_type: str | None = Query(None),
    region: str | None = Query(None),
    species: str | None = Query(None),
    material_form: str | None = Query(None),
    recovery_route: str | None = Query(None),
    batch_status: str | None = Query(None),
    current_stage: str | None = Query(None),
):
    f = FilterParams(
        period_start=period_start,
        period_end=period_end,
        source_type=source_type,
        region=region,
        species=species,
        material_form=material_form,
        recovery_route=recovery_route,
        batch_status=batch_status,
        current_stage=current_stage,
    )
    return dashboard_service.get_dashboard(conn, f)


@router.get("/dashboard/dimensions", summary="各筛选维度的可选值")
def get_dimensions(conn: sqlite3.Connection = Depends(get_conn)):
    dims = dashboard_service.get_dimensions(conn)
    dims["period_start"], dims["period_end"] = dashboard_service.get_period_bounds(conn)
    return dims