"""Management report service — deterministic structured data (no AI text).

Sections mirror the approved management_report_data.json contract. All values are
computed from the database via the overview / batches / monthly / sources services.
"""
from __future__ import annotations

import sqlite3
import statistics

from ..repositories import batches as batches_repo, costs as costs_repo
from ..repositories.operations import get_processing_event_timeline
from .. import config
from .common import TimeContext, build_meta, downgrade_rate, pct, r1, r2


def calculate_report_data(
    conn: sqlite3.Connection,
    ctx: TimeContext,
    overview: dict,
    metrics: list[dict],
    monthly: list[dict],
    realised_src: list[dict],
    open_src: list[dict],
) -> dict:
    ov = overview["kpis"]
    asm = costs_repo.get_assumptions(conn)

    # ---- recovery / economics / risk aggregates ----------------------------
    route = overview["charts"]["recovery_route_distribution"]
    processed = ov["processed_timber"]["value"]
    route_weights = {r["recovery_route"]: r["weight_t"] for r in route}

    realised_bm = [m for m in metrics if m["eligible_for_realised_comparison"]]
    neg_nsb = [m for m in metrics if m["net_sorting_benefit_aud"] < 0]
    neg_nsb_realised = [m for m in realised_bm if m["net_sorting_benefit_aud"] < 0]

    record_stats = batches_repo.get_record_stats_kg(conn)
    incoming_all = sum(m["incoming_weight_t"] for m in metrics)
    total_nsb = sum(m["net_sorting_benefit_aud"] for m in metrics)
    total_sorting = sum(m["sorting_cost_aud"] for m in metrics)
    total_inspection = sum(m["inspection_cost_aud"] for m in metrics)

    timeline = get_processing_event_timeline(conn)
    turnarounds = []
    for m in metrics:
        ev = timeline.get(m["batch_id"])
        if not ev or not ev.get("first_start"):
            continue
        if m["eligible_for_realised_comparison"]:
            if ev.get("last_end"):
                dur = (ev["last_end"] - ev["first_start"]).total_seconds() / 3600.0
            else:
                dur = (config.DATASET_AS_OF - ev["first_start"]).total_seconds() / 3600.0
        else:
            dur = (config.DATASET_AS_OF - ev["first_start"]).total_seconds() / 3600.0
        turnarounds.append(dur)

    b17 = next(m for m in metrics if m["batch_id"] == "B017")
    b30 = next(m for m in metrics if m["batch_id"] == "B030")

    sections = {
        "executive_metrics": {
            "net_recovery_value_per_t": overview["north_star"]["value"],
            "incoming_timber_t": ov["incoming_timber"]["value"],
            "processed_timber_t": ov["processed_timber"]["value"],
            "higher_value_recovery_rate": ov["higher_value_recovery_rate"]["value"],
            "processing_cost_per_processed_t": ov["processing_cost_per_processed_t"]["value"],
            "processing_cost_per_incoming_t": r2(
                sum(m["processing_cost_aud"] for m in metrics) / incoming_all
            ) if incoming_all else 0.0,
            "total_recovery_cost_per_incoming_t": r2(
                sum(m["total_recovery_cost_aud"] for m in metrics) / incoming_all
            ) if incoming_all else 0.0,
            "recovered_value_per_t": ov["recovered_value_per_t"]["value"],
            "unresolved_inspection_rate": ov["unresolved_inspection_rate"]["value"],
            "gross_recovered_value_aud": r2(sum(m["gross_recovered_value_aud"] for m in metrics)),
            "total_recovery_cost_aud": r2(sum(m["total_recovery_cost_aud"] for m in metrics)),
            "net_recovery_value_aud": r2(sum(m["net_recovery_value_aud"] for m in metrics)),
            "closed_batch_net_recovery_value_per_t": overview["north_star"].get(
                "closed_batch_net_recovery_value_per_t", 0.0
            ),
        },
        "recovery_performance": {
            "route_distribution": route,
            "board_feedstock_rate": pct(route_weights.get("Board Feedstock", 0.0), processed),
            "residual_rate": pct(route_weights.get("Residual / Disposal", 0.0), processed),
            "special_handling_rate": pct(route_weights.get("Special Handling", 0.0), processed),
            "downgrade_rate": downgrade_rate(metrics, processed),
        },
        "sorting_economics": {
            "negative_net_sorting_benefit_batch_count": len(neg_nsb),
            "negative_net_sorting_benefit_batches": [m["batch_id"] for m in neg_nsb],
            "negative_net_sorting_benefit_realised_count": len(neg_nsb_realised),
            "negative_net_sorting_benefit_realised_batches": [m["batch_id"] for m in neg_nsb_realised],
            "total_net_sorting_benefit_aud": r2(total_nsb),
            "net_sorting_benefit_per_t": r2(total_nsb / incoming_all) if incoming_all else 0.0,
            "sorting_cost_per_t": r2(total_sorting / incoming_all) if incoming_all else 0.0,
            "inspection_cost_per_t": r2(total_inspection / incoming_all) if incoming_all else 0.0,
            "top_by_net_sorting_benefit_realised": [
                {"batch_id": m["batch_id"], "net_sorting_benefit_aud": m["net_sorting_benefit_aud"]}
                for m in sorted(realised_bm, key=lambda x: x["net_sorting_benefit_aud"], reverse=True)[:5]
            ],
            "bottom_by_net_sorting_benefit_realised": [
                {"batch_id": m["batch_id"], "net_sorting_benefit_aud": m["net_sorting_benefit_aud"]}
                for m in sorted(realised_bm, key=lambda x: x["net_sorting_benefit_aud"])[:5]
            ],
        },
        "operations": {
            "throughput_t_per_day": r2(processed / 365.0),
            "average_batch_turnaround_hours": r1(statistics.mean(turnarounds)) if turnarounds else 0.0,
            "median_batch_turnaround_hours": r1(statistics.median(turnarounds)) if turnarounds else 0.0,
            "open_batch_count": sum(1 for m in metrics if not m["eligible_for_realised_comparison"]),
            "backlog": overview["charts"]["operational_backlog"],
        },
        "risk_uncertainty": {
            "unresolved_inspection_rate": ov["unresolved_inspection_rate"]["value"],
            "open_inspection_weight_t": r2(
                batches_repo.get_open_inspection_weight_kg(conn, ctx.as_of_month) / 1000.0
            ),
            "unresolved_weight_t": r2(
                batches_repo.get_material_state(conn, ctx.as_of_month).get("unresolved", 0.0) / 1000.0
            ),
            "complete_record_rate": pct(record_stats.get("complete_kg", 0.0), incoming_all * 1000.0),
            "partial_record_rate": pct(record_stats.get("partial_kg", 0.0), incoming_all * 1000.0),
            "critical_missing_rate": pct(record_stats.get("critical_kg", 0.0), incoming_all * 1000.0),
            "unknown_treatment_rate": pct(record_stats.get("unknown_treatment_kg", 0.0), incoming_all * 1000.0),
        },
        "source_performance": {
            "realised_source_performance": realised_src,
            "current_operational_exposure": open_src,
        },
        "outlier_batches": {
            "best_by_net_recovery_value_per_t_realised": [
                {"batch_id": m["batch_id"], "net_recovery_value_per_t": m["net_recovery_value_per_t"]}
                for m in sorted(realised_bm, key=lambda x: x["net_recovery_value_per_t"], reverse=True)[:3]
            ],
            "worst_by_net_sorting_benefit_realised": [
                {"batch_id": m["batch_id"], "net_sorting_benefit_aud": m["net_sorting_benefit_aud"]}
                for m in sorted(realised_bm, key=lambda x: x["net_sorting_benefit_aud"])[:3]
            ],
            "highest_unresolved_weight_t": [
                {"batch_id": m["batch_id"], "unresolved_weight_t": m["unresolved_weight_t"]}
                for m in sorted(metrics, key=lambda x: x["unresolved_weight_t"], reverse=True)[:3]
            ],
            "batch_17_sorting_plus_inspection_cost_per_t": b17["sorting_plus_inspection_cost_per_t"],
            "batch_30_provisional_exposure": {
                "economic_evaluation_status": b30["economic_evaluation_status"],
                "cost_incurred_to_date_aud": b30["total_recovery_cost_aud"],
                "unresolved_weight_t": b30["unresolved_weight_t"],
                "note": "In-progress recovery case: high provisional cost exposure and high unresolved workload; NOT a realised poor performer.",
            },
        },
        "data_limitations": [
            "All values are synthetic prototype assumptions; no real company, benchmark or market standard implied.",
            "No field claims structural safety, chemical safety or certification.",
            "North Star includes the economic effect of open/backlogged material; not accounting profit; short-period values can be volatile.",
            "Open / Partially Completed batches are labelled Provisional; their current negative values are cost-incurred-to-date vs value-realised-to-date, not final performance.",
            "Realised economic comparisons (ranking, quadrant medians) use Completed batches only.",
            "Month-end backlog snapshots are generator-computed states from raw event/inspection timelines.",
            "Comparison periods limited to what 2025 data supports (e.g. December vs November); no 2024 records fabricated.",
        ],
    }

    return {"meta": build_meta(ctx), "sections": sections}
