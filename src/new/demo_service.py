"""Demo loader — optionally seeds the workbench DB with the synthetic sample.

Opt-in only: the user explicitly requests it via POST /api/new/demo. The dashboard
otherwise starts empty and reads whatever the user uploads.
"""
from __future__ import annotations

import sqlite3

from . import config, db, upload_service

_CSV_FILES = {
    "SourceProjects": "source_projects.csv",
    "Batches": "batches.csv",
    "Materials": "materials.csv",
    "RecoveryOutputs": "recovery_outputs.csv",
    "CostLedger": "cost_ledger.csv",
    "ProcessingEvents": "processing_events.csv",
    "InspectionEvents": "inspection_events.csv",
}


def load_demo(conn: sqlite3.Connection, mode: str = "append") -> dict:
    """Seed the workbench DB with the synthetic sample.

    mode="append"  refuses when the DB already has data (opt-in only).
    mode="replace" clears all upload tables + upload history first, then loads.
    """
    if mode not in ("append", "replace"):
        raise ValueError(f"mode must be 'append' or 'replace', got {mode!r}")
    if mode == "append" and db.has_data(conn):
        return {"loaded": False, "message": "工作台已有数据；如需重置，请使用“重置为示例数据”（将清空现有数据后重新载入）。"}

    if mode == "replace":
        with conn:
            for table in db.UPLOAD_TABLES:
                conn.execute(f'DELETE FROM "{table}"')
            conn.execute("DELETE FROM Uploads")

    csv_dir = config.PROJECT_ROOT / "data" / "csv"
    if not csv_dir.exists():
        raise FileNotFoundError(f"Demo CSV directory not found: {csv_dir}")

    results = []
    with conn:
        for table in db.UPLOAD_TABLES:
            path = csv_dir / _CSV_FILES[table]
            content = path.read_bytes()
            rows = upload_service._parse_rows_csv(table, content.decode("utf-8-sig"))
            upload_service._insert(conn, table, rows, mode)
            conn.execute(
                "INSERT INTO Uploads (upload_id, table_name, filename, mode, row_count, status, message) "
                "VALUES (?, ?, ?, ?, ?, 'ok', 'demo seed')",
                (f"demo_{table.lower()}", table, path.name, mode, len(rows)),
            )
            results.append({"table": table, "rows": len(rows)})

    verb = "重置并重新载入" if mode == "replace" else "载入"
    return {"loaded": True, "message": f"示例数据已{verb}（{sum(r['rows'] for r in results)} 行）", "tables": results}