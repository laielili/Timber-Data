# BACKEND VALIDATION REPORT — Python Backend Phase 01

> All values are computed from the approved SQLite database
> (`circular_timber_synthetic.db`, seed `20260818`) via the FastAPI analytics service.
> The mock JSON files in `frontend_mock_data/` are regression references only.

Generated: 2026-08-18

---

## Database connection

**PASS** — read-only connection (`mode=ro`, foreign keys on) opens the approved SQLite
database; `GET /health` returns `{"status":"ok","database":"connected","dataset_type":"synthetic_prototype"}`.

## North Star (computed)

| Metric | Value |
|---|---|
| Net Recovery Value / t (selected period 2025) | **85.08 AUD/t** |
| Closed-batch analytical companion | 143.38 AUD/t (completed batches only) |

## Six Overview KPIs (computed)

| KPI | Value | Unit | Basis |
|---|---|---|---|
| Incoming Timber | 1,240.0 | t | selected_period |
| Processed Timber | 1,013.365 | t | selected_period |
| Higher-value Recovery Rate | 39.1 | % | selected_period |
| Processing Cost / processed t | 100.74 | AUD/t | selected_period (corrected denominator) |
| Recovered Value / t | 325.88 | AUD/t | selected_period |
| Unresolved / Inspection Rate | 10.71 | % | snapshot |

## Six chart datasets (row counts)

| Chart | Rows |
|---|---|
| 01 Recovery Route Distribution | 4 (HV 396.25 t/39.1% · Feedstock 513.73/50.7 · Special 79.12/7.81 · Residual 24.26/2.39) |
| 02 Incoming vs Processed | 12 (2025-01..2025-12, arrival vs output month) |
| 03 Operational Backlog | 4 (Sorting 14.48 · Inspection 104.09 · Processing 79.36 · Unresolved 28.7; as_of 2025-12-31) |
| 04 Net Sorting Benefit | 36 (12 negative, incl. B017 -6,172.24 AUD) |
| 05 Cost vs Recovered Value | 12 (Jan net -5,852.52 · Dec net -10,972.40 — negatives visible) |
| 06 Batch Economics | 36 (28 realised w/ quadrant, 8 provisional null) |

## Management brief

**PASS** — deterministic, computed from the DB (no LLM):

| Brief | Severity | Detail |
|---|---|---|
| brief_batch_17 | attention | Sorting + inspection: $229.52/t · realised net sorting benefit: -$6.2k |
| brief_inspection_backlog | attention | 104.09 t open · +21.7% vs November · as of 31 Dec 2025 |
| brief_higher_value | positive | 39.1% of processed output vs 30% prototype target |

Backlog growth is **calculated** from MaterialMonthlyState (104.086 vs 85.545 t →
+21.7%), not hard-coded; the 30% target is read from the Assumptions table.

## Batch regressions

| Check | B017 | B022 | B030 |
|---|---|---|---|
| status | Completed | Completed | Partially Completed |
| economic_evaluation_status | Realised | Realised | Provisional |
| eligible_for_realised_comparison | true | true | false |
| economic_quadrant | Review Required | Efficient | null |
| sorting+inspection / t | 229.52 | 54.54 | 215.41 |
| net sorting benefit | -6,172.24 AUD | +10,974.32 AUD | -10,086.30 AUD (provisional) |
| net recovery value / t | -75.22 | 317.54 | -215.41 (cost incurred to date) |
| regression | **PASS** | **PASS** | **PASS** |

B030 does **not** appear in realised rankings (chart 06 realised set = 28; parity vs
mock confirms per-batch quadrant equality, zero diffs).

## Source performance

**PASS** — two separate layers, never merged:

- Realised (6 source types, completed only): Infrastructure Salvage highest
  realised net/t 274.28; Residential Demolition lowest 20.94.
- Current exposure (5 source types, open only): Direct Salvage Purchase highest
  exposure (open incoming 106.2 t, open inspection 106.2 t, cost-to-date 22,084.43 AUD).
- Per-source values match mock `source_performance.json` within tolerance.

## Contract parity (backend vs frontend_mock_data)

**PASS** — semantic/numeric equivalence for:

| Reference | Status |
|---|---|
| overview.json | PASS |
| management_brief.json | PASS |
| batch_B017.json | PASS |
| batch_B030.json | PASS |
| batch_list.json (36 batches) | PASS |
| source_performance.json | PASS |
| monthly_performance.json (12 rows) | PASS |
| management_report_data.json | PASS |

Documented tolerances: weights/percentages ±0.05, currency ±0.011, `scenario` field
excluded (not persisted in DB — demo-only contract field).

## Pytest

```
31 passed / 0 failed
```

Coverage: 14 core formula tests · API smoke & shapes · no NaN/Infinity · parameterised
period (H1 2025 = incoming 631.2 t, 6 monthly rows) · 404/422 handling · structural
guard proving the backend never reads mock JSON.

## API smoke tests (live uvicorn on 127.0.0.1:8000)

**PASS** — `/health`, `/api/v1/overview`, `/api/v1/management-brief`, `/api/v1/batches`,
`/api/v1/batches/B017`, `/api/v1/batches/B030`, `/api/v1/batches/NOPE` (404),
`/api/v1/source-performance`, `/api/v1/monthly-performance`,
`/api/v1/management-report-data`, `/openapi.json`, `/docs`, `/redoc` all respond 200
(or expected 404/422); no runtime console errors; no NaN/Infinity in any payload.

## Run command

```bash
cd backend
uvicorn app.main:app --reload        # http://localhost:8000/docs
```

## Known limitations (genuine only)

1. `scenario` (demo-only contract field) is not persisted in the DB → returns `null`.
2. Snapshot/backlog uses month-end `MaterialMonthlyState` granularity for the `as_of`
   month (mid-month `as_of` approximates to that month's end state).
3. Batch-level datasets (batch list, charts 04/06) are lifecycle-based (match the
   approved dataset) and unaffected by the period window.
4. Processing backlog 79.36 (backend) vs 79.37 (mock) — sub-cent month-end rounding,
   within documented parity tolerance.
5. CORS allows only the two documented dev origins (localhost:5173 / 127.0.0.1:5173);
   no wildcard default.
