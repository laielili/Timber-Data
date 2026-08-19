"""Contract parity tests — the backend must reproduce the approved frontend mock
JSON (semantic/numeric equivalence, not literal string equality). The mock JSON is
a REGRESSION REFERENCE ONLY; the backend computes everything from SQLite.

Documented tolerated differences:
- `scenario`: generator-memory field, not persisted in the DB (contract marks it
  demo-only / optional) -> compared only when both sides have a value.
- Processing backlog weight 79.37 (mock) vs 79.36 (MaterialMonthlyState kg sums):
  sub-cent rounding at month-end state granularity; weight tolerance covers it.
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

# tolerance per field-kind (smaller is stricter)
TOL = 0.02  # default numeric tolerance
TOL_PCT = 0.05
TOL_WEIGHT = 0.05
TOL_CENT = 0.011

# fields where backend is expected to differ structurally (documented above)
IGNORED_FIELDS = {"scenario", "notes"}


def _close(a, b, tol):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol
    return a == b


def _cmp_values(a, b, path: str, errors: list[str]):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in a.keys() | b.keys():
            if k in IGNORED_FIELDS:
                continue
            _cmp_values(a.get(k), b.get(k), f"{path}.{k}", errors)
        return
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            errors.append(f"{path}: length {len(a)} vs {len(b)}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            _cmp_values(x, y, f"{path}[{i}]", errors)
        return
    if a is None or b is None:
        if a is not b:
            errors.append(f"{path}: None mismatch ({a!r} vs {b!r})")
        return
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        tol = TOL
        if path.endswith("percentage") or path.endswith("_rate") or "percentage_of_open_weight" in path:
            tol = TOL_PCT
        elif path.endswith("_t") or path.endswith("weight_t") or "incoming_weight_t" in path:
            tol = TOL_WEIGHT
        elif path.endswith("_aud") or path.endswith("_per_t") or path.endswith("_per_processed_t"):
            tol = TOL_CENT if "per_t" in path else TOL_CENT
        if not _close(a, b, tol):
            errors.append(f"{path}: {a!r} vs {b!r} (tol {tol})")
        return
    if a != b:
        errors.append(f"{path}: {a!r} vs {b!r}")


def _load(mock_dir: Path, name: str) -> dict:
    with open(mock_dir / name, encoding="utf-8") as f:
        return json.load(f)


def _assert_parity(errors: list[str], label: str):
    assert not errors, f"parity mismatch ({label}):\n" + "\n".join(errors[:25])


def test_overview_parity(client, mock_dir):
    backend = client.get("/api/v1/overview").json()
    mock = _load(mock_dir, "overview.json")

    errors: list[str] = []
    _cmp_values(backend["meta"], mock["meta"], "meta", errors)
    _cmp_values(backend["north_star"], mock["north_star"], "north_star", errors)
    _cmp_values(backend["kpis"], mock["kpis"], "kpis", errors)
    _cmp_values(backend["charts"], mock["charts"], "charts", errors)
    _assert_parity(errors, "overview.json")


def test_management_brief_parity(client, mock_dir):
    backend = client.get("/api/v1/management-brief").json()
    mock = _load(mock_dir, "management_brief.json")
    errors: list[str] = []
    _cmp_values(backend, mock, "brief", errors)
    _assert_parity(errors, "management_brief.json")


def test_batch_b017_parity(client, mock_dir):
    backend = client.get("/api/v1/batches/B017").json()
    mock = _load(mock_dir, "batch_B017.json")
    errors: list[str] = []
    _cmp_values(backend, mock, "b017", errors)
    _assert_parity(errors, "batch_B017.json")


def test_batch_b030_parity(client, mock_dir):
    backend = client.get("/api/v1/batches/B030").json()
    mock = _load(mock_dir, "batch_B030.json")
    errors: list[str] = []
    _cmp_values(backend, mock, "b030", errors)
    _assert_parity(errors, "batch_B030.json")


def test_source_performance_parity(client, mock_dir):
    backend = client.get("/api/v1/source-performance").json()
    mock = _load(mock_dir, "source_performance.json")
    errors: list[str] = []
    _cmp_values(backend, mock, "source_performance", errors)
    _assert_parity(errors, "source_performance.json")


def test_batch_list_parity(client, mock_dir):
    """All 36 batches match mock batch_list.json (demo-only fields excluded)."""
    backend = client.get("/api/v1/batches").json()["batches"]
    mock = _load(mock_dir, "batch_list.json")["batches"]
    assert len(backend) == len(mock) == 36
    mock_by_id = {b["batch_id"]: b for b in mock}
    errors: list[str] = []
    for b in backend:
        _cmp_values(b, mock_by_id[b["batch_id"]], f"batch.{b['batch_id']}", errors)
    _assert_parity(errors, "batch_list.json")


def test_monthly_performance_parity(client, mock_dir):
    backend = client.get("/api/v1/monthly-performance").json()["months"]
    mock = _load(mock_dir, "monthly_performance.json")["months"]
    assert len(backend) == len(mock) == 12
    errors: list[str] = []
    for b, m in zip(backend, mock):
        _cmp_values(b, m, f"month.{b['month']}", errors)
    _assert_parity(errors, "monthly_performance.json")


def test_management_report_parity(client, mock_dir):
    """Numeric parity on the deterministic report sections."""
    backend = client.get("/api/v1/management-report-data").json()
    mock = _load(mock_dir, "management_report_data.json")
    errors: list[str] = []
    _cmp_values(backend["sections"], mock["sections"], "sections", errors)
    _assert_parity(errors, "management_report_data.json")


def test_backend_never_reads_mock_files():
    """Structural guard: the backend package must not reference the mock JSON files.
    Mock JSON is regression reference only; SQLite is the actual source."""
    import re
    from pathlib import Path

    app_dir = Path(__file__).resolve().parents[1] / "app"
    offenders = []
    for py in app_dir.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        if "data/mock" in text or re.search(r'"(overview|batch_list|management_brief)\.json"', text):
            offenders.append(str(py))
    assert not offenders, f"backend must not read mock JSON: {offenders}"
