"""AI grounding tools — read-only queries over the uploaded data.

The model may only call these tools; it never gets raw SQL or filesystem access.
Each tool returns plain dict/list data that is passed back to the model. Input
schemas are JSON-schema dicts consumed directly by the OpenAI-compatible provider.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Callable, Optional

from . import dashboard_service
from .schemas import FilterParams

TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}


def _coerce(args: dict[str, Any], schema: dict) -> dict[str, Any]:
    """Coerce arguments to the declared types so queries never crash on strings."""
    out: dict[str, Any] = {}
    props = schema.get("properties", {})
    for name, spec in props.items():
        if name not in args:
            continue
        t = TYPE_MAP.get(spec.get("type", "string"))
        try:
            out[name] = t(args[name]) if t is not None and t is not bool else args[name]
        except (TypeError, ValueError):
            out[name] = args[name]
    return out


def _filters_from_args(args: dict[str, Any]) -> FilterParams:
    return FilterParams(**{k: v for k, v in args.items() if v is not None and v != ""})


# --------------------------------------------------------------------------- tools
def _get_dashboard_summary(conn, args: dict) -> dict:
    f = _filters_from_args(_coerce(args, _dashboard_schema))
    dash = dashboard_service.get_dashboard(conn, f)
    return {
        "kpis": dash["kpis"],
        "charts": dash["charts"],
        "filters": dash["filters"],
    }


_dashboard_schema = {
    "type": "object",
    "properties": {
        "period_start": {"type": "string", "description": "起始日期 YYYY-MM-DD"},
        "period_end": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
        "source_type": {"type": "string", "description": "来源类型，如 Municipal / Construction"},
        "region": {"type": "string", "description": "区域"},
        "species": {"type": "string", "description": "树种"},
        "material_form": {"type": "string", "description": "物料形态"},
        "recovery_route": {"type": "string", "description": "回收去向"},
        "batch_status": {"type": "string", "description": "批次状态"},
        "current_stage": {"type": "string", "description": "当前阶段"},
    },
}


def _get_monthly_trend(conn, args: dict) -> dict:
    f = FilterParams(
        period_start=args.get("month_from"),
        period_end=args.get("month_to") + "-31" if args.get("month_to") else None,
    )
    chart = dashboard_service._chart_monthly(conn, dashboard_service._Scope(f))
    return {"rows": chart["rows"]}


def _get_route_distribution(conn, args: dict) -> dict:
    chart = dashboard_service._chart_routes(conn, dashboard_service._Scope(FilterParams()))
    return {"rows": chart["rows"]}


def _get_source_distribution(conn, args: dict) -> dict:
    chart = dashboard_service._chart_source(conn, dashboard_service._Scope(FilterParams()))
    return {"rows": chart["rows"]}


def _get_species_distribution(conn, args: dict) -> dict:
    chart = dashboard_service._chart_species(conn, dashboard_service._Scope(FilterParams()))
    return {"rows": chart["rows"]}


def _list_batches(conn, args: dict) -> dict:
    f = FilterParams(
        source_type=args.get("source_type"),
        region=args.get("region"),
        batch_status=args.get("batch_status"),
        current_stage=args.get("current_stage"),
    )
    chart = dashboard_service._chart_batches(conn, dashboard_service._Scope(f))
    limit = int(args.get("limit") or 50)
    return {"rows": chart["rows"][:limit], "count": len(chart["rows"]), "truncated": len(chart["rows"]) > limit}


def _get_batch_detail(conn, args: dict) -> dict:
    batch_id = str(args.get("batch_id") or "")
    if not batch_id:
        return {"error": "batch_id 不能为空。"}
    batch = conn.execute(
        """
        SELECT b.*, sp.source_type, sp.region FROM Batches b
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE b.batch_id = ?
        """,
        (batch_id,),
    ).fetchone()
    if not batch:
        return {"error": f"批次 {batch_id} 不存在。"}
    materials = conn.execute(
        "SELECT * FROM Materials WHERE batch_id = ?", (batch_id,)
    ).fetchall()
    outputs = conn.execute(
        "SELECT * FROM RecoveryOutputs WHERE batch_id = ?", (batch_id,)
    ).fetchall()
    costs = conn.execute(
        "SELECT cost_category, SUM(total_cost_aud) AS total FROM CostLedger WHERE batch_id = ? GROUP BY cost_category",
        (batch_id,),
    ).fetchall()
    total_cost = sum(float(r["total"]) for r in costs)
    gross = sum(float(r["gross_value_aud"]) for r in outputs)
    processed = sum(float(r["weight_t"]) for r in outputs)
    return {
        "batch": dict(batch),
        "materials_count": len(materials),
        "materials_weight_kg": sum(float(r["estimated_weight_kg"]) for r in materials),
        "outputs": [dict(r) for r in outputs],
        "costs_by_category": [dict(r) for r in costs],
        "total_cost_aud": round(total_cost, 2),
        "gross_value_aud": round(gross, 2),
        "processed_t": round(processed, 3),
        "net_value_aud": round(gross - total_cost, 2),
    }


# --------------------------------------------------------------------------- registry
class Tool:
    def __init__(self, name: str, description: str, input_schema: dict, func: Callable[[Any, dict], dict]):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.func = func

    def run(self, conn: sqlite3.Connection, args: dict) -> dict:
        try:
            return {"success": True, "data": self.func(conn, args)}
        except Exception as exc:  # noqa: BLE001 - structured boundary for the model
            return {"success": False, "error": str(exc)}


def _list_batches_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "source_type": {"type": "string"},
            "region": {"type": "string"},
            "batch_status": {"type": "string"},
            "current_stage": {"type": "string"},
            "limit": {"type": "integer", "description": "最多返回多少批次，默认 50"},
        },
    }


def _batch_detail_schema() -> dict:
    return {"type": "object", "properties": {"batch_id": {"type": "string"}}, "required": ["batch_id"]}


def _monthly_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "month_from": {"type": "string", "description": "起始月份 YYYY-MM"},
            "month_to": {"type": "string", "description": "结束月份 YYYY-MM"},
        },
    }


TOOLS: list[Tool] = [
    Tool(
        "get_dashboard_summary",
        "获取看板汇总：核心指标(KPIs)与主要图表数据。可传维度筛选参数。",
        _dashboard_schema,
        _get_dashboard_summary,
    ),
    Tool(
        "get_monthly_trend",
        "获取月度趋势：入库、处理量、毛价值、成本，按月份。",
        _monthly_schema,
        _get_monthly_trend,
    ),
    Tool(
        "get_route_distribution",
        "获取回收去向分布（各去向的重量与占比）。",
        {"type": "object", "properties": {}},
        _get_route_distribution,
    ),
    Tool(
        "get_source_distribution",
        "获取来源结构（按来源类型的批次与入库重量）。",
        {"type": "object", "properties": {}},
        _get_source_distribution,
    ),
    Tool(
        "get_species_distribution",
        "获取物料组成（按树种的重量分布）。",
        {"type": "object", "properties": {}},
        _get_species_distribution,
    ),
    Tool(
        "list_batches",
        "列出批次及其经济性指标（成本/吨、价值/吨、净价值）。可按来源/区域/状态筛选。",
        _list_batches_schema(),
        _list_batches,
    ),
    Tool(
        "get_batch_detail",
        "查看单个批次详情：基本信息、物料、产出、成本分类、净价值。",
        _batch_detail_schema(),
        _get_batch_detail,
    ),
]

TOOL_BY_NAME: dict[str, Tool] = {t.name: t for t in TOOLS}


def provider_tools() -> list[dict]:
    """JSON-schema tools in the OpenAI tool-call format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.input_schema,
            },
        }
        for t in TOOLS
    ]