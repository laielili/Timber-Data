"""Tools: get_operational_backlog, get_uncertainty_distribution."""
from __future__ import annotations

import sqlite3

from ...repositories import batches as batches_repo
from ...services.batches import calculate_batch_metrics
from ...services.common import TimeContext, pct, r2
from ...services.overview import calculate_overview
from ..registry import make_provenance, tool
from ..schemas import (
    OperationalBacklogInput,
    OperationalBacklogOutput,
    UncertaintyInput,
    UncertaintyOutput,
)


_BUCKET_KEY = {
    "sorting": "sorting_backlog_t",
    "inspection": "inspection_backlog_t",
    "processing": "processing_backlog_t",
    "unresolved": "unresolved_backlog_t",
}


def _buckets_from_state(state: dict) -> dict[str, float]:
    return {
        "sorting_backlog_t": r2(state.get("sorting", 0.0) / 1000.0),
        "inspection_backlog_t": r2(state.get("inspection", 0.0) / 1000.0),
        "processing_backlog_t": r2(state.get("processing", 0.0) / 1000.0),
        "unresolved_backlog_t": r2(state.get("unresolved", 0.0) / 1000.0),
    }


@tool(
    name="get_operational_backlog",
    description=(
        "Use this tool when the user asks where material is currently stuck: sorting / "
        "inspection / processing / unresolved backlog at a snapshot, total open weight, open "
        "batch count, or how the inspection backlog changed versus the previous month."
    ),
    business_question="Where is material currently stuck?",
    input_schema=OperationalBacklogInput,
    output_schema=OperationalBacklogOutput,
)
def get_operational_backlog(inp: OperationalBacklogInput, conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    state = batches_repo.get_material_state(conn, ctx.as_of_month)
    buckets = _buckets_from_state(state)
    total_open = r2(sum(buckets.values()))

    metrics = calculate_batch_metrics(conn)
    open_batch_count = sum(1 for m in metrics if not m["eligible_for_realised_comparison"])

    # comparison to the previous month, only when the dataset supports it (TIME_SEMANTICS:
    # supported comparisons are Dec vs Nov and earlier real month pairs; never invented).
    comparison = None
    prev_month = _previous_month(ctx.as_of_month)
    if prev_month is not None:
        prev_state = batches_repo.get_material_state(conn, prev_month)
        prev_buckets = _buckets_from_state(prev_state)
        # change computed from unrounded kg for precision, then rounded for display
        comparison = {
            "previous_snapshot": prev_buckets,
            "change_absolute": {
                k: r2(buckets[k] - prev_buckets[k]) for k in buckets
            },
            "change_percent": {
                k: (r2((state.get(bucket, 0.0) - prev_state.get(bucket, 0.0)) / prev_state.get(bucket, 0.0) * 100)
                    if prev_state.get(bucket, 0.0) else None)
                for bucket, k in _BUCKET_KEY.items()
            },
        }

    return {
        "provenance": make_provenance(ctx),
        "as_of_date": ctx.as_of_date_str,
        "buckets": buckets,
        "total_open_weight_t": total_open,
        "open_batch_count": open_batch_count,
        "comparison": comparison,
    }


def _previous_month(month_key: str):
    year, month = int(month_key[:4]), int(month_key[5:7])
    if month == 1:
        return None  # January 2025 has no supported previous month in the dataset
    return f"{year:04d}-{month - 1:02d}"


@tool(
    name="get_uncertainty_distribution",
    description=(
        "Use this tool when the user asks where operational uncertainty is concentrated: record "
        "completeness, unknown or conflicting treatment information, open inspections, unresolved "
        "weight, and the most uncertain batches or source types. Unknown treatment information "
        "does NOT establish structural or chemical unsafety."
    ),
    business_question="Where is operational uncertainty concentrated?",
    input_schema=UncertaintyInput,
    output_schema=UncertaintyOutput,
)
def get_uncertainty_distribution(inp: UncertaintyInput, conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    ov = calculate_overview(conn, ctx)
    incoming = ov["kpis"]["incoming_timber"]["value"]
    metrics = calculate_batch_metrics(conn)

    record_stats = batches_repo.get_record_stats_kg(conn)
    treatment_weights = batches_repo.get_treatment_status_weights_kg(conn)
    state = batches_repo.get_material_state(conn, ctx.as_of_month)
    open_insp_kg = batches_repo.get_open_inspection_weight_kg(conn, ctx.as_of_month)

    total_kg = incoming * 1000.0
    unresolved_t = state.get("unresolved", 0.0) / 1000.0
    open_insp_t = open_insp_kg / 1000.0

    top_batches = sorted(
        metrics, key=lambda m: (m["unresolved_rate"], m["inspection_exposure_rate"]), reverse=True
    )[:5]

    # source-level unresolved rate (weight-based)
    by_source: dict[str, dict] = {}
    for m in metrics:
        d = by_source.setdefault(m["source_type"], {"unresolved": 0.0, "incoming": 0.0})
        d["unresolved"] += m["unresolved_weight_t"]
        d["incoming"] += m["incoming_weight_t"]
    top_sources = sorted(
        ({"source_type": st, "unresolved_rate": pct(d["unresolved"], d["incoming"])}
         for st, d in by_source.items()),
        key=lambda x: x["unresolved_rate"],
        reverse=True,
    )[:5]

    return {
        "provenance": make_provenance(ctx),
        "record_quality": {
            "complete_record_rate": pct(record_stats.get("complete_kg", 0.0), total_kg),
            "partial_record_rate": pct(record_stats.get("partial_kg", 0.0), total_kg),
            "critical_missing_rate": pct(record_stats.get("critical_kg", 0.0), total_kg),
        },
        "treatment": {
            "unknown_treatment_rate": pct(treatment_weights.get("Unknown", 0.0), total_kg),
            "conflicting_record_rate": pct(treatment_weights.get("Conflicting Record", 0.0), total_kg),
        },
        "operational": {
            "open_inspection_rate": pct(open_insp_t, incoming),
            "unresolved_rate": pct(unresolved_t, incoming),
        },
        "top_uncertainty_batches": [
            {
                "batch_id": m["batch_id"],
                "unresolved_rate": m["unresolved_rate"],
                "inspection_exposure_rate": m["inspection_exposure_rate"],
                "economic_evaluation_status": m["economic_evaluation_status"],
            }
            for m in top_batches
        ],
        "top_uncertainty_sources": top_sources,
        "limitation": "Unknown treatment information does not establish structural or chemical unsafety.",
    }
