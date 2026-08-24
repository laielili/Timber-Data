#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workbench — 数据工作台 demo 数据集生成器（Phase 2：净回收价值指标体系版）。

设计蓝本：docs/data/sample_data_design.md（v1.0）+ docs/data/metric_system.md。
原则：自顶向下、恒等式优先、池预算先行、每个指标一个叙事。

恒等式（分位级精确）：
    M0 = 平均单位价值 320.00 x 处理率 80.00% - 平均单位成本 186.00 = 70.00 AUD/入库t
    价值总额 317,440 - 成本总额 230,640 = 净额 86,800 = 70.00 x 1,240

结构要点：
  - 36 批次 / 16 来源 / 12 月 / 1,240 t（30 批 Completed = 992 t 全量输出；
    6 批 Partially Completed = 248 t 未闭环，零输出）。
  - 等级单价：Premium 650 / Character 450 / Rustic 280 / Feedstock 125（对所有路线按等级计价）。
  - 最终等级吨：175 / 199 / 238 / 380；初始等级吨：175 / 231 / 244 / 342；
    降级 C->R 32 t、R->F 38 t；路线 HV 354 / BF 546 / SH 48 / Residual 44。
  - 成本：Sorting 66,960（54/t x 1,240）+ Inspection 52,080（42/t x 1,240）
    + Processing 103,596（104.43 AUD/处理t，按批精确分摊）+ SH 5,760（120/t x 48）
    + Disposal 2,244（51/t x 44）= 230,640。Transport / Other 单列、不计入总成本。
  - 状态池（快照 as_of=2025-12-31T18:00）：Output 992 / In Progress 155（检验 96 + 处理中 59）
    / Pending 68.2 / Unresolved 24.8；积压桶：Unresolved 24.8 + Inspection 96 + Sorting 68.2
    + Processing 59 = 248。

IMPORTANT:
  - Every value in this dataset is SYNTHETIC PROTOTYPE DATA.
  - It is designed to test product and analytics behaviour, NOT to represent
    actual commercial performance, industry benchmarks, or any real company.

Usage:
    python3 scripts/generate_workbench_demo.py
"""

from __future__ import annotations

import csv
import datetime as dt
import math
import os
import random
import statistics

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEED = 20260820
RNG = random.Random(SEED)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_DIR = os.path.join(DATA_DIR, "csv")

YEAR = 2025
SNAPSHOT = dt.datetime(2025, 12, 31, 18, 0)   # dataset "as of" timestamp

# --- design targets ---------------------------------------------------------
TARGET_INCOMING_T = 1240.0
OUTPUT_T = 992.0
OPEN_T = 248.0

GRADE_KEYS = ["Premium", "Character", "Rustic", "Feedstock"]
GRADE_T = {"Premium": 175, "Character": 199, "Rustic": 238, "Feedstock": 380}  # t
GRADE_PRICES = {"Premium": 650.0, "Character": 450.0, "Rustic": 280.0, "Feedstock": 125.0}

SH_C_T, SH_F_T, RES_F_T = 20.0, 28.0, 44.0
D_C2R_T, D_R2F_T = 32.0, 38.0

SORTING_RATE = 54.0      # AUD / incoming t (sunk for every tonne)
INSPECTION_RATE = 42.0   # AUD / incoming t (sunk for every tonne)
PROCESSING_COST = 103596.0  # AUD total (exact allocation across 992 t processed)
SH_RATE = 120.0          # AUD / SH route t
DISPOSAL_RATE = 51.0     # AUD / Residual route t

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _d(y, m, d, h=0, mi=0):
    return dt.datetime(y, m, d, h, mi)

def _date(dt_):
    return dt_.date() if isinstance(dt_, dt.datetime) else dt_

def _fmt_iso(x):
    return x.isoformat() if isinstance(x, (dt.datetime, dt.date)) else x

def _fmt_date(x):
    return x.isoformat() if isinstance(x, (dt.date, dt.datetime)) else x

def _fmt_dt(x):
    return x.isoformat() if isinstance(x, (dt.datetime, dt.date)) else x


def _scale_to_sum(raw, target, dp=1):
    """Scale raw values so they sum to exactly target, rounding to dp decimals."""
    f = 10 ** dp
    total = sum(raw)
    out = [round(w * target / total * f) / f for w in raw]
    diff = round(target * f) - round(sum(out) * f)
    out[-1] = round(out[-1] + diff / f, dp)
    return out


def _matrix_round(row_targets, col_targets, weights):
    """Round a rows x cols matrix to integers with EXACT row and column sums.

    - row_targets[i] / col_targets[g] are integer targets (e.g. kg).
    - weights[i] is the scenario grade distribution for row i (sums to 1).
    Uses iterative proportional fitting (IPF) to respect the scenario mix as a
    prior, then largest-remainder rounding that preserves both margins.
    """
    nr, nc = len(row_targets), len(col_targets)
    assert sum(row_targets) == sum(col_targets)
    x = [[weights[i][g] for g in range(nc)] for i in range(nr)]
    for _ in range(300):
        for i in range(nr):
            s = sum(x[i])
            if s > 0:
                x[i] = [v * row_targets[i] / s for v in x[i]]
        for g in range(nc):
            s = sum(x[i][g] for i in range(nr))
            if s > 0:
                for i in range(nr):
                    x[i][g] = x[i][g] * col_targets[g] / s
    mat = [[int(math.floor(v)) for v in r] for r in x]
    rd = [row_targets[i] - sum(mat[i]) for i in range(nr)]
    cd = [col_targets[g] - sum(mat[i][g] for i in range(nr)) for g in range(nc)]
    assert sum(rd) == sum(cd) and all(d >= 0 for d in rd) and all(d >= 0 for d in cd)
    steps = 0
    while sum(rd) > 0:
        cand = [(x[i][g] - mat[i][g], i, g) for i in range(nr) for g in range(nc)
                if rd[i] > 0 and cd[g] > 0]
        _, i, g = max(cand)
        mat[i][g] += 1
        rd[i] -= 1
        cd[g] -= 1
        steps += 1
        assert steps < 100000
    return mat


def _allocate_exact(total, weights, dp=0):
    """Allocate `total` across items proportionally to `weights`, rounding to dp
    decimals, exact sum via largest remainder. Deterministic (stable tie-break)."""
    n = len(weights)
    f = 10 ** dp
    tot = int(round(total * f))
    if n == 0 or tot == 0:
        return [0.0] * n
    wsum = sum(weights)
    raw = [w / wsum * tot for w in weights]
    base = [int(math.floor(x)) for x in raw]
    rem = tot - sum(base)
    fracs = sorted([(raw[i] - base[i], i) for i in range(n)], reverse=True)
    for k in range(rem):
        _, i = fracs[k % len(fracs)]
        base[i] += 1
    return [b / f for b in base]


def weighted_choice(rng, items, weights):
    return rng.choices(items, weights=weights, k=1)[0]

# ---------------------------------------------------------------------------
# 1. Synthetic assumptions (single source of truth for rates / prices)
# ---------------------------------------------------------------------------
ASSUMPTION_SPECS = [
    # (key, category, metric, value, unit, description)
    ("premium_value_per_t",          "Value",  "Premium recovery value / t",     650.0, "AUD/t", "Synthetic unit value for Premium grade recovered output (all routes priced at grade)."),
    ("character_value_per_t",        "Value",  "Character recovery value / t",   450.0, "AUD/t", "Synthetic unit value for Character grade recovered output (all routes priced at grade)."),
    ("rustic_value_per_t",           "Value",  "Rustic recovery value / t",      280.0, "AUD/t", "Synthetic unit value for Rustic grade recovered output (all routes priced at grade)."),
    ("board_feedstock_value_per_t",  "Value",  "Board feedstock value / t",      125.0, "AUD/t", "Synthetic unit value for Feedstock grade recovered output (all routes priced at grade)."),
    ("sorting_cost_per_t",           "Cost",   "Sorting cost / incoming t",       54.0, "AUD/t", "Sunk sorting cost per incoming tonne (spread across all 1,240 t)."),
    ("inspection_cost_per_t",        "Cost",   "Inspection cost / incoming t",    42.0, "AUD/t", "Sunk inspection cost per incoming tonne (spread across all 1,240 t)."),
    ("processing_cost_per_t",        "Cost",   "Processing cost / processed t",   104.43, "AUD/t", "Nominal rate; exact total 103,596 AUD allocated across 992 t processed."),
    ("special_handling_cost_per_t",  "Cost",   "Special handling cost / t",       120.0, "AUD/t", "Incremental cost per tonne routed to Special Handling."),
    ("disposal_cost_per_t",          "Cost",   "Disposal cost / t",               51.0, "AUD/t", "Disposal cost per tonne of Residual route output."),
    ("transport_cost_per_t",         "Cost",   "Transport cost / t",              25.0, "AUD/t", "Inbound transport cost per tonne (reported separately, excluded from total recovery cost)."),
    ("baseline_processing_cost_per_t", "Cost", "Counterfactual processing cost / t", 95.0, "AUD/t", "Counterfactual all-feedstock processing cost used by the Baseline Scenario."),
    ("higher_value_recovery_target_pct", "Target", "Higher-value recovery prototype target", 30.0, "%", "Prototype management target; overall dataset yield is expected to exceed it."),
    ("sorting_labour_rate_per_hour", "Modelling", "Sorting labour rate / h",      48.0, "AUD/h", "Synthetic hourly rate for sorting labour (event realism only; cost booked at per-t rate)."),
    ("inspection_labour_rate_per_hour", "Modelling", "Inspection labour rate / h", 55.0, "AUD/h", "Synthetic hourly rate for inspection labour (event realism only; cost booked at per-t rate)."),
    ("machine_processing_rate_per_h", "Modelling", "Machine processing rate / h", 80.0, "AUD/h", "Synthetic machine-hour rate for processing equipment (event realism only)."),
    ("machine_hours_per_t",          "Modelling", "Machine processing hours / t", 1.15, "h/t",  "Synthetic machine-hours consumed per processed tonne (event realism only)."),
    ("sorting_labour_hours_per_8h_day", "Modelling", "Assumed labour hours per work day", 8.0, "h", "Used to convert sorting hours into calendar durations."),
]

def build_assumptions():
    rows = []
    for i, (key, cat, metric, val, unit, desc) in enumerate(ASSUMPTION_SPECS, start=1):
        rows.append({
            "assumption_id": f"AS{i:03d}",
            "assumption_key": key,
            "category": cat,
            "metric": metric,
            "value": val,
            "unit": unit,
            "description": desc,
            "source": "Prototype assumption",
        })
    return rows

# ---------------------------------------------------------------------------
# 2. Lookups (fixed taxonomies — reused by every sheet / validation)
# ---------------------------------------------------------------------------
LOOKUPS = {
    "source_type": [
        ("Commercial Demolition", "Demolition of commercial / retail buildings."),
        ("Residential Demolition", "House / renovation demolition waste streams."),
        ("Warehouse Deconstruction", "Warehouse, shed and industrial shell deconstruction."),
        ("Industrial Renewal", "Industrial facility renewal / refit recovery."),
        ("Infrastructure Salvage", "Bridge, wharf, rail and public infrastructure salvage."),
        ("Direct Salvage Purchase", "Purchased salvage lots / dealer transfers with variable provenance."),
    ],
    "region": [
        ("Victoria", "VIC, Australia (synthetic region label)"),
        ("New South Wales", "NSW, Australia (synthetic region label)"),
        ("Queensland", "QLD, Australia (synthetic region label)"),
        ("South Australia", "SA, Australia (synthetic region label)"),
        ("Western Australia", "WA, Australia (synthetic region label)"),
        ("Tasmania", "TAS, Australia (synthetic region label)"),
    ],
    "material_quality": [
        ("High", "Estimated incoming quality high (synthetic assessment)."),
        ("Medium", "Estimated incoming quality medium."),
        ("Low", "Estimated incoming quality low."),
        ("Unknown", "Estimated incoming quality not assessable."),
    ],
    "expected_complexity": [
        ("Low", "Straightforward material mix, limited sorting effort expected."),
        ("Medium", "Mixed material; moderate sorting effort expected."),
        ("High", "Complex mix, heavy contamination / record uncertainty expected."),
    ],
    "planned_sorting_intensity": [
        ("Low", "Minimal sorting effort planned."),
        ("Medium", "Standard sorting effort planned."),
        ("High", "Detailed sorting and extra inspections planned."),
    ],
    "batch_status": [
        ("Received", "Batch received, work not yet started."),
        ("Sorting", "Batch in sorting stage."),
        ("Inspection", "Batch in inspection stage."),
        ("Processing", "Batch in processing stage."),
        ("Completed", "Batch fully processed; all materials recovered."),
        ("Partially Completed", "Batch partially processed; remaining weight open at snapshot."),
    ],
    "priority": [
        ("High", "High operational priority."),
        ("Medium", "Normal priority."),
        ("Low", "Low priority."),
    ],
    "species": [
        ("Spotted Gum", "Australian hardwood (synthetic modelling label)."),
        ("Blackbutt", "Australian hardwood (synthetic modelling label)."),
        ("Ironbark", "Australian hardwood (synthetic modelling label)."),
        ("Sydney Blue Gum", "Australian hardwood (synthetic modelling label)."),
        ("Mountain Ash", "Victorian Ash group (synthetic modelling label)."),
        ("Messmate", "Victorian Ash group (synthetic modelling label)."),
        ("Radiata Pine", "Softwood (synthetic modelling label)."),
        ("Oregon", "Douglas-fir import (synthetic modelling label)."),
        ("Cypress Pine", "Australian softwood (synthetic modelling label)."),
        ("Mixed Hardwood", "Mixed hardwood lot (synthetic modelling label)."),
        ("Unknown / Mixed", "Species not identified / mixed lot."),
    ],
    "material_form": [
        ("Beam", "Large section beam."),
        ("Post", "Vertical post / column."),
        ("Board", "Sawn board."),
        ("Flooring", "Flooring strip / panel."),
        ("Cladding", "External cladding / weatherboard."),
        ("Structural Member", "Structural framing member."),
        ("Mixed Salvage", "Mixed lot not separable at intake."),
        ("Other", "Other form."),
    ],
    "known_treatment_status": [
        ("No Treatment Recorded", "No treatment recorded in source documents."),
        ("Known Treatment Recorded", "A treatment record exists (management-level note only)."),
        ("Surface Coating Recorded", "Paint / coating / varnish recorded."),
        ("Adhesive / Composite Concern", "Adhesive, glue or composite construction recorded."),
        ("Unknown", "Treatment history unknown."),
        ("Conflicting Record", "Records conflict; cannot confirm treatment status."),
    ],
    "surface_condition": [
        ("Good", "Operational assessment: sound condition."),
        ("Fair", "Operational assessment: serviceable condition."),
        ("Poor", "Operational assessment: significant defects."),
        ("Severely Degraded", "Operational assessment: severely degraded."),
    ],
    "record_completeness": [
        ("Complete", "All management fields populated."),
        ("Partial", "Some fields missing."),
        ("Critical Information Missing", "Key fields (e.g. treatment history) missing."),
    ],
    "recovery_grade": [
        ("Premium", "Prototype management segment."),
        ("Character", "Prototype management segment."),
        ("Rustic", "Prototype management segment."),
        ("Feedstock", "Prototype management segment."),
        ("Unresolved", "Prototype management segment."),
    ],
    "recovery_route": [
        ("Higher-value Recovery", "Premium / Character grade output recovered for re-sale."),
        ("Board Feedstock", "Feedstock grade output."),
        ("Special Handling", "Material requiring special handling before recovery."),
        ("Residual / Disposal", "Residual material routed to disposal."),
        ("Unresolved", "Material not yet routed; information incomplete."),
    ],
    "processing_stage": [
        ("Intake", "Batch intake / weighing."),
        ("Sorting", "Sorting operation."),
        ("Inspection Hold", "Material held pending inspection."),
        ("Processing", "Processing operation."),
        ("Grading", "Grading / final assessment."),
        ("Output", "Recovery output dispatched."),
    ],
    "inspection_type": [
        ("Record Review", "Desk review of source records."),
        ("Quality Verification", "On-site quality verification."),
        ("Treatment Information Verification", "Verification of treatment information."),
        ("Manual Material Review", "Manual material-level review."),
        ("Routing Verification", "Verification of proposed recovery routing."),
    ],
    "inspection_status": [
        ("Open", "Inspection open at snapshot."),
        ("Completed", "Inspection completed."),
        ("Cancelled", "Inspection cancelled."),
    ],
    "inspection_outcome": [
        ("Cleared", "Material cleared; no change."),
        ("Route Changed", "Recovery route changed after inspection."),
        ("Special Handling", "Material routed to special handling."),
        ("Still Unresolved", "Inspection closed but material still unresolved."),
        ("No Change", "Inspection confirmed no change."),
    ],
    "cost_category": [
        ("Sorting Labour", "Sorting labour cost."),
        ("Inspection", "Inspection labour / external cost."),
        ("Processing", "Processing machine / labour cost."),
        ("Special Handling", "Special handling incremental cost."),
        ("Disposal", "Disposal cost."),
        ("Transport", "Inbound transport cost (reported separately)."),
        ("Other", "Other operational cost (reported separately)."),
    ],
    "resolution_status": [
        ("Output", "Material recovered; output recorded."),
        ("Unresolved", "Material unresolved at snapshot."),
        ("Pending Processing", "Material awaiting processing."),
        ("In Progress", "Material in progress at snapshot."),
    ],
}

def build_lookups():
    rows = []
    for domain, items in LOOKUPS.items():
        for i, (value, desc) in enumerate(items, start=1):
            rows.append({
                "domain": domain,
                "value": value,
                "description": desc,
                "sort_order": i,
            })
    return rows

# ---------------------------------------------------------------------------
# 3. Business scenario catalogue (drives batch grade mix / cost behaviour)
#    grade_dist order: [Premium, Character, Rustic, Feedstock]
# ---------------------------------------------------------------------------
SCENARIO_PARAMS = {
    "A": dict(sort_h_per_t=0.85, insp_h_per_t=0.20, insp_prob=0.12, special_rate=0.03,
              degraded_rate=0.03, grade_dist=[0.16, 0.30, 0.28, 0.26], downgrade_prob=0.05,
              insp_ext_prob=0.02, turnaround_band=(10, 16), label="Strong Performer"),
    "B": dict(sort_h_per_t=1.70, insp_h_per_t=0.45, insp_prob=0.32, special_rate=0.03,
              degraded_rate=0.03, grade_dist=[0.28, 0.30, 0.20, 0.22], downgrade_prob=0.08,
              insp_ext_prob=0.15, turnaround_band=(16, 24), label="Expensive but Valuable"),
    "C": dict(sort_h_per_t=2.50, insp_h_per_t=0.90, insp_prob=0.42, special_rate=0.05,
              degraded_rate=0.12, grade_dist=[0.05, 0.14, 0.26, 0.55], downgrade_prob=0.30,
              insp_ext_prob=0.15, turnaround_band=(20, 30), label="Poor Sorting Economics"),
    "D": dict(sort_h_per_t=1.20, insp_h_per_t=1.10, insp_prob=0.55, special_rate=0.06,
              degraded_rate=0.08, grade_dist=[0.10, 0.18, 0.24, 0.48], downgrade_prob=0.22,
              insp_ext_prob=0.25, turnaround_band=(45, 75), label="High Uncertainty"),
    "E": dict(sort_h_per_t=0.80, insp_h_per_t=0.18, insp_prob=0.10, special_rate=0.02,
              degraded_rate=0.02, grade_dist=[0.24, 0.30, 0.22, 0.24], downgrade_prob=0.04,
              insp_ext_prob=0.02, turnaround_band=(9, 14), label="High-value Source"),
    "F": dict(sort_h_per_t=0.45, insp_h_per_t=0.10, insp_prob=0.06, special_rate=0.02,
              degraded_rate=0.06, grade_dist=[0.02, 0.08, 0.20, 0.70], downgrade_prob=0.10,
              insp_ext_prob=0.01, turnaround_band=(7, 12), label="Commodity Source"),
    "G": dict(sort_h_per_t=1.40, insp_h_per_t=0.35, insp_prob=0.18, special_rate=0.32,
              degraded_rate=0.10, grade_dist=[0.08, 0.20, 0.25, 0.47], downgrade_prob=0.18,
              insp_ext_prob=0.08, turnaround_band=(14, 22), label="Special Handling Heavy"),
    "N": dict(sort_h_per_t=1.00, insp_h_per_t=0.30, insp_prob=0.12, special_rate=0.04,
              degraded_rate=0.05, grade_dist=[0.08, 0.20, 0.28, 0.44], downgrade_prob=0.12,
              insp_ext_prob=0.05, turnaround_band=(11, 18), label="Neutral / Mixed"),
}

GRADE_IDX = {g: i for i, g in enumerate(GRADE_KEYS)}

# propensity weight per scenario for special-handling / downgrade allocation
PROP = {"G": 0.60, "C": 0.35, "D": 0.35, "B": 0.30, "A": 0.18, "E": 0.15, "N": 0.15, "F": 0.10}

# ---------------------------------------------------------------------------
# 4. Source projects (16 sources; batch plan defined below)
# ---------------------------------------------------------------------------
# (source_id, source_type, region, former_use_category, quality, complexity, first_batch_arrival)
SOURCE_PLAN = [
    ("S01", "Infrastructure Salvage",   "Victoria",         "Bridge decking / handrail renewal",        "High",    "Medium",  (4, 1)),
    ("S02", "Infrastructure Salvage",   "New South Wales",  "Railway station platform renewal",        "High",    "Medium",  (4, 2)),
    ("S03", "Industrial Renewal",       "Victoria",         "Industrial facility refit",               "High",    "Low",     (1, 1)),
    ("S04", "Industrial Renewal",       "Queensland",       "Industrial facility refit",               "Medium",  "Low",     (2, 1)),
    ("S05", "Commercial Demolition",    "New South Wales",  "Retail / office fit-out demolition",      "Medium",  "Medium",  (2, 2)),
    ("S06", "Commercial Demolition",    "Queensland",       "Commercial building demolition",          "Medium",  "Medium",  (3, 2)),
    ("S07", "Commercial Demolition",    "Victoria",         "Retail / office fit-out demolition",      "Medium",  "Medium",  (1, 2)),
    ("S08", "Residential Demolition",   "South Australia",  "House demolition",                        "Low",     "Low",     (1, 1)),
    ("S09", "Residential Demolition",   "Western Australia", "House demolition",                       "Low",     "Low",     (2, 2)),
    ("S10", "Residential Demolition",   "Victoria",         "Renovation strip-out",                    "Low",     "Medium",  (2, 2)),
    ("S11", "Residential Demolition",   "Tasmania",         "House demolition",                        "Low",     "Medium",  (3, 1)),
    ("S12", "Warehouse Deconstruction", "New South Wales",  "Warehouse / shed deconstruction",         "Medium",  "Medium",  (1, 2)),
    ("S13", "Warehouse Deconstruction", "Queensland",       "Warehouse / shed deconstruction",         "Medium",  "Medium",  (2, 2)),
    ("S14", "Warehouse Deconstruction", "Victoria",         "Pallet racking / mezzanine removal",      "Medium",  "High",    (3, 1)),
    ("S15", "Direct Salvage Purchase",  "South Australia",  "Dealer / salvage yard transfer",          "Unknown", "High",    (4, 1)),
    ("S16", "Direct Salvage Purchase",  "New South Wales",  "Private sale / mixed lot",                "Unknown", "High",    (1, 2)),
]

# ---------------------------------------------------------------------------
# 5. Batch plan — 36 batches, 3/month, Jan-Dec 2025
#    kind: completed | in_progress_inspection | in_progress_processing | pending | unresolved
#    completed weights are scaled so the 30 completed batches sum to exactly 992.0 t;
#    open weights are fixed so the 6 open batches sum to exactly 248.0 t.
# ---------------------------------------------------------------------------
# B034 splits its 75 t into 16 t inspection-held + 59 t processing at snapshot.
INSPECTION_PORTION_KG = {"B034": 16000}

# (batch_id, month, day, weight, scenario, source_id, intensity, priority, kind, note)
BATCH_PLAN = [
    ("B001", 1,  6, 31,   "N", "S04", "Medium", "Medium", "completed", "Industrial renewal; mixed hardwood and softwood; standard sort."),
    ("B002", 1, 15, 44,   "A", "S03", "Medium", "High",   "completed", "High-quality industrial refit; strong higher-value recovery expected."),
    ("B003", 1, 24, 21,   "F", "S08", "Low",    "Low",    "completed", "Residential demolition; mostly board feedstock."),
    ("B004", 2,  5, 36,   "N", "S12", "Medium", "Medium", "completed", "Warehouse deconstruction; mixed sections."),
    ("B005", 2, 13, 31,   "E", "S01", "Medium", "High",   "completed", "Bridge renewal hardwood; premium potential."),
    ("B006", 2, 23, 25,   "C", "S10", "High",   "Medium", "completed", "Renovation strip-out; heavy contamination; low value yield."),
    ("B007", 3,  4, 38,   "A", "S03", "Medium", "High",   "completed", "Industrial refit batch 2; clean sections."),
    ("B008", 3, 14, 24,   "N", "S12", "Medium", "Medium", "completed", "Warehouse deconstruction; mixed."),
    ("B009", 3, 24, 18,   "G", "S14", "High",   "Medium", "completed", "Racking / mezzanine removal; composite and nailed sections."),
    ("B010", 4,  3, 34,   "B", "S05", "High",   "Medium", "completed", "Fit-out demolition; premium shopfit timber with known treatment records."),
    ("B011", 4, 14, 31,   "F", "S08", "Low",    "Low",    "completed", "House demolition; feedstock-dominated."),
    ("B012", 4, 23, 26,   "N", "S16", "Medium", "Medium", "completed", "Purchased mixed lot; partial records."),
    ("B013", 5,  5, 46,   "E", "S01", "Medium", "High",   "completed", "Wharf decking salvage; high-grade hardwood."),
    ("B014", 5, 15, 20,   "N", "S16", "Medium", "Medium", "completed", "Purchased mixed lot; some unknowns."),
    ("B015", 5, 25, 33,   "A", "S04", "Medium", "High",   "completed", "Industrial renewal; consistent quality."),
    ("B016", 6,  4, 35,   "B", "S05", "High",   "Medium", "completed", "Office fit-out; premium joinery timber; detailed inspections."),
    ("B017", 6, 15, 42,   "C", "S10", "High",   "Medium", "completed", "Renovation strip-out; unusually heavy sorting effort, weak economics."),
    ("B018", 6, 24, 24,   "N", "S07", "Medium", "Medium", "completed", "Retail fit-out; mixed."),
    ("B019", 7,  2, 30,   "F", "S08", "Low",    "Low",    "completed", "House demolition; feedstock-heavy."),
    ("B020", 7, 13, 27,   "N", "S13", "Medium", "Medium", "completed", "Warehouse deconstruction; mixed."),
    ("B021", 7, 23, 43,   "A", "S04", "Medium", "High",   "completed", "Industrial renewal; strong yield."),
    ("B022", 8,  4, 37,   "E", "S02", "Medium", "High",   "completed", "Platform renewal hardwood; premium potential."),
    ("B023", 8, 14, 25,   "C", "S11", "High",   "Medium", "completed", "House demolition; heavy inspection load, low yield."),
    ("B024", 8, 25, 31,   "N", "S06", "Medium", "Medium", "completed", "Commercial demolition; mixed sections."),
    ("B025", 9,  3, 33,   "B", "S06", "High",   "Medium", "completed", "Commercial demolition; known-history premium sections."),
    ("B026", 9, 13, 23,   "G", "S13", "High",   "Medium", "completed", "Warehouse deconstruction; composite panels and nails."),
    ("B027", 9, 28, 32,   "D", "S15", "High",   "High",   "completed", "Purchased salvage; unknown treatment history; heavy inspection."),
    ("B028", 10, 3, 39,   "F", "S09", "Low",    "Low",    "completed", "House demolition; feedstock-dominated."),
    ("B029", 10, 13, 22,  "A", "S04", "Medium", "High",   "completed", "Industrial renewal; clean yield."),
    ("B030", 10, 21, 80,  "D", "S15", "High",   "High",   "in_progress_inspection", "Purchased salvage; conflicting records; whole batch held under inspection."),
    ("B031", 11,  6, 33,  "N", "S07", "Medium", "Medium", "completed", "Retail fit-out; completed by late November."),
    ("B032", 11, 15, 34.1, "E", "S02", "Medium", "High",  "pending",   "Platform renewal; queued for sorting at snapshot."),
    ("B033", 11, 24, 12.4, "D", "S16", "High",   "High",   "unresolved", "Purchased mixed lot; high uncertainty; inspection closed, still unresolved."),
    ("B034", 12,  3, 75,  "G", "S14", "High",   "Medium", "in_progress_processing", "Racking removal; special-handling heavy; 16 t in inspection, 59 t processing."),
    ("B035", 12, 12, 34.1, "F", "S09", "Low",    "Low",    "pending",   "House demolition; queued for sorting at snapshot."),
    ("B036", 12, 21, 12.4, "N", "S07", "Medium", "Medium", "unresolved", "Retail fit-out; inspection closed, still unresolved."),
]

def build_batches():
    """Create batch records. Completed weights scale to exactly 992.0 t;
    open weights are fixed to sum to exactly 248.0 t (total 1,240.0 t)."""
    completed_plan = [p for p in BATCH_PLAN if p[8] == "completed"]
    raw = [p[3] for p in completed_plan]
    cweights = _scale_to_sum(raw, OUTPUT_T)

    batches = []
    ci = 0
    for idx, p in enumerate(BATCH_PLAN, start=1):
        bid, mon, day, w_raw, scen, sid, intensity, priority, kind, note = p
        if kind == "completed":
            weight = cweights[ci]
            ci += 1
        else:
            weight = w_raw
        jitter = RNG.randint(0, 2)
        day = max(1, min(28, day + jitter))
        arrival = _d(YEAR, mon, day, RNG.randint(7, 10), RNG.randint(0, 50))
        pparams = dict(SCENARIO_PARAMS[scen])

        if kind == "completed":
            status, stage, f, unres_t, pool = "Completed", "Completed", 1.0, 0.0, "output"
        elif kind == "in_progress_inspection":
            status, stage, f, unres_t, pool = "Partially Completed", "Inspection", 0.0, 0.0, "in_progress"
        elif kind == "in_progress_processing":
            status, stage, f, unres_t, pool = "Partially Completed", "Processing", 0.0, 0.0, "in_progress"
        elif kind == "pending":
            status, stage, f, unres_t, pool = "Partially Completed", "Sorting", 0.0, 0.0, "pending"
        elif kind == "unresolved":
            status, stage, f, unres_t, pool = "Partially Completed", "Inspection", 0.0, 1.0, "unresolved"
        else:
            raise ValueError(f"unknown kind {kind}")

        batches.append({
            "batch_id": bid,
            "source_id": sid,
            "arrival_date": arrival,
            "incoming_weight_t": weight,
            "planned_sorting_intensity": intensity,
            "current_stage": stage,
            "batch_status": status,
            "priority": priority,
            "notes": note,
            "scenario": scen,
            "scenario_label": pparams["label"],
            "f_processed": f,
            "unresolved_target": unres_t,
            "sort_h_per_t": pparams["sort_h_per_t"],
            "insp_h_per_t": pparams["insp_h_per_t"],
            "insp_prob": pparams["insp_prob"],
            "special_rate": pparams["special_rate"],
            "degraded_rate": pparams["degraded_rate"],
            "grade_dist": list(pparams["grade_dist"]),
            "downgrade_prob": pparams["downgrade_prob"],
            "insp_ext_prob": pparams["insp_ext_prob"],
            "turnaround_band": tuple(pparams["turnaround_band"]),
            "batch_index": idx,
            "pool": pool,
        })
    assert ci == len(completed_plan)
    return batches

# ---------------------------------------------------------------------------
# 6. Species / form / treatment modelling pools
# ---------------------------------------------------------------------------
SPECIES_POOL = {
    "hardwood": ["Spotted Gum", "Blackbutt", "Ironbark", "Sydney Blue Gum", "Mountain Ash", "Messmate", "Mixed Hardwood"],
    "softwood": ["Radiata Pine", "Oregon", "Cypress Pine"],
    "unknown": ["Unknown / Mixed"],
}

SPECIES_QUALITY = {
    "Spotted Gum": 0.08, "Blackbutt": 0.07, "Ironbark": 0.09, "Sydney Blue Gum": 0.05,
    "Mountain Ash": 0.04, "Messmate": 0.03, "Mixed Hardwood": 0.02,
    "Radiata Pine": -0.05, "Oregon": -0.03, "Cypress Pine": -0.02, "Unknown / Mixed": -0.06,
}

FORM_WEIGHT_BAND = {
    "Beam": (600, 1500), "Post": (250, 700), "Board": (30, 180), "Flooring": (20, 120),
    "Cladding": (25, 140), "Structural Member": (300, 900), "Mixed Salvage": (80, 400),
    "Other": (40, 300),
}

FORM_POOL = {
    "Beam": ["Roof beam", "Floor joist", "Racking beam", "Portal frame member"],
    "Post": ["Verandah post", "Fence post", "Structural post"],
    "Board": ["Sawn board", "Formwork board", "Fence palings", "Dunnage"],
    "Flooring": ["Flooring strip", "Floor board", "Decking board"],
    "Cladding": ["Weatherboard", "Cladding panel", "Fascia board"],
    "Structural Member": ["Wall stud", "Roof rafter", "Truss member", "Purlin"],
    "Mixed Salvage": ["Mixed salvage lot", "Assorted recovered timber"],
    "Other": ["Miscellaneous timber", "Joinery offcut", "Shelving"],
}

TREATMENT_DIST = {
    "High":   [0.45, 0.28, 0.15, 0.05, 0.05, 0.02],
    "Medium": [0.38, 0.20, 0.16, 0.08, 0.12, 0.06],
    "Low":    [0.34, 0.12, 0.12, 0.08, 0.22, 0.12],
    "Unknown":[0.25, 0.08, 0.10, 0.10, 0.32, 0.15],
}
TREATMENT_KEYS = ["No Treatment Recorded", "Known Treatment Recorded", "Surface Coating Recorded",
                  "Adhesive / Composite Concern", "Unknown", "Conflicting Record"]

COMPLETENESS_DIST = {
    "High":   [0.80, 0.15, 0.05],
    "Medium": [0.55, 0.30, 0.15],
    "Low":    [0.30, 0.40, 0.30],
    "Unknown":[0.20, 0.40, 0.40],
}
COMPLETENESS_KEYS = ["Complete", "Partial", "Critical Information Missing"]

SURFACE_DIST = {
    "A": [0.55, 0.30, 0.13, 0.02],
    "B": [0.40, 0.40, 0.17, 0.03],
    "C": [0.08, 0.28, 0.44, 0.20],
    "D": [0.12, 0.32, 0.38, 0.18],
    "E": [0.58, 0.30, 0.11, 0.01],
    "F": [0.22, 0.44, 0.25, 0.09],
    "G": [0.24, 0.40, 0.28, 0.08],
    "N": [0.30, 0.40, 0.24, 0.06],
}
SURFACE_KEYS = ["Good", "Fair", "Poor", "Severely Degraded"]


def _species_for(rng, quality):
    if quality == "High":
        pool_w = [0.72, 0.18, 0.10]
    elif quality == "Medium":
        pool_w = [0.45, 0.40, 0.15]
    elif quality == "Low":
        pool_w = [0.25, 0.55, 0.20]
    else:  # Unknown
        pool_w = [0.30, 0.30, 0.40]
    pool = weighted_choice(rng, ["hardwood", "softwood", "unknown"], pool_w)
    return rng.choice(SPECIES_POOL[pool])

def _pick_form(rng, scenario, weight_kg):
    if scenario in ("F",):
        probs = {"Board": 0.34, "Flooring": 0.14, "Cladding": 0.10, "Beam": 0.10, "Post": 0.08,
                 "Structural Member": 0.12, "Mixed Salvage": 0.08, "Other": 0.04}
    elif scenario in ("E", "A", "B"):
        probs = {"Beam": 0.24, "Post": 0.12, "Board": 0.20, "Flooring": 0.10, "Cladding": 0.08,
                 "Structural Member": 0.16, "Mixed Salvage": 0.06, "Other": 0.04}
    elif scenario in ("G", "C", "D"):
        probs = {"Beam": 0.16, "Post": 0.10, "Board": 0.20, "Flooring": 0.08, "Cladding": 0.06,
                 "Structural Member": 0.22, "Mixed Salvage": 0.12, "Other": 0.06}
    else:
        probs = {"Beam": 0.20, "Post": 0.11, "Board": 0.22, "Flooring": 0.09, "Cladding": 0.08,
                 "Structural Member": 0.16, "Mixed Salvage": 0.09, "Other": 0.05}
    form = weighted_choice(rng, list(probs.keys()), list(probs.values()))
    return form

# ---------------------------------------------------------------------------
# 7. Materials (pool-budget-first: exact kg per category, attributes back-derived)
# ---------------------------------------------------------------------------
# (pool_key, init_grade, final_grade, route, special_flag, surface_hint)
CATEGORY_META = [
    ("P_HV",  "Premium",   "Premium",   "Higher-value Recovery", False, None),
    ("C_HV",  "Character", "Character", "Higher-value Recovery", False, None),
    ("C_SH",  "Character", "Character", "Special Handling",      True,  None),
    ("R_d2r", "Character", "Rustic",    "Board Feedstock",       False, "Poor"),
    ("R_BF",  "Rustic",    "Rustic",    "Board Feedstock",       False, None),
    ("F_d2f", "Rustic",    "Feedstock", "Board Feedstock",       False, "Poor"),
    ("F_BF",  "Feedstock", "Feedstock", "Board Feedstock",       False, None),
    ("F_SH",  "Feedstock", "Feedstock", "Special Handling",      True,  None),
    ("F_Res", "Feedstock", "Feedstock", "Residual / Disposal",   False, "Severely Degraded"),
]

CATEGORY_META_DICT = {m[0]: {"init_grade": m[1], "final_grade": m[2], "route": m[3],
                             "special": m[4], "surface_hint": m[5]} for m in CATEGORY_META}

def _category_pools(bg, shc, shf, res, dc2r, dr2f):
    """Per-batch category kg budgets from grade kg (bg) + route/downgrade splits."""
    P = bg["Premium"]; C = bg["Character"]; R = bg["Rustic"]; F = bg["Feedstock"]
    return {
        "P_HV":  P,
        "C_HV":  C - shc,
        "C_SH":  shc,
        "R_d2r": dc2r,
        "R_BF":  R - dc2r,
        "F_d2f": dr2f,
        "F_BF":  F - shf - res - dr2f,
        "F_SH":  shf,
        "F_Res": res,
    }


def compute_batch_budgets(batches):
    """Return per-batch category budget dicts for the 30 completed batches."""
    completed = [b for b in batches if b["batch_status"] == "Completed"]
    n = len(completed)
    row_targets = [int(round(b["incoming_weight_t"] * 1000)) for b in completed]
    col_targets = [GRADE_T[g] * 1000 for g in GRADE_KEYS]
    weights = [list(b["grade_dist"]) for b in completed]
    mat = _matrix_round(row_targets, col_targets, weights)
    bgs = [{g: mat[i][j] for j, g in enumerate(GRADE_KEYS)} for i in range(n)]
    cw = [b["incoming_weight_t"] for b in completed]
    scens = [b["scenario"] for b in completed]

    shc = _allocate_exact(SH_C_T * 1000.0,
                          [w * PROP[sc] * (bg["Character"] / 1000.0)
                           for w, sc, bg in zip(cw, scens, bgs)], 0)
    shf = _allocate_exact(SH_F_T * 1000.0,
                          [w * PROP[sc] * (bg["Feedstock"] / 1000.0)
                           for w, sc, bg in zip(cw, scens, bgs)], 0)
    res = _allocate_exact(RES_F_T * 1000.0,
                          [w * (0.9 if sc in ("C", "D", "G") else 0.4)
                           for w, sc in zip(cw, scens)], 0)
    dc2r = _allocate_exact(D_C2R_T * 1000.0, [w * PROP[sc] for w, sc in zip(cw, scens)], 0)
    dr2f = _allocate_exact(D_R2F_T * 1000.0, [w * PROP[sc] for w, sc in zip(cw, scens)], 0)

    for i in range(n):
        assert shc[i] <= bgs[i]["Character"], "shc exceeds C budget"
        assert shf[i] + res[i] <= bgs[i]["Feedstock"], "shf+res exceeds F budget"
        assert dc2r[i] <= bgs[i]["Rustic"], "dc2r exceeds R budget"
        assert dr2f[i] <= bgs[i]["Feedstock"] - shf[i] - res[i], "dr2f exceeds F_BF budget"

    proc_alloc = _allocate_exact(PROCESSING_COST,
                                 [w for w in cw], 2)
    return [(_category_pools(bgs[i], shc[i], shf[i], res[i], dc2r[i], dr2f[i]),
             {"shc": shc[i], "shf": shf[i], "res": res[i]},
             proc_alloc[i]) for i in range(n)]


def _needs_inspection(batch, special, treatment, completeness, surface):
    if special or surface == "Severely Degraded":
        return "Yes"
    p = batch["insp_prob"]
    if treatment in ("Unknown", "Conflicting Record"):
        p += 0.15
    if completeness == "Critical Information Missing":
        p += 0.10
    elif completeness == "Partial":
        p += 0.03
    if surface in ("Poor", "Severely Degraded"):
        p += 0.04
    return "Yes" if RNG.random() < min(0.85, p) else "No"


def _planned_route(init_grade, special, surface):
    if special:
        return "Special Handling"
    if surface == "Severely Degraded" and init_grade in ("Rustic", "Feedstock"):
        return "Residual / Disposal"
    if init_grade in ("Premium", "Character"):
        return "Higher-value Recovery"
    return "Board Feedstock"


def _gen_batch_materials(batch, mid, materials, *, kg, init_grade, final_grade,
                         route, special, surface_hint, resolution_status,
                         insp_hold, grade_mode="final", route_mode="final"):
    """Generate `n` materials whose weights sum EXACTLY to kg and append to
    materials (updating mid). Returns new mid."""
    src = next(s for s in SOURCE_PLAN if s[0] == batch["source_id"])
    quality = src[4]
    scen = batch["scenario"]
    n = max(1, min(120, int(round(kg / 1000.0))))
    forms = [_pick_form(RNG, scen, None) for _ in range(n)]
    raw = [RNG.uniform(*FORM_WEIGHT_BAND[f]) for f in forms]
    s = sum(raw)
    kgs = [round(w * kg / s, 1) for w in raw]
    diff = round(kg - sum(kgs), 1)
    kgs[-1] = round(kgs[-1] + diff, 1)

    for f, w in zip(forms, kgs):
        species = _species_for(RNG, quality)
        former_use = RNG.choice(FORM_POOL[f])
        treatment = weighted_choice(RNG, TREATMENT_KEYS, TREATMENT_DIST[quality])
        if special and RNG.random() < 0.6:
            treatment = "Adhesive / Composite Concern"
        completeness = weighted_choice(RNG, COMPLETENESS_KEYS, COMPLETENESS_DIST[quality])
        if surface_hint == "Poor" and RNG.random() < 0.5:
            completeness = "Partial"
        surface = surface_hint or weighted_choice(RNG, SURFACE_KEYS, SURFACE_DIST[scen])
        insp_req = _needs_inspection(batch, special, treatment, completeness, surface)
        if insp_hold and resolution_status in ("In Progress", "Unresolved"):
            insp_req = "Yes"
        elif resolution_status == "Pending Processing":
            insp_req = "No"
        elif resolution_status == "In Progress" and not insp_hold:
            insp_req = "No"

        if grade_mode == "unresolved":
            rg = "Unresolved"
            ig = "Unresolved"
        else:
            ig = init_grade
            rg = final_grade
        if route_mode == "unresolved":
            rt = "Unresolved"
        else:
            rt = route

        materials.append({
            "material_id": f"M{mid:05d}",
            "batch_id": batch["batch_id"],
            "estimated_weight_kg": w,
            "species": species,
            "material_form": f,
            "former_use": former_use,
            "known_treatment_status": treatment,
            "surface_condition": surface,
            "record_completeness": completeness,
            "requires_inspection": insp_req,
            "special_handling_flag": "Yes" if special else "No",
            "initial_recovery_grade": ig,
            "recovery_grade": rg,
            "current_route": rt,
            "resolution_status": resolution_status,
            "output_date": None,
            "_insp_hold": insp_hold,
        })
        mid += 1
    return mid


def build_materials(batches, budgets=None):
    materials = []
    mid = 1

    if budgets is None:
        budgets = compute_batch_budgets(batches)
    completed = [b for b in batches if b["batch_status"] == "Completed"]
    for b, (pools, split, _proc) in zip(completed, budgets):
        for key, ig, fg, rt, special, surf_hint in CATEGORY_META:
            kg = pools[key]
            if kg <= 0:
                continue
            mid = _gen_batch_materials(
                b, mid, materials, kg=kg, init_grade=ig, final_grade=fg, route=rt,
                special=special, surface_hint=surf_hint,
                resolution_status="Output", insp_hold=False,
                grade_mode="final", route_mode="final")
        for mm in materials:
            if mm["batch_id"] == b["batch_id"] and mm["output_date"] is None:
                mm["output_date"] = b["_output_date"]

    # open batches (zero output; state pools)
    for b in batches:
        if b["batch_status"] == "Completed":
            continue
        kg_total = int(round(b["incoming_weight_t"] * 1000))
        pool = b["pool"]
        if b["batch_id"] == "B030":
            mid = _gen_batch_materials(b, mid, materials, kg=kg_total,
                init_grade="Unknown", final_grade="Unresolved", route="Unresolved",
                special=False, surface_hint=None, resolution_status="In Progress",
                insp_hold=True, grade_mode="unresolved", route_mode="unresolved")
        elif b["batch_id"] == "B034":
            insp_kg = INSPECTION_PORTION_KG["B034"]
            proc_kg = kg_total - insp_kg
            mid = _gen_batch_materials(b, mid, materials, kg=insp_kg,
                init_grade="Unknown", final_grade="Unresolved", route="Unresolved",
                special=False, surface_hint=None, resolution_status="In Progress",
                insp_hold=True, grade_mode="unresolved", route_mode="unresolved")
            mid = _gen_batch_materials(b, mid, materials, kg=proc_kg,
                init_grade="Unknown", final_grade="Unresolved", route="Unresolved",
                special=False, surface_hint=None, resolution_status="In Progress",
                insp_hold=False, grade_mode="unresolved", route_mode="unresolved")
        elif pool == "pending":
            mid = _gen_batch_materials(b, mid, materials, kg=kg_total,
                init_grade="Unknown", final_grade="Unresolved", route="Unresolved",
                special=False, surface_hint=None, resolution_status="Pending Processing",
                insp_hold=False, grade_mode="unresolved", route_mode="unresolved")
        elif pool == "unresolved":
            mid = _gen_batch_materials(b, mid, materials, kg=kg_total,
                init_grade="Unknown", final_grade="Unresolved", route="Unresolved",
                special=False, surface_hint=None, resolution_status="Unresolved",
                insp_hold=True, grade_mode="unresolved", route_mode="unresolved")
        else:
            raise ValueError(f"unknown open pool {pool}")

    return materials

# ---------------------------------------------------------------------------
# 8. Timeline (output / processing dates) for completed batches
# ---------------------------------------------------------------------------
def assign_timeline(batches):
    """Pick turnaround days from the scenario band and derive processing / output
    dates. All completed batches finish before the snapshot."""
    for b in batches:
        if b["batch_status"] != "Completed":
            continue
        lo, hi = b["turnaround_band"]
        days = RNG.randint(lo, hi)
        out_d = _date(b["arrival_date"]) + dt.timedelta(days=days)
        out_dt = dt.datetime.combine(out_d, dt.time(15, 0))
        proc_d = out_d - dt.timedelta(days=RNG.randint(3, 5))
        insp_d = b["arrival_date"] + dt.timedelta(days=max(1, days // 3))
        b["_output_date"] = out_d
        b["_output_dt"] = out_dt
        b["_proc_date"] = _date(proc_d)
        b["_insp_date"] = _date(insp_d)

# ---------------------------------------------------------------------------
# 9. Recovery outputs (grade-price value model, all routes priced at grade)
# ---------------------------------------------------------------------------
ROUTE_LABELS = {
    "P_HV":  "Higher-value Recovery",
    "C_HV":  "Higher-value Recovery",
    "C_SH":  "Special Handling",
    "R_d2r": "Board Feedstock",
    "R_BF":  "Board Feedstock",
    "F_d2f": "Board Feedstock",
    "F_BF":  "Board Feedstock",
    "F_SH":  "Special Handling",
    "F_Res": "Residual / Disposal",
}

def build_outputs(batches, budget_map):
    rows = []
    oidx = 1
    for b in batches:
        if b["batch_status"] != "Completed":
            continue
        pools, _split, _proc = budget_map[b["batch_id"]]
        batch_rows = []
        for key, kg in pools.items():
            if kg <= 0:
                continue
            grade = CATEGORY_META_DICT[key]["final_grade"]
            weight_t = round(kg / 1000.0, 3)
            unit = GRADE_PRICES[grade]
            batch_rows.append({
                "output_id": f"OUT{oidx:05d}",
                "batch_id": b["batch_id"],
                "output_date": b["_output_date"],
                "recovery_route": ROUTE_LABELS[key],
                "recovery_grade": grade,
                "weight_t": weight_t,
                "unit_value_aud_per_t": unit,
                "gross_value_aud": round(weight_t * unit, 2),
            })
            oidx += 1
        # reconcile: make per-batch output weight sum exactly the batch weight
        total_kg = sum(pools.values())
        target_t = round(total_kg / 1000.0, 3)
        if batch_rows:
            s = round(sum(r["weight_t"] for r in batch_rows), 3)
            adj = round(target_t - s, 3)
            batch_rows[-1]["weight_t"] = round(batch_rows[-1]["weight_t"] + adj, 3)
            batch_rows[-1]["gross_value_aud"] = round(
                batch_rows[-1]["weight_t"] * batch_rows[-1]["unit_value_aud_per_t"], 2)
        rows.extend(batch_rows)
    return rows

# ---------------------------------------------------------------------------
# 10. Cost ledger (Core-5 categories only; Transport / Other excluded)
# ---------------------------------------------------------------------------
def build_cost_ledger(batches, budget_map):
    rows = []
    idx = 1
    for b in batches:
        w = b["incoming_weight_t"]
        arrival = _date(b["arrival_date"])
        # Sorting Labour (sunk, every tonne)
        rows.append({
            "cost_id": f"COST{idx:04d}", "batch_id": b["batch_id"],
            "cost_date": arrival, "cost_category": "Sorting Labour",
            "quantity": w, "unit": "t", "unit_cost_aud": SORTING_RATE,
            "total_cost_aud": round(w * SORTING_RATE, 2),
            "notes": "Sorting labour at synthetic rate 54 AUD/t (sunk for every incoming tonne).",
        })
        idx += 1
        # Inspection (sunk, every tonne)
        rows.append({
            "cost_id": f"COST{idx:04d}", "batch_id": b["batch_id"],
            "cost_date": arrival + dt.timedelta(days=1), "cost_category": "Inspection",
            "quantity": w, "unit": "t", "unit_cost_aud": INSPECTION_RATE,
            "total_cost_aud": round(w * INSPECTION_RATE, 2),
            "notes": "Inspection at synthetic rate 42 AUD/t (sunk for every incoming tonne).",
        })
        idx += 1

        if b["batch_status"] != "Completed":
            continue  # no processing / special handling / disposal for open batches

        pools, split, proc_alloc = budget_map[b["batch_id"]]
        proc_d = b["_proc_date"]
        out_d = b["_output_date"]
        # Processing (exact total allocation across completed batches)
        rows.append({
            "cost_id": f"COST{idx:04d}", "batch_id": b["batch_id"],
            "cost_date": proc_d, "cost_category": "Processing",
            "quantity": w, "unit": "t", "unit_cost_aud": round(103596.0 / 992.0, 4),
            "total_cost_aud": round(proc_alloc, 2),
            "notes": "Processing cost allocated from the exact 103,596 AUD total.",
        })
        idx += 1
        # Special Handling (incremental, only SH route tonnes)
        sh_t = round((split["shc"] + split["shf"]) / 1000.0, 3)
        if sh_t > 0:
            rows.append({
                "cost_id": f"COST{idx:04d}", "batch_id": b["batch_id"],
                "cost_date": out_d, "cost_category": "Special Handling",
                "quantity": sh_t, "unit": "t", "unit_cost_aud": SH_RATE,
                "total_cost_aud": round(sh_t * SH_RATE, 2),
                "notes": "Special handling incremental cost at 120 AUD/t.",
            })
            idx += 1
        # Disposal (Residual route tonnes)
        res_t = round(split["res"] / 1000.0, 3)
        if res_t > 0:
            rows.append({
                "cost_id": f"COST{idx:04d}", "batch_id": b["batch_id"],
                "cost_date": out_d, "cost_category": "Disposal",
                "quantity": res_t, "unit": "t", "unit_cost_aud": DISPOSAL_RATE,
                "total_cost_aud": round(res_t * DISPOSAL_RATE, 2),
                "notes": "Disposal cost at 51 AUD/t for residual output.",
            })
            idx += 1
    rows = _reconcile_costs(rows)
    return rows


def _reconcile_costs(rows):
    """Force each Core-5 category total to its exact design value so the dataset
    identity is exact (compensating rounding residual on the last row of each)."""
    targets = {"Sorting Labour": 66960.0, "Inspection": 52080.0, "Processing": 103596.0,
               "Special Handling": 5760.0, "Disposal": 2244.0}
    for cat, tgt in targets.items():
        sub = [r for r in rows if r["cost_category"] == cat]
        s = round(sum(r["total_cost_aud"] for r in sub), 2)
        diff = round(tgt - s, 2)
        if diff != 0.0 and sub:
            sub[-1]["total_cost_aud"] = round(sub[-1]["total_cost_aud"] + diff, 2)
    return rows

# ---------------------------------------------------------------------------
# 11. Processing events (pipeline visibility; open events for open batches)
# ---------------------------------------------------------------------------
STAGE_ORDER = ["Intake", "Sorting", "Inspection Hold", "Processing", "Grading", "Output"]

def build_processing_events(batches):
    rows = []
    for b in batches:
        w = b["incoming_weight_t"]
        kind = b["pool"]
        a = b["arrival_date"]
        ev = []
        def _push(stage, start, end, win, wout, lh, mh, status, note):
            ev.append({
                "event_id": f"PE{b['batch_index']:02d}{len(ev)+1:02d}",
                "batch_id": b["batch_id"], "stage": stage,
                "start_datetime": start, "end_datetime": end,
                "weight_in_t": win, "weight_out_t": wout,
                "labour_hours": lh, "machine_hours": mh,
                "status": status, "_note": note,
            })
        end_intake = a + dt.timedelta(hours=6)
        sort_hours = round(b["sort_h_per_t"] * w, 1)
        sort_days = max(1, int(math.ceil(sort_hours / 8.0)))
        sort_end = a + dt.timedelta(days=sort_days)

        if kind == "output":  # completed
            _push("Intake", a, end_intake, w, w, 1.0, 0.0, "Completed", "Batch intake / weighing.")
            _push("Sorting", end_intake, sort_end, w, w, sort_hours, 0.0, "Completed", "Sorting operation.")
            insp_end = sort_end + dt.timedelta(days=2)
            _push("Inspection Hold", sort_end, insp_end, w, w, round(b["insp_h_per_t"] * w, 1), 0.0, "Completed", "Inspection hold for the batch.")
            proc_start = insp_end + dt.timedelta(days=1)
            proc_h = round(1.15 * w, 1)
            _push("Processing", proc_start, b["_output_dt"], w, w, 0.0, proc_h, "Completed", "Processing operation.")
            _push("Grading", b["_output_dt"] - dt.timedelta(days=1), b["_output_dt"], w, w, 2.0, 0.0, "Completed", "Final grading.")
            _push("Output", b["_output_dt"], b["_output_dt"] + dt.timedelta(hours=3), w, w, 1.0, 0.0, "Completed", "Recovery output dispatched.")
        elif kind == "in_progress":  # B030 inspection open / B034 processing open
            _push("Intake", a, end_intake, w, w, 1.0, 0.0, "Completed", "Batch intake / weighing.")
            _push("Sorting", end_intake, sort_end, w, w, sort_hours, 0.0, "Completed", "Sorting operation.")
            if b["batch_id"] == "B030":
                _push("Inspection Hold", sort_end, None, w, None, round(b["insp_h_per_t"] * w, 1), 0.0, "Open", "Whole batch held under inspection at snapshot.")
            else:  # B034
                insp_kg = INSPECTION_PORTION_KG["B034"] / 1000.0
                proc_kg = round(w - insp_kg, 3)
                _push("Inspection Hold", sort_end, None, insp_kg, None, round(b["insp_h_per_t"] * insp_kg, 1), 0.0, "Open", "16 t held in inspection at snapshot.")
                _push("Processing", sort_end + dt.timedelta(days=1), None, proc_kg, None, 0.0, round(1.15 * proc_kg, 1), "Open", "59 t in processing at snapshot.")
        elif kind == "pending":
            _push("Intake", a, end_intake, w, w, 1.0, 0.0, "Completed", "Batch intake / weighing; queued for sorting at snapshot.")
        else:  # unresolved
            _push("Intake", a, end_intake, w, w, 1.0, 0.0, "Completed", "Batch intake / weighing.")
            _push("Sorting", end_intake, sort_end, w, w, sort_hours, 0.0, "Completed", "Sorting operation.")
            _push("Inspection Hold", sort_end, sort_end + dt.timedelta(days=2), w, w,
                  round(b["insp_h_per_t"] * w, 1), 0.0, "Completed", "Inspection closed; material still unresolved.")
        rows.extend(ev)
    return rows

# ---------------------------------------------------------------------------
# 12. Inspection events (one per material requiring inspection)
# ---------------------------------------------------------------------------
INSPECTION_TYPES = ["Record Review", "Quality Verification", "Treatment Information Verification",
                    "Manual Material Review", "Routing Verification"]

def build_inspection_events(batches, materials):
    rows = []
    idx = 1
    for m in materials:
        if m["requires_inspection"] != "Yes":
            continue
        b = next(x for x in batches if x["batch_id"] == m["batch_id"])
        a = b["arrival_date"]
        i_type = RNG.choice(INSPECTION_TYPES)
        opened = a + dt.timedelta(days=RNG.randint(1, 5), hours=RNG.randint(8, 16))
        insp_hours = round(RNG.uniform(0.5, 4.0), 1)
        if b["pool"] == "in_progress":
            status, closed, outcome = "Open", None, None
        elif m["_insp_hold"] and m["resolution_status"] == "Unresolved":
            status, closed, outcome = "Completed", opened + dt.timedelta(days=RNG.randint(2, 6)), "Still Unresolved"
        else:
            if m["special_handling_flag"] == "Yes":
                outcome = "Special Handling"
            elif m["recovery_grade"] != m["initial_recovery_grade"]:
                outcome = "Route Changed"
            else:
                outcome = "Cleared"
            status, closed = "Completed", opened + dt.timedelta(days=RNG.randint(1, 5), hours=RNG.randint(1, 8))
        ext = round(RNG.uniform(0, 450), 2)
        rows.append({
            "inspection_id": f"INSP{idx:05d}",
            "batch_id": b["batch_id"],
            "material_id": m["material_id"],
            "inspection_type": i_type,
            "reason": "Synthetic inspection triggered by risk flags on the material record.",
            "opened_datetime": opened,
            "closed_datetime": closed,
            "status": status,
            "labour_hours": insp_hours,
            "external_cost_aud": ext,
            "outcome": outcome,
        })
        idx += 1
    return rows

# ---------------------------------------------------------------------------
# 13. Metrics + identity verification
# ---------------------------------------------------------------------------
def _t(kg):
    return kg / 1000.0

def compute_metrics(batches, materials, outputs, costs, budget_map):
    """Return a metrics dict used by validation and the summary report."""
    m = {}

    def _sum_cost(pred):
        return round(sum(c["total_cost_aud"] for c in costs if pred(c)), 2)

    def _sum_out(pred):
        return round(sum(o["weight_t"] for o in outputs if pred(o)), 3)

    def _sum_gross(pred):
        return round(sum(o["gross_value_aud"] for o in outputs if pred(o)), 2)

    def _sum_kg(pred):
        return round(sum(x["estimated_weight_kg"] for x in materials if pred(x)), 1)

    m["incoming_t"] = round(sum(b["incoming_weight_t"] for b in batches), 1)
    m["output_t"] = _sum_out(lambda o: True)
    m["gross_aud"] = _sum_gross(lambda o: True)
    m["cost_aud"] = _sum_cost(lambda c: True)
    m["net_aud"] = round(m["gross_aud"] - m["cost_aud"], 2)
    m["net_per_t"] = round(m["net_aud"] / m["incoming_t"], 2)
    m["avg_value_per_t"] = round(m["gross_aud"] / m["output_t"], 2)
    m["avg_cost_per_t"] = round(m["cost_aud"] / m["incoming_t"], 2)
    m["processing_rate"] = round(m["output_t"] * 100.0 / m["incoming_t"], 2)

    # grade totals (output, from outputs table)
    m["grade_t"] = {g: round(sum(o["weight_t"] for o in outputs if o["recovery_grade"] == g), 3)
                    for g in GRADE_KEYS}
    # initial grades (from materials of completed batches)
    m["init_grade_t"] = {g: round(_t(_sum_kg(lambda x: x["initial_recovery_grade"] == g)), 3)
                         for g in GRADE_KEYS}
    # route totals
    m["route_t"] = {r: round(sum(o["weight_t"] for o in outputs if o["recovery_route"] == r), 3)
                    for r in ["Higher-value Recovery", "Board Feedstock", "Special Handling", "Residual / Disposal"]}

    # state pools (from materials resolution status)
    m["state_t"] = {
        "Output": round(_t(_sum_kg(lambda x: x["resolution_status"] == "Output")), 2),
        "In Progress": round(_t(_sum_kg(lambda x: x["resolution_status"] == "In Progress")), 2),
        "Pending Processing": round(_t(_sum_kg(lambda x: x["resolution_status"] == "Pending Processing")), 2),
        "Unresolved": round(_t(_sum_kg(lambda x: x["resolution_status"] == "Unresolved")), 2),
    }
    # backlog buckets (month-end state: open inspection / processing / sorting / unresolved)
    m["backlog"] = {
        "Inspection": 96.0,   # B030 80 t (Oct 21) + B034 16 t — December month-end
        "Processing": 59.0,   # B034 59 t
        "Sorting": 68.2,      # B032 + B035 (pending, queued)
        "Unresolved": 24.8,   # B033 + B036
    }
    m["backlog_total"] = round(sum(m["backlog"].values()), 2)

    # month-end inspection backlog for Dec vs Nov comparison
    m["insp_backlog_dec"] = 96.0
    m["insp_backlog_nov"] = 80.0
    m["insp_backlog_delta_pct"] = round((96.0 - 80.0) / 80.0 * 100.0, 2)

    # pool economics (Realised = completed; Provisional = open)
    realised = [b for b in batches if b["batch_status"] == "Completed"]
    open_b = [b for b in batches if b["batch_status"] != "Completed"]
    r_ids = {b["batch_id"] for b in realised}
    o_ids = {b["batch_id"] for b in open_b}
    r_t = round(sum(b["incoming_weight_t"] for b in realised), 1)
    o_t = round(sum(b["incoming_weight_t"] for b in open_b), 1)
    r_val = _sum_gross(lambda o: o["batch_id"] in r_ids)
    r_cost = _sum_cost(lambda c: c["batch_id"] in r_ids)
    o_val = _sum_gross(lambda o: o["batch_id"] in o_ids)
    o_cost = _sum_cost(lambda c: c["batch_id"] in o_ids)
    m["realised"] = {"t": r_t, "value_aud": r_val, "cost_aud": r_cost,
                     "net_aud": round(r_val - r_cost, 2),
                     "net_per_t": round((r_val - r_cost) / r_t, 2)}
    m["provisional"] = {"t": o_t, "value_aud": o_val, "cost_aud": o_cost,
                        "net_aud": round(o_val - o_cost, 2),
                        "net_per_t": round((o_val - o_cost) / o_t, 2)}

    # materials
    m["n_materials"] = len(materials)
    m["n_inspections"] = sum(1 for x in materials if x["requires_inspection"] == "Yes")
    m["material_kg_total"] = _sum_kg(lambda x: True)

    # per-batch economics for report
    m["batch_econ"] = []
    for b in batches:
        inc = b["incoming_weight_t"]
        gross = round(sum(o["gross_value_aud"] for o in outputs if o["batch_id"] == b["batch_id"]), 2)
        cost = round(sum(c["total_cost_aud"] for c in costs if c["batch_id"] == b["batch_id"]), 2)
        m["batch_econ"].append({
            "batch_id": b["batch_id"], "t": inc,
            "value_aud": gross, "cost_aud": cost,
            "net_aud": round(gross - cost, 2),
            "net_per_t": round((gross - cost) / inc, 2),
        })
    return m

# ---------------------------------------------------------------------------
# 14. Validation — design doc §7 checklist (12 items) + structural checks
# ---------------------------------------------------------------------------
def validate(batches, materials, outputs, costs, events, inspections, m):
    checks = []
    def ck(ok, name, detail=""):
        checks.append((bool(ok), name, detail))

    # 1. identity
    ck(abs(m["net_per_t"] - 70.00) < 1e-9, "恒等式 net/t = 70.00",
       f"net {m['net_aud']} / incoming {m['incoming_t']} = {m['net_per_t']}")
    ck(abs(m["avg_value_per_t"] - 320.00) < 1e-9, "平均单位价值 = 320.00", f"{m['avg_value_per_t']}")
    ck(abs(m["processing_rate"] - 80.00) < 1e-9, "处理率 = 80.00%", f"{m['processing_rate']}%")
    ck(abs(m["avg_cost_per_t"] - 186.00) < 1e-9, "平均单位成本 = 186.00", f"{m['avg_cost_per_t']}")
    ck(abs(m["value_identity"]) < 1e-9, "恒等式 320x80%-186=70",
       f"320x{m['processing_rate']}%-186 = {m['identity_check']}")

    # 2. matrix self-consistency
    for g in GRADE_KEYS:
        ck(abs(m["grade_t"][g] - GRADE_T[g]) < 1e-6, f"最终等级 {g} = {GRADE_T[g]} t",
           f"{m['grade_t'][g]}")
    for g in GRADE_KEYS:
        ck(abs(m["init_grade_t"][g] - {"Premium": 175, "Character": 231, "Rustic": 244, "Feedstock": 342}[g]) < 1e-6,
           f"初始等级 {g} 校验", f"{m['init_grade_t'][g]}")
    ck(abs(m["route_t"]["Higher-value Recovery"] - 354.0) < 1e-6, "HV 路线 = 354 t", f"{m['route_t']['Higher-value Recovery']}")
    ck(abs(m["route_t"]["Board Feedstock"] - 546.0) < 1e-6, "BF 路线 = 546 t", f"{m['route_t']['Board Feedstock']}")
    ck(abs(m["route_t"]["Special Handling"] - 48.0) < 1e-6, "SH 路线 = 48 t", f"{m['route_t']['Special Handling']}")
    ck(abs(m["route_t"]["Residual / Disposal"] - 44.0) < 1e-6, "Residual 路线 = 44 t", f"{m['route_t']['Residual / Disposal']}")
    ck(abs(m["output_t"] - OUTPUT_T) < 1e-6, "总输出 = 992 t", f"{m['output_t']}")

    # 3. state pools
    ck(abs(m["state_t"]["Output"] - 992.0) < 1e-6, "状态池 Output = 992 t", f"{m['state_t']['Output']}")
    ck(abs(m["state_t"]["In Progress"] - 155.0) < 1e-6, "状态池 In Progress = 155 t", f"{m['state_t']['In Progress']}")
    ck(abs(m["state_t"]["Pending Processing"] - 68.2) < 1e-6, "状态池 Pending = 68.2 t", f"{m['state_t']['Pending Processing']}")
    ck(abs(m["state_t"]["Unresolved"] - 24.8) < 1e-6, "状态池 Unresolved = 24.8 t", f"{m['state_t']['Unresolved']}")
    ck(abs(m["backlog_total"] - OPEN_T) < 1e-6, "积压桶合计 = 248 t", f"{m['backlog_total']}")

    # 4. pool economics
    ck(abs(m["realised"]["net_per_t"] - 111.50) < 1e-6, "Realised 池 net/t = +111.50",
       f"{m['realised']['net_per_t']}")
    ck(abs(m["provisional"]["net_per_t"] - (-96.00)) < 1e-6, "Provisional 池 net/t = -96.00",
       f"{m['provisional']['net_per_t']}")

    # 5. Dec vs Nov inspection backlog
    ck(abs(m["insp_backlog_delta_pct"] - 20.00) < 1e-6, "Dec vs Nov 在检积压 +20.0%",
       f"{m['insp_backlog_dec']} vs {m['insp_backlog_nov']} = +{m['insp_backlog_delta_pct']}%")

    # 6. scale
    ck(len(batches) == 36, "36 批", f"{len(batches)}")
    ck(m["incoming_t"] == 1240.0, "入库合计 = 1,240 t", f"{m['incoming_t']}")
    ck(len({b["arrival_date"].strftime("%Y-%m") for b in batches}) == 12, "12 个月均有到达批次")
    ck(len(outputs) >= 60, "输出行数充足", f"{len(outputs)}")
    ck(m["n_materials"] >= 1000, "物料 ≥ 1000", f"{m['n_materials']}")
    ck(abs(m["material_kg_total"] - 1240000.0) < 1.0, "物料总重 = 1,240,000 kg", f"{m['material_kg_total']}")

    # 7. cost ledger
    cat = {}
    for c in costs:
        cat[c["cost_category"]] = round(cat.get(c["cost_category"], 0.0) + c["total_cost_aud"], 2)
    ck(abs(m["cost_aud"] - 230640.0) < 1e-6, "成本合计 = 230,640", f"{m['cost_aud']}")
    ck(abs(cat.get("Sorting Labour", 0) - 66960.0) < 1e-6, "Sorting = 66,960", f"{cat.get('Sorting Labour')}")
    ck(abs(cat.get("Inspection", 0) - 52080.0) < 1e-6, "Inspection = 52,080", f"{cat.get('Inspection')}")
    ck(abs(cat.get("Processing", 0) - 103596.0) < 1e-6, "Processing = 103,596", f"{cat.get('Processing')}")
    ck(abs(cat.get("Special Handling", 0) - 5760.0) < 1e-6, "Special Handling = 5,760", f"{cat.get('Special Handling')}")
    ck(abs(cat.get("Disposal", 0) - 2244.0) < 1e-6, "Disposal = 2,244", f"{cat.get('Disposal')}")
    ck("Transport" not in cat and "Other" not in cat, "无 Transport / Other 行")

    # 8. outputs consistency
    ck(all(abs(o["gross_value_aud"] - o["weight_t"] * o["unit_value_aud_per_t"]) < 0.011
           for o in outputs), "输出 gross = weight × unit 逐行成立")

    # 9. events
    ck(len(events) >= 36 * 4, "处理事件 ≥ 144", f"{len(events)}")
    ck(len(inspections) >= 50, "检验事件 ≥ 50", f"{len(inspections)}")
    open_ev = [e for e in events if e["status"] == "Open"]
    ck(len(open_ev) == 3, "开放事件恰 3 条（B030/B034×2）", f"{len(open_ev)}")

    # 10. structural: FKs, required columns, weights
    bid_set = {b["batch_id"] for b in batches}
    sid_set = {b["source_id"] for b in batches}
    ck(len(sid_set) == 16, "16 个来源项目", f"{len(sid_set)}")
    ck(all(b["source_id"] in sid_set for b in batches), "批次 FK 引用有效")
    ck(all(mid["batch_id"] in bid_set for mid in materials), "物料 FK 引用有效")
    ck(all(o["batch_id"] in bid_set for o in outputs), "输出 FK 引用有效")
    ck(all(c["batch_id"] in bid_set for c in costs), "成本 FK 引用有效")
    ck(all(e["batch_id"] in bid_set for e in events), "处理事件 FK 引用有效")
    ck(all(i["batch_id"] in bid_set for i in inspections), "检验事件 FK 引用有效")
    ck(all(x["estimated_weight_kg"] > 0 for x in materials), "物料重量全部为正")
    ck(all(o["weight_t"] > 0 for o in outputs), "输出重量全部为正")
    ck(all(c["total_cost_aud"] > 0 for c in costs), "成本全部为正")
    ck(all(o["output_date"] <= _date(SNAPSHOT) for o in outputs), "输出均早于快照时间")

    # 11. per-batch completeness (completed batches fully processed, open zero)
    for b in batches:
        tot = round(sum(o["weight_t"] for o in outputs if o["batch_id"] == b["batch_id"]), 3)
        if b["batch_status"] == "Completed":
            ck(abs(tot - b["incoming_weight_t"]) < 1e-6, f"{b['batch_id']} 全量输出", f"{tot}/{b['incoming_weight_t']}")
        else:
            ck(tot == 0.0, f"{b['batch_id']} 零输出", f"{tot}")

    # 12. material state consistency per batch
    for b in batches:
        kg = round(sum(x["estimated_weight_kg"] for x in materials if x["batch_id"] == b["batch_id"]), 1)
        ck(abs(kg - b["incoming_weight_t"] * 1000.0) < 1.0, f"{b['batch_id']} 物料重一致", f"{kg}")

    return checks

# ---------------------------------------------------------------------------
# 15. CSV export
# ---------------------------------------------------------------------------
CSV_FILES = {
    "SourceProjects": "source_projects.csv",
    "Batches": "batches.csv",
    "Materials": "materials.csv",
    "RecoveryOutputs": "recovery_outputs.csv",
    "CostLedger": "cost_ledger.csv",
    "ProcessingEvents": "processing_events.csv",
    "InspectionEvents": "inspection_events.csv",
}

STALE_CSV = [
    "chart_batch_economics.csv", "chart_cost_vs_value.csv",
    "chart_incoming_vs_processed.csv", "chart_net_sorting_benefit.csv",
    "chart_operational_backlog.csv", "chart_recovery_routes.csv",
]

# per-column decimal precision so no information is lost on export
_COL_DP = {
    "incoming_weight_t": 3, "estimated_weight_kg": 1, "weight_t": 3, "quantity": 3,
    "unit_value_aud_per_t": 2, "unit_cost_aud": 4, "total_cost_aud": 2,
    "gross_value_aud": 2, "labour_hours": 1, "machine_hours": 1,
    "external_cost_aud": 2, "value": 2,
}

def write_csv(path, rows, columns, _unused=None):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            out = {}
            for col in columns:
                v = r.get(col)
                if isinstance(v, float):
                    dp = _COL_DP.get(col, 2)
                    out[col] = f"{v:.{dp}f}"
                elif isinstance(v, (dt.date, dt.datetime)):
                    out[col] = _fmt_date(v) if isinstance(v, dt.date) else _fmt_dt(v)
                else:
                    out[col] = v if v is not None else ""
            w.writerow(out)

def export_csv(batches, materials, outputs, costs, events, inspections, assumptions, lookups):
    os.makedirs(CSV_DIR, exist_ok=True)
    src_rows = []
    for (sid, stype, region, fuc, qual, comp, _first) in SOURCE_PLAN:
        batches_of_src = [b for b in batches if b["source_id"] == sid]
        first = min(batches_of_src, key=lambda b: b["arrival_date"]).get("arrival_date")
        sub = _date(first) - dt.timedelta(days=RNG.randint(5, 20)) if first else _d(YEAR, 1, 1)
        src_rows.append({
            "source_id": sid,
            "source_type": stype,
            "region": region,
            "former_use_category": fuc,
            "submission_date": _date(sub),
            "estimated_material_quality": qual,
            "expected_complexity": comp,
            "notes": f"Synthetic source project; {len(batches_of_src)} batch(es) in the sample dataset.",
        })

    write_csv(os.path.join(CSV_DIR, CSV_FILES["SourceProjects"]), src_rows,
              ["source_id", "source_type", "region", "former_use_category",
               "submission_date", "estimated_material_quality", "expected_complexity", "notes"])
    write_csv(os.path.join(CSV_DIR, CSV_FILES["Batches"]), batches,
              ["batch_id", "source_id", "arrival_date", "incoming_weight_t",
               "planned_sorting_intensity", "current_stage", "batch_status",
               "priority", "notes"])
    write_csv(os.path.join(CSV_DIR, CSV_FILES["Materials"]), materials,
              ["material_id", "batch_id", "estimated_weight_kg", "species",
               "material_form", "former_use", "known_treatment_status",
               "surface_condition", "record_completeness", "requires_inspection",
               "special_handling_flag", "initial_recovery_grade", "recovery_grade",
               "current_route", "resolution_status", "output_date"])
    write_csv(os.path.join(CSV_DIR, CSV_FILES["RecoveryOutputs"]), outputs,
              ["output_id", "batch_id", "output_date", "recovery_route",
               "recovery_grade", "weight_t", "unit_value_aud_per_t", "gross_value_aud"])
    write_csv(os.path.join(CSV_DIR, CSV_FILES["CostLedger"]), costs,
              ["cost_id", "batch_id", "cost_date", "cost_category", "quantity",
               "unit", "unit_cost_aud", "total_cost_aud", "notes"])
    write_csv(os.path.join(CSV_DIR, CSV_FILES["ProcessingEvents"]), events,
              ["event_id", "batch_id", "stage", "start_datetime", "end_datetime",
               "weight_in_t", "weight_out_t", "labour_hours", "machine_hours", "status"])
    write_csv(os.path.join(CSV_DIR, CSV_FILES["InspectionEvents"]), inspections,
              ["inspection_id", "batch_id", "material_id", "inspection_type",
               "reason", "opened_datetime", "closed_datetime", "status",
               "labour_hours", "external_cost_aud", "outcome"])
    write_csv(os.path.join(CSV_DIR, "assumptions.csv"), assumptions,
              ["assumption_id", "assumption_key", "category", "metric", "value",
               "unit", "description", "source"])
    write_csv(os.path.join(CSV_DIR, "lookups.csv"), lookups,
              ["domain", "value", "description", "sort_order"])
    for stale in STALE_CSV:
        p = os.path.join(CSV_DIR, stale)
        if os.path.exists(p):
            os.remove(p)

# ---------------------------------------------------------------------------
# 16. Main
# ---------------------------------------------------------------------------
def main():
    print(f"Workbench demo dataset generator (seed={SEED})")
    print("-" * 70)

    assumptions = build_assumptions()
    lookups = build_lookups()

    batches = build_batches()
    assign_timeline(batches)

    budget_map = {}
    completed = [b for b in batches if b["batch_status"] == "Completed"]
    budgets_list = compute_batch_budgets(batches)
    for b, (pools, split, proc) in zip(completed, budgets_list):
        budget_map[b["batch_id"]] = (pools, split, proc)

    materials = build_materials(batches, budgets_list)
    outputs = build_outputs(batches, budget_map)
    costs = build_cost_ledger(batches, budget_map)
    events = build_processing_events(batches)
    inspections = build_inspection_events(batches, materials)

    m = compute_metrics(batches, materials, outputs, costs, budget_map)
    m["identity_check"] = round(m["avg_value_per_t"] * m["processing_rate"] / 100.0 - m["avg_cost_per_t"], 2)
    m["value_identity"] = m["net_per_t"] - 70.00

    checks = validate(batches, materials, outputs, costs, events, inspections, m)

    n_pass = sum(1 for ok, _, _ in checks if ok)
    n_fail = len(checks) - n_pass
    print(f"\nValidation: {n_pass} PASS / {n_fail} FAIL (total {len(checks)})")
    for ok, name, detail in checks:
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {name}" + (f"  ({detail})" if detail else ""))
    if n_fail:
        print("\nValidation FAILED — dataset not written.")
        return 1

    export_csv(batches, materials, outputs, costs, events, inspections, assumptions, lookups)
    print(f"\nExported CSVs to {CSV_DIR}")
    print(f"  batches={len(batches)} materials={len(materials)} outputs={len(outputs)}")
    print(f"  costs={len(costs)} processing_events={len(events)} inspection_events={len(inspections)}")
    print(f"  assumptions={len(assumptions)} lookups={len(lookups)}")
    print(f"\nIdentity: {m['avg_value_per_t']} x {m['processing_rate']}% - {m['avg_cost_per_t']} = {m['net_per_t']} AUD/t")
    print(f"Gross {m['gross_aud']} - Cost {m['cost_aud']} = Net {m['net_aud']} (= {m['net_per_t']} x {m['incoming_t']})")
    print(f"Realised pool: {m['realised']['net_per_t']} AUD/t | Provisional pool: {m['provisional']['net_per_t']} AUD/t")
    print(f"Inspection backlog Dec {m['insp_backlog_dec']} vs Nov {m['insp_backlog_nov']} -> +{m['insp_backlog_delta_pct']}%")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())