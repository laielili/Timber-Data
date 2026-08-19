"""Batches / materials repository — factual data questions only, no interpretation."""
from __future__ import annotations

import sqlite3
from typing import Optional

# Synthetic-model grade ordering used by the approved generator for the downgrade
# metric. NOTE: the approved dataset internally treats a LOWER index as the
# "downgrade" direction (see SYNTHETIC_DATA_METHOD / generator _assign_route_and_grade);
# we replicate the exact condition so results match the approved mock.
GRADE_INDEX_SQL = """
  CASE recovery_grade
    WHEN 'Premium' THEN 0 WHEN 'Character' THEN 1 WHEN 'Rustic' THEN 2
    WHEN 'Feedstock' THEN 3 ELSE 4 END
"""
INITIAL_GRADE_INDEX_SQL = """
  CASE initial_recovery_grade
    WHEN 'Premium' THEN 0 WHEN 'Character' THEN 1 WHEN 'Rustic' THEN 2
    WHEN 'Feedstock' THEN 3 ELSE 4 END
"""


def _normalise_batch(row: dict) -> dict:
    """arrival_date is stored as ISO datetime text; the contract exposes date-only."""
    d = dict(row)
    d["arrival_date"] = str(d["arrival_date"])[:10]
    return d


def get_batches(conn: sqlite3.Connection) -> list[dict]:
    """All batches joined with their source type."""
    rows = conn.execute(
        """
        SELECT b.batch_id, b.source_id, sp.source_type, b.arrival_date, b.incoming_weight_t,
               b.planned_sorting_intensity, b.current_stage, b.batch_status, b.priority, b.notes
        FROM Batches b
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        ORDER BY b.batch_id
        """
    ).fetchall()
    return [_normalise_batch(dict(r)) for r in rows]


def get_batch(conn: sqlite3.Connection, batch_id: str) -> Optional[dict]:
    row = conn.execute(
        """
        SELECT b.batch_id, b.source_id, sp.source_type, b.arrival_date, b.incoming_weight_t,
               b.planned_sorting_intensity, b.current_stage, b.batch_status, b.priority, b.notes
        FROM Batches b
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE b.batch_id = ?
        """,
        (batch_id,),
    ).fetchone()
    return _normalise_batch(dict(row)) if row else None


def get_incoming_in_period(conn: sqlite3.Connection, start: str, end: str) -> float:
    """Total incoming weight of batches arriving in [start, end] (selected period)."""
    row = conn.execute(
        "SELECT COALESCE(SUM(incoming_weight_t), 0) FROM Batches WHERE arrival_date BETWEEN ? AND ?",
        (start, end),
    ).fetchone()
    return float(row[0])


def get_incoming_by_month(conn: sqlite3.Connection, start: str, end: str) -> dict[str, float]:
    """Incoming weight by arrival month within the selected period."""
    rows = conn.execute(
        """
        SELECT substr(arrival_date, 1, 7) AS month, SUM(incoming_weight_t) AS incoming_t
        FROM Batches
        WHERE arrival_date BETWEEN ? AND ?
        GROUP BY substr(arrival_date, 1, 7)
        """,
        (start, end),
    ).fetchall()
    return {r["month"]: float(r["incoming_t"]) for r in rows}


def get_material_aggregates(conn: sqlite3.Connection) -> dict[str, dict]:
    """Per-batch material aggregates: unresolved kg, inspection-exposure kg, downgraded kg."""
    rows = conn.execute(
        f"""
        SELECT batch_id,
          COALESCE(SUM(CASE WHEN resolution_status='Unresolved' THEN estimated_weight_kg ELSE 0 END), 0) AS unresolved_kg,
          COALESCE(SUM(CASE WHEN requires_inspection='Yes' THEN estimated_weight_kg ELSE 0 END), 0) AS insp_exposure_kg,
          COALESCE(SUM(CASE WHEN resolution_status='Output' AND ({GRADE_INDEX_SQL}) < ({INITIAL_GRADE_INDEX_SQL})
                     THEN estimated_weight_kg ELSE 0 END), 0) AS downgraded_kg
        FROM Materials
        GROUP BY batch_id
        """
    ).fetchall()
    return {r["batch_id"]: dict(r) for r in rows}


def get_material_state(conn: sqlite3.Connection, month_key: str) -> dict[str, float]:
    """Month-end material state: bucket -> summed weight kg (MaterialMonthlyState)."""
    rows = conn.execute(
        """
        SELECT bucket, COALESCE(SUM(weight_kg), 0) AS kg
        FROM MaterialMonthlyState
        WHERE month_key = ?
        GROUP BY bucket
        """,
        (month_key,),
    ).fetchall()
    return {r["bucket"]: float(r["kg"]) for r in rows}


def get_open_inspection_weight_kg(conn: sqlite3.Connection, month_key: str) -> float:
    row = conn.execute(
        "SELECT COALESCE(SUM(weight_kg), 0) FROM MaterialMonthlyState WHERE month_key = ? AND open_inspection = 1",
        (month_key,),
    ).fetchone()
    return float(row[0])


def get_unresolved_union_weight_kg(conn: sqlite3.Connection, month_key: str) -> float:
    """Union of unresolved OR open-inspection materials (each material counted once)."""
    row = conn.execute(
        """
        SELECT COALESCE(SUM(weight_kg), 0) FROM MaterialMonthlyState
        WHERE month_key = ? AND (bucket = 'unresolved' OR open_inspection = 1)
        """,
        (month_key,),
    ).fetchone()
    return float(row[0])


def get_record_stats_kg(conn: sqlite3.Connection) -> dict[str, float]:
    """Material weight by record-completeness class and unknown/conflicting treatment."""
    row = conn.execute(
        """
        SELECT
          COALESCE(SUM(CASE WHEN record_completeness='Complete' THEN estimated_weight_kg ELSE 0 END), 0) AS complete_kg,
          COALESCE(SUM(CASE WHEN record_completeness='Partial' THEN estimated_weight_kg ELSE 0 END), 0) AS partial_kg,
          COALESCE(SUM(CASE WHEN record_completeness='Critical Information Missing' THEN estimated_weight_kg ELSE 0 END), 0) AS critical_kg,
          COALESCE(SUM(CASE WHEN known_treatment_status IN ('Unknown','Conflicting Record') THEN estimated_weight_kg ELSE 0 END), 0) AS unknown_treatment_kg
        FROM Materials
        """
    ).fetchone()
    return dict(row)


def get_treatment_status_weights_kg(conn: sqlite3.Connection) -> dict[str, float]:
    """Material weight per known_treatment_status value (for uncertainty distribution)."""
    rows = conn.execute(
        """
        SELECT known_treatment_status, COALESCE(SUM(estimated_weight_kg), 0) AS kg
        FROM Materials
        GROUP BY known_treatment_status
        """
    ).fetchall()
    return {r["known_treatment_status"]: float(r["kg"]) for r in rows}


def get_materials_by_batch(conn: sqlite3.Connection, batch_ids: Optional[list[str]] = None) -> list[dict]:
    if batch_ids:
        placeholders = ",".join("?" * len(batch_ids))
        rows = conn.execute(
            f"""
            SELECT batch_id, estimated_weight_kg, resolution_status, output_date, requires_inspection
            FROM Materials WHERE batch_id IN ({placeholders})
            """,
            batch_ids,
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT batch_id, estimated_weight_kg, resolution_status, output_date, requires_inspection FROM Materials"
        ).fetchall()
    return [dict(r) for r in rows]
