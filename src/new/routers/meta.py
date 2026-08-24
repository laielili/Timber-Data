"""Meta endpoints — dataset summary + API reference (for the in-page API console)."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from .. import db
from ..dependencies import get_conn

router = APIRouter(prefix="/api/new", tags=["meta"])

API_REFERENCE: list[dict] = [
    {
        "method": "POST",
        "path": "/api/new/upload/csv",
        "summary": "上传 CSV 到指定表",
        "content_type": "multipart/form-data",
        "fields": [
            {"name": "file", "type": "file", "required": True, "description": "UTF-8 编码的 CSV，首行为表头"},
            {"name": "table", "type": "string", "required": True, "description": "目标表名，如 Batches"},
            {"name": "mode", "type": "string", "required": False, "description": "append（默认，按主键 upsert）或 replace（清空后写入）"},
        ],
        "example": 'curl -X POST http://localhost:8100/api/new/upload/csv \\\n  -F "table=Batches" -F "mode=append" -F "file=@batches.csv"',
    },
    {
        "method": "POST",
        "path": "/api/new/upload/json",
        "summary": "上传 JSON 行数据到指定表",
        "content_type": "multipart/form-data",
        "fields": [
            {"name": "file", "type": "file", "required": True, "description": 'JSON 文件：{"rows": [...]} 或直接是行数组'},
            {"name": "table", "type": "string", "required": True, "description": "目标表名"},
            {"name": "mode", "type": "string", "required": False, "description": "append / replace"},
        ],
        "example": 'curl -X POST http://localhost:8100/api/new/upload/json \\\n  -F "table=SourceProjects" -F "file=@source_projects.json"',
    },
    {
        "method": "POST",
        "path": "/api/new/upload/bundle",
        "summary": "上传多表 JSON bundle",
        "content_type": "multipart/form-data",
        "fields": [
            {"name": "file", "type": "file", "required": True, "description": '{"tables": {"Batches": {"rows": [...]}, ...}}'},
        ],
        "example": 'curl -X POST http://localhost:8100/api/new/upload/bundle -F "file=@bundle.json"',
    },
    {
        "method": "POST",
        "path": "/api/new/demo",
        "summary": "载入合成示例数据（可选，非预设）",
        "content_type": "application/json",
        "fields": [],
        "example": "curl -X POST http://localhost:8100/api/new/demo",
    },
    {
        "method": "GET",
        "path": "/api/new/upload/tables",
        "summary": "可上传的表及字段定义",
        "content_type": "application/json",
        "fields": [],
        "example": "curl http://localhost:8100/api/new/upload/tables",
    },
    {
        "method": "GET",
        "path": "/api/new/dashboard",
        "summary": "数据看板（支持维度筛选查询参数）",
        "content_type": "application/json",
        "fields": [
            {"name": "period_start", "type": "string", "required": False, "description": "YYYY-MM-DD"},
            {"name": "period_end", "type": "string", "required": False, "description": "YYYY-MM-DD"},
            {"name": "source_type", "type": "string", "required": False, "description": "来源类型"},
            {"name": "region", "type": "string", "required": False, "description": "区域"},
            {"name": "species", "type": "string", "required": False, "description": "树种"},
            {"name": "material_form", "type": "string", "required": False, "description": "物料形态"},
            {"name": "recovery_route", "type": "string", "required": False, "description": "回收去向"},
            {"name": "batch_status", "type": "string", "required": False, "description": "批次状态"},
            {"name": "current_stage", "type": "string", "required": False, "description": "当前阶段"},
        ],
        "example": 'curl "http://localhost:8100/api/new/dashboard?source_type=Municipal&period_start=2025-01-01"',
    },
    {
        "method": "POST",
        "path": "/api/new/ai/chat",
        "summary": "AI 对话（基于已上传数据的问答）",
        "content_type": "application/json",
        "fields": [
            {"name": "messages", "type": "json", "required": True, "description": '[{"role": "user", "content": "..."}]'},
            {"name": "conversation_id", "type": "string", "required": False, "description": "会话 ID（可选）"},
        ],
        "example": 'curl -X POST http://localhost:8100/api/new/ai/chat \\\n  -H "Content-Type: application/json" \\\n  -d \'{"messages": [{"role": "user", "content": "What is the total incoming volume?"}]}\'',
    },
    {
        "method": "POST",
        "path": "/api/new/ai/test",
        "summary": "测试 AI 服务连接",
        "content_type": "application/json",
        "fields": [
            {"name": "base_url", "type": "string", "required": False},
            {"name": "model", "type": "string", "required": False},
            {"name": "api_key", "type": "string", "required": False},
        ],
        "example": 'curl -X POST http://localhost:8100/api/new/ai/test -H "Content-Type: application/json" -d \'{}\'',
    },
]


@router.get("/meta", summary="数据集摘要 + API 参考")
def meta(conn: sqlite3.Connection = Depends(get_conn)):
    return {"dataset": db.dataset_summary(conn), "api_reference": API_REFERENCE}