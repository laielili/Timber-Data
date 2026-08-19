"""Tools: get_monthly_performance, get_management_report_data."""
from __future__ import annotations

import sqlite3

from ...services.batches import assign_economic_quadrants, calculate_batch_metrics
from ...services.common import TimeContext, r2
from ...services.monthly import calculate_monthly
from ...services.overview import calculate_overview
from ...services.reports import calculate_report_data
from ...services.sources import calculate_source_performance
from ..registry import make_provenance, tool
from ..schemas import (
    ManagementReportToolInput,
    ManagementReportToolOutput,
    MonthlyPerformanceInput,
    MonthlyPerformanceOutput,
)


@tool(
    name="get_monthly_performance",
    description=(
        "Use this tool when the user asks how performance has changed over time — monthly "
        "incoming/processed timber, higher-value rate, costs, value, net value and month-end "
        "backlog for the selected period."
    ),
    business_question="How has performance changed over time?",
    input_schema=MonthlyPerformanceInput,
    output_schema=MonthlyPerformanceOutput,
)
def get_monthly_performance(inp: MonthlyPerformanceInput, conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    rows = calculate_monthly(conn, ctx)
    months = []
    for m in rows:
        months.append({
            "month": m["month"],
            "incoming_timber_t": m["incoming_timber_t"],
            "processed_timber_t": m["processed_timber_t"],
            "higher_value_recovery_rate": m["higher_value_recovery_rate"],
            "processing_cost_per_processed_t": m["processing_cost_per_processed_t"],
            "total_recovery_cost_per_incoming_t": r2(
                m["total_recovery_cost_aud"] / m["incoming_timber_t"]) if m["incoming_timber_t"] else 0.0,
            "recovered_value_per_t": m["recovered_value_per_t"],
            "net_recovery_value_per_t": m["net_recovery_value_per_t"],
            "sorting_backlog_t": m["sorting_backlog_t"],
            "inspection_backlog_t": m["inspection_backlog_t"],
            "processing_backlog_t": m["processing_backlog_t"],
            "unresolved_backlog_t": m["unresolved_backlog_t"],
        })
    return {"provenance": make_provenance(ctx), "months": months}


@tool(
    name="get_management_report_data",
    description=(
        "Use this tool when the user asks to assemble deterministic evidence for a management "
        "report — executive metrics, recovery, sorting economics, operations, risk/uncertainty, "
        "source performance, outlier batches and data limitations. No AI interpretation is added."
    ),
    business_question="Assemble deterministic evidence for a management report.",
    input_schema=ManagementReportToolInput,
    output_schema=ManagementReportToolOutput,
)
def get_management_report_data(inp: ManagementReportToolInput, conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    overview = calculate_overview(conn, ctx)
    metrics = calculate_batch_metrics(conn)
    assign_economic_quadrants(metrics)
    monthly = calculate_monthly(conn, ctx)
    realised_src, open_src = calculate_source_performance(conn, ctx, metrics)
    payload = calculate_report_data(conn, ctx, overview, metrics, monthly, realised_src, open_src)
    return {"provenance": make_provenance(ctx), "sections": payload["sections"]}
