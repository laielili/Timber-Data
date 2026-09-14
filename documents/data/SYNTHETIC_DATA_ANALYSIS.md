# SYNTHETIC DATA ANALYSIS — descriptive, computed from the dataset

> Pure data analysis. Every conclusion below is traceable to the metrics in sheets 20-24.

## Dataset overview
- 16 source projects; 36 batches; 1252 material records; 207 processing events; 412 inspection events; 164 recovery output rows; 201 cost ledger rows.
- Total incoming 1240.0 t; processed 1013.365 t.

## North Star
- Net Recovery Value / t = **85.08 AUD/t** (gross 330,236 AUD - total recovery cost 224,734 AUD, per incoming t).

## Recovery performance
- Higher-value recovery rate **39.1%** vs 30% prototype target (soft band 32-40%).
- Route distribution: Higher-value Recovery 396.25t (39.1%), Board Feedstock 513.73t (50.7%), Special Handling 79.12t (7.81%), Residual / Disposal 24.26t (2.39%)
- Board feedstock rate 50.7%, residual 2.39%, special handling 7.81%, downgrade 7.7%.

## Sorting economics
- 12 of 36 batches have negative net sorting benefit.
- Total net sorting benefit 37,301 AUD (30.08 AUD/t).
- Batch B017 sorting+inspection cost/t is 229.52 AUD/t vs 92.89 AUD/t year average (anomaly by design).

## Risk & uncertainty
- Unresolved / inspection rate 10.71% (union, no double counting).
- Complete record rate 52.9%, partial 30.36%, critical missing 16.74%, unknown/conflicting treatment 25.63%.

## Operations
- Throughput 2.78 t/day; average turnaround 589.1 h; median 447.0 h; 8 open batches at snapshot.
- December inspection backlog 104.09 t vs November 85.54 t (+21.7%, target ~+18%).

## Cost & value
- Processing cost / processed t 100.74 AUD/t (Overview KPI; denominator = processed output weight); total recovery cost / incoming t 181.24 AUD/t; recovered value/t 325.88 AUD/t; net/t 85.08 AUD/t.

## Source performance
- **Infrastructure Salvage**: HV rate 60.31%, recovered value/t 409.72 AUD/t, cost/t 145.34 AUD/t, net/t 207.33 AUD/t, batches 4.
- **Commercial Demolition**: HV rate 53.67%, recovered value/t 402.62 AUD/t, cost/t 191.03 AUD/t, net/t 131.01 AUD/t, batches 7.
- **Industrial Renewal**: HV rate 43.03%, recovered value/t 346.84 AUD/t, cost/t 160.61 AUD/t, net/t 186.23 AUD/t, batches 6.
- **Direct Salvage Purchase**: HV rate 29.98%, recovered value/t 268.56 AUD/t, cost/t 192.16 AUD/t, net/t -103.89 AUD/t, batches 5.
- **Warehouse Deconstruction**: HV rate 26.26%, recovered value/t 284.77 AUD/t, cost/t 182.82 AUD/t, net/t 63.49 AUD/t, batches 6.
- **Residential Demolition**: HV rate 21.9%, recovered value/t 236.61 AUD/t, cost/t 204.38 AUD/t, net/t 8.55 AUD/t, batches 8.

## Outlier batches
- Best net/t: B022 (317.54 AUD/t).
- Worst sorting economics: B030 (net sorting benefit -10,086 AUD).
- Highest unresolved: B030 (9.758 t).
- Batch 17 anomaly: sorting+inspection cost/t 229.52 AUD/t, net sorting benefit -6,172 AUD.

## Monthly trends
- 2025-01: incoming 108.4 t | processed 35.001 t | HV 32.58% | net -5,853 AUD | inspection backlog 0.0 t
- 2025-02: incoming 103.9 t | processed 114.1 t | HV 27.99% | net 17,806 AUD | inspection backlog 0.0 t
- 2025-03: incoming 90.3 t | processed 133.198 t | HV 35.68% | net 22,133 AUD | inspection backlog 0.0 t
- 2025-04: incoming 102.8 t | processed 58.701 t | HV 59.49% | net 5,801 AUD | inspection backlog 0.0 t
- 2025-05: incoming 111.8 t | processed 138.9 t | HV 39.7% | net 30,910 AUD | inspection backlog 0.0 t
- 2025-06: incoming 114.0 t | processed 76.801 t | HV 47.03% | net 2,215 AUD | inspection backlog 0.0 t
- 2025-07: incoming 113.0 t | processed 138.899 t | HV 32.31% | net 20,330 AUD | inspection backlog 0.0 t
- 2025-08: incoming 105.0 t | processed 90.4 t | HV 63.4% | net 17,835 AUD | inspection backlog 0.0 t
- 2025-09: incoming 99.4 t | processed 100.501 t | HV 44.72% | net 12,601 AUD | inspection backlog 9.15 t
- 2025-10: incoming 106.1 t | processed 94.8 t | HV 26.98% | net 2,375 AUD | inspection backlog 54.82 t
- 2025-11: incoming 101.7 t | processed 21.709 t | HV 29.84% | net -9,679 AUD | inspection backlog 85.54 t
- 2025-12: incoming 83.6 t | processed 10.355 t | HV 0.0% | net -10,972 AUD | inspection backlog 104.09 t

## Data limitations
- All values synthetic; assumptions documented in 01_Assumptions and METRIC_DICTIONARY.md.
- No safety/certification claims. Backlog snapshots are model states, not physical counts.
- Monthly net value attributes costs/outputs by event date; open-batch costs may precede their outputs.

## Findings (sheet 28)
- **North Star**: Full-year Net Recovery Value / t is 85.08 AUD/t (gross recovered value 330,236 AUD minus total recovery cost 224,734 AUD, over 1240.0 incoming t).
- **Best Performer**: Batch B022 (E) leads the year with net recovery value 317.54 AUD/t (net 13,273 AUD, HV rate 76.5%).
- **Batch 17 Anomaly**: Batch B017 shows unusually high sorting economics pressure: sorting+inspection cost 229.52 AUD/t vs year average 92.89 AUD/t (ratio 2.5x); net sorting benefit -6,172 AUD (negative).
- **Worst Sorting Economics**: Batch B017 has the most negative net sorting benefit (-6,172 AUD); detailed sorting does not pay off here.
- **Negative Sorting Benefit Count**: 12 of 36 batches (33%) have negative net sorting benefit (4 of them are realised/completed: B006, B017, B023, B026); open batches are provisional, not final performance.
- **Inspection Backlog Peak**: Inspection backlog rises through Q4 and peaks in December at 104.09 t (November 85.54 t, +21.7%); concentrated in high-uncertainty salvage purchases.
- **Best Source Type**: 'Infrastructure Salvage' delivers the highest higher-value recovery rate (60.31%) across 4 batches.
- **Weakest Source Type**: 'Residential Demolition' has the lowest higher-value recovery rate (21.9%) and the lowest recovered value / t (236.61 AUD/t).
- **Higher-value Target**: Full-year higher-value recovery rate is 39.1% vs the 30% prototype target (soft band 32-40%) — target maintained by the underlying data, not hard-coded.
- **Unresolved Concentration**: Batch B030 holds the most unresolved weight (9.758 t, 26.16% of its incoming) — a high-uncertainty salvage purchase.
- **Special Handling Economics**: Batch B026 (special-handling heavy) shows the largest special handling weight (13.105 t, 50.4% of processed) with elevated special handling cost (1,048 AUD).
- **Cost vs Value Relationship**: Pearson correlation between sorting+inspection cost/t and recovered value/t is -0.33 — weak/negative: sorting effort does not reliably buy value.
- **Economic Quadrants**: Batch economics scatter splits into {'Commodity': 6, 'Efficient': 8, 'High-value / High-cost': 6, 'Review Required': 8} (realised batches only; medians x=61.120000000000005 AUD/t, y=306.985 AUD/t; 8 open batches have no quadrant until completion).
- **Top Gross Value Batch**: Batch B013 produced the highest gross recovered value (23,642 AUD on 51.9 t).
- **Downgrade Concentration**: Batch B034 has the highest downgrade rate (52.36% of processed weight recovered below its initial assessed grade) — value loss is concentrated in low-completeness / low-quality sources.
- **Throughput**: Throughput 2.78 t/day on 1013.365 processed t across the year; 8 batches remain open at snapshot.