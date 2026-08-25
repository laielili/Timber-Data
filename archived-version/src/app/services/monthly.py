"""Monthly performance service — 12 typed monthly rows (contract fields only)."""
from __future__ import annotations

import sqlite3

from ..repositories import batches as batches_repo, costs as costs_repo, recovery as recovery_repo
from ..repositories.operations import get_months
from .common import TimeContext, pct, r1, r2, r3


def calculate_monthly(conn: sqlite3.Connection, ctx: TimeContext) -> list[dict]:
    ps, pe = ctx.period_start.isoformat(), ctx.period_end.isoformat()

    incoming_by_month = batches_repo.get_incoming_by_month(conn, ps, pe)
    out_by_month = {r["month"]: r for r in recovery_repo.get_outputs_by_month(conn, ctx.period_start, ctx.period_end)}
    cost_by_month = {c["month"]: c for c in costs_repo.get_costs_by_month(conn, ctx.period_start, ctx.period_end)}

    months = [m for m in get_months(conn) if ps[:7] <= m <= pe[:7]]
    rows: list[dict] = []
    for mk in months:
        incoming = incoming_by_month.get(mk, 0.0)
        out = out_by_month.get(mk, {})
        processed = out.get("processed_t", 0.0) or 0.0
        hv = out.get("hv_t", 0.0) or 0.0
        gross = out.get("gross_aud", 0.0) or 0.0
        cost = cost_by_month.get(mk, {})
        processing_cost = cost.get("processing_aud", 0.0) or 0.0
        core_total = cost.get("core_total_aud", 0.0) or 0.0
        net = gross - core_total

        state = batches_repo.get_material_state(conn, mk)
        rows.append({
            "month": mk,
            "incoming_timber_t": r1(incoming),
            "processed_timber_t": r3(processed),
            "higher_value_recovery_rate": pct(hv, processed),
            "processing_cost_aud": r2(processing_cost),
            "total_recovery_cost_aud": r2(core_total),
            "gross_recovered_value_aud": r2(gross),
            "net_recovery_value_aud": r2(net),
            "processing_cost_per_processed_t": r2(processing_cost / processed) if processed else 0.0,
            "recovered_value_per_t": r2(gross / processed) if processed else 0.0,
            "net_recovery_value_per_t": r2(net / incoming) if incoming else 0.0,
            "sorting_backlog_t": r2(state.get("sorting", 0.0) / 1000.0),
            "inspection_backlog_t": r2(state.get("inspection", 0.0) / 1000.0),
            "processing_backlog_t": r2(state.get("processing", 0.0) / 1000.0),
            "unresolved_backlog_t": r2(state.get("unresolved", 0.0) / 1000.0),
        })
    return rows
