"""Regenerate the generated region of `static/new/src/mock.ts` from the backend.

`mock.ts` is declared to be the verbatim output of
`dashboard_service.get_dashboard()`, so the static prototype in `docs/` cannot
drift away from the real implementation. This script rewrites only the generated
region — everything from `const SOURCE_TYPES` up to `export function mockHealth(`
— and leaves the hand-written tail (mockHealth) alone.

    python scripts/_dump_dashboard.py > .workbuddy/tmp/dash.json
    python scripts/_sync_mock.py .workbuddy/tmp/dash.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MOCK = ROOT / "static" / "new" / "src" / "mock.ts"

HEADER = """// Static-prototype mock data.
//
// This module powers the standalone `docs/` build so the product can be demoed
// without a running backend. Wire it in via the `USE_MOCK` flag in api.ts:
// flip it to `false` to talk to a real backend again. Filters are acknowledged
// but the dataset is intentionally static for the prototype.
//
// GENERATED REGION — do not hand-edit. The block below `const SOURCE_TYPES` is
// the verbatim response of `src/new/dashboard_service.get_dashboard()` run
// against the bundled sample dataset in `data/workbench.db`, so the dashboard,
// the API contract in `documents/frontend/FRONTEND_DATA_CONTRACT.md` and this
// prototype all agree. Currency is AUD; per-tonne rates name their own
// denominator (per processed tonne for value, per incoming tonne for cost),
// because that asymmetry is what makes the M0 identity hold.
//
// Re-sync with:
//   python scripts/_dump_dashboard.py > .workbuddy/tmp/dash.json
//   python scripts/_sync_mock.py .workbuddy/tmp/dash.json
"""

IDENT = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def ts(value: Any, indent: int = 0) -> str:
    """Emit a JS-object literal (unquoted keys, single-quoted strings)."""
    pad = "  " * indent
    inner = "  " * (indent + 1)
    if isinstance(value, dict):
        if not value:
            return "{}"
        parts = []
        for k, v in value.items():
            key = k if IDENT.match(k) else ts_str(k)
            parts.append(f"{inner}{key}: {ts(v, indent + 1)}")
        return "{\n" + ",\n".join(parts) + f",\n{pad}}}"
    if isinstance(value, list):
        if not value:
            return "[]"
        if all(not isinstance(v, (dict, list)) for v in value):
            return "[" + ", ".join(ts(v, indent) for v in value) + "]"
        parts = [f"{inner}{ts(v, indent + 1)}" for v in value]
        return "[\n" + ",\n".join(parts) + f",\n{pad}]"
    return ts_str(value) if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def ts_str(s: str) -> str:
    if "'" in s:
        return json.dumps(s, ensure_ascii=False)
    return "'" + s + "'"


def names(values: list[str]) -> str:
    return "[" + ", ".join(ts_str(v) for v in values) + "]"


def build(dash: dict) -> str:
    dims = dash["dimensions"]
    meta = dash["meta"]

    out: list[str] = []
    a = out.append
    a("const SOURCE_TYPES = " + names(dims["source_types"]) + ";")
    a("const REGIONS = " + names(dims["regions"]) + ";")
    a("const SPECIES = " + names(dims["species"]) + ";")
    a("const MATERIAL_FORMS = " + names(dims["material_forms"]) + ";")
    a("const RECOVERY_ROUTES = " + names(dims["recovery_routes"]) + ";")
    a("const BATCH_STATUSES = " + names(dims["batch_statuses"]) + ";")
    a("const CURRENT_STAGES = " + names(dims["current_stages"]) + ";")
    a("")
    a("export function mockDimensions(): Dimensions {")
    a("  return {")
    a(f"    period_start: {ts_str(dims['period_start'])},")
    a(f"    period_end: {ts_str(dims['period_end'])},")
    a("    source_types: SOURCE_TYPES,")
    a("    regions: REGIONS,")
    a("    species: SPECIES,")
    a("    material_forms: MATERIAL_FORMS,")
    a("    recovery_routes: RECOVERY_ROUTES,")
    a("    batch_statuses: BATCH_STATUSES,")
    a("    current_stages: CURRENT_STAGES,")
    a("  };")
    a("}")
    a("")
    a("// M0 — the one number every other metric has to explain.")
    a("const NORTH_STAR: NorthStar = " + ts(dash["north_star"]) + ";")
    a("")
    a("const KPIS: Kpi[] = " + ts(dash["kpis"]) + ";")
    a("")
    a("const GUARDRAILS: Guardrail[] = " + ts(dash["guardrails"]) + ";")
    a("")
    a("const CHARTS: Chart[] = " + ts(dash["charts"]) + ";")
    a("")
    a("// Row counts of the bundled sample dataset (`data/workbench.db`).")
    a("const TABLE_COUNTS: Record<string, number> = " + ts(meta["tables"]) + ";")
    a(f"const TOTAL_ROWS = {meta['total_rows']};")
    a("")
    a("export function mockDashboard(): DashboardResponse {")
    a("  return {")
    a("    meta: {")
    a(f"      dataset_type: {ts_str('user_uploaded')},")
    a(f"      currency: {ts_str(meta['currency'])},")
    a(f"      weight_unit: {ts_str(meta['weight_unit'])},")
    a("      empty: false,")
    a("      tables: TABLE_COUNTS,")
    a("      total_rows: TOTAL_ROWS,")
    a("      last_upload: " + ts(meta["last_upload"]) + ",")
    a("    },")
    a("    filters: {},")
    a("    dimensions: mockDimensions(),")
    a("    north_star: NORTH_STAR,")
    a("    kpis: KPIS,")
    a("    guardrails: GUARDRAILS,")
    a("    charts: CHARTS,")
    a("  };")
    a("}")
    a("")
    return "\n".join(out)


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".workbuddy" / "tmp" / "dash.json"
    dash = json.loads(src.read_text(encoding="utf-8"))
    text = MOCK.read_text(encoding="utf-8")

    start = text.index("const SOURCE_TYPES")
    end = text.index("export function mockHealth()")

    imports = (
        "import type {\n"
        "  Chart,\n"
        "  DashboardResponse,\n"
        "  Dimensions,\n"
        "  Guardrail,\n"
        "  Kpi,\n"
        "  NorthStar,\n"
        "  TableSchemaInfo,\n"
        "} from './types';"
    )

    MOCK.write_text(HEADER + "\n" + imports + "\n\n" + build(dash) + text[end:], encoding="utf-8")
    print(f"synced {MOCK.relative_to(ROOT)} from {src}")


if __name__ == "__main__":
    main()
