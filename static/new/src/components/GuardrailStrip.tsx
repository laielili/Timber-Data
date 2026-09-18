import type { Guardrail } from '../types';
import { fmtMetric } from '../format';
import { MetricTip } from './MetricTip';
import { useI18n } from '../i18n';

/**
 * Guardrails are not more KPIs — they are the counterweights that stop the North
 * Star from being inflated. Each one answers "what would this look like if
 * someone gamed the metric above?"
 *
 * The ring is the alert light: green / amber / red, three bands deep. The band
 * numbers live in `dashboard_service.GUARDRAIL_BANDS`, the level is computed
 * server-side, and the thresholds are spelled out in the hover annotation — the
 * ring itself never tries to explain why it is amber.
 */
export function GuardrailStrip({ items }: { items: Guardrail[] }) {
  const { t } = useI18n();
  if (items.length === 0) return null;

  return (
    <section className="guardrails">
      <header className="guardrails__head">
        <span className="guardrails__title">{t('护栏指标 · 防止北极星被做高')}</span>
      </header>
      <div className="guardrails__grid">
        {items.map((g) => (
          <div className={`guardrail guardrail--${g.level} has-tip`} key={g.id} tabIndex={0}>
            <span className="guardrail__light" aria-hidden="true" />
            <span className="guardrail__label">{t(g.label)}</span>
            <span className="guardrail__value">
              {fmtMetric(g.value, g.unit)}
              <span className="guardrail__unit">{t(g.unit)}</span>
            </span>
            <MetricTip basis={g.basis} description={g.description} level={g.level} />
          </div>
        ))}
      </div>
    </section>
  );
}
