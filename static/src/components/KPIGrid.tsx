// Layer 04 — six supporting KPIs. Data-driven from overview.json.
// Snapshot-based KPI carries an explicit as_of indicator; no fabricated trends.

import type { Kpi, Meta, OverviewKpis } from '../types/contract';
import { basisLabel, formatAsOf, formatPercent, formatWeightWithUnit, formatAUDPerT } from '../lib/format';

function formatKpiValue(kpi: Kpi): string {
  switch (kpi.unit) {
    case 't':
      return formatWeightWithUnit(kpi.value);
    case '%':
      return formatPercent(kpi.value);
    case 'AUD/t':
      return formatAUDPerT(kpi.value);
    default:
      return String(kpi.value);
  }
}

function KpiCard({ kpi, meta }: { kpi: Kpi; meta: Meta }) {
  const isSnapshot = kpi.basis === 'snapshot';
  return (
    <article className="kpi-card" aria-label={kpi.label}>
      <header className="kpi-card__head">
        <h3 className="kpi-card__label">{kpi.label}</h3>
        <span className={`chip chip--basis ${isSnapshot ? 'chip--snapshot' : ''}`}>
          {basisLabel(kpi.basis)}
          {isSnapshot ? ` · as of ${formatAsOf(meta.as_of)}` : ''}
        </span>
      </header>
      <div className="kpi-card__value">
        {formatKpiValue(kpi)}
      </div>
      <p className="kpi-card__desc" title={kpi.description}>
        {kpi.description}
      </p>
    </article>
  );
}

export function KPIGrid({ kpis, meta }: { kpis: OverviewKpis; meta: Meta }) {
  const ordered: Kpi[] = [
    kpis.incoming_timber,
    kpis.processed_timber,
    kpis.higher_value_recovery_rate,
    kpis.processing_cost_per_processed_t,
    kpis.recovered_value_per_t,
    kpis.unresolved_inspection_rate,
  ];
  return (
    <section className="kpi-grid" aria-label="Key performance indicators">
      {ordered.map((kpi) => (
        <KpiCard key={kpi.id} kpi={kpi} meta={meta} />
      ))}
    </section>
  );
}
