# ANALYST TOOL VALIDATION REPORT — AI Phase 01

> Deterministic analyst tool layer over the approved FastAPI analytics services.
> All values computed from SQLite; no real LLM API is connected in this phase.
> Generated: 2026-08-18

## Tool registry

**12 tools** registered (target 9–12): `get_overview_metrics`, `get_recovery_performance`,
`get_operational_backlog`, `get_batch_details`, `compare_batches`, `get_sorting_economics`,
`get_batch_economics`, `get_source_performance`, `get_uncertainty_distribution`,
`get_monthly_performance`, `get_management_report_data`, `find_batches`.

## Tool list

See `ANALYST_TOOL_CATALOG.md` (purpose / when-to-use / inputs / outputs / metric definitions /
time basis / limitations / examples for every tool) and `ANALYST_TOOL_SCHEMAS.json`
(machine-readable schemas generated from the Pydantic models — 12 entries, provider-neutral).

## Schema validation

**PASS** — all tools have unique names, non-empty descriptions and business questions,
typed input & output Pydantic models; every schema serialises to JSON; invalid inputs
fail validation (`InvalidInput`); no core tool output uses unrestricted `dict[str, Any]`
(typed models only).

## Service parity

**PASS** — tools reuse the same services as the API (no divergent analytics):

| Tool | API reference | Result |
|---|---|---|
| get_overview_metrics | GET /api/v1/overview (North Star + 6 KPIs) | PASS (exact) |
| get_batch_details | GET /api/v1/batches/{B017,B022,B030} | PASS (exact) |
| get_source_performance | GET /api/v1/source-performance | PASS (exact, both layers) |
| get_monthly_performance | GET /api/v1/monthly-performance | PASS (exact) |
| get_management_report_data | GET /api/v1/management-report-data | PASS (exact sections) |
| get_operational_backlog | overview chart 03 | PASS (exact buckets) |
| get_batch_economics | overview chart 06 (quadrants) | PASS (exact per batch) |

## B017

**PASS** — `get_batch_details(batch_id="B017")`: Completed / Realised /
eligible_for_realised_comparison=true / **Review Required** / s+i 229.52 AUD/t /
nsb **-6,172.24** AUD / net/t **-75.22** AUD/t · evidence_status `realised`. No hard-coding.

## B022

**PASS** — Realised / eligible=true / Efficient / net/t 317.54 AUD/t / positive performance.

## B030

**PASS** — Partially Completed / **Provisional** / eligible=false / economic_quadrant=**null** ·
evidence_status `provisional` with note: values are cost/value realised to date, not final.
Any future AI can understand B030 has high current cost exposure but non-final economics.

## Realised / provisional logic

**PASS** — `compare_batches(["B017","B006","B023"])` returns 3 comparable realised
residential-demolition rows; helpers rank realised only (scope note); `compare_batches`
with only provisional batches raises `InsufficientComparableData`. `get_batch_economics`
provisional points always have quadrant null.

## Tool audit logging

**PASS** — every invocation (success and failure) is logged to `cti.analyst_tools` with
event, tool name, input summary, success, duration_ms, result_count, error_type (verified
by test; failure path logs `BatchNotFound`).

## Tests

```
pytest: 63 passed / 0 failed
```

Covers: 12 tool executions · regressions (B017/B022/B030) · compare_batches · schema tests
(unique names / descriptions / JSON serialisation / invalid input rejection) · error types
(BatchNotFound, InvalidPeriod, UnsupportedPrototypeDateRange, InsufficientComparableData,
UnknownTool) · audit logging · provenance on every output · tool↔API parity (7 endpoints).

## No AI API

**Confirmed true** — no OpenAI/Anthropic/Gemini/langchain/llama-index installed; no model
call occurs; the tool layer is provider-neutral (a future adapter may translate the
registry to any provider's tool format).

## Safety boundary

**Confirmed** — tools are read-only; no update/delete/certify tools; no `is_timber_safe`;
no direct SQL / filesystem / shell access exposed to any future model. Development-only
endpoints: `GET /api/v1/dev/analyst-tools` and `POST /api/v1/dev/analyst-tools/{tool}/execute`
(marked development prototype).
