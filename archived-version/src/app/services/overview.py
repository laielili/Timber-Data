"""Overview analytics service — North Star, six KPIs and six chart datasets,
all computed from the approved SQLite database with selected-period/snapshot semantics."""
from __future__ import annotations

import sqlite3

from ..repositories import batches as batches_repo, costs as costs_repo, recovery as recovery_repo
from ..repositories.operations import get_months
from . import batches as batches_service
from .common import TimeContext, build_meta, make_kpi, pct, r1, r2, r3

ROUTE_ORDER = ["Higher-value Recovery", "Board Feedstock", "Special Handling", "Residual / Disposal"]
BACKLOG_ORDER = ["Sorting", "Inspection", "Processing", "Unresolved"]
BUCKET_TO_STAGE = {"sorting": "Sorting", "inspection": "Inspection", "processing": "Processing", "unresolved": "Unresolved"}


def calculate_overview(conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    ps, pe, as_of = ctx.iso()

    # ---- flow aggregates (selected period) ---------------------------------
    incoming = batches_repo.get_incoming_in_period(conn, ps, pe)
    outputs = recovery_repo.get_outputs_in_period(conn, ctx.period_start, ctx.period_end)
    processed = sum(o["weight_t"] for o in outputs)
    hv = sum(o["weight_t"] for o in outputs if o["recovery_route"] == "Higher-value Recovery")
    gross = sum(o["gross_value_aud"] for o in outputs)

    costs_by_month = costs_repo.get_costs_by_month(conn, ctx.period_start, ctx.period_end)
    total_cost = sum(c["core_total_aud"] for c in costs_by_month)
    proc_cost = sum(c["processing_aud"] for c in costs_by_month)
    net = gross - total_cost

    # ---- snapshot metrics (as_of) ------------------------------------------
    state = batches_repo.get_material_state(conn, ctx.as_of_month)
    unresolved_w = state.get("unresolved", 0.0) / 1000.0
    open_insp_w = batches_repo.get_open_inspection_weight_kg(conn, ctx.as_of_month) / 1000.0
    union_w = batches_repo.get_unresolved_union_weight_kg(conn, ctx.as_of_month) / 1000.0

    # ---- batch-level metrics (lifecycle; needed for charts 04/06 + closed companion)
    metrics = batches_service.calculate_batch_metrics(conn)
    med_x, med_y = batches_service.assign_economic_quadrants(metrics)
    closed = [m for m in metrics if m["eligible_for_realised_comparison"]]
    closed_incoming = sum(m["incoming_weight_t"] for m in closed)
    closed_net = sum(m["net_recovery_value_aud"] for m in closed)

    # ---- prototype target from database assumptions (never hard-coded) ------
    asm = costs_repo.get_assumptions(conn)
    hv_target = asm["higher_value_recovery_target_pct"]

    # ---- charts -------------------------------------------------------------
    chart01 = _chart01(conn, ctx, processed)
    chart02 = _chart02(conn, ctx, ps, pe)
    chart03 = _chart03(state, ctx)
    chart04 = _chart04(metrics)
    chart05 = _chart05(costs_by_month, conn, ctx)
    chart06 = _chart06(metrics)

    # ---- KPIs / North Star --------------------------------------------------
    north_star_value = r2(net / incoming) if incoming else 0.0
    north_star = make_kpi(
        "net_recovery_value_per_t", "Net Recovery Value / t", north_star_value, "AUD/t",
        "selected_period",
        "Net commercial recovery value generated to date, after core recovery costs, "
        "per tonne of timber entering the operation within the selected prototype period.",
        "positive" if north_star_value > 0 else "neutral",
    )
    north_star["closed_batch_net_recovery_value_per_t"] = (
        r2(closed_net / closed_incoming) if closed_incoming else 0.0
    )
    north_star["closed_batch_basis"] = "completed batches only (analytical companion)"

    kpis = {
        "incoming_timber": make_kpi("incoming_timber", "Incoming Timber", r1(incoming), "t",
                                    "selected_period", "Total batch incoming weight within the selected period."),
        "processed_timber": make_kpi("processed_timber", "Processed Timber", r3(processed), "t",
                                     "selected_period", "Total recovered output weight within the selected period."),
        "higher_value_recovery_rate": make_kpi(
            "higher_value_recovery_rate", "Higher-value Recovery Rate", pct(hv, processed), "%",
            "selected_period", "Higher-value recovered output weight / total processed output weight.",
            "positive" if processed and hv * 100.0 / processed >= hv_target else "neutral"),
        "processing_cost_per_processed_t": make_kpi(
            "processing_cost_per_processed_t", "Processing Cost / t",
            r2(proc_cost / processed) if processed else 0.0, "AUD/t", "selected_period",
            "Direct processing cost per tonne of timber processed (denominator = processed output weight, not incoming)."),
        "recovered_value_per_t": make_kpi(
            "recovered_value_per_t", "Recovered Value / t",
            r2(gross / processed) if processed else 0.0, "AUD/t", "selected_period",
            "Gross recovered output value / processed output weight."),
        "unresolved_inspection_rate": make_kpi(
            "unresolved_inspection_rate", "Unresolved / Inspection Rate",
            pct(union_w, incoming), "%", "snapshot",
            "Weight of materials unresolved OR under open inspection at as_of, / incoming t (union, no double counting)."),
    }

    return {
        "meta": build_meta(ctx),
        "north_star": north_star,
        "kpis": kpis,
        "charts": {
            "recovery_route_distribution": chart01,
            "incoming_vs_processed": chart02,
            "operational_backlog": chart03,
            "net_sorting_benefit": chart04,
            "cost_vs_recovered_value": chart05,
            "batch_economics": chart06,
        },
        "_quadrant_medians": {"median_x": med_x, "median_y": med_y},
        # internal aggregates reused by the analyst tool layer (stripped from API
        # responses by response_model; single source of truth for totals).
        "totals": {
            "total_recovery_cost_aud": r2(total_cost),
            "gross_recovered_value_aud": r2(gross),
            "net_recovery_value_aud": r2(net),
        },
        "prototype_target_pct": hv_target,
    }


# --------------------------------------------------------------------------- chart builders


def _chart01(conn, ctx, processed) -> list[dict]:
    route_rows = {r["recovery_route"]: float(r["weight_t"]) for r in
                  recovery_repo.get_outputs_by_route(conn, ctx.period_start, ctx.period_end)}
    rows = []
    for route in ROUTE_ORDER:
        w = route_rows.get(route, 0.0)
        rows.append({"recovery_route": route, "weight_t": r2(w), "percentage": pct(w, processed)})
    return rows


def _chart02(conn, ctx, ps, pe) -> list[dict]:
    incoming_by_month = batches_repo.get_incoming_by_month(conn, ps, pe)
    out_by_month = {r["month"]: r for r in recovery_repo.get_outputs_by_month(conn, ctx.period_start, ctx.period_end)}
    months = [m for m in get_months(conn) if ps[:7] <= m <= pe[:7]]
    rows = []
    for mk in months:
        rows.append({
            "month": mk,
            "incoming_timber_t": r1(incoming_by_month.get(mk, 0.0)),
            "processed_timber_t": r3(out_by_month.get(mk, {}).get("processed_t", 0.0) or 0.0),
        })
    return rows


def _chart03(state: dict, ctx: TimeContext) -> list[dict]:
    weights = {stage: state.get(bucket, 0.0) / 1000.0 for bucket, stage in BUCKET_TO_STAGE.items()}
    open_total = sum(weights.values())
    return [
        {
            "backlog_stage": stage,
            "weight_t": r2(weights[stage]),
            "percentage_of_open_weight": pct(weights[stage], open_total),
            "as_of_date": ctx.as_of_date_str,
        }
        for stage in BACKLOG_ORDER
    ]


def _chart04(metrics: list[dict]) -> list[dict]:
    rows = sorted(metrics, key=lambda m: m["net_sorting_benefit_aud"], reverse=True)
    return [
        {
            "batch_id": m["batch_id"],
            "source_type": m["source_type"],
            "incoming_weight_t": m["incoming_weight_t"],
            "net_sorting_benefit_aud": m["net_sorting_benefit_aud"],
            "net_sorting_benefit_per_t": r2(m["net_sorting_benefit_aud"] / m["incoming_weight_t"])
            if m["incoming_weight_t"] else 0.0,
            "economic_evaluation_status": m["economic_evaluation_status"],
            "eligible_for_realised_comparison": m["eligible_for_realised_comparison"],
        }
        for m in rows
    ]


def _chart05(costs_by_month, conn, ctx) -> list[dict]:
    cost_map = {c["month"]: c for c in costs_by_month}
    out_map = {r["month"]: r for r in recovery_repo.get_outputs_by_month(conn, ctx.period_start, ctx.period_end)}
    months = [m for m in get_months(conn) if ctx.period_start.isoformat()[:7] <= m <= ctx.period_end.isoformat()[:7]]
    rows = []
    for mk in months:
        cost = cost_map.get(mk, {}).get("core_total_aud", 0.0) or 0.0
        gross = out_map.get(mk, {}).get("gross_aud", 0.0) or 0.0
        rows.append({
            "month": mk,
            "total_recovery_cost_aud": r2(cost),
            "gross_recovered_value_aud": r2(gross),
            "net_recovery_value_aud": r2(gross - cost),
        })
    return rows


def _chart06(metrics: list[dict]) -> list[dict]:
    rows = sorted(metrics, key=lambda m: m["batch_id"])
    return [
        {
            "batch_id": m["batch_id"],
            "source_type": m["source_type"],
            "scenario": m.get("scenario"),
            "sorting_plus_inspection_cost_per_t": m["sorting_plus_inspection_cost_per_t"],
            "recovered_value_per_t": m["recovered_value_per_t"],
            "incoming_weight_t": m["incoming_weight_t"],
            "economic_quadrant": m["economic_quadrant"],
            "economic_evaluation_status": m["economic_evaluation_status"],
            "eligible_for_realised_comparison": m["eligible_for_realised_comparison"],
        }
        for m in rows
    ]
