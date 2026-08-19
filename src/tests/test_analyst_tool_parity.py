"""Tool/API parity tests — analyst tools must agree with the approved FastAPI/service
outputs (no divergent AI analytics)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.analyst_tools.registry import REGISTRY
from app.db import session
from app.main import app


def run(tool_name: str, payload: dict) -> dict:
    with session() as conn:
        result = REGISTRY.execute(tool_name, payload, conn)
    assert result.success, f"{tool_name} failed: {result.error}"
    return result.data


def test_overview_tool_matches_api():
    client = TestClient(app)
    api = client.get("/api/v1/overview").json()
    tool = run("get_overview_metrics", {})

    assert tool["north_star"]["value"] == api["north_star"]["value"]
    api_kpi_keys = {
        "incoming_timber_t": "incoming_timber",
        "processed_timber_t": "processed_timber",
        "higher_value_recovery_rate": "higher_value_recovery_rate",
        "processing_cost_per_processed_t": "processing_cost_per_processed_t",
        "recovered_value_per_t": "recovered_value_per_t",
        "unresolved_inspection_rate": "unresolved_inspection_rate",
    }
    for tool_key, api_key in api_kpi_keys.items():
        assert tool["kpis"][tool_key] == api["kpis"][api_key]["value"], tool_key


def test_batch_details_tool_matches_api():
    client = TestClient(app)
    for bid in ("B017", "B022", "B030"):
        api_batch = client.get(f"/api/v1/batches/{bid}").json()["batch"]
        tool_batch = run("get_batch_details", {"batch_id": bid})["batch"]
        for field in ("status", "economic_evaluation_status", "eligible_for_realised_comparison",
                      "economic_quadrant", "incoming_weight_t", "processed_weight_t",
                      "sorting_plus_inspection_cost_per_t", "net_sorting_benefit_aud",
                      "net_recovery_value_per_t", "higher_value_recovery_rate",
                      "inspection_exposure_rate", "unresolved_rate", "downgrade_rate"):
            assert tool_batch[field] == api_batch[field], f"{bid}.{field}"


def test_source_performance_tool_matches_api():
    client = TestClient(app)
    api = client.get("/api/v1/source-performance").json()
    tool = run("get_source_performance", {})
    assert tool["realised_source_performance"] == api["realised_source_performance"]
    assert tool["current_operational_exposure"] == api["current_operational_exposure"]


def test_monthly_tool_matches_api():
    client = TestClient(app)
    api = client.get("/api/v1/monthly-performance").json()["months"]
    tool = run("get_monthly_performance", {})["months"]
    assert len(tool) == len(api) == 12
    for t, a in zip(tool, api):
        for field in ("month", "incoming_timber_t", "processed_timber_t",
                      "higher_value_recovery_rate", "processing_cost_per_processed_t",
                      "recovered_value_per_t", "net_recovery_value_per_t",
                      "sorting_backlog_t", "inspection_backlog_t",
                      "processing_backlog_t", "unresolved_backlog_t"):
            assert t[field] == a[field], f"{t['month']}.{field}"


def test_management_report_tool_matches_api():
    client = TestClient(app)
    api = client.get("/api/v1/management-report-data").json()["sections"]
    tool = run("get_management_report_data", {})["sections"]
    assert tool["executive_metrics"] == api["executive_metrics"]
    assert tool["recovery_performance"] == api["recovery_performance"]
    assert tool["risk_uncertainty"] == api["risk_uncertainty"]
    assert tool["outlier_batches"] == api["outlier_batches"]


def test_backlog_tool_matches_overview_chart():
    client = TestClient(app)
    api_backlog = client.get("/api/v1/overview").json()["charts"]["operational_backlog"]
    tool = run("get_operational_backlog", {})["buckets"]
    api_map = {r["backlog_stage"]: r["weight_t"] for r in api_backlog}
    assert tool["sorting_backlog_t"] == api_map["Sorting"]
    assert tool["inspection_backlog_t"] == api_map["Inspection"]
    assert tool["processing_backlog_t"] == api_map["Processing"]
    assert tool["unresolved_backlog_t"] == api_map["Unresolved"]


def test_batch_economics_tool_matches_overview_chart():
    client = TestClient(app)
    api_econ = client.get("/api/v1/overview").json()["charts"]["batch_economics"]
    tool = run("get_batch_economics", {"include_provisional": True})["batches"]
    api_map = {r["batch_id"]: r for r in api_econ}
    for t in tool:
        a = api_map[t["batch_id"]]
        assert t["economic_quadrant"] == a["economic_quadrant"], t["batch_id"]
        assert t["sorting_plus_inspection_cost_per_t"] == a["sorting_plus_inspection_cost_per_t"]
        assert t["recovered_value_per_t"] == a["recovered_value_per_t"]


def test_sorting_economics_consistent_with_report():
    tool = run("get_sorting_economics", {})["results"]
    assert tool["negative_sorting_benefit_count"] == 4  # matches approved report (realised negatives)
    assert tool["realised_batch_count"] == 28
