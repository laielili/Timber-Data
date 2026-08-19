"""Core formula tests — the backend must derive these from the approved SQLite
database. Values are used as regression expectations only (never hard-coded into
the services)."""
from __future__ import annotations

from fastapi.testclient import TestClient


def _overview(client: TestClient) -> dict:
    r = client.get("/api/v1/overview")
    assert r.status_code == 200
    return r.json()


def _batch(client: TestClient, batch_id: str) -> dict:
    r = client.get(f"/api/v1/batches/{batch_id}")
    assert r.status_code == 200
    return r.json()["batch"]


def test_01_incoming_timber_full_year(client):
    ov = _overview(client)
    assert abs(ov["kpis"]["incoming_timber"]["value"] - 1240.0) <= 0.01


def test_02_processed_timber(client):
    ov = _overview(client)
    assert abs(ov["kpis"]["processed_timber"]["value"] - 1013.365) <= 0.01


def test_03_higher_value_recovery_rate(client):
    ov = _overview(client)
    assert abs(ov["kpis"]["higher_value_recovery_rate"]["value"] - 39.1) <= 0.05


def test_04_north_star(client):
    ov = _overview(client)
    assert abs(ov["north_star"]["value"] - 85.08) <= 0.01
    # analytical companion
    assert abs(ov["north_star"]["closed_batch_net_recovery_value_per_t"] - 143.38) <= 0.01


def test_05_processing_cost_per_processed_t(client):
    ov = _overview(client)
    v = ov["kpis"]["processing_cost_per_processed_t"]["value"]
    assert 99.5 <= v <= 102.0  # corrected denominator = processed t


def test_06_recovery_route_weights_sum_to_processed(client):
    ov = _overview(client)
    routes = ov["charts"]["recovery_route_distribution"]
    total = sum(r["weight_t"] for r in routes)
    assert abs(total - ov["kpis"]["processed_timber"]["value"]) <= 0.02


def test_07_recovery_route_percentages_sum_100(client):
    ov = _overview(client)
    pct_sum = sum(r["percentage"] for r in ov["charts"]["recovery_route_distribution"])
    assert abs(pct_sum - 100.0) <= 0.05


def test_08_backlog_buckets_no_double_count(client):
    ov = _overview(client)
    backlog = ov["charts"]["operational_backlog"]
    stages = [b["backlog_stage"] for b in backlog]
    assert len(stages) == len(set(stages)) == 4  # mutually exclusive stages
    # percentage_of_open_weight derived from the four buckets
    total = sum(b["weight_t"] for b in backlog)
    for b in backlog:
        assert abs(b["percentage_of_open_weight"] - b["weight_t"] / total * 100) <= 0.05


def test_09_b017_realised_poor_sorting(client):
    b = _batch(client, "B017")
    assert b["economic_evaluation_status"] == "Realised"
    assert b["eligible_for_realised_comparison"] is True
    assert b["net_sorting_benefit_aud"] < 0
    assert b["economic_quadrant"] == "Review Required"
    assert abs(b["sorting_plus_inspection_cost_per_t"] - 229.52) <= 0.01


def test_10_b030_provisional(client):
    b = _batch(client, "B030")
    assert b["economic_evaluation_status"] == "Provisional"
    assert b["eligible_for_realised_comparison"] is False
    assert b["economic_quadrant"] is None


def test_11_realised_economics_excludes_b030(client):
    ov = _overview(client)
    realised_ids = {
        r["batch_id"]
        for r in ov["charts"]["batch_economics"]
        if r["eligible_for_realised_comparison"]
    }
    assert "B030" not in realised_ids
    assert len(realised_ids) == 28


def test_12_management_brief_growth_calculated(client):
    r = client.get("/api/v1/management-brief")
    assert r.status_code == 200
    item = next(b for b in r.json()["briefs"] if b["id"] == "brief_inspection_backlog")
    growth = item["values"]["inspection_backlog_growth_vs_nov_pct"]
    # growth is computed from the database (104.086 vs 85.545), not hard-coded
    assert growth is not None and abs(growth - 21.7) <= 0.1
    assert "21.7%" in item["detail"]


def test_13_invalid_batch_returns_404(client):
    assert client.get("/api/v1/batches/NOPE").status_code == 404


def test_14_invalid_period_returns_422(client):
    assert client.get("/api/v1/overview", params={"period_start": "2026-01-01"}).status_code == 422
    assert (
        client.get(
            "/api/v1/overview",
            params={"period_start": "2025-06-01", "period_end": "2025-05-01"},
        ).status_code
        == 422
    )
    assert client.get("/api/v1/overview", params={"as_of": "not-a-date"}).status_code == 422
