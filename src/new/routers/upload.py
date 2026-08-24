"""Upload + demo endpoints."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile

from .. import db, demo_service, upload_service
from ..dependencies import get_conn

router = APIRouter(prefix="/api/new", tags=["upload"])


@router.get("/upload/tables", summary="可上传的表及其字段定义")
def list_tables():
    return [
        {
            "table_name": table,
            "primary_key": db.UPLOAD_TABLES[table],
            "columns": [
                {"name": name, "type": ctype, "nullable": nullable, "required": required}
                for name, (ctype, nullable, required) in cols.items()
            ],
        }
        for table, cols in db.SCHEMA.items()
    ]


@router.get("/upload/schema/{table}", summary="某张表的字段定义与示例行")
def table_schema(table: str):
    if table not in db.SCHEMA:
        raise HTTPException(status_code=404, detail=f"未知表 {table}")
    conn = db.connect()
    try:
        example = {}
        row = conn.execute(f'SELECT * FROM "{table}" LIMIT 1').fetchone()
        if row:
            example = dict(row)
    finally:
        conn.close()
    return {
        "table_name": table,
        "primary_key": db.UPLOAD_TABLES[table],
        "columns": [
            {"name": name, "type": ctype, "nullable": nullable, "required": required}
            for name, (ctype, nullable, required) in db.SCHEMA[table].items()
        ],
        "example_row": example,
    }


@router.get("/upload/history", summary="最近的上传记录")
def upload_history(conn: sqlite3.Connection = Depends(get_conn), limit: int = 20):
    rows = conn.execute(
        "SELECT * FROM Uploads ORDER BY created_at DESC LIMIT ?", (max(1, min(limit, 200)),)
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("/upload/csv", summary="上传 CSV 到指定表（multipart）")
async def upload_csv(
    file: UploadFile = File(...),
    table: str = Form(...),
    mode: str = Form("append"),
    conn: sqlite3.Connection = Depends(get_conn),
):
    content = await file.read()
    try:
        result = upload_service.upload_csv(conn, table, file.filename or "upload.csv", content, mode)
    except upload_service.UploadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result


@router.post("/upload/json", summary="上传 JSON 行数据到指定表（multipart）")
async def upload_json(
    file: UploadFile = File(...),
    table: str = Form(...),
    mode: str = Form("append"),
    conn: sqlite3.Connection = Depends(get_conn),
):
    content = await file.read()
    try:
        result = upload_service.upload_json(conn, table, file.filename or "upload.json", content, mode)
    except upload_service.UploadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result


@router.post("/upload/bundle", summary="上传多表 JSON bundle：{\"tables\": {表: {rows: [...]}}}")
async def upload_bundle(
    file: UploadFile = File(...),
    conn: sqlite3.Connection = Depends(get_conn),
):
    content = await file.read()
    try:
        result = upload_service.upload_bundle(conn, content)
    except upload_service.UploadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result


@router.post("/demo", summary="载入合成示例数据（可选，非预设）；mode=replace 时清空现有数据后载入")
def load_demo(mode: str = "append", conn: sqlite3.Connection = Depends(get_conn)):
    if mode not in ("append", "replace"):
        raise HTTPException(status_code=422, detail="mode must be 'append' or 'replace'.")
    try:
        return demo_service.load_demo(conn, mode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except upload_service.UploadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc