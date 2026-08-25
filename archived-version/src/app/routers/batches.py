"""Batch endpoints — list (with filters) and single batch."""
from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_conn
from ..models.api import BatchListResponse, SingleBatchResponse
from ..services.batches import calculate_batch_metrics, assign_economic_quadrants, get_batch_summary, to_batch_summary
from ..services.common import build_meta, default_context

router = APIRouter(prefix="/api/v1", tags=["batches"])

_META = build_meta(default_context())


def _all_summaries(conn: sqlite3.Connection) -> list[dict]:
    metrics = calculate_batch_metrics(conn)
    assign_economic_quadrants(metrics)
    return [to_batch_summary(m) for m in metrics]


@router.get("/batches", response_model=BatchListResponse, summary="List batches")
def list_batches(
    status: Optional[str] = None,
    source_type: Optional[str] = None,
    economic_evaluation_status: Optional[str] = None,
    economic_quadrant: Optional[str] = None,
    conn: sqlite3.Connection = Depends(get_conn),
) -> BatchListResponse:
    """All 36 batches as BatchSummary. Optional simple filters (no complex search yet)."""
    summaries = _all_summaries(conn)
    if status is not None:
        summaries = [s for s in summaries if s["status"] == status]
    if source_type is not None:
        summaries = [s for s in summaries if s["source_type"] == source_type]
    if economic_evaluation_status is not None:
        summaries = [s for s in summaries if s["economic_evaluation_status"] == economic_evaluation_status]
    if economic_quadrant is not None:
        if economic_quadrant.lower() in ("null", "none"):
            summaries = [s for s in summaries if s["economic_quadrant"] is None]
        else:
            summaries = [s for s in summaries if s["economic_quadrant"] == economic_quadrant]
    return BatchListResponse.model_validate({"meta": _META, "batches": summaries})


@router.get("/batches/{batch_id}", response_model=SingleBatchResponse, summary="Single batch")
def get_batch(
    batch_id: str,
    conn: sqlite3.Connection = Depends(get_conn),
) -> SingleBatchResponse:
    """A single BatchSummary. Unknown batch -> HTTP 404 (never an empty batch)."""
    summary = get_batch_summary(conn, batch_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found.")
    return SingleBatchResponse.model_validate({"meta": _META, "batch": summary})
