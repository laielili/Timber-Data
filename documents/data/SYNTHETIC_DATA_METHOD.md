# SYNTHETIC DATA METHOD — Circular Timber Intelligence (Phase 01)

> **This dataset is designed to test product and analytics behaviour, not to represent actual
> commercial performance or industry benchmarks.**
> Kennedy's Timbers is used only as business context; no real company data is implied.

## 1. Purpose and scope
The generator produces a complete synthetic 12-month dataset (2025-01-01 to 2025-12-31) for a
reclaimed timber recovery operation: 16 source projects, 36 batches (~1,240 t incoming),
~1,200 material records, processing events, inspection events, recovery outputs and a
normalised cost ledger. Everything is derived from raw tables; no metric is hard-coded.

## 2. Random seed and reproducibility
- Seed: **20260818**. Single RNG instance, deterministic call order.
- Running `python3 generate_synthetic_database.py` regenerates the SQLite database, CSVs,
  Excel workbook and all markdown documents identically.

## 3. Synthetic assumptions
All rates and values live in sheet `01_Assumptions` (single source of truth): unit values
(Premium > Character > Rustic > Board Feedstock > Special Handling > Residual), labour/machine
rates, baseline processing cost, and the 30% higher-value recovery prototype target.
Unit values vary per batch within +/-10% so batches are never identical.

## 4. Business scenarios
Eight designed batch behaviours (plus neutral batches):
- **A Strong Performer** (5 batches): moderate cost, strong HV recovery, low unresolved.
- **B Expensive but Valuable** (3): high sorting/inspection cost, high premium yield, positive net sorting benefit.
- **C Poor Sorting Economics** (3, incl. **B017**): heavy sorting + inspection effort, low HV yield, negative net sorting benefit. B017 is an explicit anomaly (sorting hours/t set ~3.3 vs ~1.3 year average) so a future AI brief can say "Batch 17 is generating unusually high sorting costs".
- **D High Uncertainty** (3): salvage purchases with unknown/conflicting records; high inspection requirement and high unresolved weight (batches remain open at snapshot).
- **E High-value Source** (4): infrastructure salvage; strong grades and recovered value / t.
- **F Commodity Source** (5): residential demolition; mostly board feedstock, low cost, stable low value, limited sorting benefit.
- **G Special Handling Heavy** (3): elevated special-handling proportion and cost.
- **H Operational Backlog** (period effect): inspection backlog rises through Q4 (Oct-Nov-Dec), with the December vs November comparison designed near +18%.

## 5. Relationship logic (model-internal, not industry causal law)
- Higher inspection workload -> higher inspection cost.
- Higher sorting labour -> higher sorting cost.
- Higher higher-value output -> higher gross recovered value.
- Higher residual output -> lower recovered value and higher disposal cost.
- Higher special handling -> higher special handling cost.
- Unknown/conflicting treatment info raises inspection probability and unresolved probability —
  it never equals "unsafe". Special handling raises cost — it never equals "hazardous chemical certification".
- Species/grade relationships are synthetic modelling relationships only.

## 6. Cost logic
CostLedger is normalised. Batch Total Recovery Cost = Sorting Labour + Inspection + Processing +
Special Handling + Disposal. Transport and Other are reported separately. Ledger rows trace to
ProcessingEvents labour/machine hours, InspectionEvents labour/external cost, and output route
weights, all multiplied by Assumption rates.

## 7. Value logic
RecoveryOutputs is a ledger: gross_value_aud = weight_t x unit_value_aud_per_t. Unit values come
from Assumptions with +/-10% batch variation, preserving the grade ordering.

## 8. Baseline counterfactual
For each batch: Baseline Net Value = incoming x feedstock value/t - incoming x baseline
processing cost/t (an all-feedstock "no detailed sorting" counterfactual).
Net Sorting Benefit = Actual Net Recovery Value - Baseline Net Value (prototype counterfactual
metric, explicitly not a real financial model). Negative-benefit batches exist by design.

## 9. Anomalies and variation
Batch sizes, material mixes, costs, yields, inspection loads and unresolved levels vary with
business logic: B017 (sorting-cost anomaly), D batches (uncertainty), Q4 backlog (Scenario H),
downgrade-heavy low-quality sources. Batch 17 must remain a clear but not exaggerated outlier.

## 10. Backlog and snapshot model
The dataset snapshot is 2025-12-31 18:00. Materials are in one of five states (Output,
Unresolved, Pending Processing, In Progress) and batches carry a current stage. Month-end backlog
snapshots are computed by the generator from raw processing-event timelines and inspection
opened/closed dates (reproducible; stored in SQLite table `MaterialMonthlyState`, which
`vw_monthly_metrics` joins).

## 11. Limitations
- All values are synthetic prototype assumptions; no market standard is implied.
- No structural safety, chemical safety or certification claims anywhere.
- North Star includes the economic effect of open/backlogged material: it is net commercial recovery
  value generated to date, per incoming tonne in the selected period, not accounting profit.
- Batch-level inspections carry no weight in backlog/KPI-06 union calculations.
- Monthly net recovery value attributes outputs/costs by their event dates; short-period values can be
  volatile because cost and output timing may differ.

## 12. Phase 1.5 — frontend data contract (see FRONTEND_DATA_CONTRACT.md)
- Time semantics are defined in TIME_SEMANTICS.md (selected period / snapshot / comparison period).
- Explicit chart datasets live in workbook sheet 24_ChartData (six named tables).
- `frontend_mock_data/*.json` are generated programmatically from this database; the frontend consumes
  these until the Python backend exists.
- `FRONTEND_DATA_SCHEMA.json` (JSON Schema) and `frontend-data-types.ts` (interfaces only) define the
  contract. No React/FastAPI/LLM code is included.
