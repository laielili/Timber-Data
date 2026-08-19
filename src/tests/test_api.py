"""API contract smoke tests — every endpoint returns valid JSON with the expected
shape. Uses FastAPI TestClient (no live server needed)."""
from __future__ import annotations

from fastapi.testclient import TestClient

ENDPOINTS = [
    "/health",
    "/api/v1/overview",
    "/api/v1/management-brief",
    "/api/v1/batches",
    "/api/v1/batches/B017",
    "/api/v1/batches/B030",
    "/api/v1/source-performance",
    "/api/v1/monthly-performance",
    "/api/v1/management-report-data",
]


def test_all_endpoints_return_valid_json(client):
    for path in ENDPOINTS:
        r = client.get(path)
        assert r.status_code == 200, f"{path} -> {r.status_code}"
        data = r.json()
        assert isinstance(data, dict)


def test_health(client):
    j = client.get("/health").json()
    assert j["status"] == "ok"
    assert j["database"] == "connected"
    assert j["dataset_type"] == "synthetic_prototype"


def test_overview_shape(client):
    j = client.get("/api/v1/overview").json()
    assert set(j["kpis"].keys()) == {
        "incoming_timber",
        "processed_timber",
        "higher_value_recovery_rate",
        "processing_cost_per_processed_t",
        "recovered_value_per_t",
        "unresolved_inspection_rate",
    }
    assert set(j["charts"].keys()) == {
        "recovery_route_distribution",
        "incoming_vs_processed",
        "operational_backlog",
        "net_sorting_benefit",
        "cost_vs_recovered_value",
        "batch_economics",
    }
    assert len(j["charts"]["incoming_vs_processed"]) == 12
    assert len(j["charts"]["cost_vs_recovered_value"]) == 12
    assert len(j["charts"]["net_sorting_benefit"]) == 36
    assert len(j["charts"]["batch_economics"]) == 36


def test_batch_list_filters(client):
    j = client.get("/api/v1/batches", params={"economic_evaluation_status": "Realised"}).json()
    assert len(j["batches"]) == 28
    assert all(b["eligible_for_realised_comparison"] for b in j["batches"])
    j = client.get("/api/v1/batches", params={"source_type": "Direct Salvage Purchase"}).json()
    assert all(b["source_type"] == "Direct Salvage Purchase" for b in j["batches"])


def test_single_batch_404(client):
    assert client.get("/api/v1/batches/DOES_NOT_EXIST").status_code == 404


def test_monthly_performance_typed(client):
    j = client.get("/api/v1/monthly-performance").json()
    assert len(j["months"]) == 12
    row = j["months"][0]
    for field in (
        "month",
        "incoming_timber_t",
        "processed_timber_t",
        "higher_value_recovery_rate",
        "processing_cost_aud",
        "total_recovery_cost_aud",
        "gross_recovered_value_aud",
        "net_recovery_value_aud",
        "processing_cost_per_processed_t",
        "recovered_value_per_t",
        "net_recovery_value_per_t",
        "sorting_backlog_t",
        "inspection_backlog_t",
        "processing_backlog_t",
        "unresolved_backlog_t",
    ):
        assert field in row


def test_no_nan_or_infinity_in_payloads(client):
    import math

    for path in ENDPOINTS:
        r = client.get(path)
        if r.status_code != 200:
            continue
        text = r.text
        assert "NaN" not in text and "Infinity" not in text, path
        # also validate numbers are finite at the JSON level
        def walk(v):
            if isinstance(v, float):
                assert math.isfinite(v), path
            elif isinstance(v, dict):
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)

        walk(r.json())


def test_period_parameter_half_year(client):
    r = client.get(
        "/api/v1/overview",
        params={"period_start": "2025-01-01", "period_end": "2025-06-30", "as_of": "2025-06-30T18:00:00"},
    )
    assert r.status_code == 200
    j = r.json()
    assert abs(j["kpis"]["incoming_timber"]["value"] - 631.2) <= 0.1
    assert len(j["charts"]["incoming_vs_processed"]) == 6
    assert len(j["charts"]["cost_vs_recovered_value"]) == 6
