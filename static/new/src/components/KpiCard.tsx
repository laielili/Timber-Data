import type { Kpi } from '../types';
import { useI18n } from '../i18n';

export function KpiCard({ kpi }: { kpi: Kpi }) {
  const { t } = useI18n();
  const formatted = Number.isFinite(kpi.value)
    ? kpi.value.toLocaleString('en-US', { maximumFractionDigits: 2 })
    : '—';
  return (
    <div className="kpi-card" title={t(kpi.description)}>
      <div className="kpi-card__label">{t(kpi.label)}</div>
      <div className="kpi-card__value">
        {formatted}
        {kpi.unit && <span className="kpi-card__unit">{kpi.unit}</span>}
      </div>
      <div className="kpi-card__basis">{t(kpi.basis)}</div>
    </div>
  );
}