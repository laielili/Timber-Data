# Circular Timber Intelligence — Python Backend (Phase 01)

> **All data is synthetic prototype data.** No real company, benchmark or market
> standard is implied. The backend is **read-only** and contains **no AI** for this phase.

## Purpose

Replace the manually exported frontend mock-data generation logic with a real,
deterministic Python analytics backend. The backend is the **single source of truth
for business calculations**; the React frontend performs presentation/formatting only.

Target architecture (frontend integration happens in Backend Phase 02):

```text
SQLite synthetic database
        ↓
Python repository / query layer
        ↓
Python analytics services
        ↓
FastAPI
        ↓
Contract-compatible JSON responses
```

## Architecture

```
backend/
├── app/
│   ├── main.py            FastAPI app, CORS (dev origins), /health
│   ├── config.py          DATABASE_PATH (env override), dataset bounds, core-cost categories
│   ├── db.py              read-only SQLite connection/session (mode=ro, FK on)
│   ├── dependencies.py    DB session + validated time-context FastAPI dependencies
│   ├── models/api.py      Pydantic response models (aligned with FRONTEND_DATA_SCHEMA.json)
│   ├── repositories/      factual grouped-SQL queries (batches, recovery, costs, operations, sources)
│   ├── services/          deterministic analytics (overview, batches, monthly, sources,
│   │                      management_brief, reports, common)
│   └── routers/           HTTP input / validation / typed responses (overview, batches,
│                          performance, reports)
├── tests/                 pytest: core formulas, API smoke, contract parity
├── requirements.txt
└── README_BACKEND.md
```

Responsibilities:

| Layer | Responsibility |
|---|---|
| repositories | factual data questions (no interpretation) |
| services | formulas & deterministic analytics (North Star, KPIs, quadrants, backlog, brief) |
| routers | HTTP input, validation, calling services, typed responses (no SQL-heavy logic) |

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

The database path resolves to `<project-root>/circular_timber_synthetic.db` by default.
Override with the `CTI_DATABASE_PATH` (or `DATABASE_PATH`) environment variable:

```bash
CTI_DATABASE_PATH=/path/to/circular_timber_synthetic.db uvicorn app.main:app --reload
```

## Run

```bash
uvicorn app.main:app --reload          # http://localhost:8000
```

Interactive API docs: http://localhost:8000/docs · ReDoc: http://localhost:8000/redoc

## Database

- Source of truth: `circular_timber_synthetic.db` (approved synthetic dataset, seed `20260818`).
- Access is **read-only** (`?mode=ro`); no POST/PATCH/DELETE business operations exist.
- The backend computes everything from **raw tables** (Batches, Materials,
  RecoveryOutputs, CostLedger, InspectionEvents, ProcessingEvents, Assumptions,
  SourceProjects, MaterialMonthlyState). The approved `vw_*` views were inspected;
  `vw_overview_metrics`/`vw_batch_metrics` already carry the corrected definitions
  (Processing Cost / processed t, realised-only quadrants) but are **fixed-period**,
  so the Python services recompute equivalent logic with parameterised time windows
  and are the authoritative implementation. `MaterialMonthlyState` (month-end material
  states) is reused for snapshot backlog / open-inspection / unresolved weights.
- `scenario` is a generator-memory field **not persisted in the DB**; the contract
  marks it demo-only/optional, so the backend returns `null` for it.

## Analyst tool layer (AI Phase 01)

A deterministic, typed, read-only tool layer (`app/analyst_tools/`) prepares the backend
for a future LLM analyst. **No real AI API is connected.** 12 tools (see
`ANALYST_TOOL_CATALOG.md` and `ANALYST_TOOL_SCHEMAS.json`) call the Python analytics
services directly — never via HTTP to our own FastAPI — and every invocation is
audit-logged. Development-only endpoints:

```text
GET  /api/v1/dev/analyst-tools                     (registered tool metadata + schemas)
POST /api/v1/dev/analyst-tools/{tool_name}/execute  (validated tool execution)
```

Safety boundary: tools are read-only; no SQL / filesystem / shell access is exposed;
no `certify`/`update`/`delete` tools exist. Errors are structured
(`BatchNotFound`, `InvalidPeriod`, `UnsupportedPrototypeDateRange`,
`InsufficientComparableData`, `InvalidInput`) — never stack traces.

## API endpoints

| Method | Path | Summary |
|---|---|---|
| GET | `/health` | service + database health probe |
| GET | `/api/v1/overview` | North Star + 6 KPIs + 6 chart datasets |
| GET | `/api/v1/management-brief` | 3 deterministic attention items |
| GET | `/api/v1/batches` | all 36 `BatchSummary` (+ simple filters) |
| GET | `/api/v1/batches/{batch_id}` | single batch (404 when unknown) |
| GET | `/api/v1/source-performance` | realised performance + current exposure (two layers) |
| GET | `/api/v1/monthly-performance` | 12 typed monthly rows |
| GET | `/api/v1/management-report-data` | deterministic structured report sections |

All business endpoints live under `/api/v1/`. `/health` intentionally has no prefix.

### Time parameters

`overview`, `management-brief`, `source-performance`, `monthly-performance` and
`management-report-data` accept:

```text
period_start=2025-01-01   (default)
period_end=2025-12-31     (default)
as_of=2025-12-31T18:00:00 (default)
```

Validation (HTTP 422 with a message): `period_start <= period_end`; the range must lie
inside the supported dataset (2025-01-01..2025-12-31); `as_of` must be a valid ISO
datetime at or before the dataset snapshot. Dates outside the dataset are rejected
explicitly — never silently clamped.

## Time semantics (TIME_SEMANTICS.md)

- **Selected period** (default 2025-01-01..2025-12-31): Incoming/Processed Timber,
  HV rate, Processing Cost / processed t, Recovered Value / t, North Star, monthly
  performance, recovery routes, cost-vs-value, realised batch economics.
- **Snapshot** (default 2025-12-31T18:00:00): operational backlog, open-inspection
  weight, unresolved weight, open batch count, Unresolved/Inspection rate. Backlog is
  resolved to the month-end `MaterialMonthlyState` of the `as_of` month (documented
  month-end granularity).
- **Comparison period**: only December vs November 2025 (supported by the dataset);
  no 2024 records are fabricated.

## Metric responsibilities (backend owns all of these)

Net Recovery Value(/t) · Higher-value Recovery Rate · Processing Cost / processed t ·
Total Recovery Cost / incoming t · Recovered Value / t · Unresolved/Inspection Rate ·
Net Sorting Benefit · Economic Quadrants (medians from **realised batches only**) ·
Backlog · Comparison calculations · Management Brief evidence · Source performance ·
Realised/Provisional classification. The frontend does none of these.

## Testing

```bash
cd backend
python -m pytest tests -q
```

- `test_core_metrics.py` — 14 core formulas (1240 t incoming, 1013.365 t processed,
  39.1% HV, 85.08 AUD/t North Star, ~100.7 AUD/processed t, route sums, backlog no
  double-count, B017/B030 regressions, brief growth computed, 404/422 handling).
- `test_api.py` — API smoke + shapes + no NaN/Infinity + parameterised period.
- `test_contract_parity.py` — semantic/numeric parity of backend responses vs
  `frontend_mock_data/*.json` (regression reference only; the backend reads SQLite,
  never the mock JSON — enforced by a structural guard test).

## Known limitations

- `scenario` is not persisted in the DB (demo-only contract field) → `null`.
- Snapshot metrics use month-end `MaterialMonthlyState` granularity for the `as_of`
  month; mid-month `as_of` values approximate to that month's end state.
- Batch-level datasets (batch list, chart 04, chart 06) are lifecycle-based and
  unaffected by the period window — matching the approved dataset.
- The synthetic model internally treats a lower grade index as the "downgrade"
  direction for `downgrade_rate`; the backend replicates the approved generator's
  exact condition.
- Processing backlog 79.36 t (backend) vs 79.37 t (mock) differs by sub-cent rounding
  at month-end state granularity (tolerance-covered in parity tests).
- No auth / deployment / cloud / AI in this phase.
