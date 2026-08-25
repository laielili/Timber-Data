"""Source performance service — two separate layers that must never be merged:
realised source performance (completed batches only) and current operational
exposure (non-completed batches only)."""
from __future__ import annotations

import sqlite3

from ..repositories import batches as batches_repo
from .common import TimeContext, pct, r1, r2


def calculate_source_performance(
    conn: sqlite3.Connection, ctx: TimeContext, metrics: list[dict]
) -> tuple[list[dict], list[dict]]:
    # per-batch source_type lookup (metrics already carry it)
    by_batch = {m["batch_id"]: m for m in metrics}

    # materials for unresolved exposure weights + open-inspection month state
    open_insp_kg_by_source = _open_inspection_kg_by_source(conn, ctx.as_of_month)

    source_types = sorted({m["source_type"] for m in metrics})
    realised_rows: list[dict] = []
    exposure_rows: list[dict] = []

    for st in source_types:
        realised = [m for m in metrics if m["source_type"] == st and m["eligible_for_realised_comparison"]]
        open_m = [m for m in metrics if m["source_type"] == st and not m["eligible_for_realised_comparison"]]

        if realised:
            incoming = sum(m["incoming_weight_t"] for m in realised)
            processed = sum(m["processed_weight_t"] for m in realised)
            hv = sum(m["higher_value_weight_t"] for m in realised)
            gross = sum(m["gross_recovered_value_aud"] for m in realised)
            total_cost = sum(m["total_recovery_cost_aud"] for m in realised)
            proc_cost = sum(m["processing_cost_aud"] for m in realised)
            realised_rows.append({
                "source_type": st,
                "completed_batch_count": len(realised),
                "completed_incoming_weight_t": r1(incoming),
                "realised_higher_value_recovery_rate": pct(hv, processed),
                "realised_processing_cost_per_processed_t": r2(proc_cost / processed) if processed else 0.0,
                "realised_total_recovery_cost_per_incoming_t": r2(total_cost / incoming) if incoming else 0.0,
                "realised_recovered_value_per_t": r2(gross / processed) if processed else 0.0,
                "realised_net_recovery_value_per_t": r2((gross - total_cost) / incoming) if incoming else 0.0,
                "realised_net_sorting_benefit_aud": r2(sum(m["net_sorting_benefit_aud"] for m in realised)),
            })

        if open_m:
            open_ids = [m["batch_id"] for m in open_m]
            out_by_batch = _output_aggregates(conn, open_ids)
            open_incoming = sum(m["incoming_weight_t"] for m in open_m)
            open_processed = sum(o.get("processed_t", 0.0) or 0.0 for o in out_by_batch.values())
            open_unresolved = sum(
                m["unresolved_weight_t"] for m in open_m
            )
            cost_to_date = sum(m["total_recovery_cost_aud"] for m in open_m)
            value_to_date = sum(o.get("gross_aud", 0.0) or 0.0 for o in out_by_batch.values())
            exposure_rows.append({
                "source_type": st,
                "open_batch_count": len(open_m),
                "open_incoming_weight_t": r1(open_incoming),
                "open_processed_weight_t": r2(open_processed),
                "open_unresolved_weight_t": r2(open_unresolved),
                "open_inspection_weight_t": r2(open_insp_kg_by_source.get(st, 0.0) / 1000.0),
                "cost_incurred_to_date_aud": r2(cost_to_date),
                "value_realised_to_date_aud": r2(value_to_date),
            })

    return realised_rows, exposure_rows


def _output_aggregates(conn: sqlite3.Connection, batch_ids: list[str]) -> dict[str, dict]:
    if not batch_ids:
        return {}
    placeholders = ",".join("?" * len(batch_ids))
    rows = conn.execute(
        f"""
        SELECT batch_id, SUM(weight_t) AS processed_t, SUM(gross_value_aud) AS gross_aud
        FROM RecoveryOutputs WHERE batch_id IN ({placeholders}) GROUP BY batch_id
        """,
        batch_ids,
    ).fetchall()
    return {r["batch_id"]: dict(r) for r in rows}


def _open_inspection_kg_by_source(conn: sqlite3.Connection, month_key: str) -> dict[str, float]:
    rows = conn.execute(
        """
        SELECT sp.source_type, COALESCE(SUM(mms.weight_kg), 0) AS kg
        FROM MaterialMonthlyState mms
        JOIN Materials m ON m.material_id = mms.material_id
        JOIN Batches b ON b.batch_id = m.batch_id
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE mms.month_key = ? AND mms.open_inspection = 1
        GROUP BY sp.source_type
        """,
        (month_key,),
    ).fetchall()
    return {r["source_type"]: float(r["kg"]) for r in rows}
