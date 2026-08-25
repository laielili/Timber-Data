"""Cost ledger repository — grouped queries over CostLedger."""
from __future__ import annotations

import sqlite3
from datetime import date

from ..config import CORE_COST_CATEGORIES

_CORE_IN = ",".join("?" * len(CORE_COST_CATEGORIES))


def get_core_costs_by_batch(conn: sqlite3.Connection) -> dict[str, dict]:
    """Per-batch lifecycle core costs by category (Sorting Labour / Inspection / Processing /
    Special Handling / Disposal). Transport and Other are reported separately."""
    rows = conn.execute(
        f"""
        SELECT batch_id, cost_category, SUM(total_cost_aud) AS total
        FROM CostLedger
        WHERE cost_category IN ({_CORE_IN})
        GROUP BY batch_id, cost_category
        """,
        CORE_COST_CATEGORIES,
    ).fetchall()
    out: dict[str, dict] = {}
    for r in rows:
        out.setdefault(r["batch_id"], {})[r["cost_category"]] = float(r["total"])
    return out


def get_costs_by_month(conn: sqlite3.Connection, start: date, end: date) -> list[dict]:
    """Monthly core-cost aggregates (cost-date grain): processing + core total."""
    rows = conn.execute(
        f"""
        SELECT substr(cost_date, 1, 7) AS month,
          COALESCE(SUM(CASE WHEN cost_category='Processing' THEN total_cost_aud ELSE 0 END), 0) AS processing_aud,
          COALESCE(SUM(CASE WHEN cost_category IN ({_CORE_IN}) THEN total_cost_aud ELSE 0 END), 0) AS core_total_aud
        FROM CostLedger
        WHERE cost_date BETWEEN ? AND ?
        GROUP BY substr(cost_date, 1, 7)
        ORDER BY month
        """,
        (*CORE_COST_CATEGORIES, start.isoformat(), end.isoformat()),
    ).fetchall()
    return [dict(r) for r in rows]


def get_assumptions(conn: sqlite3.Connection) -> dict[str, float]:
    """Assumption key -> value. Centralised; services never hard-code assumptions."""
    rows = conn.execute("SELECT assumption_key, value FROM Assumptions").fetchall()
    return {r["assumption_key"]: float(r["value"]) for r in rows}
