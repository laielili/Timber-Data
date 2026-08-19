# TIME SEMANTICS — Circular Timber Intelligence

> Purpose: the future frontend must never confuse **selected-period** metrics, **current snapshot**
> metrics, and **comparison-period** metrics. Every number the frontend displays must carry an
> explicit time basis. This document defines the three concepts and their prototype defaults.

---

## A. Selected Period

**Definition.** The time period chosen by the user for flow metrics. It is a *window*, not a moment.

**Prototype defaults.**

```
period_start = 2025-01-01
period_end   = 2025-12-31
```

**Which metrics use it.** Any metric that accumulates flows over the window:

- Incoming Timber (t) — arrivals within the period.
- Processed Timber (t) — recovery outputs dated within the period.
- Higher-value Recovery Rate (%) — HV route weight / processed output weight, within the period.
- Processing Cost / t (AUD/t) — processing cost / incoming t, within the period.
- Recovered Value / t (AUD/t) — gross recovered output value / processed output weight, within the period.
- Net Recovery Value / t (North Star, AUD/t) — (gross value to date − core costs to date) / incoming t in period.
- All monthly charts (Chart 02, Chart 05).

**Rule.** A metric is "selected period" if and only if it aggregates events dated inside
`[period_start, period_end]`.

---

## B. Snapshot

**Definition.** The operational state of the system at one specific moment in time. It answers
"what is open / stuck / queued right now", not "what happened over a window".

**Prototype default.**

```
as_of = 2025-12-31T18:00:00
```

**Which metrics use it.** State metrics evaluated at `as_of`:

- Operational Backlog (t) by stage — Sorting / Inspection / Processing / Unresolved.
- Open Inspection Weight (t) — weight of materials with an open inspection at `as_of`.
- Unresolved Weight (t) — materials still unresolved at `as_of`.
- Open Batch Count — batches not Completed at `as_of`.
- Unresolved / Inspection Rate (%) — (unresolved ∪ open-inspection weight at `as_of`) / incoming t.

**Rules.**
- A material is counted in **exactly one** backlog stage (priority: Unresolved > Inspection > Sorting > Processing), so backlog stages never double-count.
- Unresolved / Inspection Rate uses the **union** (each material counted once), even though a material may simultaneously be unresolved AND under open inspection.
- Snapshot metrics must be labelled with their `as_of` timestamp whenever they are exported or displayed.

---

## C. Comparison Period

**Definition.** A previous, comparable period used to derive trend indicators
(`comparison_value`, `change_absolute`, `change_percent`, `trend`).

**Prototype examples supported by existing 2025 data:**

```
current  = December 2025
previous = November 2025
```

**Constraint.** We do NOT invent 2024 operational records just to create comparison data. Only
comparisons that can be computed from existing 2025 data are supported. Where no supported
comparison exists, the contract returns `null` for comparison fields — never a fabricated number.

**Where it is used.** KPI trend chips, month-over-month backlog growth (Scenario H: December vs
November inspection backlog), and any delta displayed next to a selected-period KPI.

---

## Quick reference

| Metric family | Basis | Identifier in contract |
|---|---|---|
| Incoming / Processed / HV rate / costs / values / North Star | selected period | `basis: "selected_period"` |
| Backlog / open inspection / unresolved / open batches / unresolved-inspection rate | snapshot | `basis: "snapshot"` |
| Trend deltas (Dec vs Nov) | comparison period | `comparison_value`, `change_percent`, `trend` |

---

## D. Realised vs Provisional (economic comparability)

Completion is a second axis that must never be conflated with the three bases above.

- **Realised** (`economic_evaluation_status = "Realised"`, `eligible_for_realised_comparison = true`):
  batches with `batch_status = Completed`. Their economics are final for the period and are the
  only records used in formal comparisons (Net Sorting Benefit ranking, economic quadrant medians).
- **Provisional** (`"Provisional"`, `eligible_for_realised_comparison = false`): any open batch.
  Its current financial values are `cost incurred to date` / `value realised to date`; a negative
  current net value is NOT final poor performance (costs may precede output realisation).
- Rule: realised batches are ranked against realised batches; open batches are shown separately
  (distinct point style / "In Progress" filter) and never move the realised economic benchmark.
