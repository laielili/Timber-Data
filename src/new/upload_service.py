"""Upload ingestion — CSV / JSON into the workbench database.

Rules:
- CSV columns must include every required column of the target table (extra
  columns are ignored, so exports from the old generator CSVs import cleanly).
- Primary keys are validated; ``append`` upserts (INSERT OR REPLACE) while
  ``replace`` clears the table first.
- Foreign keys are validated in Python with clear error messages so uploads may
  arrive in any order.
"""
from __future__ import annotations

import csv
import io
import json
import uuid
from typing import Any, Optional

from . import db, config

_NUMERIC_TYPES = ("REAL", "INTEGER")
_REQUIRED_REF: dict[str, Optional[str]] = {
    "Batches": "SourceProjects",
    "Materials": "Batches",
    "RecoveryOutputs": "Batches",
    "CostLedger": "Batches",
    "ProcessingEvents": "Batches",
    "InspectionEvents": "Batches",
}


class UploadError(Exception):
    pass


def _normalise_value(table: str, col: str, raw: Any) -> Any:
    """Coerce a raw cell to the target SQLite type; None when empty/absent."""
    if raw is None:
        return None
    text = str(raw).strip()
    if text == "":
        return None
    ctype = db.SCHEMA[table][col][0]
    if ctype == "REAL":
        try:
            return float(text)
        except ValueError as exc:
            raise UploadError(f"{table}.{col}: '{text}' is not a number.") from exc
    if ctype in ("DATE", "DATETIME"):
        return text[:10] if ctype == "DATE" else text
    return text


def _validate_row(table: str, row: dict[str, Any], row_index: int) -> dict[str, Any]:
    out: dict[str, Any] = {}
    errors: list[str] = []
    for col, (ctype, _nullable, required) in db.SCHEMA[table].items():
        value = _normalise_value(table, col, row.get(col))
        if required and value is None:
            errors.append(f"row {row_index + 1}: missing required column '{col}'")
        out[col] = value
    if errors:
        raise UploadError("; ".join(errors))
    return out


def _validate_references(conn, table: str, rows: list[dict[str, Any]]) -> list[str]:
    """Check FK references exist. Returns a list of error strings (up to 5)."""
    ref = _REQUIRED_REF.get(table)
    if not ref:
        return []
    key_col = "source_id" if ref == "SourceProjects" else "batch_id"
    ref_pk = db.UPLOAD_TABLES[ref]
    ids = {str(r.get(key_col) or "").strip() for r in rows if str(r.get(key_col) or "").strip()}
    missing = [
        i for i in ids
        if not conn.execute(f'SELECT 1 FROM "{ref}" WHERE "{ref_pk}" = ?', (i,)).fetchone()
    ]
    errors = [f"{key_col} '{m}' not found in {ref}" for m in missing[:5]]
    if len(missing) > 5:
        errors.append(f"... and {len(missing) - 5} more missing references")
    return errors


def _insert(conn, table: str, rows: list[dict[str, Any]], mode: str) -> None:
    if not rows:
        return
    cols = list(db.SCHEMA[table].keys())
    if mode == "replace":
        conn.execute(f'DELETE FROM "{table}"')
    placeholders = ", ".join("?" * len(cols))
    col_sql = ", ".join(f'"{c}"' for c in cols)
    conn.executemany(
        f'INSERT OR REPLACE INTO "{table}" ({col_sql}) VALUES ({placeholders})',
        [[r.get(c) for c in cols] for r in rows],
    )


def _parse_rows_csv(table: str, content: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise UploadError("CSV has no header row.")
    header = {h.strip() for h in reader.fieldnames}
    required = {c for c, (_, _n, req) in db.SCHEMA[table].items() if req}
    missing = sorted(required - header)
    if missing:
        raise UploadError(f"CSV is missing required columns: {', '.join(missing)}")
    rows: list[dict[str, Any]] = []
    for i, raw in enumerate(reader):
        row = {k.strip(): v for k, v in raw.items()}
        rows.append(_validate_row(table, row, i))
    return rows


def _parse_rows_json(table: str, data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and "rows" in data:
        data = data["rows"]
    if not isinstance(data, list):
        raise UploadError("JSON payload must be an array of rows or {'rows': [...]}.")
    rows: list[dict[str, Any]] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise UploadError(f"row {i + 1} must be an object.")
        rows.append(_validate_row(table, item, i))
    return rows


def upload_csv(conn, table: str, filename: str, content: bytes, mode: str) -> dict:
    return _do_upload(conn, table, filename, content, mode, is_json=False)


def upload_json(conn, table: str, filename: str, content: bytes, mode: str) -> dict:
    return _do_upload(conn, table, filename, content, mode, is_json=True)


def _do_upload(conn, table: str, filename: str, content: bytes, mode: str, *, is_json: bool):
    if table not in db.UPLOAD_TABLES:
        raise UploadError(f"Unknown table '{table}'. Choose from: {', '.join(db.UPLOAD_TABLES)}")
    if mode not in ("append", "replace"):
        raise UploadError("mode must be 'append' or 'replace'.")
    if len(content) > config.MAX_UPLOAD_BYTES:
        raise UploadError("File exceeds the upload size limit.")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise UploadError("File must be UTF-8 encoded.") from exc

    if is_json:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise UploadError(f"Invalid JSON: {exc}") from exc
        rows = _parse_rows_json(table, payload)
    else:
        rows = _parse_rows_csv(table, text)

    ref_errors = _validate_references(conn, table, rows)
    if ref_errors:
        raise UploadError("; ".join(ref_errors))

    upload_id = f"up_{uuid.uuid4().hex[:12]}"
    try:
        with conn:  # transaction
            _insert(conn, table, rows, mode)
            conn.execute(
                "INSERT INTO Uploads (upload_id, table_name, filename, mode, row_count, status, message) "
                "VALUES (?, ?, ?, ?, ?, 'ok', '')",
                (upload_id, table, filename, mode, len(rows)),
            )
    except Exception as exc:  # noqa: BLE001 - surfaced to the API
        raise UploadError(f"Database write failed: {exc}") from exc

    return {
        "upload_id": upload_id,
        "table_name": table,
        "filename": filename,
        "mode": mode,
        "row_count": len(rows),
        "status": "ok",
        "message": f"Imported {len(rows)} row(s) into {table}",
        "errors": [],
    }


def upload_bundle(conn, content: bytes) -> dict:
    """Import a whole JSON bundle: {"tables": {Table: {"rows": [...], "mode": "..."}}}."""
    try:
        payload = json.loads(content.decode("utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise UploadError("File must be UTF-8 encoded.") from exc
    except json.JSONDecodeError as exc:
        raise UploadError(f"Invalid JSON: {exc}") from exc

    tables = payload.get("tables")
    if not isinstance(tables, dict):
        raise UploadError("Bundle must be {\"tables\": {Table: {rows: [...]}}}")

    upload_id = f"up_{uuid.uuid4().hex[:12]}"
    total = 0
    statuses = []
    with conn:
        for table, spec in tables.items():
            mode = spec.get("mode", "append") if isinstance(spec, dict) else "append"
            rows_spec = spec.get("rows", spec) if isinstance(spec, dict) else spec
            rows = _parse_rows_json(table, rows_spec)
            ref_errors = _validate_references(conn, table, rows)
            if ref_errors:
                raise UploadError(f"{table}: {'; '.join(ref_errors)}")
            _insert(conn, table, rows, mode)
            total += len(rows)
            statuses.append(f"{table}: {len(rows)}")
        conn.execute(
            "INSERT INTO Uploads (upload_id, table_name, filename, mode, row_count, status, message) "
            "VALUES (?, 'bundle', ?, 'append', ?, 'ok', ?)",
            (upload_id, "bundle.json", total, "; ".join(statuses)),
        )
    return {
        "upload_id": upload_id,
        "table_name": "bundle",
        "filename": "bundle.json",
        "mode": "append",
        "row_count": total,
        "status": "ok",
        "message": f"Imported bundle: {', '.join(statuses)}",
        "errors": [],
    }