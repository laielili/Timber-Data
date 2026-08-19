# DATA CONTRACT VALIDATION — Circular Timber Intelligence (Phase 1.6)

> Validates the frontend data contract and the generated mock JSON against the approved database.

PASS  |  01 every KPI in overview.json matches the database: 6 KPIs compared; mismatches: none
PASS  |  02 North Star matches 85.08 AUD/t within rounding tolerance: north_star=85.08 vs database 85.08
PASS  |  03 six chart datasets are non-empty: empty charts: none
PASS  |  04 recovery route percentages sum to ~100%: SUM(percentage)=100.00%; SUM(weight_t)=1013.36 t (Processed Timber 1013.365 t)
PASS  |  05 monthly chart has exactly 12 months: incoming_vs_processed=12 rows; cost_vs_recovered_value=12 rows
PASS  |  06 operational backlog uses snapshot date: as_of_date={'2025-12-31'}
PASS  |  07 all 36 batches in sorting-benefit and economics datasets: net_sorting_benefit=36; batch_economics=36
PASS  |  08 Batch B017 remains a high-cost anomaly: B017 S+I cost/t=229.52 vs avg 92.89 (ratio 2.5x); quadrant=Review Required
PASS  |  09 negative sorting benefit batches remain represented: 12 negative batches (e.g. B026, B036, B032, B023, B031)
PASS  |  10 no frontend JSON contains NaN / Infinity: files flagged: none
PASS  |  11 all units explicit: Every KPI carries a unit; chart measures documented in FRONTEND_DATA_CONTRACT.md.
PASS  |  12 all time bases explicit: meta carries period_start/period_end/as_of; every KPI carries basis (see TIME_SEMANTICS.md).
PASS  |  13 all data marked synthetic prototype: meta.dataset_type / meta.prototype set on every JSON payload.
PASS  |  14 workbook formula-error scan (no #NAME? / #REF! / #VALUE! / #DIV/0! / #N/A): issues found: none
PASS  |  15 Processing Cost / processed t recalculated from raw database (expected ~100-101): processing_cost_per_processed_t = 100.74 AUD / processed t (database 100.74)
PASS  |  16 demo cases: B017 realised poor sorting economics; B022 strong realised; B030 provisional with quadrant null: B017=Realised/-6172.24/Review Required; B022=Realised/317.54; B030=Provisional/None
PASS  |  17 economic quadrant medians use realised batches only; open batches have quadrant null: median_x=61.120000000000005 (recomputed 61.120000000000005), median_y=306.985 (recomputed 306.985); 28 realised, 8 provisional with null quadrant
PASS  |  18 source performance split into realised vs open exposure layers: realised layers=6, open layers=5
PASS  |  19 all mock JSON validate against FRONTEND_DATA_SCHEMA.json: files with errors: none (8/8 PASS)

## Summary
- 19/19 checks PASS.
