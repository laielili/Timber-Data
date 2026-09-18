import { useI18n } from '../i18n';

export type TipLevel = 'ok' | 'warn' | 'severe';

interface Props {
  /** Names the tonne denominator — this is what keeps the identity honest. */
  basis: string;
  description: string;
  /** Renders a status badge. Used by the guardrails, whose circle is colour-only. */
  level?: TipLevel;
}

/**
 * Hover/focus annotation for a metric card.
 *
 * Carries a *definition* only: what the metric divides by, and what it means.
 * Deliberately no observed values — the card face already shows the value, and
 * restating it here just adds noise. Also no M-codes: those are design-layer
 * scaffolding (`documents/data/metric_system.md`), not something a reader needs.
 *
 * The optional `level` badge exists because the guardrail ring encodes status by
 * colour alone; the badge gives the same information in words.
 *
 * The card must be `position: relative` — see `.has-tip` in styles.css.
 */
export function MetricTip({ basis, description, level }: Props) {
  const { t } = useI18n();
  return (
    <div className="metric-tip" role="tooltip">
      {level && (
        <p className={`metric-tip__level metric-tip__level--${level}`}>
          {t(level === 'ok' ? '正常' : level === 'warn' ? '预警' : '严重')}
        </p>
      )}
      <p className="metric-tip__basis">
        <span className="metric-tip__key">{t('计算口径')}</span>
        {t(basis)}
      </p>
      <p className="metric-tip__desc">{t(description)}</p>
    </div>
  );
}
