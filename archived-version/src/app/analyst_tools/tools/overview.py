"""Tools: get_overview_metrics, get_recovery_performance."""
from __future__ import annotations

import sqlite3

from ...services.batches import calculate_batch_metrics
from ...services.common import TimeContext, downgrade_rate, pct, r2
from ...services.monthly import calculate_monthly
from ...services.overview import calculate_overview
from ..registry import make_provenance, tool
from ..schemas import (
    OverviewMetricsInput,
    OverviewMetricsOutput,
    RecoveryPerformanceInput,
    RecoveryPerformanceOutput,
)


@tool(
    name="get_overview_metrics",
    description=(
        "Use this tool when the user asks for the overall management picture: the North Star "
        "(Net Recovery Value / t), the six executive KPIs, total cost/value/net, or how the "
        "business is performing for a selected period."
    ),
    business_question="What is the current overall management picture?",
    input_schema=OverviewMetricsInput,
    output_schema=OverviewMetricsOutput,
)
def get_overview_metrics(inp: OverviewMetricsInput, conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    ov = calculate_overview(conn, ctx)
    ns = ov["north_star"]
    k = ov["kpis"]
    totals = ov["totals"]
    return {
        "provenance": make_provenance(ctx),
        "time_basis": "selected_period",
        "north_star": {
            "value": ns["value"],
            "unit": "AUD/t",
            "basis": "selected_period",
            "closed_batch_net_recovery_value_per_t": ns["closed_batch_net_recovery_value_per_t"],
        },
        "kpis": {
            "incoming_timber_t": k["incoming_timber"]["value"],
            "processed_timber_t": k["processed_timber"]["value"],
            "higher_value_recovery_rate": k["higher_value_recovery_rate"]["value"],
            "processing_cost_per_processed_t": k["processing_cost_per_processed_t"]["value"],
            "recovered_value_per_t": k["recovered_value_per_t"]["value"],
            "unresolved_inspection_rate": k["unresolved_inspection_rate"]["value"],
        },
        "totals": {
            "total_recovery_cost_aud": totals["total_recovery_cost_aud"],
            "gross_recovered_value_aud": totals["gross_recovered_value_aud"],
            "net_recovery_value_aud": totals["net_recovery_value_aud"],
        },
        "prototype_target": {
            "higher_value_recovery_target_pct": ov["prototype_target_pct"],
            "note": "Read from the Assumptions table; prototype target, not an industry benchmark.",
        },
    }


@tool(
    name="get_recovery_performance",
    description=(
        "Use this tool when the user asks how reclaimed timber recovery is performing: route "
        "distribution (higher-value / board feedstock / special handling / residual), recovery "
        "rates, downgrade rate, or monthly recovery trends."
    ),
    business_question="How is reclaimed timber recovery performing?",
    input_schema=RecoveryPerformanceInput,
    output_schema=RecoveryPerformanceOutput,
)
def get_recovery_performance(inp: RecoveryPerformanceInput, conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    ov = calculate_overview(conn, ctx)
    routes = {r["recovery_route"]: r for r in ov["charts"]["recovery_route_distribution"]}
    processed = ov["kpis"]["processed_timber"]["value"]

    metrics = calculate_batch_metrics(conn)
    monthly = calculate_monthly(conn, ctx)

    return {
        "provenance": make_provenance(ctx),
        "processed_weight_t": processed,
        "routes": {
            "higher_value_weight_t": routes["Higher-value Recovery"]["weight_t"],
            "board_feedstock_weight_t": routes["Board Feedstock"]["weight_t"],
            "special_handling_weight_t": routes["Special Handling"]["weight_t"],
            "residual_weight_t": routes["Residual / Disposal"]["weight_t"],
        },
        "rates": {
            "higher_value_recovery_rate": routes["Higher-value Recovery"]["percentage"],
            "board_feedstock_rate": routes["Board Feedstock"]["percentage"],
            "special_handling_rate": routes["Special Handling"]["percentage"],
            "residual_rate": routes["Residual / Disposal"]["percentage"],
            "downgrade_rate": downgrade_rate(metrics, processed),
        },
        "monthly_recovery_performance": [
            {
                "month": m["month"],
                "processed_timber_t": m["processed_timber_t"],
                "higher_value_recovery_rate": m["higher_value_recovery_rate"],
            }
            for m in monthly
        ],
    }
