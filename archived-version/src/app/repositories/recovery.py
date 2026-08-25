"""Recovery outputs repository — grouped queries over RecoveryOutputs (no N+1)."""
from __future__ import annotations

import sqlite3
from datetime import date


def get_outputs_by_batch(conn: sqlite3.Connection) -> dict[str, dict]:
    """Per-batch lifecycle aggregates: processed/hv/bf/sh/res weight + gross value."""
    rows = conn.execute(
        """
        SELECT batch_id,
          SUM(weight_t) AS processed_t,
          COALESCE(SUM(CASE WHEN recovery_route='Higher-value Recovery' THEN weight_t ELSE 0 END), 0) AS hv_t,
          COALESCE(SUM(CASE WHEN recovery_route='Board Feedstock' THEN weight_t ELSE 0 END), 0) AS bf_t,
          COALESCE(SUM(CASE WHEN recovery_route='Special Handling' THEN weight_t ELSE 0 END), 0) AS sh_t,
          COALESCE(SUM(CASE WHEN recovery_route='Residual / Disposal' THEN weight_t ELSE 0 END), 0) AS res_t,
          SUM(gross_value_aud) AS gross_aud
        FROM RecoveryOutputs
        GROUP BY batch_id
        """
    ).fetchall()
    return {r["batch_id"]: dict(r) for r in rows}


def get_outputs_in_period(conn: sqlite3.Connection, start: date, end: date) -> list[dict]:
    rows = conn.execute(
        """
        SELECT batch_id, output_date, recovery_route, weight_t, gross_value_aud
        FROM RecoveryOutputs
        WHERE output_date BETWEEN ? AND ?
        ORDER BY output_date
        """,
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    return [dict(r) for r in rows]


def get_outputs_by_month(conn: sqlite3.Connection, start: date, end: date) -> list[dict]:
    """Monthly aggregates: processed weight, HV weight, gross value (output-date grain)."""
    rows = conn.execute(
        """
        SELECT substr(output_date, 1, 7) AS month,
          SUM(weight_t) AS processed_t,
          COALESCE(SUM(CASE WHEN recovery_route='Higher-value Recovery' THEN weight_t ELSE 0 END), 0) AS hv_t,
          SUM(gross_value_aud) AS gross_aud
        FROM RecoveryOutputs
        WHERE output_date BETWEEN ? AND ?
        GROUP BY substr(output_date, 1, 7)
        ORDER BY month
        """,
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    return [dict(r) for r in rows]


def get_outputs_by_route(conn: sqlite3.Connection, start: date, end: date) -> list[dict]:
    rows = conn.execute(
        """
        SELECT recovery_route, SUM(weight_t) AS weight_t
        FROM RecoveryOutputs
        WHERE output_date BETWEEN ? AND ?
        GROUP BY recovery_route
        """,
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    return [dict(r) for r in rows]
