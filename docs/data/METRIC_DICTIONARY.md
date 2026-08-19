# METRIC DICTIONARY — Circular Timber Intelligence (synthetic prototype)

All metrics are **prototype management metrics**, not industry accounting standards.
Units: AUD, t (tonnes), h (hours), %.

## Time basis (see TIME_SEMANTICS.md)
- **Selected period** (prototype `2025-01-01`..`2025-12-31`): flow metrics — Incoming Timber, Processed Timber, Higher-value Recovery Rate, Processing Cost / t, Recovered Value / t, Net Recovery Value / t, monthly charts.
- **Snapshot** (`as_of = 2025-12-31T18:00:00`): state metrics — Operational Backlog, Open Inspection Weight, Unresolved Weight, Open Batch Count, Unresolved / Inspection Rate.
- **Comparison period** (e.g. December vs November 2025): trend indicators. No 2024 records are fabricated; only comparisons supported by existing 2025 data are used.

## 1. North Star Metric
### Net Recovery Value / t

- **Business Question:** Per tonne of timber entering the operation within the selected prototype period: how much net commercial recovery value has been generated to date, after core recovery costs?
- **Formula:** (Gross Recovered Output Value to date − Core Recovery Costs to date) ÷ Incoming Timber in selected period
- **Numerator:** Gross Recovered Output Value to date − Core Recovery Costs to date (Sorting Labour + Inspection + Processing + Special Handling + Disposal)
- **Denominator:** Incoming Timber in the selected period (full-year prototype: all 36 batches, 1,240 t)
- **Unit:** AUD/t
- **Grain:** Selected period (prototype: full year 2025)
- **Known Limitations:** Includes the economic effect of open/backlogged material; it is a prototype operational management metric, not accounting profit; short-period values can be volatile because cost and output timing may differ.
- **Prototype Assumption:** Prototype Management Metric. Full-year value: **85.08 AUD/t**.

### Closed Batch Net Recovery Value / t (optional analytical)

- **Business Question:** For batches already fully recovered: how much net value per incoming tonne was retained?
- **Formula:** Net Recovery Value of completed batches ÷ incoming weight of completed batches
- **Numerator:** Σ(net_recovery_value_aud) for batch_status = Completed
- **Denominator:** Σ(incoming_weight_t) for batch_status = Completed
- **Unit:** AUD/t
- **Grain:** Completed batches only
- **Known Limitations:** Analytical companion only; does NOT replace the North Star; ignores open/backlogged economic effects.
- **Prototype Assumption:** Full-year value: **143.38 AUD/t** (over 981.3 t of completed batches).

## 2. Overview KPIs (6)
### Incoming Timber

- **Business Question:** How much timber entered the system?
- **Formula:** SUM(Batches.incoming_weight_t)
- **Numerator:** Batch incoming weights
- **Denominator:** All batches
- **Unit:** t
- **Grain:** Month / year
- **Known Limitations:** Snapshot of arrivals only.
- **Prototype Assumption:** 1240.0 t.

### Processed Timber

- **Business Question:** How much timber was actually recovered?
- **Formula:** SUM(RecoveryOutputs.weight_t)
- **Numerator:** Recovery output weights
- **Denominator:** All outputs
- **Unit:** t
- **Grain:** Month / year
- **Known Limitations:** Excludes unresolved / backlog weight.
- **Prototype Assumption:** 1013.365 t.

### Higher-value Recovery Rate

- **Business Question:** What share of processed output is higher-value?
- **Formula:** Higher-value recovered output weight ÷ Total processed output weight
- **Numerator:** Higher-value route weight
- **Denominator:** Processed output weight (HV+BF+SH+Residual)
- **Unit:** %
- **Grain:** Batch / month / year
- **Known Limitations:** Depends on grade segmentation; prototype grades only.
- **Prototype Assumption:** 39.1%.

### Processing Cost / Processed t (Overview KPI id: processing_cost_per_processed_t)

- **Business Question:** How much direct processing cost is incurred per tonne actually processed?
- **Formula:** Processing Cost ÷ Processed Timber
- **Numerator:** Processing category cost from CostLedger
- **Denominator:** Processed output weight
- **Unit:** AUD/t
- **Grain:** Selected period (batch / month / year)
- **Known Limitations:** Denominator is processed output weight (not incoming). Do not confuse with Total Recovery Cost / Incoming t.
- **Prototype Assumption:** 100.74 AUD / processed t (database-derived; expected band ~100-101).

### Total Recovery Cost / Incoming t (secondary management metric)

- **Business Question:** What is the full core recovery cost intensity per incoming tonne?
- **Formula:** (Sorting Labour + Inspection + Processing + Special Handling + Disposal) ÷ Incoming Timber
- **Numerator:** Core-5 cost from CostLedger
- **Denominator:** Incoming weight
- **Unit:** AUD / incoming t
- **Grain:** Selected period (batch / month / year)
- **Known Limitations:** A different metric from Processing Cost / Processed t; both are reported and must not be confused.
- **Prototype Assumption:** 181.24 AUD / incoming t.

### Recovered Value / t

- **Business Question:** What gross value is recovered per processed tonne?
- **Formula:** Gross recovered output value ÷ Processed output weight
- **Numerator:** SUM(gross_value_aud)
- **Denominator:** Processed output weight
- **Unit:** AUD/t
- **Grain:** Batch / month / year
- **Known Limitations:** Gross, not net; unresolved weight excluded from denominator.
- **Prototype Assumption:** 325.88 AUD/t.

### Unresolved / Inspection Rate

- **Business Question:** How much material is stuck (unresolved or under open inspection)?
- **Formula:** Weight of materials unresolved OR under open inspection ÷ Incoming weight
- **Numerator:** Union of unresolved materials and materials with open inspection (no double counting)
- **Denominator:** Incoming weight
- **Unit:** %
- **Grain:** Snapshot at 2025-12-31
- **Known Limitations:** Batch-level inspections (material_id null) carry no weight.
- **Prototype Assumption:** 10.71%.

## 2b. Economic evaluation status (Realised vs Provisional)

Every batch is classified: `Realised` (batch_status = Completed, eligible_for_realised_comparison = true) or `Provisional` (open batch, eligible = false).
- Realised batches are the only records used in formal comparisons: Net Sorting Benefit ranking and economic quadrant medians.
- Provisional values are `cost incurred to date` / `value realised to date`; a negative current net value is NOT final poor performance.

## 2c. BatchSummary inspection_exposure_rate

`inspection_exposure_rate` = share of incoming material associated with inspection activity during the batch lifecycle (inspection-flagged material weight / incoming weight). It does NOT mean 'currently under inspection'; current inspection state is a snapshot metric (open_inspection_weight_t), kept separate.

## 3. Chart metrics (6 dashboard charts)
### Recovery Route Distribution

- **Business Question:** Where did recovered weight go?
- **Formula:** Route weight ÷ total output weight
- **Numerator:** Route weights
- **Denominator:** Total output weight
- **Unit:** t, %
- **Grain:** Year
- **Known Limitations:** Unresolved never appears in outputs.
- **Prototype Assumption:** 4 fixed routes.

### Incoming vs Processed Timber

- **Business Question:** Is processing capacity trailing incoming volume?
- **Formula:** Monthly incoming vs processed weight
- **Numerator:** Monthly sums
- **Denominator:** Month
- **Unit:** t
- **Grain:** Month
- **Known Limitations:** Processed lags arrivals by batch turnaround.
- **Prototype Assumption:** 12 months.

### Operational Backlog

- **Business Question:** Where is the current backlog?
- **Formula:** Open weight by bucket (Sorting/Inspection/Processing/Unresolved)
- **Numerator:** Material weights in each bucket at snapshot
- **Denominator:** All open material weight
- **Unit:** t
- **Grain:** Snapshot
- **Known Limitations:** Disjoint buckets; priority unresolved > inspection > sorting > processing.
- **Prototype Assumption:** Material-level state model.

### Net Sorting Benefit by Batch

- **Business Question:** Which batches justify detailed sorting?
- **Formula:** Actual Net Recovery Value − Baseline Net Value
- **Numerator:** Per-batch actual net minus baseline (all-feedstock counterfactual)
- **Denominator:** Per batch
- **Unit:** AUD
- **Grain:** Batch
- **Known Limitations:** Prototype counterfactual metric; not a real financial model.
- **Prototype Assumption:** Baseline: incoming × feedstock value/t − incoming × baseline processing cost/t.

### Cost vs Recovered Value

- **Business Question:** Do months with higher cost deliver higher value?
- **Formula:** Monthly recovery cost vs recovered value
- **Numerator:** Monthly core costs and gross output values
- **Denominator:** Month
- **Unit:** AUD
- **Grain:** Month
- **Known Limitations:** Cost-date vs output-date attribution.
- **Prototype Assumption:** 12 months.

### Batch Economics

- **Business Question:** Which batches are efficient vs review-required?
- **Formula:** Scatter of batches on (Sorting+Inspection cost/t, Recovered value/t); quadrants by medians
- **Numerator:** Per-batch x and y
- **Denominator:** Per batch
- **Unit:** AUD/t
- **Grain:** Batch
- **Known Limitations:** Quadrants computed from dataset medians, never hand-labelled.
- **Prototype Assumption:** Median split.

## 4. Secondary management metrics
### Board Feedstock Rate

- **Business Question:** How much output is board feedstock?
- **Formula:** Board feedstock weight ÷ processed weight
- **Numerator:** BF route weight
- **Denominator:** Processed weight
- **Unit:** %
- **Grain:** Batch/year
- **Known Limitations:** Route taxonomy fixed.
- **Prototype Assumption:** 50.7%.

### Residual Rate

- **Business Question:** How much goes to residual/disposal?
- **Formula:** Residual weight ÷ processed weight
- **Numerator:** Residual route weight
- **Denominator:** Processed weight
- **Unit:** %
- **Grain:** Batch/year
- **Known Limitations:** Includes severely degraded routing.
- **Prototype Assumption:** 2.39%.

### Special Handling Rate

- **Business Question:** How much needs special handling?
- **Formula:** Special handling weight ÷ processed weight
- **Numerator:** SH route weight
- **Denominator:** Processed weight
- **Unit:** %
- **Grain:** Batch/year
- **Known Limitations:** Not a hazardous-chemical certification.
- **Prototype Assumption:** 7.81%.

### Downgrade Rate

- **Business Question:** How much value is lost via downgrades?
- **Formula:** Downgraded output weight ÷ processed weight
- **Numerator:** Output weight with final grade < initial grade
- **Denominator:** Processed weight
- **Unit:** %
- **Grain:** Batch/year
- **Known Limitations:** Prototype grade ordering.
- **Prototype Assumption:** 7.7%.

### Throughput t/day

- **Business Question:** How fast is material flowing?
- **Formula:** Processed t ÷ 365
- **Numerator:** Processed weight
- **Denominator:** 365 days
- **Unit:** t/day
- **Grain:** Year
- **Known Limitations:** Flat annualisation.
- **Prototype Assumption:** 2.78 t/day.

### Average Batch Turnaround

- **Business Question:** How long does a batch take?
- **Formula:** Mean of batch turnaround hours
- **Numerator:** Sum of turnaround hours
- **Denominator:** Batch count
- **Unit:** h
- **Grain:** Batch
- **Known Limitations:** Open batches measured to snapshot.
- **Prototype Assumption:** 589.1 h.

### Median Batch Turnaround

- **Business Question:** Typical batch duration?
- **Formula:** Median of batch turnaround hours
- **Numerator:** -
- **Denominator:** -
- **Unit:** h
- **Grain:** Batch
- **Known Limitations:** Robust to outliers.
- **Prototype Assumption:** 447.0 h.

### Open Batch Count

- **Business Question:** How many batches are open?
- **Formula:** COUNT(batch_status != Completed)
- **Numerator:** -
- **Denominator:** -
- **Unit:** count
- **Grain:** Snapshot
- **Known Limitations:** Partial batches counted.
- **Prototype Assumption:** 8.

### Sorting Cost / t

- **Business Question:** Sorting cost intensity
- **Formula:** Sorting cost ÷ incoming t
- **Numerator:** Sorting Labour cost
- **Denominator:** Incoming weight
- **Unit:** AUD/t
- **Grain:** Batch/month/year
- **Known Limitations:** Labour-rate assumption.
- **Prototype Assumption:** 53.98 AUD/t.

### Inspection Cost / t

- **Business Question:** Inspection cost intensity
- **Formula:** Inspection cost ÷ incoming t
- **Numerator:** Inspection cost
- **Denominator:** Incoming weight
- **Unit:** AUD/t
- **Grain:** Batch/month/year
- **Known Limitations:** Includes external costs.
- **Prototype Assumption:** 38.95 AUD/t.

### Total Recovery Cost / t

- **Business Question:** Full recovery cost intensity
- **Formula:** Core-5 cost ÷ incoming t
- **Numerator:** Core-5 cost
- **Denominator:** Incoming weight
- **Unit:** AUD/t
- **Grain:** Batch/month/year
- **Known Limitations:** Transport excluded.
- **Prototype Assumption:** 181.24 AUD/t.

### Net Sorting Benefit / t

- **Business Question:** Is sorting worth it per tonne?
- **Formula:** Net sorting benefit ÷ incoming t
- **Numerator:** Net sorting benefit
- **Denominator:** Incoming weight
- **Unit:** AUD/t
- **Grain:** Batch/year
- **Known Limitations:** Counterfactual metric.
- **Prototype Assumption:** 30.08 AUD/t.

### Complete Record Rate

- **Business Question:** How complete are records?
- **Formula:** Complete-record weight ÷ incoming
- **Numerator:** Complete-record material weight
- **Denominator:** Incoming weight
- **Unit:** %
- **Grain:** Year
- **Known Limitations:** Weight-based.
- **Prototype Assumption:** 52.9%.

### Partial Record Rate

- **Business Question:** Share of partial records
- **Formula:** Partial-record weight ÷ incoming
- **Numerator:** Partial-record material weight
- **Denominator:** Incoming weight
- **Unit:** %
- **Grain:** Year
- **Known Limitations:** Weight-based.
- **Prototype Assumption:** 30.36%.

### Critical Missing Rate

- **Business Question:** Share with critical missing info
- **Formula:** Critical-missing weight ÷ incoming
- **Numerator:** Critical-missing material weight
- **Denominator:** Incoming weight
- **Unit:** %
- **Grain:** Year
- **Known Limitations:** Weight-based.
- **Prototype Assumption:** 16.74%.

### Open Inspection Rate

- **Business Question:** Share under open inspection
- **Formula:** Open-inspection weight ÷ incoming
- **Numerator:** Open-inspection material weight
- **Denominator:** Incoming weight
- **Unit:** %
- **Grain:** Snapshot
- **Known Limitations:** Overlaps unresolved; KPI 06 uses the union.
- **Prototype Assumption:** 10.71%.

### Unknown Treatment Rate

- **Business Question:** Share with unknown/conflicting treatment info
- **Formula:** Unknown+conflicting weight ÷ incoming
- **Numerator:** Unknown/conflicting treatment weight
- **Denominator:** Incoming weight
- **Unit:** %
- **Grain:** Year
- **Known Limitations:** Management-level only.
- **Prototype Assumption:** 25.63%.

## 5. Economic quadrant definition (CHART 06)

- x = sorting + inspection cost / t; y = recovered value / t.
- Quadrant thresholds: median x = 61.120000000000005 AUD/t, median y = 306.985 AUD/t (computed from the dataset, never hand-assigned).
- Q1 low-cost/high-value: Efficient | Q2 high-cost/high-value: High-value / High-cost | Q3 low-cost/low-value: Commodity | Q4 high-cost/low-value: Review Required.
