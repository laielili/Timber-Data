"""Circular Timber Intelligence — Python Backend Phase 01.

Deterministic analytics engine + FastAPI data service over the approved synthetic
SQLite database. READ ONLY. No AI. Contract-compatible JSON responses for the
approved frontend data contract.

Run:  uvicorn app.main:app --reload
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config, db
from .analyst_tools import tools as _analyst_tools  # noqa: F401  (registers analyst tools)
from .routers import analyst, analyst_tools, batches, overview, performance, reports, settings

app = FastAPI(
    title="Circular Timber Intelligence — Analytics Service",
    version="0.1.0",
    description=(
        "Deterministic analytics over the approved synthetic prototype database "
        "(SQLite). All data is synthetic prototype data; no real company, benchmark "
        "or market standard is implied. Read-only for this phase."
    ),
)

# Development CORS for the future React dev server (Backend Phase 02). Isolated here;
# no wildcard production default. The AI Analyst endpoint is a POST; include it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(overview.router)
app.include_router(batches.router)
app.include_router(performance.router)
app.include_router(reports.router)
app.include_router(analyst_tools.router)
app.include_router(analyst.router)
app.include_router(settings.router)


@app.get("/health", tags=["system"], summary="Health check")
def health() -> JSONResponse:
    """Service + database health probe (no /api/v1 prefix)."""
    if not db.database_ok():
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable", "dataset_type": "synthetic_prototype"},
        )
    return JSONResponse(
        content={"status": "ok", "database": "connected", "dataset_type": "synthetic_prototype"}
    )
