"""Dashboard analytics — KPIs + charts computed from the uploaded data.

Every query respects the active dimension filters. Two scopes are combined:

- *batch scope*: batch-level dimensions (source_type, region, batch_status,
  current_stage) plus material-derived dimensions (species, material_form) and
  recovery_route. Material dimensions select the *batches* containing matching
  materials; all metrics stay batch-level.
- *period scope*: date range applied to the natural date column of each table
  (arrival_date / output_date / cost_date).

When no data has been uploaded the dashboard reports ``empty`` so the frontend
can show a friendly prompt.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Optional

from . import db
from .schemas import FilterParams


def _pct(num: float, den: float) -> float:
    return round(num * 100.0 / den, 2) if den else 0.0


def _r2(v: float) -> float:
    return round(float(v), 2)


class _Scope:
    """Builds the SQL fragments + params for the batch scope and period scope."""

    def __init__(self, f: FilterParams):
        self.f = f
        self.params: dict[str, Any] = {}

    # -- batch scope (applies to Batches b / SourceProjects sp) -------------
    def batch_where(self, alias: str = "b", sp_alias: str = "sp") -> str:
        conds: list[str] = []
        p = self.params
        f = self.f
        if f.source_type:
            conds.append(f'{sp_alias}.source_type = :d_st')
            p["d_st"] = f.source_type
        if f.region:
            conds.append(f'{sp_alias}.region = :d_rg')
            p["d_rg"] = f.region
        if f.batch_status:
            conds.append(f'{alias}.batch_status = :d_bs')
            p["d_bs"] = f.batch_status
        if f.current_stage:
            conds.append(f'{alias}.current_stage = :d_cs')
            p["d_cs"] = f.current_stage
        m_conds: list[str] = []
        if f.species:
            m_conds.append("species = :d_sp")
            p["d_sp"] = f.species
        if f.material_form:
            m_conds.append("material_form = :d_mf")
            p["d_mf"] = f.material_form
        if m_conds:
            sub = "SELECT DISTINCT batch_id FROM Materials WHERE " + " AND ".join(m_conds)
            conds.append(f"{alias}.batch_id IN ({sub})")
        if f.recovery_route:
            sub = "SELECT DISTINCT batch_id FROM RecoveryOutputs WHERE recovery_route = :d_rr"
            p["d_rr"] = f.recovery_route
            conds.append(f"{alias}.batch_id IN ({sub})")
        return " AND ".join(conds) if conds else "1=1"

    # -- period scope (applied per date column) -----------------------------
    def period_where(self, col: str) -> str:
        conds: list[str] = []
        p = self.params
        if self.f.period_start:
            conds.append(f"{col} >= :d_ps")
            p["d_ps"] = self.f.period_start
        if self.f.period_end:
            conds.append(f"{col} <= :d_pe")
            p["d_pe"] = self.f.period_end
        return " AND ".join(conds) if conds else "1=1"


def _fetch_all(conn: sqlite3.Connection, sql: str, params: dict) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _fetch_one(conn: sqlite3.Connection, sql: str, params: dict) -> dict:
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row else {}


# --------------------------------------------------------------------------- KPI
def _kpi(conn, scope: _Scope) -> list[dict]:
    bwhere = scope.batch_where("b", "sp")

    incoming = _fetch_one(
        conn,
        f"""
        SELECT COALESCE(SUM(b.incoming_weight_t),0) AS v FROM Batches b
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE {bwhere} AND {scope.period_where('b.arrival_date')}
        """,
        scope.params,
    )["v"]

    out_rows = _fetch_one(
        conn,
        f"""
        SELECT COALESCE(SUM(o.weight_t),0) AS processed,
               COALESCE(SUM(CASE WHEN o.recovery_route='Higher-value Recovery' THEN o.weight_t ELSE 0 END),0) AS hv,
               COALESCE(SUM(o.gross_value_aud),0) AS gross
        FROM RecoveryOutputs o JOIN Batches b ON b.batch_id = o.batch_id
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE {bwhere} AND {scope.period_where('o.output_date')}
        """,
        scope.params,
    )
    processed = float(out_rows["processed"])
    hv = float(out_rows["hv"])
    gross = float(out_rows["gross"])

    cost = _fetch_one(
        conn,
        f"""
        SELECT COALESCE(SUM(c.total_cost_aud),0) AS v FROM CostLedger c
        JOIN Batches b ON b.batch_id = c.batch_id
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE {bwhere} AND {scope.period_where('c.cost_date')}
        """,
        scope.params,
    )["v"]

    unresolved = _fetch_one(
        conn,
        f"""
        SELECT COALESCE(SUM(m.estimated_weight_kg),0) AS v FROM Materials m
        JOIN Batches b ON b.batch_id = m.batch_id
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE m.resolution_status='Unresolved' AND {bwhere}
        """,
        scope.params,
    )["v"] / 1000.0

    kpis = [
        _kpi_item("incoming", "入库量", round(float(incoming), 1), "t",
                  "期间内到达批次", "所选维度下，期间内到达批次的总入库重量。"),
        _kpi_item("processed", "处理量", round(processed, 3), "t",
                  "期间内回收产出", "所选维度下，期间内回收产出的总重量。"),
        _kpi_item("hv_rate", "高值回收率", _pct(hv, processed), "%",
                  "期间内产出", "高值回收去向重量占处理量的比例。"),
        _kpi_item("value_per_t", "回收价值/吨", _r2(gross / processed) if processed else 0.0, "AUD/t",
                  "期间内产出", "毛回收价值 / 处理量。"),
        _kpi_item("cost_per_t", "成本/吨", _r2(float(cost) / processed) if processed else 0.0, "AUD/t",
                  "期间内产出", "成本台账总成本 / 处理量。"),
        _kpi_item("unresolved", "未解决物料", round(unresolved, 2), "t",
                  "快照", "状态为 Unresolved 的物料总重量。"),
    ]
    return kpis


def _kpi_item(kpi_id: str, label: str, value: float, unit: str, basis: str, desc: str) -> dict:
    return {"id": kpi_id, "label": label, "value": value, "unit": unit, "basis": basis, "description": desc}


# --------------------------------------------------------------------------- charts
def _months(conn, scope: _Scope, start: Optional[str], end: Optional[str]) -> list[str]:
    """Contiguous month keys between the data (or filter) bounds."""
    bounds = _fetch_one(
        conn,
        """
        SELECT MIN(x) AS mn, MAX(x) AS mx FROM (
          SELECT substr(arrival_date,1,7) AS x FROM Batches
          UNION SELECT substr(output_date,1,7) FROM RecoveryOutputs
          UNION SELECT substr(cost_date,1,7) FROM CostLedger
        )
        """,
        {},
    )
    lo = (start or bounds.get("mn"))[:7]
    hi = (end or bounds.get("mx"))[:7]
    if not lo or not hi:
        return []
    out, y, m = [], int(lo[:4]), int(lo[5:7])
    hiy, him = int(hi[:4]), int(hi[5:7])
    while (y, m) <= (hiy, him):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def _chart_monthly(conn, scope: _Scope) -> dict:
    months = _months(conn, scope, scope.f.period_start, scope.f.period_end)
    bwhere = scope.batch_where("b", "sp")
    if not months:
        return {"id": "monthly_trend", "title": "月度趋势", "type": "bar", "rows": []}

    incoming = _fetch_all(
        conn,
        f"""
        SELECT substr(b.arrival_date,1,7) AS m, SUM(b.incoming_weight_t) AS v FROM Batches b
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} GROUP BY m
        """,
        scope.params,
    )
    outs = _fetch_all(
        conn,
        f"""
        SELECT substr(o.output_date,1,7) AS m,
               SUM(o.weight_t) AS wt, SUM(o.gross_value_aud) AS gross
        FROM RecoveryOutputs o JOIN Batches b ON b.batch_id=o.batch_id
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} GROUP BY m
        """,
        scope.params,
    )
    costs = _fetch_all(
        conn,
        f"""
        SELECT substr(c.cost_date,1,7) AS m, SUM(c.total_cost_aud) AS v FROM CostLedger c
        JOIN Batches b ON b.batch_id=c.batch_id
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} GROUP BY m
        """,
        scope.params,
    )
    in_map = {r["m"]: r["v"] for r in incoming}
    out_map = {r["m"]: r for r in outs}
    cost_map = {r["m"]: r["v"] for r in costs}
    rows = [
        {
            "month": m,
            "incoming_t": round(float(in_map.get(m, 0)), 1),
            "processed_t": round(float(out_map.get(m, {}).get("wt", 0) or 0), 3),
            "gross_value_aud": _r2(out_map.get(m, {}).get("gross", 0) or 0),
            "cost_aud": _r2(cost_map.get(m, 0) or 0),
        }
        for m in months
    ]
    return {"id": "monthly_trend", "title": "月度趋势", "type": "bar", "rows": rows}


def _chart_routes(conn, scope: _Scope) -> dict:
    bwhere = scope.batch_where("b", "sp")
    rows = _fetch_all(
        conn,
        f"""
        SELECT o.recovery_route AS route, SUM(o.weight_t) AS wt, SUM(o.gross_value_aud) AS gross
        FROM RecoveryOutputs o JOIN Batches b ON b.batch_id=o.batch_id
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} AND {scope.period_where('o.output_date')}
        GROUP BY o.recovery_route ORDER BY wt DESC
        """,
        scope.params,
    )
    total = sum(float(r["wt"]) for r in rows)
    out = [
        {"route": r["route"], "weight_t": round(float(r["wt"]), 2), "gross_value_aud": _r2(r["gross"]),
         "percentage": _pct(float(r["wt"]), total)}
        for r in rows
    ]
    return {"id": "route_distribution", "title": "回收去向分布", "type": "pie", "rows": out}


def _chart_batches(conn, scope: _Scope) -> dict:
    bwhere = scope.batch_where("b", "sp")
    rows = _fetch_all(
        conn,
        f"""
        SELECT b.batch_id, b.incoming_weight_t,
          (SELECT COALESCE(SUM(o.weight_t),0) FROM RecoveryOutputs o WHERE o.batch_id=b.batch_id) AS processed_t,
          (SELECT COALESCE(SUM(o.gross_value_aud),0) FROM RecoveryOutputs o WHERE o.batch_id=b.batch_id) AS gross_aud,
          (SELECT COALESCE(SUM(c.total_cost_aud),0) FROM CostLedger c WHERE c.batch_id=b.batch_id) AS cost_aud,
          sp.source_type
        FROM Batches b JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere}
        ORDER BY b.batch_id
        """,
        scope.params,
    )
    out = []
    for r in rows:
        inc = float(r["incoming_weight_t"])
        processed = float(r["processed_t"])
        gross = float(r["gross_aud"])
        cost = float(r["cost_aud"])
        out.append({
            "batch_id": r["batch_id"],
            "source_type": r["source_type"],
            "incoming_t": round(inc, 1),
            "processed_t": round(processed, 3),
            "gross_value_aud": _r2(gross),
            "cost_aud": _r2(cost),
            "net_value_aud": _r2(gross - cost),
            "cost_per_t": _r2(cost / inc) if inc else 0.0,
            "value_per_t": _r2(gross / inc) if inc else 0.0,
        })
    return {"id": "batch_economics", "title": "批次经济性", "type": "scatter", "rows": out}


def _chart_source(conn, scope: _Scope) -> dict:
    bwhere = scope.batch_where("b", "sp")
    rows = _fetch_all(
        conn,
        f"""
        SELECT sp.source_type AS k, COUNT(*) AS n, SUM(b.incoming_weight_t) AS wt
        FROM Batches b JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere}
        GROUP BY sp.source_type ORDER BY wt DESC
        """,
        scope.params,
    )
    out = [{"key": r["k"], "count": int(r["n"]), "weight_t": round(float(r["wt"]), 1)} for r in rows]
    return {"id": "source_distribution", "title": "来源结构", "type": "bar", "rows": out}


def _chart_species(conn, scope: _Scope) -> dict:
    bwhere = scope.batch_where("b", "sp")
    rows = _fetch_all(
        conn,
        f"""
        SELECT m.species AS k, COUNT(*) AS n, SUM(m.estimated_weight_kg) AS kg
        FROM Materials m JOIN Batches b ON b.batch_id=m.batch_id
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} GROUP BY m.species ORDER BY kg DESC
        """,
        scope.params,
    )
    out = [{"key": r["k"], "count": int(r["n"]), "weight_t": round(float(r["kg"]) / 1000.0, 2)} for r in rows]
    return {"id": "species_distribution", "title": "物料组成", "type": "bar", "rows": out}


def _chart_state(conn, scope: _Scope) -> dict:
    bwhere = scope.batch_where("b", "sp")
    rows = _fetch_all(
        conn,
        f"""
        SELECT m.resolution_status AS k, COUNT(*) AS n, SUM(m.estimated_weight_kg) AS kg
        FROM Materials m JOIN Batches b ON b.batch_id=m.batch_id
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} GROUP BY m.resolution_status ORDER BY kg DESC
        """,
        scope.params,
    )
    out = [{"key": r["k"], "count": int(r["n"]), "weight_t": round(float(r["kg"]) / 1000.0, 2)} for r in rows]
    return {"id": "material_state", "title": "物料状态", "type": "pie", "rows": out}


# --------------------------------------------------------------------------- dimensions
def _distinct(conn, sql: str) -> list[str]:
    return [r[0] for r in conn.execute(sql).fetchall() if r[0]]


def get_dimensions(conn: sqlite3.Connection) -> dict:
    return {
        "period_start": None,
        "period_end": None,
        "source_types": _distinct(conn, "SELECT DISTINCT source_type FROM SourceProjects ORDER BY 1"),
        "regions": _distinct(conn, "SELECT DISTINCT region FROM SourceProjects ORDER BY 1"),
        "species": _distinct(conn, "SELECT DISTINCT species FROM Materials ORDER BY 1"),
        "material_forms": _distinct(conn, "SELECT DISTINCT material_form FROM Materials ORDER BY 1"),
        "recovery_routes": _distinct(conn, "SELECT DISTINCT recovery_route FROM RecoveryOutputs ORDER BY 1"),
        "batch_statuses": _distinct(conn, "SELECT DISTINCT batch_status FROM Batches ORDER BY 1"),
        "current_stages": _distinct(conn, "SELECT DISTINCT current_stage FROM Batches ORDER BY 1"),
    }


def get_period_bounds(conn: sqlite3.Connection) -> tuple[Optional[str], Optional[str]]:
    row = _fetch_one(
        conn,
        """
        SELECT MIN(x) AS mn, MAX(x) AS mx FROM (
          SELECT MIN(arrival_date) AS x FROM Batches
          UNION ALL SELECT MAX(arrival_date) FROM Batches
          UNION ALL SELECT MIN(output_date) FROM RecoveryOutputs
          UNION ALL SELECT MAX(output_date) FROM RecoveryOutputs
        )
        """,
        {},
    )
    return (row.get("mn"), row.get("mx"))


# --------------------------------------------------------------------------- entry
def get_dashboard(conn: sqlite3.Connection, f: FilterParams) -> dict:
    scope = _Scope(f)
    summary = db.dataset_summary(conn)
    empty = summary["total_rows"] == 0
    dims = get_dimensions(conn)
    mn, mx = get_period_bounds(conn)
    dims["period_start"] = (f.period_start or mn)
    dims["period_end"] = (f.period_end or mx)

    charts = []
    kpis = []
    if not empty:
        kpis = _kpi(conn, scope)
        charts = [
            _chart_monthly(conn, scope),
            _chart_routes(conn, scope),
            _chart_batches(conn, scope),
            _chart_source(conn, scope),
            _chart_species(conn, scope),
            _chart_state(conn, scope),
        ]

    return {
        "meta": {
            "dataset_type": "user_uploaded",
            "currency": "AUD",
            "weight_unit": "t",
            "empty": empty,
            "tables": summary["tables"],
            "total_rows": summary["total_rows"],
            "last_upload": summary["last_upload"],
        },
        "filters": f.model_dump(),
        "dimensions": dims,
        "kpis": kpis,
        "charts": charts,
    }