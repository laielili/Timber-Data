"""Backend Phase 02 — end-to-end data propagation test.

Proves the pipeline really derives output from raw SQLite data: we copy the approved
database to a temporary file, mutate ONE controlled raw input (B022 RecoveryOutputs
unit values), point the backend at the copy, and confirm the API metrics change.

The approved database is never touched (hash verified before and after).
"""
from __future__ import annotations

import hashlib
import shutil
import sqlite3

from fastapi.testclient import TestClient

from app import config
from app.main import app

APPROVED_DB = config.PROJECT_ROOT / "data" / "circular_timber_synthetic.db"


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_mutation_propagates_from_sqlite_through_api(tmp_path, monkeypatch):
    before_hash = _sha256(APPROVED_DB)

    # ---- baseline from the APPROVED database (before mutation) -------------
    approved_client = TestClient(app)
    base_ov = approved_client.get("/api/v1/overview").json()
    base_rv = base_ov["kpis"]["recovered_value_per_t"]["value"]
    base_ns = base_ov["north_star"]["value"]
    base_b22_gross = approved_client.get("/api/v1/batches/B022").json()["batch"]["gross_recovered_value_aud"]

    # ---- 1. copy DB to a temporary test database ----------------------------
    tmp_db = tmp_path / "mutated.db"
    shutil.copy2(APPROVED_DB, tmp_db)

    # ---- 2. point the backend test environment at the copy ------------------
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_db)

    # ---- 3. mutate ONE controlled raw input: raise B022 output unit values --
    conn = sqlite3.connect(tmp_db)
    conn.execute(
        "UPDATE RecoveryOutputs SET unit_value_aud_per_t = ROUND(unit_value_aud_per_t * 1.1, 2) WHERE batch_id = 'B022'"
    )
    conn.execute(
        "UPDATE RecoveryOutputs SET gross_value_aud = ROUND(weight_t * unit_value_aud_per_t, 2) WHERE batch_id = 'B022'"
    )
    conn.commit()
    conn.close()

    # ---- 4-6. fetch the API against the mutated copy ------------------------
    mutated_client = TestClient(app)
    mut_ov = mutated_client.get("/api/v1/overview").json()
    mut_rv = mut_ov["kpis"]["recovered_value_per_t"]["value"]
    mut_ns = mut_ov["north_star"]["value"]
    mut_b22_gross = mutated_client.get("/api/v1/batches/B022").json()["batch"]["gross_recovered_value_aud"]

    # ---- 7. confirm calculated output changed in the expected direction -----
    assert mut_b22_gross > base_b22_gross + 100.0, "B022 gross recovered value must rise after unit-value increase"
    assert mut_rv > base_rv + 1.0, "Recovered Value / t must rise"
    assert mut_ns > base_ns + 1.0, "North Star must rise"

    # sanity: an unrelated batch metric should be unchanged by the B022 edit
    assert approved_client.get("/api/v1/batches/B017").json()["batch"]["gross_recovered_value_aud"] == \
           mutated_client.get("/api/v1/batches/B017").json()["batch"]["gross_recovered_value_aud"]

    # ---- 8-9. cleanup + approved database unchanged --------------------------
    shutil.rmtree(tmp_path, ignore_errors=True)
    assert _sha256(APPROVED_DB) == before_hash, "approved database must remain byte-identical"
