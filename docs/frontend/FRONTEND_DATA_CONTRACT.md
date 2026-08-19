# FRONTEND DATA CONTRACT — Circular Timber Intelligence

> Technology-neutral interface between the future frontend and the future Python backend.
> It defines WHAT the frontend receives, not HOW FastAPI will eventually implement it.
> All data is **synthetic prototype** data. No visual styling is part of this contract.

---

## 1. OverviewResponse

The dashboard Overview screen receives exactly one response object:

```json
{
  "meta": {
    "dataset_type": "synthetic_prototype",
    "currency": "AUD",
    "weight_unit": "t",
    "period_start": "2025-01-01",
    "period_end": "2025-12-31",
    "as_of": "2025-12-31T18:00:00",
    "prototype": true
  },
  "north_star": { "...": "KPI object (Part 8)" },
  "kpis": {
    "incoming_timber": {},
    "processed_timber": {},
    "higher_value_recovery_rate": {},
    "processing_cost_per_processed_t": {},
    "recovered_value_per_t": {},
    "unresolved_inspection_rate": {}
  },
  "charts": {
    "recovery_route_distribution": [],
    "incoming_vs_processed": [],
    "operational_backlog": [],
    "net_sorting_benefit": [],
    "cost_vs_recovered_value": [],
    "batch_economics": []
  }
}
```

## 2. KPI object standard

Every KPI uses one consistent shape:

```json
{
  "id": "processing_cost_per_processed_t",
  "label": "Processing Cost / t",
  "value": 100.74,
  "unit": "AUD/t",
  "basis": "selected_period",
  "status": "neutral",
  "description": "Direct processing cost per tonne of timber processed (denominator = processed output weight, not incoming).",
  "prototype": true,
  "comparison_value": null,
  "change_absolute": null,
  "change_percent": null,
  "trend": null
}
```

Rules:
- `basis` is one of `selected_period` | `snapshot` | `comparison_period` (see TIME_SEMANTICS.md).
- `status` is a simple deterministic label (`positive` / `negative` / `neutral`), not a design token.
- Comparison fields are `null` when no supported comparison exists. Never fabricate comparison data.
- `value` and all numbers are JSON numbers; NaN / Infinity are forbidden.

## 3. Chart object standards

For every chart the contract fixes: chart id, business question, time basis, dimensions, measures,
units, field definitions and empty-state behaviour. Visual styling (colours, line widths, card
sizes) is deliberately absent.

### Chart 01 — recovery_route_distribution
| Item | Value |
|---|---|
| chart id | `recovery_route_distribution` |
| business question | Where did recovered weight go? |
| time basis | selected_period |
| dimensions | recovery_route (4 fixed routes) |
| measures | weight_t, percentage |
| units | t, % |
| fields | recovery_route: string; weight_t: number; percentage: number (0-100) |
| empty-state | empty `[]`; frontend renders "no output in period" |

### Chart 02 — incoming_vs_processed
| Item | Value |
|---|---|
| chart id | `incoming_vs_processed` |
| business question | Is processing capacity trailing incoming volume? |
| time basis | selected_period (monthly grain) |
| dimensions | month (2025-01..2025-12) |
| measures | incoming_timber_t, processed_timber_t |
| units | t |
| empty-state | empty `[]`; frontend renders empty time axis |

### Chart 03 — operational_backlog
| Item | Value |
|---|---|
| chart id | `operational_backlog` |
| business question | Where is the current backlog? |
| time basis | snapshot (`as_of`) |
| dimensions | backlog_stage (Sorting / Inspection / Processing / Unresolved; mutually exclusive) |
| measures | weight_t, percentage_of_open_weight, as_of_date |
| units | t, %, date |
| empty-state | four rows with weight_t = 0 when nothing is open |

### Chart 04 — net_sorting_benefit
| Item | Value |
|---|---|
| chart id | `net_sorting_benefit` |
| business question | Which batches justify detailed sorting? |
| time basis | selected_period (per batch) |
| dimensions | batch_id (all 36) |
| measures | source_type, incoming_weight_t, net_sorting_benefit_aud, net_sorting_benefit_per_t, economic_evaluation_status, eligible_for_realised_comparison |
| units | AUD, AUD/t |
| ordering | net_sorting_benefit_aud DESC (formal ranking defaults to eligible_for_realised_comparison = true; open batches remain available separately) |
| empty-state | empty `[]` |

### Chart 05 — cost_vs_recovered_value
| Item | Value |
|---|---|
| chart id | `cost_vs_recovered_value` |
| business question | Do months with higher cost deliver higher value? |
| time basis | selected_period (monthly grain) |
| dimensions | month |
| measures | total_recovery_cost_aud, gross_recovered_value_aud, net_recovery_value_aud |
| units | AUD |
| rule | negative net months are NOT hidden |
| empty-state | empty `[]` |

### Chart 06 — batch_economics
| Item | Value |
|---|---|
| chart id | `batch_economics` |
| business question | Which batches are efficient vs review-required? |
| time basis | selected_period (per batch) |
| dimensions | batch_id, source_type, scenario |
| measures | sorting_plus_inspection_cost_per_t (X), recovered_value_per_t (Y), incoming_weight_t (size), economic_quadrant, economic_evaluation_status, eligible_for_realised_comparison |
| units | AUD/t, t |
| rule | quadrant medians computed from REALISED (Completed) batches only; open batches get economic_quadrant = null until completion; quadrants never hand-assigned |
| empty-state | empty `[]` |

## 4. BatchSummary

Enough to investigate an outlier without reading raw Materials:

```text
batch_id, source_id, source_type, arrival_date, status,
incoming_weight_t, processed_weight_t,
higher_value_weight_t, board_feedstock_weight_t, special_handling_weight_t,
residual_weight_t, unresolved_weight_t,
higher_value_recovery_rate,
sorting_cost_aud, inspection_cost_aud, processing_cost_aud, total_recovery_cost_aud,
gross_recovered_value_aud, net_recovery_value_aud, net_recovery_value_per_t,
sorting_plus_inspection_cost_per_t, net_sorting_benefit_aud,
inspection_rate, unresolved_rate, downgrade_rate,
economic_evaluation_status,   // "Realised" | "Provisional"
eligible_for_realised_comparison,  // true only when Completed
economic_quadrant,          // null while Provisional
inspection_exposure_rate,   // share of incoming material with inspection activity during the batch lifecycle; NOT "currently under inspection"
scenario, notes             // prototype demonstration only
```

Rules:
- `economic_evaluation_status = "Realised"` iff `status = Completed`; otherwise `"Provisional"`.
- `eligible_for_realised_comparison = true` only for Realised batches.
- Provisional batches' current values are `cost incurred to date` / `value realised to date` — never treated as final poor performance.
- `inspection_exposure_rate` is a lifecycle exposure share; current inspection state is a snapshot metric (`open_inspection_weight_t`), kept separate.

## 5. SourcePerformance — two layers (never combined into one profitability conclusion)

A. **Realised Source Performance** (Completed batches only):

```text
source_type, completed_batch_count, completed_incoming_weight_t,
realised_higher_value_recovery_rate, realised_processing_cost_per_processed_t,
realised_total_recovery_cost_per_incoming_t, realised_recovered_value_per_t,
realised_net_recovery_value_per_t, realised_net_sorting_benefit_aud
```

Answers: "Historically, when batches from this source type have completed recovery, how have they performed?"

B. **Current Operational Exposure** (non-completed batches only):

```text
source_type, open_batch_count, open_incoming_weight_t, open_processed_weight_t,
open_unresolved_weight_t, open_inspection_weight_t,
cost_incurred_to_date_aud, value_realised_to_date_aud
```

Answers: "How much unfinished material and cost exposure currently exists from this source type?"

## 5b. SingleBatch

Single-batch responses (e.g. `batch_B017.json`) use:

```json
{ "meta": { "...": "Meta" }, "batch": { "...": "BatchSummary" } }
```

## 6. ManagementReportData (static report; no AI)

Sections (numeric / structured data only):

```text
executive_metrics, recovery_performance, sorting_economics,
operations, risk_uncertainty, source_performance, outlier_batches, data_limitations
```

No natural-language AI interpretation is part of this contract yet.

## 6b. Realised vs Provisional economic comparability

- Realised (Completed) and Provisional (open) batches are NOT economically comparable.
- An incomplete batch can carry incurred costs while recovered value is not yet realised; a
  negative current net value for a Provisional batch does NOT mean poor realised economics.
- Formal comparisons (Net Sorting Benefit ranking, economic quadrant medians) use realised
  batches only, by default.
- Provisional records remain fully available to the frontend with
  `economic_evaluation_status = "Provisional"` — the frontend may show them separately, use a
  different point style, exclude them from formal ranking, or expose an "In Progress" filter.

## 7. Time basis contract

Every response object carries `meta.period_start`, `meta.period_end` and `meta.as_of`.
Every KPI carries `basis`. See TIME_SEMANTICS.md.

## 8. Non-negotiable rules

- All data marked `prototype: true` / `dataset_type: synthetic_prototype`.
- No NaN, Infinity or invalid nulls in any JSON payload.
- All units explicit; all time bases explicit.
- Comparison values are never fabricated; unsupported comparisons are `null`.
