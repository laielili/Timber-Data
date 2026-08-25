"""Batch analytics service — lifecycle batch metrics, realised/provisional classification,
economic quadrants (computed dynamically from realised batches only), batch summaries."""
from __future__ import annotations

import sqlite3
import statistics
from typing import Optional

from ..repositories import batches as batches_repo, costs as costs_repo, recovery as recovery_repo
from .common import pct, r1, r2, r3

CORE_5 = ("Sorting Labour", "Inspection", "Processing", "Special Handling", "Disposal")


def calculate_batch_metrics(conn: sqlite3.Connection) -> list[dict]:
    """All 36 batch metrics, computed from raw tables (lifecycle basis — matches the
    approved dataset; batch economics are not period-filtered in this prototype)."""
    batches = batches_repo.get_batches(conn)
    out_by_batch = recovery_repo.get_outputs_by_batch(conn)
    mat_agg = batches_repo.get_material_aggregates(conn)
    cost_by_batch = costs_repo.get_core_costs_by_batch(conn)
    asm = costs_repo.get_assumptions(conn)

    feedstock_value = asm["board_feedstock_value_per_t"]
    baseline_processing = asm["baseline_processing_cost_per_t"]

    metrics: list[dict] = []
    for b in batches:
        bid = b["batch_id"]
        w = float(b["incoming_weight_t"])
        o = out_by_batch.get(bid, {})
        processed = float(o.get("processed_t", 0.0) or 0.0)
        hv = float(o.get("hv_t", 0.0) or 0.0)
        bf = float(o.get("bf_t", 0.0) or 0.0)
        sh = float(o.get("sh_t", 0.0) or 0.0)
        res = float(o.get("res_t", 0.0) or 0.0)
        gross = float(o.get("gross_aud", 0.0) or 0.0)

        ma = mat_agg.get(bid, {})
        unresolved_t = (ma.get("unresolved_kg", 0.0) or 0.0) / 1000.0
        insp_exposure_t = (ma.get("insp_exposure_kg", 0.0) or 0.0) / 1000.0
        downgraded_t = (ma.get("downgraded_kg", 0.0) or 0.0) / 1000.0

        cs = cost_by_batch.get(bid, {})
        sorting_cost = cs.get("Sorting Labour", 0.0)
        inspection_cost = cs.get("Inspection", 0.0)
        processing_cost = cs.get("Processing", 0.0)
        sh_cost = cs.get("Special Handling", 0.0)
        disposal_cost = cs.get("Disposal", 0.0)
        total_cost = sorting_cost + inspection_cost + processing_cost + sh_cost + disposal_cost

        net = gross - total_cost
        baseline_net = w * feedstock_value - w * baseline_processing
        nsb = net - baseline_net

        realised = b["batch_status"] == "Completed"

        metrics.append(
            {
                "batch_id": bid,
                "source_id": b["source_id"],
                "source_type": b["source_type"],
                "arrival_date": b["arrival_date"],
                "status": b["batch_status"],
                "scenario": None,  # scenario is a generator-memory field; not persisted in DB
                "notes": b["notes"],
                "incoming_weight_t": r1(w),
                "processed_weight_t": r3(processed),
                "higher_value_weight_t": r3(hv),
                "board_feedstock_weight_t": r3(bf),
                "special_handling_weight_t": r3(sh),
                "residual_weight_t": r3(res),
                "unresolved_weight_t": r3(unresolved_t),
                "higher_value_recovery_rate": pct(hv, processed),
                "sorting_cost_aud": r2(sorting_cost),
                "inspection_cost_aud": r2(inspection_cost),
                "processing_cost_aud": r2(processing_cost),
                "special_handling_cost_aud": r2(sh_cost),
                "disposal_cost_aud": r2(disposal_cost),
                "total_recovery_cost_aud": r2(total_cost),
                "gross_recovered_value_aud": r2(gross),
                "net_recovery_value_aud": r2(net),
                "net_recovery_value_per_t": r2(net / w) if w else 0.0,
                "processing_cost_per_t": r2(processing_cost / w) if w else 0.0,
                "total_recovery_cost_per_t": r2(total_cost / w) if w else 0.0,
                "recovered_value_per_t": r2(gross / processed) if processed else 0.0,
                "sorting_plus_inspection_cost_per_t": r2((sorting_cost + inspection_cost) / w) if w else 0.0,
                "baseline_net_value_aud": r2(baseline_net),
                "net_sorting_benefit_aud": r2(nsb),
                "inspection_exposure_rate": pct(insp_exposure_t, w),
                "unresolved_rate": pct(unresolved_t, w),
                "downgrade_rate": pct(downgraded_t, processed),
                "special_handling_rate": pct(sh, processed),
                "economic_evaluation_status": "Realised" if realised else "Provisional",
                "eligible_for_realised_comparison": realised,
            }
        )
    return metrics


def assign_economic_quadrants(metrics: list[dict]) -> tuple[float, float]:
    """Assign quadrants using medians computed from REALISED batches only.
    Provisional batches get economic_quadrant = None. Returns (median_x, median_y)."""
    realised = [m for m in metrics if m["eligible_for_realised_comparison"]]
    xs = sorted(m["sorting_plus_inspection_cost_per_t"] for m in realised)
    ys = sorted(m["recovered_value_per_t"] for m in realised)
    med_x = statistics.median(xs)
    med_y = statistics.median(ys)

    for m in metrics:
        if not m["eligible_for_realised_comparison"]:
            m["economic_quadrant"] = None
            continue
        x = m["sorting_plus_inspection_cost_per_t"]
        y = m["recovered_value_per_t"]
        if x <= med_x and y > med_y:
            q = "Efficient"
        elif x > med_x and y > med_y:
            q = "High-value / High-cost"
        elif x <= med_x and y <= med_y:
            q = "Commodity"
        else:
            q = "Review Required"
        m["economic_quadrant"] = q
    return med_x, med_y


def to_batch_summary(m: dict) -> dict:
    """Map an internal metric dict to the BatchSummary contract shape."""
    return {
        "batch_id": m["batch_id"],
        "source_id": m["source_id"],
        "source_type": m["source_type"],
        "arrival_date": m["arrival_date"],
        "status": m["status"],
        "incoming_weight_t": m["incoming_weight_t"],
        "processed_weight_t": m["processed_weight_t"],
        "higher_value_weight_t": m["higher_value_weight_t"],
        "board_feedstock_weight_t": m["board_feedstock_weight_t"],
        "special_handling_weight_t": m["special_handling_weight_t"],
        "residual_weight_t": m["residual_weight_t"],
        "unresolved_weight_t": m["unresolved_weight_t"],
        "higher_value_recovery_rate": m["higher_value_recovery_rate"],
        "sorting_cost_aud": m["sorting_cost_aud"],
        "inspection_cost_aud": m["inspection_cost_aud"],
        "processing_cost_aud": m["processing_cost_aud"],
        "total_recovery_cost_aud": m["total_recovery_cost_aud"],
        "gross_recovered_value_aud": m["gross_recovered_value_aud"],
        "net_recovery_value_aud": m["net_recovery_value_aud"],
        "net_recovery_value_per_t": m["net_recovery_value_per_t"],
        "sorting_plus_inspection_cost_per_t": m["sorting_plus_inspection_cost_per_t"],
        "net_sorting_benefit_aud": m["net_sorting_benefit_aud"],
        "inspection_exposure_rate": m["inspection_exposure_rate"],
        "unresolved_rate": m["unresolved_rate"],
        "downgrade_rate": m["downgrade_rate"],
        "economic_evaluation_status": m["economic_evaluation_status"],
        "eligible_for_realised_comparison": m["eligible_for_realised_comparison"],
        "economic_quadrant": m.get("economic_quadrant"),
        "scenario": m.get("scenario"),
        "notes": m.get("notes"),
    }


def get_batch_summary(conn: sqlite3.Connection, batch_id: str) -> Optional[dict]:
    """BatchSummary for a single batch, or None when the batch does not exist."""
    metrics = calculate_batch_metrics(conn)
    assign_economic_quadrants(metrics)
    for m in metrics:
        if m["batch_id"] == batch_id:
            return to_batch_summary(m)
    return None
