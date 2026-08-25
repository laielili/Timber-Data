"""Tool: get_source_performance."""
from __future__ import annotations

import sqlite3

from ...services.batches import calculate_batch_metrics
from ...services.common import TimeContext
from ...services.sources import calculate_source_performance
from ..registry import make_provenance, tool
from ..schemas import SourcePerformanceInput, SourcePerformanceOutput


@tool(
    name="get_source_performance",
    description=(
        "Use this tool when the user asks which sourcing categories perform best after recovery "
        "or how much open cost/inspection exposure each source type currently carries. Returns "
        "two separate layers — realised performance (completed batches) and current operational "
        "exposure (open batches) — which must never be merged into one profitability view."
    ),
    business_question="Which sourcing categories perform best after recovery?",
    input_schema=SourcePerformanceInput,
    output_schema=SourcePerformanceOutput,
)
def get_source_performance(inp: SourcePerformanceInput, conn: sqlite3.Connection, ctx: TimeContext) -> dict:
    metrics = calculate_batch_metrics(conn)
    realised_src, open_src = calculate_source_performance(conn, ctx, metrics)
    return {
        "provenance": make_provenance(ctx),
        "realised_source_performance": realised_src,
        "current_operational_exposure": open_src,
        "note": "Two separate layers — never merged into one profitability conclusion.",
    }
