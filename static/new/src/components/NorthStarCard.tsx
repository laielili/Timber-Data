import type { NorthStar } from '../types';
import { fmtMetric } from '../format';
import { MetricTip } from './MetricTip';
import { useI18n } from '../i18n';

/**
 * The North Star — the one number every other metric has to explain.
 *
 * The card is deliberately bare: name and value, nothing else. The identity that
 * used to be spelled out here was removed — the three drivers are already laid
 * out as the groups below, and the hover annotation defines the metric in words.
 * What remains sits beside the guardrail strip, so the anchor and its
 * counterweights are read together.
 */
export function NorthStarCard({ ns }: { ns: NorthStar }) {
  const { t } = useI18n();
  return (
    <section className="north-star has-tip" tabIndex={0}>
      <span className="north-star__eyebrow">{t('北极星')}</span>
      <h2 className="north-star__label">{t(ns.label)}</h2>
      <div className="north-star__value">
        {fmtMetric(ns.value, ns.unit)}
        <span className="north-star__unit">{t(ns.unit)}</span>
      </div>
      <MetricTip basis={ns.basis} description={ns.description} />
    </section>
  );
}
