"""Tools: get_sorting_economics, get_batch_economics."""
from __future__ import annotations

import sqlite3

from ...services.batches import assign_economic_quadrants, calculate_batch_metrics
from ...services.common import TimeContext, r2
from ...services.overview import calculate_overview
from ..registry import make_provenance, tool
from ..schemas import BatchEconomicsInput, BatchEconomicsOutput, SortingEconomicsInput, SortingEconomicsOutput

BASELINE_DEFINITION = (
    "Prototype all-feedstock counterfactual: baseline net value = incoming t x "
    "(board feedstock value/t - baseline processing cost/t), read from the Assumptions table."
)
METRIC_LIMITATION = (
    "Net sorting benefit is a prototype counterfactual metric, not an industry financial standard."
)


@tool(
    name="get_sorting_economics",
    description=(
        "Use this tool when the user asks whether detailed sorting is economically worthwhile: "
        "how many realised batches have positive vs negative net sorting benefit, totals, cost "
        "per tonne, and the best/worst batches. Optionally filter by source type or include "
        "provisional batches."
    ),
    business_question="Is detailed sorting economically worthwhile?",
    input_schema=SortingEconomicsInput,
    output_schema=SortingEconomicsOutput,
)
def get_sorting_economics(inp: SortingEconomicsInput, conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    ov = calculate_overview(conn, ctx)
    chart_rows = ov["charts"]["net_sorting_benefit"]  # sorted DESC by nsb, includes eligibility

    selected = chart_rows
    if inp.realised_only:
        selected = [r for r in selected if r["eligible_for_realised_comparison"]]
    if inp.source_type is not None:
        selected = [r for r in selected if r["source_type"] == inp.source_type]

    positive = [r for r in selected if r["net_sorting_benefit_aud"] > 0]
    negative = [r for r in selected if r["net_sorting_benefit_aud"] < 0]
    total_nsb = sum(r["net_sorting_benefit_aud"] for r in selected)
    total_incoming = sum(r["incoming_weight_t"] for r in selected)
    realised_in_scope = sum(1 for r in selected if r["eligible_for_realised_comparison"])

    # cost per tonne over the same scope (aggregation of approved per-batch values)
    metrics = calculate_batch_metrics(conn)
    scope_ids = {r["batch_id"] for r in selected}
    scope_metrics = [m for m in metrics if m["batch_id"] in scope_ids]
    sorting_cost_per_t = r2(
        sum(m["sorting_cost_aud"] for m in scope_metrics) / total_incoming) if total_incoming else 0.0
    inspection_cost_per_t = r2(
        sum(m["inspection_cost_aud"] for m in scope_metrics) / total_incoming) if total_incoming else 0.0

    return {
        "provenance": make_provenance(ctx),
        "scope": {
            "realised_only": inp.realised_only,
            "source_type": inp.source_type,
            "batch_count": len(selected),
            "note": "Net sorting benefit is lifecycle-based per batch (matches the approved dataset).",
        },
        "results": {
            "realised_batch_count": realised_in_scope,
            "positive_sorting_benefit_count": len(positive),
            "negative_sorting_benefit_count": len(negative),
            "total_net_sorting_benefit_aud": r2(total_nsb),
            "average_net_sorting_benefit_per_t": r2(total_nsb / total_incoming) if total_incoming else 0.0,
            "sorting_cost_per_t": sorting_cost_per_t,
            "inspection_cost_per_t": inspection_cost_per_t,
        },
        "top_positive_batches": [
            {"batch_id": r["batch_id"], "net_sorting_benefit_aud": r["net_sorting_benefit_aud"]}
            for r in selected[:5] if r["net_sorting_benefit_aud"] > 0
        ],
        "top_negative_batches": [
            {"batch_id": r["batch_id"], "net_sorting_benefit_aud": r["net_sorting_benefit_aud"]}
            for r in sorted(selected, key=lambda x: x["net_sorting_benefit_aud"])[:5]
            if r["net_sorting_benefit_aud"] < 0
        ],
        "baseline_definition": BASELINE_DEFINITION,
        "metric_limitation": METRIC_LIMITATION,
    }


@tool(
    name="get_batch_economics",
    description=(
        "Use this tool when the user asks which completed batches are efficient, high-value/"
        "high-cost, commodity, or review-required, or when they ask about the economic quadrant "
        "benchmark (medians are computed from realised batches only)."
    ),
    business_question="Which completed batches are high-cost, high-value, efficient or review-required?",
    input_schema=BatchEconomicsInput,
    output_schema=BatchEconomicsOutput,
)
def get_batch_economics(inp: BatchEconomicsInput, conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    metrics = calculate_batch_metrics(conn)
    med_x, med_y = assign_economic_quadrants(metrics)

    points = []
    for m in metrics:
        if not m["eligible_for_realised_comparison"] and not inp.include_provisional:
            continue
        points.append({
            "batch_id": m["batch_id"],
            "source_type": m["source_type"],
            "sorting_plus_inspection_cost_per_t": m["sorting_plus_inspection_cost_per_t"],
            "recovered_value_per_t": m["recovered_value_per_t"],
            "incoming_weight_t": m["incoming_weight_t"],
            "economic_quadrant": m["economic_quadrant"],
        })

    return {
        "provenance": make_provenance(ctx),
        "benchmark": {
            "realised_median_x": r2(med_x),
            "realised_median_y": r2(med_y),
            "note": "Medians computed from realised (completed) batches only.",
        },
        "batches": points,
    }
