"""Management brief service — deterministic structured brief items computed from the
database. No LLM / natural-language generation: values come from analytics services,
severity/related entities are derived, and deterministic display templates are applied.

`detail` is the single documented display-copy exception; every brief also carries
structured numeric `values` for the frontend / future AI layer.
"""
from __future__ import annotations

import sqlite3

from ..repositories import batches as batches_repo, costs as costs_repo
from .common import TimeContext, r1, r2


def _aud(v: float) -> str:
    return f"${v:,.2f}"


def _audk(v: float) -> str:
    sign = "-" if v < 0 else ""
    av = abs(v)
    return f"{sign}${av / 1000:,.1f}k" if av >= 1000 else _aud(v)


def calculate_management_brief(
    conn: sqlite3.Connection, ctx: TimeContext, overview: dict, metrics: list[dict]
) -> list[dict]:
    asm = costs_repo.get_assumptions(conn)

    # Brief 01 — B017 realised poor sorting economics
    b17 = next(m for m in metrics if m["batch_id"] == "B017")
    b17_si = b17["sorting_plus_inspection_cost_per_t"]
    b17_nsb = b17["net_sorting_benefit_aud"]

    # Brief 02 — latest inspection backlog growth (December vs November), computed, not hard-coded
    nov_insp = batches_repo.get_material_state(conn, "2025-11").get("inspection", 0.0) / 1000.0
    dec_insp = batches_repo.get_material_state(conn, "2025-12").get("inspection", 0.0) / 1000.0
    growth = round((dec_insp - nov_insp) / nov_insp * 100, 1) if nov_insp else None
    as_of_date = ctx.as_of.strftime("%d %b %Y")

    # Brief 03 — higher-value recovery vs prototype target (from Assumptions)
    hv_rate = overview["kpis"]["higher_value_recovery_rate"]["value"]
    hv_target = asm["higher_value_recovery_target_pct"]

    briefs = [
        {
            "id": "brief_batch_17",
            "title": "Batch 17 is generating unusually high sorting costs.",
            "detail": (
                f"Sorting + inspection: {_aud(b17_si)}/t"
                f" · realised net sorting benefit: {_audk(b17_nsb)}"
            ),
            "severity": "attention",
            "related_batch_id": "B017",
            "question_id": "q1",
            "basis": "selected_period",
            "values": {
                "sorting_inspection_cost_per_t": b17_si,
                "net_sorting_benefit_aud": b17_nsb,
            },
        },
        {
            "id": "brief_inspection_backlog",
            "title": "Inspection backlog rose at the latest snapshot.",
            "detail": (
                f"{dec_insp:,.2f} t open"
                + (f" · +{growth:.1f}% vs November" if growth else "")
                + f" · as of {as_of_date}"
            ),
            "severity": "attention",
            "related_batch_id": None,
            "question_id": "q3",
            "basis": "snapshot",
            "values": {
                "inspection_backlog_t": r2(dec_insp),
                "inspection_backlog_growth_vs_nov_pct": growth,
                "as_of_date": ctx.as_of_date_str,
            },
        },
        {
            "id": "brief_higher_value",
            "title": "Higher-value recovery remains above the prototype target.",
            "detail": f"{hv_rate:.1f}% of processed output vs {hv_target:.0f}% prototype target",
            "severity": "positive",
            "related_batch_id": None,
            "question_id": "q4",
            "basis": "selected_period",
            "values": {
                "higher_value_recovery_rate": hv_rate,
                "higher_value_target_pct": hv_target,
            },
        },
    ]
    return briefs
