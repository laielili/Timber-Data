"""Analyst tool layer tests — execution, regressions, schemas, errors, audit logging."""
from __future__ import annotations

import json
import logging

import pytest

from app.analyst_tools.registry import REGISTRY, ToolExecutionResult
from app.db import session

ALL_TOOL_NAMES = [
    "get_overview_metrics",
    "get_recovery_performance",
    "get_operational_backlog",
    "get_batch_details",
    "compare_batches",
    "get_sorting_economics",
    "get_batch_economics",
    "get_source_performance",
    "get_uncertainty_distribution",
    "get_monthly_performance",
    "get_management_report_data",
    "find_batches",
]


def run(tool_name: str, payload: dict) -> ToolExecutionResult:
    with session() as conn:
        return REGISTRY.execute(tool_name, payload, conn)


# --------------------------------------------------------------------------- registry/schemas


def test_tool_count_and_names():
    assert set(REGISTRY.names()) == set(ALL_TOOL_NAMES)
    assert len(REGISTRY.all()) == 12


def test_schema_tests_unique_descriptions_and_json():
    names = set()
    for spec in REGISTRY.all():
        assert spec.name not in names, f"duplicate tool name {spec.name}"
        names.add(spec.name)
        assert spec.description and spec.business_question
        assert spec.input_schema and spec.output_schema
        # schemas serialise to JSON (future LLM tool definitions)
        json.dumps(spec.input_schema.model_json_schema())
        json.dumps(spec.output_schema.model_json_schema())


def test_invalid_inputs_fail_validation():
    r = run("get_batch_details", {"batch_id": ""})
    assert not r.success and r.error_type == "InvalidInput"
    r = run("compare_batches", {"batch_ids": ["B017"]})  # min 2
    assert not r.success and r.error_type == "InvalidInput"
    r = run("compare_batches", {"batch_ids": [f"B{i:03d}" for i in range(12)]})  # max 10
    assert not r.success and r.error_type == "InvalidInput"


# --------------------------------------------------------------------------- tool 01-03


def test_tool_01_overview_metrics():
    r = run("get_overview_metrics", {})
    assert r.success
    d = r.data
    assert d["north_star"]["value"] == 85.08
    assert d["kpis"]["incoming_timber_t"] == 1240.0
    assert d["kpis"]["processed_timber_t"] == 1013.365
    assert d["kpis"]["processing_cost_per_processed_t"] == 100.74
    assert d["totals"]["net_recovery_value_aud"] > 100_000
    assert d["prototype_target"]["higher_value_recovery_target_pct"] == 30.0
    assert d["provenance"]["prototype"] is True


def test_tool_02_recovery_performance():
    r = run("get_recovery_performance", {})
    assert r.success
    d = r.data
    assert d["routes"]["higher_value_weight_t"] == 396.25
    assert abs(sum(d["routes"].values()) - d["processed_weight_t"]) < 0.01
    assert abs(d["rates"]["higher_value_recovery_rate"] - 39.1) < 0.05
    assert len(d["monthly_recovery_performance"]) == 12


def test_tool_03_operational_backlog():
    r = run("get_operational_backlog", {})
    assert r.success
    d = r.data
    assert d["buckets"]["inspection_backlog_t"] == 104.09
    assert d["open_batch_count"] == 8
    assert d["comparison"] is not None
    growth = d["comparison"]["change_percent"]["inspection_backlog_t"]
    assert growth is not None and abs(growth - 21.7) < 0.1


# --------------------------------------------------------------------------- tool 04 regressions


def test_tool_04_batch_details_b017_regression():
    r = run("get_batch_details", {"batch_id": "B017"})
    assert r.success
    b = r.data["batch"]
    assert b["status"] == "Completed"
    assert b["economic_evaluation_status"] == "Realised"
    assert b["eligible_for_realised_comparison"] is True
    assert b["economic_quadrant"] == "Review Required"
    assert abs(b["sorting_plus_inspection_cost_per_t"] - 229.52) < 0.01
    assert abs(b["net_sorting_benefit_aud"] - (-6172.24)) < 0.01
    assert abs(b["net_recovery_value_per_t"] - (-75.22)) < 0.01
    assert b["evidence_status"] == "realised"


def test_tool_04_batch_details_b022():
    r = run("get_batch_details", {"batch_id": "B022"})
    assert r.success
    b = r.data["batch"]
    assert b["economic_evaluation_status"] == "Realised"
    assert b["net_recovery_value_per_t"] > 100
    assert b["economic_quadrant"] == "Efficient"


def test_tool_04_batch_details_b030_provisional():
    r = run("get_batch_details", {"batch_id": "B030"})
    assert r.success
    b = r.data["batch"]
    assert b["status"] == "Partially Completed"
    assert b["economic_evaluation_status"] == "Provisional"
    assert b["eligible_for_realised_comparison"] is False
    assert b["economic_quadrant"] is None
    assert b["evidence_status"] == "provisional"
    assert "not final" in b["economics_note"].lower()


def test_tool_04_unknown_batch():
    r = run("get_batch_details", {"batch_id": "B999"})
    assert not r.success and r.error_type == "BatchNotFound"


# --------------------------------------------------------------------------- tool 05-08


def test_tool_05_compare_batches_b017_b006_b023():
    r = run("compare_batches", {"batch_ids": ["B017", "B006", "B023"]})
    assert r.success
    d = r.data
    assert len(d["rows"]) == 3
    assert all(row["economic_evaluation_status"] == "Realised" for row in d["rows"])
    # B017 reveals unusually high sorting+inspection cost without causal claims
    assert d["helpers"]["highest_sorting_inspection_cost_per_t"]["batch_id"] == "B017"
    assert d["helpers"]["worst_realised_net_sorting_benefit"]["batch_id"] == "B017"
    assert d["helpers"]["scope"] == "realised"


def test_tool_05_compare_insufficient_realised():
    r = run("compare_batches", {"batch_ids": ["B027", "B030"]})  # both provisional
    assert not r.success and r.error_type == "InsufficientComparableData"


def test_tool_06_sorting_economics():
    r = run("get_sorting_economics", {})
    assert r.success
    d = r.data
    assert d["results"]["realised_batch_count"] == 28
    assert d["results"]["negative_sorting_benefit_count"] == 4
    assert d["results"]["positive_sorting_benefit_count"] == 24
    assert "counterfactual" in d["metric_limitation"].lower()
    assert d["top_negative_batches"][0]["batch_id"] in {"B033", "B030", "B027", "B034", "B017"}


def test_tool_07_batch_economics():
    r = run("get_batch_economics", {})
    assert r.success
    d = r.data
    assert abs(d["benchmark"]["realised_median_x"] - 61.12) < 0.02
    assert abs(d["benchmark"]["realised_median_y"] - 306.99) < 0.02
    realised = [b for b in d["batches"] if b["economic_quadrant"] is not None]
    assert len(realised) == 28
    r2 = run("get_batch_economics", {"include_provisional": True})
    assert len(r2.data["batches"]) == 36
    b030 = next(b for b in r2.data["batches"] if b["batch_id"] == "B030")
    assert b030["economic_quadrant"] is None


def test_tool_08_source_performance():
    r = run("get_source_performance", {})
    assert r.success
    d = r.data
    assert len(d["realised_source_performance"]) == 6
    assert len(d["current_operational_exposure"]) == 5
    assert d["note"]


# --------------------------------------------------------------------------- tool 09-12


def test_tool_09_uncertainty_distribution():
    r = run("get_uncertainty_distribution", {})
    assert r.success
    d = r.data
    assert d["record_quality"]["complete_record_rate"] > 0
    assert "unsafety" in d["limitation"].lower()
    assert len(d["top_uncertainty_batches"]) == 5
    assert len(d["top_uncertainty_sources"]) == 5


def test_tool_10_monthly_performance():
    r = run("get_monthly_performance", {})
    assert r.success
    d = r.data
    assert len(d["months"]) == 12
    dec = d["months"][-1]
    assert dec["inspection_backlog_t"] == 104.09
    assert dec["total_recovery_cost_per_incoming_t"] > 0


def test_tool_11_management_report_data():
    r = run("get_management_report_data", {})
    assert r.success
    assert set(r.data["sections"].keys()) == {
        "executive_metrics", "recovery_performance", "sorting_economics", "operations",
        "risk_uncertainty", "source_performance", "outlier_batches", "data_limitations",
    }


def test_tool_12_find_batches():
    r = run("find_batches", {"economic_quadrant": "Review Required"})
    assert r.success and r.data["count"] == 8
    r = run("find_batches", {"economic_evaluation_status": "Provisional", "min_unresolved_rate": 20})
    assert r.success
    assert all(b["unresolved_rate"] >= 20 for b in r.data["batches"])
    assert all(b["economic_evaluation_status"] == "Provisional" for b in r.data["batches"])


# --------------------------------------------------------------------------- errors + audit


def test_invalid_period_error_types():
    r = run("get_overview_metrics", {"period_start": "2026-01-01"})
    assert not r.success and r.error_type == "UnsupportedPrototypeDateRange"
    r = run("get_overview_metrics", {"period_start": "2025-06-01", "period_end": "2025-05-01"})
    assert not r.success and r.error_type == "InvalidPeriod"
    r = run("get_overview_metrics", {"as_of": "2025-06-30T12:00:00", "period_start": "2025-07-01"})
    assert not r.success and r.error_type == "InvalidPeriod"


def test_unknown_tool():
    with session() as conn:
        r = REGISTRY.execute("not_a_tool", {}, conn)
    assert not r.success and r.error_type == "UnknownTool"


def test_audit_logging(caplog):
    with caplog.at_level(logging.INFO, logger="cti.analyst_tools"):
        run("get_batch_details", {"batch_id": "B017"})
        run("get_batch_details", {"batch_id": "B999"})  # failure path
    messages = [r.getMessage() for r in caplog.records if r.name == "cti.analyst_tools"]
    ok_msgs = [m for m in messages if m.startswith("analyst_tool_ok")]
    fail_msgs = [m for m in messages if m.startswith("analyst_tool_fail")]
    assert len(ok_msgs) == 1 and "get_batch_details" in ok_msgs[0] and "'success': True" in ok_msgs[0]
    assert len(fail_msgs) == 1 and "BatchNotFound" in fail_msgs[0]


def test_provenance_present_on_all_successful_outputs():
    for name in ALL_TOOL_NAMES:
        payload = {"batch_id": "B017", "batch_ids": ["B017", "B006"]} if name in (
            "get_batch_details", "compare_batches") else {}
        r = run(name, payload)
        assert r.success, f"{name} failed: {r.error}"
        assert r.data["provenance"]["dataset_type"] == "synthetic_prototype"
        assert r.data["provenance"]["prototype"] is True
