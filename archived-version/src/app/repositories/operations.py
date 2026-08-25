"""Operations repository — processing events, inspection events, monthly dimension."""
from __future__ import annotations

import sqlite3
from datetime import datetime


def _parse_ts(value):
    """ProcessingEvents timestamps are stored as ISO text; parse to datetime."""
    if value is None:
        return None
    return datetime.fromisoformat(value) if isinstance(value, str) else value


def get_processing_event_timeline(conn: sqlite3.Connection) -> dict[str, dict]:
    """Per batch: earliest start and latest end among processing events (for turnaround)."""
    rows = conn.execute(
        """
        SELECT batch_id,
          MIN(start_datetime) AS first_start,
          MAX(end_datetime) AS last_end
        FROM ProcessingEvents
        GROUP BY batch_id
        """
    ).fetchall()
    out = {}
    for r in rows:
        out[r["batch_id"]] = {
            "first_start": _parse_ts(r["first_start"]),
            "last_end": _parse_ts(r["last_end"]),
        }
    return out


def get_open_inspection_material_ids(conn: sqlite3.Connection) -> set[str]:
    """Material-level inspection events still Open at the dataset snapshot."""
    rows = conn.execute(
        "SELECT DISTINCT material_id FROM InspectionEvents WHERE status = 'Open' AND material_id IS NOT NULL"
    ).fetchall()
    return {r["material_id"] for r in rows}


def get_months(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT month_key FROM DimMonths ORDER BY month_key").fetchall()
    return [r["month_key"] for r in rows]
