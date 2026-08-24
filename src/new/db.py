"""Workbench SQLite access + schema bootstrap.

The upload database starts empty; the dashboard and AI read whatever the user
has uploaded. Core tables mirror the timber schema used by the old prototype so
CSV exports from that dataset can be imported directly.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from . import config

# Tables that users may upload into, in dependency order (used by validation and
# the demo loader). Each maps to its primary key column.
UPLOAD_TABLES: dict[str, str] = {
    "SourceProjects": "source_id",
    "Batches": "batch_id",
    "Materials": "material_id",
    "RecoveryOutputs": "output_id",
    "CostLedger": "cost_id",
    "ProcessingEvents": "event_id",
    "InspectionEvents": "inspection_id",
}

# Column -> (type, nullable, required-for-upload). Columns marked required must be
# present in an uploaded CSV/JSON row. Optional columns default to NULL / 0.
SCHEMA: dict[str, dict[str, tuple[str, bool, bool]]] = {
    "SourceProjects": {
        "source_id": ("TEXT", False, True),
        "source_type": ("TEXT", False, True),
        "region": ("TEXT", True, True),
        "former_use_category": ("TEXT", True, True),
        "submission_date": ("DATE", True, True),
        "estimated_material_quality": ("TEXT", True, False),
        "expected_complexity": ("TEXT", True, False),
        "notes": ("TEXT", True, False),
    },
    "Batches": {
        "batch_id": ("TEXT", False, True),
        "source_id": ("TEXT", False, True),
        "arrival_date": ("DATE", False, True),
        "incoming_weight_t": ("REAL", False, True),
        "planned_sorting_intensity": ("TEXT", True, False),
        "current_stage": ("TEXT", True, False),
        "batch_status": ("TEXT", True, False),
        "priority": ("TEXT", True, False),
        "notes": ("TEXT", True, False),
    },
    "Materials": {
        "material_id": ("TEXT", False, True),
        "batch_id": ("TEXT", False, True),
        "estimated_weight_kg": ("REAL", False, True),
        "species": ("TEXT", True, False),
        "material_form": ("TEXT", True, False),
        "former_use": ("TEXT", True, False),
        "known_treatment_status": ("TEXT", True, False),
        "surface_condition": ("TEXT", True, False),
        "record_completeness": ("TEXT", True, False),
        "requires_inspection": ("TEXT", True, False),
        "special_handling_flag": ("TEXT", True, False),
        "initial_recovery_grade": ("TEXT", True, False),
        "recovery_grade": ("TEXT", True, False),
        "current_route": ("TEXT", True, False),
        "resolution_status": ("TEXT", True, False),
        "output_date": ("DATE", True, False),
    },
    "RecoveryOutputs": {
        "output_id": ("TEXT", False, True),
        "batch_id": ("TEXT", False, True),
        "output_date": ("DATE", False, True),
        "recovery_route": ("TEXT", False, True),
        "recovery_grade": ("TEXT", True, False),
        "weight_t": ("REAL", False, True),
        "unit_value_aud_per_t": ("REAL", True, False),
        "gross_value_aud": ("REAL", True, False),
    },
    "CostLedger": {
        "cost_id": ("TEXT", False, True),
        "batch_id": ("TEXT", False, True),
        "cost_date": ("DATE", False, True),
        "cost_category": ("TEXT", False, True),
        "quantity": ("REAL", True, False),
        "unit": ("TEXT", True, False),
        "unit_cost_aud": ("REAL", True, False),
        "total_cost_aud": ("REAL", False, True),
        "notes": ("TEXT", True, False),
    },
    "ProcessingEvents": {
        "event_id": ("TEXT", False, True),
        "batch_id": ("TEXT", False, True),
        "stage": ("TEXT", False, True),
        "start_datetime": ("DATETIME", False, True),
        "end_datetime": ("DATETIME", True, False),
        "weight_in_t": ("REAL", False, True),
        "weight_out_t": ("REAL", True, False),
        "labour_hours": ("REAL", True, False),
        "machine_hours": ("REAL", True, False),
        "status": ("TEXT", True, False),
    },
    "InspectionEvents": {
        "inspection_id": ("TEXT", False, True),
        "batch_id": ("TEXT", False, True),
        "material_id": ("TEXT", True, False),
        "inspection_type": ("TEXT", False, True),
        "reason": ("TEXT", True, False),
        "opened_datetime": ("DATETIME", False, True),
        "closed_datetime": ("DATETIME", True, False),
        "status": ("TEXT", False, True),
        "labour_hours": ("REAL", True, False),
        "external_cost_aud": ("REAL", True, False),
        "outcome": ("TEXT", True, False),
    },
}

FK_REFS: dict[str, str] = {
    "Batches": "SourceProjects",
    "Materials": "Batches",
    "RecoveryOutputs": "Batches",
    "CostLedger": "Batches",
    "ProcessingEvents": "Batches",
    "InspectionEvents": "Batches",
}


def connect() -> sqlite3.Connection:
    Path(config.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    """Create the upload tables + uploads metadata table if missing. Idempotent."""
    for table, cols in SCHEMA.items():
        col_defs = []
        for name, (ctype, nullable, _required) in cols.items():
            col_defs.append(f'"{name}" {ctype} {"NOT NULL" if not nullable else ""}'.rstrip())
        pk = UPLOAD_TABLES[table]
        ddl = (
            f'CREATE TABLE IF NOT EXISTS "{table}" '
            f"({', '.join(col_defs)}, PRIMARY KEY (\"{pk}\"))"
        )
        conn.execute(ddl)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS Uploads (
            upload_id TEXT PRIMARY KEY,
            table_name TEXT NOT NULL,
            filename TEXT NOT NULL,
            mode TEXT NOT NULL,
            row_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            message TEXT NOT NULL DEFAULT '',
            created_at DATETIME NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_uploads_created ON Uploads(created_at)")
    conn.commit()


def dataset_summary(conn: sqlite3.Connection) -> dict:
    """Row counts per uploadable table + latest upload activity."""
    counts = {}
    for table in UPLOAD_TABLES:
        try:
            row = conn.execute(f'SELECT COUNT(*) AS c FROM "{table}"').fetchone()
            counts[table] = int(row["c"])
        except sqlite3.Error:
            counts[table] = 0
    last = conn.execute("SELECT * FROM Uploads ORDER BY created_at DESC LIMIT 1").fetchone()
    return {
        "tables": counts,
        "total_rows": sum(counts.values()),
        "last_upload": dict(last) if last else None,
    }


def has_data(conn: sqlite3.Connection) -> bool:
    return dataset_summary(conn)["total_rows"] > 0