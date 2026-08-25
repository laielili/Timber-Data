"""Tools: get_batch_details, compare_batches, find_batches."""
from __future__ import annotations

import sqlite3

from ...services.batches import assign_economic_quadrants, calculate_batch_metrics, get_batch_summary
from ...services.common import TimeContext, r2
from ..errors import BatchNotFound, InsufficientComparableData
from ..registry import make_provenance, tool
from ..schemas import (
    BatchDetailsInput,
    BatchDetailsOutput,
    CompareBatchesInput,
    CompareBatchesOutput,
    FindBatchesInput,
    FindBatchesOutput,
)

_BATCH_SUMMARY_TO_EVIDENCE = {
    "batch_id", "source_id", "source_type", "arrival_date", "status", "incoming_weight_t",
    "processed_weight_t", "higher_value_weight_t", "board_feedstock_weight_t",
    "special_handling_weight_t", "residual_weight_t", "unresolved_weight_t",
    "higher_value_recovery_rate", "sorting_cost_aud", "inspection_cost_aud",
    "processing_cost_aud", "total_recovery_cost_aud", "gross_recovered_value_aud",
    "net_recovery_value_aud", "net_recovery_value_per_t", "sorting_plus_inspection_cost_per_t",
    "net_sorting_benefit_aud", "inspection_exposure_rate", "unresolved_rate", "downgrade_rate",
    "economic_evaluation_status", "eligible_for_realised_comparison", "economic_quadrant",
    "scenario", "notes",
}


@tool(
    name="get_batch_details",
    description=(
        "Use this tool when the user asks about one specific batch — its status, recovery "
        "performance, cost, value, uncertainty, economic quadrant, or whether its economics "
        "are realised or provisional. Requires a batch id such as B017."
    ),
    business_question="What is happening with a specific batch?",
    input_schema=BatchDetailsInput,
    output_schema=BatchDetailsOutput,
)
def get_batch_details(inp: BatchDetailsInput, conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    summary = get_batch_summary(conn, inp.batch_id)
    if summary is None:
        raise BatchNotFound(f"Batch {inp.batch_id} not found.")
    realised = summary["economic_evaluation_status"] == "Realised"
    evidence = {k: summary[k] for k in _BATCH_SUMMARY_TO_EVIDENCE if k in summary}
    evidence["evidence_status"] = "realised" if realised else "provisional"
    evidence["economics_note"] = (
        "Realised economics — final for the period; eligible for realised comparison."
        if realised
        else "Provisional economics — values are cost/value realised to date; not final performance."
    )
    return {"provenance": make_provenance(ctx), "batch": evidence}


@tool(
    name="compare_batches",
    description=(
        "Use this tool when the user asks to compare two or more batches (2-10) on recovery, "
        "cost, value, sorting economics or uncertainty. Deterministic helpers rank realised "
        "economics only; provisional batches are never ranked as final winners or losers."
    ),
    business_question="How do two or more batches compare?",
    input_schema=CompareBatchesInput,
    output_schema=CompareBatchesOutput,
)
def compare_batches(inp: CompareBatchesInput, conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    summaries = []
    for bid in inp.batch_ids:
        s = get_batch_summary(conn, bid)
        if s is None:
            raise BatchNotFound(f"Batch {bid} not found.")
        summaries.append(s)

    rows = []
    for s in summaries:
        rows.append({
            "batch_id": s["batch_id"],
            "status": s["status"],
            "economic_evaluation_status": s["economic_evaluation_status"],
            "incoming_weight_t": s["incoming_weight_t"],
            "higher_value_recovery_rate": s["higher_value_recovery_rate"],
            "sorting_plus_inspection_cost_per_t": s["sorting_plus_inspection_cost_per_t"],
            "processing_cost_per_processed_t": r2(
                s["processing_cost_aud"] / s["processed_weight_t"]) if s["processed_weight_t"] else 0.0,
            "total_recovery_cost_per_incoming_t": r2(
                s["total_recovery_cost_aud"] / s["incoming_weight_t"]) if s["incoming_weight_t"] else 0.0,
            "recovered_value_per_t": r2(
                s["gross_recovered_value_aud"] / s["processed_weight_t"]) if s["processed_weight_t"] else 0.0,
            "net_recovery_value_per_t": s["net_recovery_value_per_t"],
            "net_sorting_benefit_aud": s["net_sorting_benefit_aud"],
            "unresolved_rate": s["unresolved_rate"],
            "downgrade_rate": s["downgrade_rate"],
            "economic_quadrant": s["economic_quadrant"],
        })

    realised = [r for r in rows if r["economic_evaluation_status"] == "Realised"]
    if not realised:
        raise InsufficientComparableData(
            "None of the requested batches are realised — realised economic comparison is not possible."
        )

    helpers = {
        "scope": "realised",
        "highest_recovered_value_per_t": _extreme(realised, "recovered_value_per_t", max),
        "lowest_recovered_value_per_t": _extreme(realised, "recovered_value_per_t", min),
        "highest_sorting_inspection_cost_per_t": _extreme(realised, "sorting_plus_inspection_cost_per_t", max),
        "lowest_sorting_inspection_cost_per_t": _extreme(realised, "sorting_plus_inspection_cost_per_t", min),
        "best_realised_net_sorting_benefit": _extreme(realised, "net_sorting_benefit_aud", max),
        "worst_realised_net_sorting_benefit": _extreme(realised, "net_sorting_benefit_aud", min),
    }

    return {
        "provenance": make_provenance(ctx),
        "scope_note": (
            f"{len(realised)} of {len(rows)} batches are realised; helpers rank realised batches only."
        ),
        "rows": rows,
        "helpers": helpers,
        "limitation": (
            "Only realised batches are ranked as economic winners/losers; provisional values "
            "are cost/value realised to date, not final performance."
        ),
    }


def _extreme(rows: list[dict], field: str, fn) -> dict:
    chosen = fn(rows, key=lambda r: r[field])
    return {"batch_id": chosen["batch_id"], "value": chosen[field]}


@tool(
    name="find_batches",
    description=(
        "Use this tool to filter the batch list by status, source type, economic evaluation "
        "status, economic quadrant, net sorting benefit range, or unresolved rate. Deterministic "
        "filter only — not a natural-language search."
    ),
    business_question="Which batches match a set of filters?",
    input_schema=FindBatchesInput,
    output_schema=FindBatchesOutput,
)
def find_batches(inp: FindBatchesInput, conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    metrics = calculate_batch_metrics(conn)
    assign_economic_quadrants(metrics)
    selected = []
    for m in metrics:
        if inp.status is not None and m["status"] != inp.status:
            continue
        if inp.source_type is not None and m["source_type"] != inp.source_type:
            continue
        if inp.economic_evaluation_status is not None and m["economic_evaluation_status"] != inp.economic_evaluation_status:
            continue
        if inp.economic_quadrant is not None:
            want = None if inp.economic_quadrant.lower() in ("null", "none") else inp.economic_quadrant
            if m["economic_quadrant"] != want:
                continue
        if inp.min_net_sorting_benefit is not None and m["net_sorting_benefit_aud"] < inp.min_net_sorting_benefit:
            continue
        if inp.max_net_sorting_benefit is not None and m["net_sorting_benefit_aud"] > inp.max_net_sorting_benefit:
            continue
        if inp.min_unresolved_rate is not None and m["unresolved_rate"] < inp.min_unresolved_rate:
            continue
        selected.append({
            "batch_id": m["batch_id"],
            "status": m["status"],
            "source_type": m["source_type"],
            "incoming_weight_t": m["incoming_weight_t"],
            "processed_weight_t": m["processed_weight_t"],
            "higher_value_recovery_rate": m["higher_value_recovery_rate"],
            "net_sorting_benefit_aud": m["net_sorting_benefit_aud"],
            "unresolved_rate": m["unresolved_rate"],
            "economic_evaluation_status": m["economic_evaluation_status"],
            "eligible_for_realised_comparison": m["eligible_for_realised_comparison"],
            "economic_quadrant": m["economic_quadrant"],
        })
    return {
        "provenance": make_provenance(ctx),
        "count": len(selected),
        "batches": selected,
    }
