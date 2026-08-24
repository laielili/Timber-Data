"""Workbench — FastAPI application (new application).

Run:  uvicorn new.main:app --reload --port 8100
Docs: http://localhost:8100/docs
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config, db
from .routers import ai, dashboard, meta, upload

app = FastAPI(
    title="Workbench — 数据工作台",
    version="0.1.0",
    description=(
        "用户驱动的数据工作台：上传自己的木材回收数据（timber schema）、"
        "交互式看板（右侧维度筛选）、以及基于已上传数据的 OpenAI 兼容 AI 对话。"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    with db.session() as conn:
        db.init_schema(conn)


app.include_router(upload.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(meta.router)


@app.get("/health", tags=["system"], summary="健康检查")
def health() -> JSONResponse:
    try:
        with db.session() as conn:
            db.init_schema(conn)
            summary = db.dataset_summary(conn)
    except Exception:  # noqa: BLE001
        return JSONResponse(status_code=503, content={"status": "error", "database": "unavailable"})
    return JSONResponse(
        content={
            "status": "ok",
            "database": "connected",
            "dataset_type": "user_uploaded",
            "total_rows": summary["total_rows"],
        }
    )