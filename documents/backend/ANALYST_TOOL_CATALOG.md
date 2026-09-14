# ANALYST TOOL CATALOG — Circular Timber Intelligence (AI Phase 01)

> Deterministic, typed, read-only analytical tools the future LLM analyst will be allowed
> to call. Every value comes from the approved Python analytics services (SQLite is the
> source of truth). **No real AI API is connected in this phase.** The tool layer is
> provider-neutral (no OpenAI/Anthropic/Gemini-specific formats).
>
> Machine-readable schemas: `ANALYST_TOOL_SCHEMAS.json` (generated from the Pydantic models).

---

## Tool 01 — get_overview_metrics

- **Purpose:** Current overall management picture.
- **When to use:** overall health, North Star, six executive KPIs, totals, prototype target.
- **Inputs:** `period_start?`, `period_end?`, `as_of?`
- **Outputs:** `north_star` (value/unit/basis/closed-batch companion), `kpis` (6), `totals`
  (cost/gross/net), `prototype_target` (from Assumptions), `time_basis`, `provenance`.
- **Metric definitions used:** Net Recovery Value/t, six Overview KPIs (services/overview).
- **Time basis:** selected period (default 2025-01-01..2025-12-31); snapshot for the
  Unresolved/Inspection rate.
- **Limitations:** North Star is a prototype management metric, not accounting profit.
- **Example input:** `{}` · **Example output summary:** north_star 85.08 AUD/t; totals
  gross 330,235.59 / cost 224,734.19 / net 105,501.40 AUD; target 30%.

## Tool 02 — get_recovery_performance

- **Purpose:** How reclaimed timber recovery is performing.
- **When to use:** route distribution, recovery rates, downgrade, monthly recovery trends.
- **Inputs:** `period_start?`, `period_end?`
- **Outputs:** `processed_weight_t`, `routes` (4 weights), `rates` (5), `monthly_recovery_performance` (12).
- **Metric definitions used:** route weights/percentages, weighted downgrade rate (services/overview, services/common.downgrade_rate, services/monthly).
- **Time basis:** selected period.
- **Limitations:** rates are prototype model relationships, not industry benchmarks.
- **Example output summary:** processed 1,013.365 t; HV 39.1% / feedstock 50.7% / special 7.8% / residual 2.4%; downgrade 7.7%.

## Tool 03 — get_operational_backlog

- **Purpose:** Where material is currently stuck.
- **When to use:** backlog by stage, total open weight, open batch count, month-over-month change.
- **Inputs:** `as_of?`
- **Outputs:** `buckets` (4 mutually exclusive), `total_open_weight_t`, `open_batch_count`,
  `comparison` (previous snapshot + change_absolute + change_percent, only when the dataset supports it).
- **Metric definitions used:** MaterialMonthlyState (month-end states), TIME_SEMANTICS priority
  (Unresolved > Inspection > Sorting > Processing).
- **Time basis:** snapshot (as_of month).
- **Limitations:** month-end granularity; comparisons only for real month pairs (e.g. Dec vs Nov).
- **Example output summary:** inspection 104.09 t (+21.7% vs Nov), processing 79.36, sorting 14.48, unresolved 28.7; open weight 226.63 t; 8 open batches.

## Tool 04 — get_batch_details

- **Purpose:** What is happening with a specific batch.
- **When to use:** one batch's status, recovery, cost, value, uncertainty, quadrant, realised/provisional.
- **Inputs:** `batch_id` (required).
- **Outputs:** full approved `BatchSummary` + `evidence_status` (`realised`/`provisional`) + `economics_note`.
- **Metric definitions used:** batch metrics service (all lifecycle).
- **Time basis:** lifecycle (per batch).
- **Limitations:** provisional economics are cost/value realised to date — not final.
- **Example:** `{"batch_id": "B017"}` → Completed / Realised / Review Required / s+i 229.52 AUD/t /
  nsb -6,172.24 AUD / net/t -75.22 AUD/t, evidence_status `realised`.
- **Errors:** BatchNotFound.

## Tool 05 — compare_batches

- **Purpose:** Compare two or more batches.
- **When to use:** side-by-side batch comparison; ranking realised economics.
- **Inputs:** `batch_ids` (2–10).
- **Outputs:** comparison `rows` (13 fields), deterministic `helpers` (highest/lowest
  recovered value/t, highest/lowest s+i cost/t, best/worst realised nsb — realised scope only).
- **Metric definitions used:** BatchSummary-derived rates (aggregation of approved values).
- **Time basis:** lifecycle.
- **Limitations:** only realised batches are ranked as winners/losers; provisional values are
  cost/value to date. No causal claims are generated.
- **Example:** `["B017","B006","B023"]` → B017 highest s+i (229.52) and worst realised nsb (-6,172.24).
- **Errors:** BatchNotFound, InsufficientComparableData (no realised batch in the set).

## Tool 06 — get_sorting_economics

- **Purpose:** Is detailed sorting economically worthwhile?
- **When to use:** positive/negative net sorting benefit counts, totals, cost/t, best/worst batches; optional source filter.
- **Inputs:** `period_start?`, `period_end?`, `source_type?`, `realised_only?` (default true).
- **Outputs:** `results` (realised_batch_count, positive/negative counts, total & average nsb,
  sorting & inspection cost/t), `top_positive_batches`, `top_negative_batches`, `baseline_definition`,
  `metric_limitation`.
- **Metric definitions used:** net sorting benefit (prototype all-feedstock counterfactual from Assumptions).
- **Time basis:** lifecycle (per batch; period params recorded for provenance).
- **Limitations:** `metric_limitation` explicitly states it is a prototype counterfactual, not an
  industry financial standard.
- **Example output summary:** 28 realised, 24 positive / 4 negative, worst B017 -6,172.24 AUD.

## Tool 07 — get_batch_economics

- **Purpose:** Which completed batches are efficient / high-value-high-cost / commodity / review-required.
- **When to use:** quadrant benchmark (realised-only medians) or per-batch quadrant.
- **Inputs:** `period_start?`, `period_end?`, `include_provisional?` (default false).
- **Outputs:** `benchmark` (realised_median_x/y), `batches` (quadrant per batch; provisional = null).
- **Metric definitions used:** services/batches quadrant logic (medians from realised only).
- **Time basis:** lifecycle.
- **Limitations:** provisional batches never classified; medians never hand-assigned.
- **Example output summary:** medians x=61.12, y=306.99; 28 realised points (Efficient 8 / HV-HC 6 / Commodity 6 / RR 8).

## Tool 08 — get_source_performance

- **Purpose:** Which sourcing categories perform best after recovery.
- **When to use:** source-type realised performance or current open exposure.
- **Inputs:** `period_start?`, `period_end?`
- **Outputs:** `realised_source_performance` (6 rows) + `current_operational_exposure` (5 rows) — **never merged**.
- **Metric definitions used:** services/sources two-layer logic.
- **Time basis:** selected period + snapshot for exposure.
- **Limitations:** open exposure is not realised profitability.
- **Example output summary:** Infrastructure Salvage realised net/t 274.28 (highest); Direct Salvage Purchase open exposure 106.2 t inspection, 22,084.43 AUD cost-to-date.

## Tool 09 — get_uncertainty_distribution

- **Purpose:** Where operational uncertainty is concentrated.
- **When to use:** record completeness, unknown/conflicting treatment, open inspections, unresolved, most uncertain batches/sources.
- **Inputs:** `period_start?`, `period_end?`, `as_of?`
- **Outputs:** `record_quality` (3 rates), `treatment` (unknown & conflicting rates), `operational`
  (open-inspection & unresolved rates), `top_uncertainty_batches` (5), `top_uncertainty_sources` (5), `limitation`.
- **Metric definitions used:** material record/treatment weights (repositories), MaterialMonthlyState, batch metrics.
  Source unresolved rate = unresolved weight of source / total incoming of source (all batches).
- **Time basis:** selected period + snapshot (as_of).
- **Limitations:** explicitly — *"Unknown treatment information does not establish structural or chemical unsafety."*
- **Example output summary:** complete 52.9% / partial 30.4% / critical 16.7%; top batch B033; top source Direct Salvage Purchase.

## Tool 10 — get_monthly_performance

- **Purpose:** How performance has changed over time.
- **When to use:** monthly trends of incoming/processed, HV rate, costs, values, backlog.
- **Inputs:** `period_start?`, `period_end?`
- **Outputs:** `months` (12 typed rows incl. `total_recovery_cost_per_incoming_t`).
- **Metric definitions used:** services/monthly.
- **Time basis:** selected period, monthly grain.
- **Limitations:** no AI interpretation; costs/outputs attributed by their event dates.
- **Example output summary:** Dec: processed 10.355 t, inspection backlog 104.09 t, net/t -131.25.

## Tool 11 — get_management_report_data

- **Purpose:** Assemble deterministic evidence for a management report.
- **When to use:** full structured report evidence (8 sections); future AI analyst / report narration.
- **Inputs:** `period_start?`, `period_end?`, `as_of?`
- **Outputs:** `sections` (executive_metrics, recovery_performance, sorting_economics, operations,
  risk_uncertainty, source_performance, outlier_batches, data_limitations).
- **Metric definitions used:** services/reports (reuses all analytics services — no duplicated calculations).
- **Time basis:** selected period + snapshot.
- **Limitations:** structured data only; no natural-language interpretation.
- **Example output summary:** 8 sections identical to `GET /api/v1/management-report-data`.

## Tool 12 — find_batches

- **Purpose:** Filter the batch list deterministically.
- **When to use:** filter by status / source / evaluation status / quadrant / nsb range / unresolved rate.
- **Inputs:** `status?`, `source_type?`, `economic_evaluation_status?`, `economic_quadrant?`,
  `min_net_sorting_benefit?`, `max_net_sorting_benefit?`, `min_unresolved_rate?`
- **Outputs:** `count` + concise `batches` rows.
- **Metric definitions used:** batch metrics service.
- **Time basis:** lifecycle.
- **Limitations:** filter only — not a natural-language search.
- **Example output summary:** `{"economic_quadrant": "Review Required"}` → 8 batches.

---

## Tool metadata contract

Every registered tool carries: `name`, `description`, `business_question`, `input_schema`,
`output_schema`. Descriptions are written for a future LLM to choose the right tool.

## Audit logging

Every invocation (success or failure) is logged via `logging.getLogger("cti.analyst_tools")`
with: timestamp, tool name, input summary, success, duration_ms, result_count, error_type.
No prompts/secrets are logged (the synthetic prototype contains no sensitive commercial data).

## Safety boundary

- Tools are **read-only**; no `update_*`/`delete_*`/`certify_*` tools exist.
- No direct SQL, filesystem write or shell access is exposed to any future model.
- **No `is_timber_safe` / `certify_timber` tool exists** — the system has no evidence for these.
- Errors are structured (`BatchNotFound`, `InvalidPeriod`, `UnsupportedPrototypeDateRange`,
  `InsufficientComparableData`, `InvalidInput`, `UnknownTool`) — never stack traces.
