"""Dashboard analytics — the metric system computed from the uploaded data.

The panel is not a bag of KPIs: it is **one identity plus its drivers**.

    M0 净回收价值 / 入库吨  ≡  M1.2 平均单位价值 × M3.1 处理率  −  M2.2 平均单位成本
                            =  320.00 AUD/处理t  ×  80.00%      −  186.00 AUD/入库t

Three strategy groups feed that identity (S1 value / S2 cost / S3 conversion), a
status matrix reconciles them back to the same number, and a small guardrail set
stops the North Star from being gamed. Design layer:
`documents/data/metric_system.md`; dictionary: `METRIC_DICTIONARY.md`; time bases:
`TIME_SEMANTICS.md`.

Scope rules
-----------
- *batch scope*: batch-level dimensions (source_type, region, batch_status,
  current_stage) plus material-derived dimensions (species, material_form) and
  recovery_route. Material dimensions select the *batches* containing matching
  materials; all metrics stay batch-level.
- *period scope*: date range applied to the natural date column of each table
  (arrival_date / output_date / cost_date).

Two calibration rules — they are exactly what makes the identity hold, so do not
"fix" either one in isolation:
- value is measured **per processed tonne**, cost **per incoming tonne**; the
  processing rate is the conversion factor between the two. Every metric that
  carries a tonne denominator says *which* tonne in its ``basis`` string.
- cost is the **full Core-5 ledger**, including cost already sunk on batches with
  no output yet. Dropping those tonnes from the numerator while keeping the
  processed-tonne denominator silently converts M0 into an Output-pool figure
  (111.50 instead of 70.00 on the sample dataset).

When no data has been uploaded the dashboard reports ``empty`` so the frontend
can show a friendly prompt.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Optional

from . import db
from .schemas import FilterParams

# Cost categories that make up M2.1. Transport / Other are deliberately excluded;
# if they are ever admitted here the North Star has to be recomputed.
CORE5: tuple[str, ...] = (
    "Sorting Labour",
    "Inspection",
    "Processing",
    "Special Handling",
    "Disposal",
)
_CORE5_SQL = "(" + ", ".join(f"'{c}'" for c in CORE5) + ")"
# Split by attribution rule (metric_system.md §4.2): the first pair lands on every
# tonne, the rest only on tonnes that actually produced an output.
_SPREAD_SQL = "('Sorting Labour', 'Inspection')"
_OUTPUT_ONLY_SQL = "('Processing', 'Special Handling', 'Disposal')"

# Grade ordering for the downgrade guardrail. Alphabetical comparison is wrong
# ('Feedstock' > 'Character' as strings), so ranking is explicit.
GRADE_RANK: dict[str, int] = {"Feedstock": 1, "Rustic": 2, "Character": 3, "Premium": 4}
_GRADE_RANK_SQL = (
    "CASE {col} WHEN 'Premium' THEN 4 WHEN 'Character' THEN 3 "
    "WHEN 'Rustic' THEN 2 WHEN 'Feedstock' THEN 1 ELSE 0 END"
)

STATE_ORDER: tuple[str, ...] = ("Output", "In Progress", "Pending Processing", "Unresolved")

# Guardrail bands — (green_edge, amber_edge) plus which way is worse. A guardrail
# without a band is just another KPI, so every guardrail carries all three levels.
#
# The numbers are operational heuristics, not statistics. A recovery line always
# carries *some* loss-making batches and *some* downgrades, so the green bands sit
# where normal variation ends rather than at zero. `gr_net_margin` is deliberately
# expressed as a margin (net ÷ recovered value) rather than an absolute, because
# an absolute AUD threshold would be meaningless across different intake volumes.
GUARDRAIL_BANDS: dict[str, tuple[float, float, str]] = {
    # id                        green   amber   direction
    "gr_loss_batch_share":     (20.0,  35.0,  "higher_is_worse"),
    "gr_downgrade_rate":       (10.0,  20.0,  "higher_is_worse"),
    "gr_record_completeness":  (95.0,  80.0,  "lower_is_worse"),
    "gr_inspection_gap":       ( 0.0,   2.0,  "higher_is_worse"),
    # band applies to net ÷ recovered value, not to the absolute AUD it displays
    "gr_net_value":            (25.0,   0.0,  "lower_is_worse"),
}


def _level(value: float, gr_id: str) -> str:
    """ok | warn | severe for a guardrail reading."""
    green, amber, worse = GUARDRAIL_BANDS[gr_id]
    if worse == "higher_is_worse":
        if value <= green:
            return "ok"
        return "warn" if value <= amber else "severe"
    if value >= green:
        return "ok"
    return "warn" if value >= amber else "severe"


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


def _scalar(conn: sqlite3.Connection, sql: str, params: dict, key: str = "v") -> float:
    return float(_fetch_one(conn, sql, params).get(key) or 0.0)


# --------------------------------------------------------------------------- KPI
def _totals(conn: sqlite3.Connection, scope: _Scope) -> dict:
    """The five raw quantities every metric in the system is built from."""
    bwhere = scope.batch_where("b", "sp")

    incoming = _scalar(
        conn,
        f"""
        SELECT COALESCE(SUM(b.incoming_weight_t),0) AS v FROM Batches b
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE {bwhere} AND {scope.period_where('b.arrival_date')}
        """,
        scope.params,
    )

    outs = _fetch_one(
        conn,
        f"""
        SELECT COALESCE(SUM(o.weight_t),0) AS processed,
               COALESCE(SUM(CASE WHEN o.recovery_route='Higher-value Recovery'
                                 THEN o.weight_t ELSE 0 END),0) AS hv,
               COALESCE(SUM(o.gross_value_aud),0) AS gross
        FROM RecoveryOutputs o JOIN Batches b ON b.batch_id = o.batch_id
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE {bwhere} AND {scope.period_where('o.output_date')}
        """,
        scope.params,
    )

    cost = _scalar(
        conn,
        f"""
        SELECT COALESCE(SUM(c.total_cost_aud),0) AS v FROM CostLedger c
        JOIN Batches b ON b.batch_id = c.batch_id
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE {bwhere} AND {scope.period_where('c.cost_date')}
          AND c.cost_category IN {_CORE5_SQL}
        """,
        scope.params,
    )

    state_rows = _fetch_all(
        conn,
        f"""
        SELECT m.resolution_status AS state, SUM(m.estimated_weight_kg)/1000.0 AS wt
        FROM Materials m JOIN Batches b ON b.batch_id = m.batch_id
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE {bwhere} GROUP BY m.resolution_status
        """,
        scope.params,
    )
    states = {r["state"]: float(r["wt"]) for r in state_rows}

    return {
        "incoming_t": incoming,
        "processed_t": float(outs["processed"]),
        "hv_t": float(outs["hv"]),
        "gross_value_aud": float(outs["gross"]),
        "cost_aud": cost,
        "states": states,
    }


def _north_star(t: dict) -> dict:
    """M0 — the one number everything else has to explain."""
    inc = t["incoming_t"]
    proc = t["processed_t"]
    net = t["gross_value_aud"] - t["cost_aud"]
    return {
        "id": "net_recovery_value_per_incoming_t",
        "label": "净回收价值 / 入库吨",
        "value": _r2(net / inc) if inc else 0.0,
        "unit": "AUD/t",
        "net_value_aud": _r2(net),
        "incoming_t": round(inc, 1),
        "processed_t": round(proc, 3),
        "basis": "期间内产出与成本 ÷ 期间内到达",
        "description": (
            "回收价值总额减去回收成本总额，再除以期间入库吨，即每一入库吨净赚多少。"
            "分子是至今累计（含已沉没成本），分母是期间入库 —— 这是运营管理度量，不是会计利润。"
        ),
        "expression": {
            "value_per_processed_t": _r2(t["gross_value_aud"] / proc) if proc else 0.0,
            "processing_rate": _pct(proc, inc),
            "cost_per_incoming_t": _r2(t["cost_aud"] / inc) if inc else 0.0,
        },
        # Design-layer metadata only. Not rendered anywhere in the UI — the M-codes
        # are scaffolding for whoever maintains the metric system, not for readers.
        "identity": "M0 ≡ M1.2 × M3.1 − M2.2",
    }


def _top_cost_category(conn: sqlite3.Connection, scope: _Scope) -> str:
    row = _fetch_one(
        conn,
        f"""
        SELECT c.cost_category AS k FROM CostLedger c
        JOIN Batches b ON b.batch_id = c.batch_id
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE {scope.batch_where('b', 'sp')} AND {scope.period_where('c.cost_date')}
          AND c.cost_category IN {_CORE5_SQL}
        GROUP BY c.cost_category ORDER BY SUM(c.total_cost_aud) DESC LIMIT 1
        """,
        scope.params,
    )
    return str(row.get("k") or "—")


def _kpi_trends(conn: sqlite3.Connection, scope: _Scope, top_category: str) -> dict[str, list[float]]:
    """Monthly series behind each KPI — the card sparklines read from this.

    Only metrics with a real time column get a series. **未决率 and 在途率 are
    snapshots**: `Materials.resolution_status` is a current state and unresolved
    material never got an `output_date`, so there is no history to plot. They come
    back as empty lists and those cards render no sparkline at all, rather than a
    fabricated one.
    """
    keys = (
        "value_per_processed_t", "value_total", "hv_rate",
        "cost_per_incoming_t", "cost_total", "cost_top_share",
        "processing_rate", "unresolved_rate", "inflight_rate",
    )
    months = _months(conn, scope, scope.f.period_start, scope.f.period_end)
    if not months:
        return {k: [] for k in keys}

    bwhere = scope.batch_where("b", "sp")

    incoming = {r["m"]: float(r["v"]) for r in _fetch_all(conn, f"""
        SELECT substr(b.arrival_date,1,7) AS m, SUM(b.incoming_weight_t) AS v
        FROM Batches b JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} GROUP BY m""", scope.params)}

    outs = {r["m"]: r for r in _fetch_all(conn, f"""
        SELECT substr(o.output_date,1,7) AS m, SUM(o.weight_t) AS wt,
               SUM(o.gross_value_aud) AS gross,
               SUM(CASE WHEN o.recovery_route='Higher-value Recovery' THEN o.weight_t ELSE 0 END) AS hv
        FROM RecoveryOutputs o JOIN Batches b ON b.batch_id=o.batch_id
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} GROUP BY m""", scope.params)}

    costs = {r["m"]: float(r["v"]) for r in _fetch_all(conn, f"""
        SELECT substr(c.cost_date,1,7) AS m, SUM(c.total_cost_aud) AS v
        FROM CostLedger c JOIN Batches b ON b.batch_id=c.batch_id
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} AND c.cost_category IN {_CORE5_SQL} GROUP BY m""", scope.params)}

    scope.params["d_top_cat"] = top_category
    top = {r["m"]: float(r["v"]) for r in _fetch_all(conn, f"""
        SELECT substr(c.cost_date,1,7) AS m, SUM(c.total_cost_aud) AS v
        FROM CostLedger c JOIN Batches b ON b.batch_id=c.batch_id
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} AND c.cost_category = :d_top_cat GROUP BY m""", scope.params)}

    series: dict[str, list[float]] = {k: [] for k in keys}
    for m in months:
        inc_m = incoming.get(m, 0.0)
        row = outs.get(m, {})
        proc_m = float(row.get("wt") or 0.0)
        gross_m = float(row.get("gross") or 0.0)
        hv_m = float(row.get("hv") or 0.0)
        cost_m = costs.get(m, 0.0)
        series["value_total"].append(_r2(gross_m))
        series["value_per_processed_t"].append(_r2(gross_m / proc_m) if proc_m else 0.0)
        series["hv_rate"].append(_pct(hv_m, proc_m))
        series["cost_total"].append(_r2(cost_m))
        series["cost_per_incoming_t"].append(_r2(cost_m / inc_m) if inc_m else 0.0)
        series["cost_top_share"].append(_pct(top.get(m, 0.0), cost_m))
        series["processing_rate"].append(_pct(proc_m, inc_m))
    return series


def _kpi(conn, scope: _Scope, t: dict, trends: dict[str, list[float]], top_cat: str) -> list[dict]:
    inc = t["incoming_t"]
    proc = t["processed_t"]
    cost = t["cost_aud"]
    gross = t["gross_value_aud"]
    states = t["states"]

    scope.params["d_top_cat"] = top_cat
    top_share_value = _scalar(
        conn,
        f"""
        SELECT COALESCE(SUM(c.total_cost_aud),0) AS v FROM CostLedger c
        JOIN Batches b ON b.batch_id = c.batch_id
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE {scope.batch_where('b', 'sp')} AND {scope.period_where('c.cost_date')}
          AND c.cost_category = :d_top_cat
        """,
        scope.params,
    )

    inflight = states.get("In Progress", 0.0) + states.get("Pending Processing", 0.0)
    unresolved = states.get("Unresolved", 0.0)

    return [
        # Ordering: within each group the term the identity reads leads, then the
        # supporting breakdowns. Do not re-sort these numerically.
        #
        # Descriptions are written for a *reader*, not for the design layer: they
        # name other metrics in words instead of by M-code, and they carry no
        # observed values — the card face already shows the value, and the hover
        # annotation is meant to define the metric, not restate the data. The
        # M-codes live in `documents/data/metric_system.md`.
        #
        # ---- S1 价值端：让每一吨卖出更高价值 --------------------------------
        _kpi_item("value_per_processed_t", "平均单位价值", _r2(gross / proc) if proc else 0.0,
                  "AUD/处理t", "期间内产出 ÷ 处理量",
                  "回收价值总额 ÷ 处理量，即每一处理吨平均卖出多少钱。基准是处理吨。", "s1",
                  "提高每一吨已处理木材的售价", trends["value_per_processed_t"]),
        _kpi_item("value_total", "回收价值总额", _r2(gross), "AUD", "期间内产出",
                  "期间内回收产出的毛价值合计，尚未扣减任何成本。", "s1",
                  "提高每一吨已处理木材的售价", trends["value_total"]),
        _kpi_item("hv_rate", "高值回收率", _pct(t["hv_t"], proc), "%", "期间内产出",
                  "高值回收去向的重量 ÷ 处理量，衡量有多少吨卖出了高单价。", "s1",
                  "提高每一吨已处理木材的售价", trends["hv_rate"]),
        # ---- S2 成本端：让每一吨消耗更低 ------------------------------------
        _kpi_item("cost_per_incoming_t", "平均单位成本", _r2(cost / inc) if inc else 0.0,
                  "AUD/入库t", "期间内成本 ÷ 入库量",
                  "回收成本总额 ÷ 入库量，即每一入库吨平均花了多少钱。基准是入库吨。", "s2",
                  "降低每一吨入库木材的核心回收成本", trends["cost_per_incoming_t"]),
        _kpi_item("cost_total", "回收成本总额 Core-5", _r2(cost), "AUD", "期间内成本台账",
                  "Core-5 成本合计：分拣、检验、处理、特殊处理、处置五类，不含运输与其他。", "s2",
                  "降低每一吨入库木材的核心回收成本", trends["cost_total"]),
        _kpi_item("cost_top_share", f"最大成本项占比 · {top_cat}",
                  _pct(float(top_share_value) or 0, cost), "%", "期间内成本台账",
                  "成本结构中占比最大的一类，占回收成本总额的比例。明细见成本结构图。", "s2",
                  "降低每一吨入库木材的核心回收成本", trends["cost_top_share"]),
        # ---- S3 转化端：让更多入库吨成为产出 --------------------------------
        _kpi_item("processing_rate", "处理率", _pct(proc, inc), "%", "期间内产出 ÷ 期间内到达",
                  "处理量 ÷ 入库量，衡量收进来的吨有多少已经变成产出。", "s3",
                  "让更多入库吨成为已产出", trends["processing_rate"]),
        # snapshot metrics: no time column exists, so no series — see _kpi_trends
        _kpi_item("unresolved_rate", "未决率", _pct(unresolved, inc), "%", "快照",
                  "状态为未决的物料重量 ÷ 入库量。未决吨既没有实现价值，成本也已沉没。", "s3",
                  "让更多入库吨成为已产出", trends["unresolved_rate"]),
        _kpi_item("inflight_rate", "在途率", _pct(inflight, inc), "%", "快照",
                  "状态为在途或待处理的物料重量 ÷ 入库量。这些吨成本已付、价值尚未实现。", "s3",
                  "让更多入库吨成为已产出", trends["inflight_rate"]),
    ]


def _kpi_item(kpi_id: str, label: str, value: float, unit: str, basis: str, desc: str,
              group: str, group_label: str, trend: list[float]) -> dict:
    return {
        "id": kpi_id, "label": label, "value": value, "unit": unit,
        "basis": basis, "description": desc,
        "group": group, "group_label": group_label,
        # monthly series for the card sparkline; [] when the metric is a snapshot
        "trend": trend,
    }


# --------------------------------------------------------------------------- guardrails
def _guardrails(conn, scope: _Scope, t: dict) -> list[dict]:
    """Metrics that exist to stop the North Star being gamed. Each one is a
    counterweight to a specific way of inflating M0."""
    bwhere = scope.batch_where("b", "sp")
    inc = t["incoming_t"]
    proc = t["processed_t"]

    # 规模：绝对值。充分母（少收货）能抬高每吨比率，但绝对净价值会掉。预警线按
    # 「净额 ÷ 回收价值」判定——绝对 AUD 阈值换个收货体量就没有意义了。
    net_value = t["gross_value_aud"] - t["cost_aud"]
    net_margin = _pct(net_value, t["gross_value_aud"])

    # 分布：均值掩盖。北极星为正，不代表多数批次为正。
    batch_rows = _fetch_all(
        conn,
        f"""
        SELECT b.batch_id,
          (SELECT COALESCE(SUM(o.gross_value_aud),0) FROM RecoveryOutputs o
            WHERE o.batch_id = b.batch_id) AS gross,
          (SELECT COALESCE(SUM(c.total_cost_aud),0) FROM CostLedger c
            WHERE c.batch_id = b.batch_id AND c.cost_category IN {_CORE5_SQL}) AS cost
        FROM Batches b JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE {bwhere} AND {scope.period_where('b.arrival_date')}
        """,
        scope.params,
    )
    loss_n = sum(1 for r in batch_rows if float(r["gross"]) - float(r["cost"]) < 0)
    loss_share = _pct(loss_n, len(batch_rows))

    # 品质：为冲高值率而过度定级，最终会在实际定级时降级。
    # `Unresolved` appears as a fifth value in both grade columns, but it is a
    # *status*, not a grade — it ranks 0, so both sides must be rank > 0 or a
    # material that was graded and later went Unresolved would read as a downgrade.
    down_t = _scalar(
        conn,
        f"""
        SELECT COALESCE(SUM(m.estimated_weight_kg),0)/1000.0 AS v
        FROM Materials m JOIN Batches b ON b.batch_id = m.batch_id
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE {bwhere}
          AND {_GRADE_RANK_SQL.format(col='m.recovery_grade')} > 0
          AND {_GRADE_RANK_SQL.format(col='m.initial_recovery_grade')} > 0
          AND {_GRADE_RANK_SQL.format(col='m.recovery_grade')}
              < {_GRADE_RANK_SQL.format(col='m.initial_recovery_grade')}
        """,
        scope.params,
    )
    downgrade_rate = _pct(down_t, proc)

    # 度量：记录不全，上面所有数字都失去审计基础。
    complete_t = _scalar(
        conn,
        f"""
        SELECT COALESCE(SUM(CASE WHEN m.record_completeness='Complete'
                                 THEN m.estimated_weight_kg ELSE 0 END),0)/1000.0 AS v
        FROM Materials m JOIN Batches b ON b.batch_id = m.batch_id
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE {bwhere} AND {scope.period_where('b.arrival_date')}
        """,
        scope.params,
    )
    completeness = _pct(complete_t, inc)

    # 履约：为省检验成本而漏检（快照，不随期间变化）。
    gap = _fetch_one(
        conn,
        f"""
        SELECT COUNT(*) AS flagged,
               SUM(CASE WHEN NOT EXISTS (SELECT 1 FROM InspectionEvents e
                                         WHERE e.material_id = m.material_id)
                        THEN 1 ELSE 0 END) AS missed
        FROM Materials m JOIN Batches b ON b.batch_id = m.batch_id
        JOIN SourceProjects sp ON sp.source_id = b.source_id
        WHERE m.requires_inspection = 'Yes' AND {bwhere}
        """,
        scope.params,
    )
    inspection_gap = _pct(float(gap.get("missed") or 0), float(gap.get("flagged") or 0))

    return [
        _guardrail("gr_net_value", "规模护栏 · 绝对净回收价值", _r2(net_value), "AUD",
                   "期间内产出与成本", _level(net_margin, "gr_net_value"),
                   f"北极星是比率，缩分母（少收货）就能把它抬高，但绝对净价值会掉，两者必须一起看。"
                   f"预警线按净额占回收价值的比例判定：低于 {GUARDRAIL_BANDS['gr_net_value'][0]:.0f}% 转黄，"
                   f"归零或为负转红。"),
        _guardrail("gr_loss_batch_share", "分布护栏 · 亏损批次占比", loss_share, "%",
                   "期间内批次", _level(loss_share, "gr_loss_batch_share"),
                   f"均值掩盖结构：北极星为正不代表多数批次为正。"
                   f"绿灯 ≤ {GUARDRAIL_BANDS['gr_loss_batch_share'][0]:.0f}%，"
                   f"{GUARDRAIL_BANDS['gr_loss_batch_share'][1]:.0f}% 以上转红。"),
        _guardrail("gr_downgrade_rate", "品质护栏 · 降级率", downgrade_rate, "%",
                   "期间内产出 ÷ 处理量", _level(downgrade_rate, "gr_downgrade_rate"),
                   f"为冲高值回收率而过度定级，会在实际定级时暴露为降级。"
                   f"绿灯 ≤ {GUARDRAIL_BANDS['gr_downgrade_rate'][0]:.0f}%，"
                   f"{GUARDRAIL_BANDS['gr_downgrade_rate'][1]:.0f}% 以上转红。"),
        _guardrail("gr_record_completeness", "度量护栏 · 记录完整率", completeness, "%",
                   "期间内到达批次物料", _level(completeness, "gr_record_completeness"),
                   f"记录不完整的吨越多，上面所有指标越不可审计。"
                   f"绿灯 ≥ {GUARDRAIL_BANDS['gr_record_completeness'][0]:.0f}%，"
                   f"低于 {GUARDRAIL_BANDS['gr_record_completeness'][1]:.0f}% 转红。"),
        _guardrail("gr_inspection_gap", "履约护栏 · 应检未检率", inspection_gap, "%",
                   "快照", _level(inspection_gap, "gr_inspection_gap"),
                   f"裁检验成本最直接的办法是漏检；本项盯住标记需检验却没有检验记录的物料。"
                   f"绿灯 = {GUARDRAIL_BANDS['gr_inspection_gap'][0]:.0f}%，"
                   f"高于 {GUARDRAIL_BANDS['gr_inspection_gap'][1]:.0f}% 转红。"),
    ]


def _guardrail(gr_id: str, label: str, value: float, unit: str, basis: str,
               level: str, desc: str) -> dict:
    return {"id": gr_id, "label": label, "value": value, "unit": unit,
            "basis": basis, "level": level, "description": desc}


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
        return {"id": "monthly_trend", "title": "月度趋势", "type": "bar",
                "group": "drivers", "rows": []}

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
        WHERE {bwhere} AND c.cost_category IN {_CORE5_SQL}
        GROUP BY m
        """,
        scope.params,
    )
    in_map = {r["m"]: r["v"] for r in incoming}
    out_map = {r["m"]: r for r in outs}
    cost_map = {r["m"]: r["v"] for r in costs}
    rows = []
    for m in months:
        gross = float(out_map.get(m, {}).get("gross", 0) or 0)
        cost = float(cost_map.get(m, 0) or 0)
        rows.append({
            "month": m,
            "incoming_t": round(float(in_map.get(m, 0)), 1),
            "processed_t": round(float(out_map.get(m, {}).get("wt", 0) or 0), 3),
            "gross_value_aud": _r2(gross),
            "cost_aud": _r2(cost),
            "net_value_aud": _r2(gross - cost),
        })
    return {
        "id": "monthly_trend", "title": "月度趋势", "type": "bar", "group": "drivers",
        "bars": ["incoming_t", "processed_t"],
        "lines": ["net_value_aud"],
        "dual_axis": True,
        "rows": rows,
    }


def _chart_state_matrix(conn, scope: _Scope, t: dict) -> dict:
    """§4.2 attribution (方案 B) — the reconciliation point of all three strategies.

    Sorting + Inspection are borne by *every* tonne; Processing / Special Handling
    / Disposal only by tonnes that produced an output; value only ever on Output.
    The four rows must sum back to M0, which is what makes the panel auditable.
    """
    bwhere = scope.batch_where("b", "sp")

    spread = _scalar(
        conn,
        f"""
        SELECT COALESCE(SUM(c.total_cost_aud),0) AS v FROM CostLedger c
        JOIN Batches b ON b.batch_id=c.batch_id
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} AND {scope.period_where('c.cost_date')}
          AND c.cost_category IN {_SPREAD_SQL}
        """,
        scope.params,
    )
    output_only = _scalar(
        conn,
        f"""
        SELECT COALESCE(SUM(c.total_cost_aud),0) AS v FROM CostLedger c
        JOIN Batches b ON b.batch_id=c.batch_id
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} AND {scope.period_where('c.cost_date')}
          AND c.cost_category IN {_OUTPUT_ONLY_SQL}
        """,
        scope.params,
    )

    states = t["states"]
    total_wt = sum(states.values())
    spread_rate = (spread / total_wt) if total_wt else 0.0
    output_wt = states.get("Output", 0.0)

    rows = []
    for state in STATE_ORDER:
        wt = float(states.get(state, 0.0))
        if not wt and state not in states:
            continue
        is_output = state == "Output"
        cost = spread_rate * wt + (output_only if is_output else 0.0)
        value = t["gross_value_aud"] if is_output else 0.0
        net = value - cost
        rows.append({
            "state": state,
            "weight_t": round(wt, 2),
            "weight_pct": _pct(wt, total_wt),
            "cost_aud": _r2(cost),
            "value_aud": _r2(value),
            "net_aud": _r2(net),
            "net_per_t": _r2(net / wt) if wt else 0.0,
        })

    return {
        "id": "state_matrix", "title": "状态矩阵 · 三条策略的汇合点", "type": "matrix",
        "group": "matrix",
        "columns": [
            {"key": "state", "label": "状态", "type": "text"},
            {"key": "weight_t", "label": "重量 t", "type": "num", "format": "weight"},
            {"key": "cost_aud", "label": "归属成本 AUD", "type": "num", "format": "money"},
            {"key": "value_aud", "label": "归属价值 AUD", "type": "num", "format": "money"},
            {"key": "net_aud", "label": "净贡献 AUD", "type": "num", "format": "money"},
            {"key": "net_per_t", "label": "每吨净 AUD", "type": "num", "format": "per_t"},
        ],
        "rows": rows,
        # carried so the frontend can show the reconciliation without recomputing
        "total": {
            "weight_t": round(total_wt, 2),
            "cost_aud": _r2(sum(r["cost_aud"] for r in rows)),
            "value_aud": _r2(sum(r["value_aud"] for r in rows)),
            "net_aud": _r2(sum(r["net_aud"] for r in rows)),
            "net_per_t": _r2(sum(r["net_aud"] for r in rows) / total_wt) if total_wt else 0.0,
        },
        "output_wt": round(output_wt, 2),
    }


def _chart_cost_structure(conn, scope: _Scope) -> dict:
    """M2.3 — which cost lever actually matters."""
    rows = _fetch_all(
        conn,
        f"""
        SELECT c.cost_category AS category, SUM(c.total_cost_aud) AS v FROM CostLedger c
        JOIN Batches b ON b.batch_id=c.batch_id
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {scope.batch_where('b', 'sp')} AND {scope.period_where('c.cost_date')}
          AND c.cost_category IN {_CORE5_SQL}
        GROUP BY c.cost_category ORDER BY v DESC
        """,
        scope.params,
    )
    total = sum(float(r["v"]) for r in rows)
    out = [{"category": r["category"], "cost_aud": _r2(r["v"]), "percentage": _pct(float(r["v"]), total)}
           for r in rows]
    return {"id": "cost_structure", "title": "成本结构", "type": "bar", "group": "drivers",
            "bars": ["cost_aud"], "rows": out}


def _chart_grade_structure(conn, scope: _Scope) -> dict:
    """M1.5 — M1.2 ≡ Σ(等级占比 × 等级单价), so structure and price must be read together."""
    rows = _fetch_all(
        conn,
        f"""
        SELECT o.recovery_grade AS grade, SUM(o.weight_t) AS wt,
               SUM(o.gross_value_aud) AS gross
        FROM RecoveryOutputs o JOIN Batches b ON b.batch_id=o.batch_id
        JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {scope.batch_where('b', 'sp')} AND {scope.period_where('o.output_date')}
        GROUP BY o.recovery_grade
        """,
        scope.params,
    )
    total = sum(float(r["wt"]) for r in rows)
    out = []
    for r in rows:
        wt = float(r["wt"])
        gross = float(r["gross"])
        out.append({
            "grade": r["grade"],
            "weight_t": round(wt, 2),
            "percentage": _pct(wt, total),
            "gross_value_aud": _r2(gross),
            "unit_value_aud_per_t": _r2(gross / wt) if wt else 0.0,
        })
    out.sort(key=lambda r: GRADE_RANK.get(str(r["grade"]), 0), reverse=True)
    return {"id": "grade_structure", "title": "等级结构", "type": "bar", "group": "drivers",
            "bars": ["weight_t"], "lines": ["unit_value_aud_per_t"], "dual_axis": True, "rows": out}


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
    return {"id": "route_distribution", "title": "回收去向分布", "type": "pie",
            "group": "slices", "rows": out}


def _chart_batches(conn, scope: _Scope) -> dict:
    bwhere = scope.batch_where("b", "sp")
    rows = _fetch_all(
        conn,
        f"""
        SELECT b.batch_id, b.incoming_weight_t,
          (SELECT COALESCE(SUM(o.weight_t),0) FROM RecoveryOutputs o WHERE o.batch_id=b.batch_id) AS processed_t,
          (SELECT COALESCE(SUM(o.gross_value_aud),0) FROM RecoveryOutputs o WHERE o.batch_id=b.batch_id) AS gross_aud,
          (SELECT COALESCE(SUM(c.total_cost_aud),0) FROM CostLedger c
            WHERE c.batch_id=b.batch_id AND c.cost_category IN {_CORE5_SQL}) AS cost_aud,
          sp.source_type
        FROM Batches b JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} AND {scope.period_where('b.arrival_date')}
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
            "processing_rate": _pct(processed, inc),
            # every per-tonne figure below is per **incoming** tonne, so batch rows
            # aggregate straight back to M0; the KPI group uses per-processed-t
            # for M1.2 and says so in its basis string.
            "cost_per_incoming_t": _r2(cost / inc) if inc else 0.0,
            "value_per_incoming_t": _r2(gross / inc) if inc else 0.0,
            "net_per_incoming_t": _r2((gross - cost) / inc) if inc else 0.0,
        })
    return {"id": "batch_economics", "title": "批次经济性", "type": "scatter",
            "group": "slices", "rows": out}


def _chart_source(conn, scope: _Scope) -> dict:
    bwhere = scope.batch_where("b", "sp")
    rows = _fetch_all(
        conn,
        f"""
        SELECT sp.source_type AS k, COUNT(*) AS n, SUM(b.incoming_weight_t) AS wt
        FROM Batches b JOIN SourceProjects sp ON sp.source_id=b.source_id
        WHERE {bwhere} GROUP BY sp.source_type ORDER BY wt DESC
        """,
        scope.params,
    )
    out = [{"key": r["k"], "count": int(r["n"]), "weight_t": round(float(r["wt"]), 1)} for r in rows]
    return {"id": "source_distribution", "title": "来源结构", "type": "bar",
            "group": "slices", "bars": ["weight_t"], "rows": out}


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
    out = [{"key": r["k"], "count": int(r["n"]), "weight_t": round(float(r["kg"]) / 1000.0, 2)}
           for r in rows]
    return {"id": "species_distribution", "title": "物料组成", "type": "bar",
            "group": "slices", "bars": ["weight_t"], "rows": out}


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


# Legend labels per chart series, so a reader is never shown a raw column name
# like `incoming_t` or `unit_value_aud_per_t`.
SERIES_LABELS: dict[str, dict[str, str]] = {
    "monthly_trend": {
        "incoming_t": "入库量 (t)",
        "processed_t": "处理量 (t)",
        "net_value_aud": "净回收价值 (AUD)",
    },
    "cost_structure": {"cost_aud": "成本 (AUD)"},
    "grade_structure": {"weight_t": "重量 (t)", "unit_value_aud_per_t": "单位价值 (AUD/t)"},
    "source_distribution": {"weight_t": "入库量 (t)"},
    "species_distribution": {"weight_t": "物料重量 (t)"},
}


# --------------------------------------------------------------------------- entry
def get_dashboard(conn: sqlite3.Connection, f: FilterParams) -> dict:
    scope = _Scope(f)
    summary = db.dataset_summary(conn)
    empty = summary["total_rows"] == 0
    dims = get_dimensions(conn)
    mn, mx = get_period_bounds(conn)
    dims["period_start"] = (f.period_start or mn)
    dims["period_end"] = (f.period_end or mx)

    charts: list[dict] = []
    kpis: list[dict] = []
    guardrails: list[dict] = []
    north_star: Optional[dict] = None

    if not empty:
        t = _totals(conn, scope)
        north_star = _north_star(t)
        top_cat = _top_cost_category(conn, scope)
        kpis = _kpi(conn, scope, t, _kpi_trends(conn, scope, top_cat), top_cat)
        guardrails = _guardrails(conn, scope, t)
        charts = [
            _chart_state_matrix(conn, scope, t),
            _chart_monthly(conn, scope),
            _chart_cost_structure(conn, scope),
            _chart_grade_structure(conn, scope),
            _chart_routes(conn, scope),
            _chart_source(conn, scope),
            _chart_species(conn, scope),
            _chart_batches(conn, scope),
        ]
        for chart in charts:
            if chart["id"] in SERIES_LABELS:
                chart["series_labels"] = SERIES_LABELS[chart["id"]]

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
        "north_star": north_star,
        "kpis": kpis,
        "guardrails": guardrails,
        "charts": charts,
    }
