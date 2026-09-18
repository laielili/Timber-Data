import type { Kpi } from '../types';
import { fmtMetric } from '../format';
import { MetricTip } from './MetricTip';
import { Sparkline } from './Sparkline';
import { useI18n } from '../i18n';

/** Sparkline hue per strategy group, matching the group accent bars. */
const TONE: Record<string, string> = {
  s1: '#5e7d4f',
  s2: '#dfa52a',
  s3: '#6c5fa8',
};

export function KpiCard({ kpi }: { kpi: Kpi }) {
  const { t } = useI18n();
  const hasTrend = kpi.trend.filter((v) => Number.isFinite(v)).length > 1;
  return (
    <div className="kpi-card has-tip" tabIndex={0}>
      <div className="kpi-card__main">
        <div className="kpi-card__label">{t(kpi.label)}</div>
        <div className="kpi-card__value">
          {fmtMetric(kpi.value, kpi.unit)}
          {kpi.unit && <span className="kpi-card__unit">{t(kpi.unit)}</span>}
        </div>
      </div>
      {/* snapshot metrics (未决率 / 在途率) carry no series and get no sparkline */}
      {hasTrend && (
        <Sparkline
          values={kpi.trend}
          tone={TONE[kpi.group] ?? '#3b2f21'}
          label={`${t(kpi.label)} · ${t('月度趋势')}`}
        />
      )}
      <MetricTip basis={kpi.basis} description={kpi.description} />
    </div>
  );
}
