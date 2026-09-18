"""Dump `dashboard_service.get_dashboard()` to JSON.

`static/new/src/mock.ts` is declared to be the verbatim output of this call, so
the static prototype in `docs/` and the real backend can never drift apart. Run
this after any change to the metric system, then paste the result into mock.ts.

    python scripts/_dump_dashboard.py > /tmp/dashboard.json

The stub below exists only because this machine has no pydantic installed; it
replaces `new.schemas` with a minimal FilterParams so the service can run
standalone. Delete the stub once the venv is healthy.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# `src/` must come first: the project root also holds `new.py`, which would
# otherwise shadow the `new` package under `src/`.
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def _install_schemas_stub() -> None:
    try:
        import pydantic  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    mod = types.ModuleType("new.schemas")

    class FilterParams:  # noqa: D401 - minimal stand-in for the pydantic model
        _FIELDS = (
            "period_start", "period_end", "source_type", "region", "species",
            "material_form", "recovery_route", "batch_status", "current_stage",
        )

        def __init__(self, **kw):
            for name in self._FIELDS:
                setattr(self, name, kw.get(name))

        def model_dump(self) -> dict:
            return {name: getattr(self, name) for name in self._FIELDS}

    mod.FilterParams = FilterParams
    sys.modules["new.schemas"] = mod


def main() -> None:
    _install_schemas_stub()
    from new import dashboard_service, db
    from new.schemas import FilterParams

    conn = db.connect()
    try:
        data = dashboard_service.get_dashboard(conn, FilterParams())
    finally:
        conn.close()
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
