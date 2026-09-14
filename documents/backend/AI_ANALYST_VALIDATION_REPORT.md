# AI Analyst Validation Report — Circular Timber Intelligence (Phase 02)

Generated: 2026-08-18 · Status: **AI_ANALYST_READY_FOR_REVIEW**

## Provider

- Configured adapter: `OpenAICompatibleProvider` (OpenAI-compatible chat completions).
- Configured via env: `AI_PROVIDER` (default `openai-compatible`), `AI_MODEL`, `AI_API_KEY`,
  `AI_BASE_URL`. Default `AI_BASE_URL = https://api.openai.com/v1`.
- **No API key is present in this environment**, so the live provider was **NOT** exercised.
  The endpoint is correctly disabled (`AI_ENABLED=false`).

## Credentials

- **Absent** in this environment. Never printed, never sent to the frontend.

## Tool registry

- **12 tools** available and registered (verified via `REGISTRY.names()` and the
  provider-adapter conversion test):
  `get_overview_metrics`, `get_recovery_performance`, `get_operational_backlog`,
  `get_batch_details`, `compare_batches`, `get_sorting_economics`,
  `get_batch_economics`, `get_source_performance`, `get_uncertainty_distribution`,
  `get_monthly_performance`, `get_management_report_data`, `find_batches`.

## Offline tests

- **79 passed, 1 skipped (live), 0 failed** (`pytest` over the whole backend, including
  Phase 01/02 tool + endpoint suites).
- AI-specific offline suite (`tests/test_ai_analyst.py`, `tests/test_ai_endpoint.py`):
  tool selection, multi-tool, invalid tool, tool error, max rounds, provider error,
  evidence validator, conversation continuity, B030 provisional reasoning, malformed
  synthesis, request validation, HTTP endpoint (disabled clean error + live-mode
  structured answer via `FakeModelProvider`).

## Tool orchestration

- **PASS** — multi-round tool calling verified (B017 single tool; overview+source
  two-tool; continuity uses compare after a prior B017 detail call). Max-round cap
  raises `MaxToolRoundsExceeded`.

## Structured output

- **PASS** — final answer parsed from model JSON and validated by the Pydantic
  `AnalystResponse` model before delivery. Malformed synthesis raises
  `AIProviderMalformedResponse` (clean error).

## Evidence validation

- **PASS** — unsupported evidence (e.g. a value not present in any executed tool
  output) is dropped and noted in `data_limitation`. Grounded B017 values
  (229.52 / -6172.24 / -75.22 AUD/t, Realised, Review Required) survive.

## B017 test

- **PASS** — `get_batch_details(B017)` is called; answer cites sorting+inspection cost
  229.52 AUD/t, net sorting benefit -6172.24 AUD, net recovery value -75.22 AUD/t,
  status Realised, quadrant Review Required. No unsupported physical causes claimed.

## B030 provisional reasoning

- **PASS** — both B017 and B030 details retrieved; the answer states B030 is
  **Provisional** and must **not** be ranked as a final realised loser; no final
  economic quadrant is assigned to B030 (its `economic_quadrant` is `null`).

## Sorting economics test

- **PASS** — `get_sorting_economics` is the expected tool; answers note that Net
  Sorting Benefit is a prototype all-feedstock counterfactual (not industry-standard
  ROI).

## Backlog test

- **PASS** — `get_operational_backlog` is the expected tool; inspection is the dominant
  stage (104.09 t in the prototype snapshot).

## Multi-tool prioritisation

- **PASS** — for "which three issues to investigate first", the model may call several
  tools (`get_operational_backlog`, `get_sorting_economics`, `get_uncertainty_distribution`);
  the final prioritisation is returned as `suggested_investigation` (interpretation),
  clearly separated from deterministic evidence.

## Frontend real-mode connection

- **PASS** — `VITE_ANALYST_MODE=real` sends free-text questions to
  `POST /api/v1/analyst/query`; `AskCircularDrawer` renders the structured
  `AnalystResponse` (Conclusion / Evidence / Business implication / Suggested
  investigation / Data limitation) plus an Evidence-sources expander and confidence
  badge. The four suggested questions remain as quick-send shortcuts. Enter=send,
  Shift+Enter=newline, send disabled while active, empty submissions blocked.
- Frontend: **11 vitest passed, `tsc --noEmit` clean, `vite build` succeeds**.

## Live model test

- **NOT RUN** — no credentials in this environment. A live test exists
  (`pytest -m live_ai`) and is skipped unless `AI_LIVE_TEST=1` and `AI_API_KEY` are set.
- Implementation status: **implementation ready**. Live provider: **not verified here**.

## Safety boundary

- **PASS** — model can access only the 12 approved read-only tools. No write/certify/
  approve tools exist. Safety questions return prototype uncertainty/inspection/record
  context, never a structural/chemical certification.

## Summary

| Check | Result |
|---|---|
| Provider adapter (real LLM boundary) | PASS |
| API key server-side only | PASS |
| 12 approved tools only | PASS |
| Multi-round orchestration | PASS |
| Evidence grounding | PASS |
| Structured validated response | PASS |
| B017 behaviour | PASS |
| B030 provisional logic | PASS |
| Free-text frontend | PASS |
| Suggested questions retained | PASS |
| Conversation continuity | PASS |
| Dashboard independent if AI fails | PASS |
| Offline tests | 79 passed / 1 skipped / 0 failed |
| Live model test | NOT RUN (no credentials) |
