# FULL STACK INTEGRATION REPORT — Backend Phase 02

> React ↔ FastAPI integration. Frontend now consumes the same Executive Overview from
> the FastAPI analytics service (Backend Phase 01) instead of local mock JSON. The
> approved visual interface and data contract are preserved.
>
> **All data is synthetic prototype data.** No AI API is connected. Read-only.

---

## Architecture

```
SQLite (circular_timber_synthetic.db, seed 20260818)
    ↓
Python repositories (grouped SQL, read-only)
    ↓
Python analytics services (North Star, KPIs, quadrants, backlog, brief)
    ↓
FastAPI (uvicorn, http://localhost:8000)
    ↓   GET /api/v1/overview · /management-brief · /batches · /batches/{id}
    ↓   /source-performance · /monthly-performance · /management-report-data
    ↓
ApiDashboardDataSource  (implements DashboardDataSource, replaces Mock)
    ↓
useDashboardData() → typed DashboardData
    ↓
React Executive Overview (unchanged)
```

The frontend data layer still exposes one abstraction — `DashboardDataSource` — so
components remain unaware of mock vs api. A small factory picks the source from
`VITE_DATA_SOURCE=api|mock`. No visual component calls `fetch("/api/...")` directly.

## Backend status

**PASS** — Phase 01 frozen: 32/32 pytest (incl. contract parity + mutation test).
`/health` + 8 business endpoints → 200. DB hash `f75c28d5…` byte-identical (read-only).
CORS allows the documented dev origins `http://localhost:5173` and
`http://127.0.0.1:5173`; a request from an unlisted origin surfaces a clear "Unable to
connect to the data service." error and Retry (verified at 5174 during testing).

## Frontend status

**PASS** — visual interface preserved (pixel-level diff vs mock = 0.04 %, sub-rendering
noise only — no card reflow, no colour/typography change, no missing labels). The
contract remains authoritative: `frontend-data-types.ts` is the single source of types;
`apiClient.ts` + `validateContract.ts` add a tiny runtime guard on the critical
responses (Overview / Management Brief / Single Batch).

## API endpoints consumed (verified via browser network capture)

| Endpoint | API-mode network call | Mock-mode network call |
|---|---|---|
| GET /api/v1/overview | observed | **NOT** observed |
| GET /api/v1/management-brief | observed | **NOT** observed |
| GET /api/v1/batches | observed | **NOT** observed |
| GET /api/v1/batches/B017, /B022, /B030 | observed (3) | **NOT** observed |
| GET /api/v1/source-performance | observed | **NOT** observed |
| GET /api/v1/monthly-performance | observed | **NOT** observed |
| GET /api/v1/management-report-data | observed | **NOT** observed |
| GET /data/*.json | **NOT** observed (verified 0 calls) | observed (9 files) |

## Overview metric parity (API vs mock vs approved dataset)

| Metric | Rendered (API) | Rendered (mock) | Approved |
|---|---|---|---|
| Net Recovery Value / t | $85.08/t | $85.08/t | 85.08 |
| Incoming Timber | 1,240 t | 1,240 t | 1,240.0 |
| Processed Timber | 1,013.37 t | 1,013.37 t | 1,013.365 |
| Higher-value Recovery Rate | 39.1% | 39.1% | 39.1 |
| Processing Cost / t | $100.74/t | $100.74/t | 100.74 |
| Recovered Value / t | $325.88/t | $325.88/t | 325.88 |
| Unresolved / Inspection Rate | 10.7% | 10.7% | 10.71 |

## Chart parity (6/6, all backend-driven in API mode)

| Chart | Rows | API-mode | Mock-mode |
|---|---|---|---|
| Cost vs Recovered Value | 12 | observed (Jan -5,852.52, Dec -10,972.40) | identical |
| Recovery Route Distribution | 4 | observed (HV 39.1%, Feedstock 50.7%, Special 7.8%, Residual 2.4%) | identical |
| Batch Economics | 36 | observed (28 realised, 8 provisional null) | identical |
| Net Sorting Benefit by Batch | 36 | observed (B017 -6,172.24 realised, B030 excluded) | identical |
| Incoming vs Processed Timber | 12 | observed | identical |
| Operational Backlog | 4 | observed (Inspection 104.09, Processing 79.36, Sorting 14.48, Unresolved 28.7) | identical |

## B017 regression

- `GET /api/v1/batches/B017` → Completed / Realised / eligible=true / **Review Required** /
  s+i 229.52 / nsb -6,172.24 / net/t -75.22.
- Ask Circular Q1 evidence drawn from API-loaded B017: "Sorting + Inspection
  $229.52/t · Net sorting benefit -$6.2k · Net recovery value -$75.22/t · Status Realised
  · Quadrant Review Required" — no static-fallback values.

## B030 regression

- `GET /api/v1/batches/B030` → Partially Completed / **Provisional** / eligible=**false** /
  economic_quadrant=**null**.
- B030 does **not** appear in chart 06 realised set (28) nor in default Net Sorting
  Benefit slice (B030 excluded assertion PASS).

## Management Brief

Backend-driven (no React business logic). API mode fetches `GET /api/v1/management-brief`
and renders:

| Brief | Severity | Detail (computed by backend) |
|---|---|---|
| brief_batch_17 | attention | Sorting + inspection: $229.52/t · realised net sorting benefit: -$6.2k |
| brief_inspection_backlog | attention | 104.09 t open · +21.7% vs November · as of 31 Dec 2025 |
| brief_higher_value | positive | 39.1% of processed output vs 30% prototype target |

The 30 % prototype target is read from `Assumptions`; the +21.7 % growth is computed
from MaterialMonthlyState (104.086 vs 85.545 t). No React calculation remains.

## Ask Circular

Deterministic Q&A (no LLM). In API mode, every evidence value is derived from
backend-loaded B017 / batchList / monthly / brief data — no static fallback. All 4
questions (B017, negative NSB, backlog, HV) render correct numbers and the
brief-item pre-load / Esc-close / structured 5-block responses all work.

## Temporary database mutation test (Backend Phase 02 Test 08)

| Step | Detail |
|---|---|
| Approved DB hash before | `f75c28d528b0d32ebb34fb7ee9553282166cb76f…` |
| Copy DB to | `<tmp>/mutated.db` |
| `config.DATABASE_PATH` monkeypatched to | `<tmp>/mutated.db` |
| Mutation | `UPDATE RecoveryOutputs SET unit_value_aud_per_t = ROUND(unit_value_aud_per_t*1.1, 2) WHERE batch_id='B022'`, then `UPDATE RecoveryOutputs SET gross_value_aud = ROUND(weight_t * unit_value_aud_per_t, 2) WHERE batch_id='B022'` |
| `B022.gross_recovered_value_aud` before | 14,628.66 (mock + approved, equivalent) |
| `B022.gross_recovered_value_aud` after | 16,091.53 (raised by +1,462.87, +10 %) |
| `recovered_value_per_t` before / after | 325.88 → 327.32 (+1.44) |
| `north_star` before / after | 85.08 → 86.55 (+1.47) |
| Unrelated batch B017 (sanity) | unchanged |
| Approved DB hash after | `f75c28d528b0d32ebb34fb7ee9553282166cb76f…` — **byte-identical** |
| Result | **PASS** |

This proves the pipeline genuinely drives the frontend from SQLite. No manual edits
to API responses or mock JSON.

## Mock mode (regression reference only)

- `VITE_DATA_SOURCE=mock` → MockDashboardDataSource active → only `/data/*.json` fetched,
  no `/api/v1/*` calls (verified). 20/20 E2E checks PASS in mock mode.
- Mock files kept at `frontend_mock_data/` (do not delete) — used for offline demo
  and the existing playwright `cti_qa.cjs` regression.

## API mode (primary integrated mode)

- `VITE_DATA_SOURCE=api` → ApiDashboardDataSource active. 23/23 E2E checks PASS including
  network-routing assertions (only `/api/v1/*` observed, zero `/data/*.json`).
- "Fail visibly" verified at the unauthorized origin 5174 → "Unable to connect to the
  data service." with Retry (no stack trace to user; technical details in dev console).

## Build

- **Frontend typecheck** (tsc --noEmit): **PASS** (0 error)
- **Frontend production build** (vite build): **PASS** (848 modules)
- **Frontend tests** (vitest run): **11 / 11 PASS** (01-07 + factory + runtime-validation suite)
- **Backend tests** (pytest): **32 / 32 PASS** (14 core + API smoke + contract parity + mutation)
- **Browser E2E (playwright-core + system Chrome)**:
  - API mode: 23/23 PASS · 0 console error · 0 uncaught runtime · 0 React key warning
  - Mock mode: 20/20 PASS · 0 console error
- **Visual regression**: API vs mock desktop pixel-diff = 0.04 % (sub-rendering noise only)

## Local run workflow

Terminal 1 (backend):
```bash
cd /Users/apple/Desktop/木材回收/backend
uvicorn app.main:app --reload        # http://localhost:8000/docs
```

Terminal 2 (frontend, API mode — primary integrated mode):
```bash
cd /Users/apple/Desktop/木材回收/frontend
VITE_DATA_SOURCE=api VITE_API_BASE_URL=http://localhost:8000 npm run dev
# http://localhost:5173
```

Frontend, mock mode (offline demo / regression):
```bash
cd /Users/apple/Desktop/木材回收/frontend
npm run dev
# http://localhost:5173 (mock by default)
```

## Frontend files added (Backend Phase 02)

- `frontend/src/data/apiClient.ts` — fetch helper + typed errors + `describeError`
- `frontend/src/data/validateContract.ts` — `assertOverviewResponse` / `assertManagementBriefResponse` / `assertSingleBatchResponse`
- `frontend/src/data/dashboardData.ts` — `ApiDashboardDataSource` + `createDashboardDataSource` factory + `LoadState.error: Error | null`
- `frontend/src/data/dashboardData.test.ts` — vitest integration suite
- `frontend/src/vite-env.d.ts` — `import.meta.env` typing
- `frontend/.env.example` — `VITE_DATA_SOURCE=api` · `VITE_API_BASE_URL=...`
- `frontend/docs/screenshots/desktop_api_mode.png` · `desktop_mock_mode.png` · `ask_circular_api_mode.png` · `tablet_api_mode.png`

## Frontend files modified

- `App.tsx` — `describeError(error)` for friendly message mapping
- `package.json` — scripts.test = "vitest run"; devDeps: `vitest@^2.1.8`, `@types/node`

## Backend files added (Backend Phase 02)

- `backend/tests/test_mutation.py` — temporary DB → API metric propagation; approved DB unchanged

## Known limitations (genuine only)

1. The frontend runs in mock mode by default when no env is set (offline demo). Set
   `VITE_DATA_SOURCE=api` explicitly to switch to the integrated pipeline.
2. CORS is restricted to the two documented dev origins (5173 / 127.0.0.1:5173); any
   other origin surfaces an integration error.
3. `scenario` (demo-only contract field) is `null` in API responses (not persisted in DB).
4. Snapshot/backlog uses month-end MaterialMonthlyState granularity for the `as_of` month.
5. No request cancellation / caching / state management — concurrent `Promise.all` is
   enough for the prototype dataset (32/32 tests PASS).
