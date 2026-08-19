// Layer 03 — North Star. The single most important visual metric.
// Value read from overview.json (never hard-coded).

import type { Meta } from '../types/contract';
import { formatAUDPerT, formatAsOf, formatWeight } from '../lib/format';

interface NorthStarCardProps {
  value: number;
  unit: string;
  label: string;
  description: string;
  meta: Meta;
  closedBatchValue?: number;
  processedWeight?: number;
}

export function NorthStarCard({
  value,
  unit,
  label,
  description,
  meta,
  closedBatchValue,
  processedWeight,
}: NorthStarCardProps) {
  return (
    <section className="northstar" aria-labelledby="northstar-title">
      <div className="northstar__topline">
        <span className="northstar__label">{label}</span>
        <span className="chip chip--on-yellow">Period · Jan–Dec {meta.period_start.slice(0, 4)}</span>
      </div>
      <div className="northstar__value" id="northstar-title">
        {formatAUDPerT(value, unit.split('/')[1] ?? 't')}
      </div>
      <p className="northstar__def">{description}</p>
      <dl className="northstar__meta">
        {processedWeight !== undefined && (
          <div className="northstar__meta-row">
            <dt>Processed output</dt>
            <dd>{formatWeight(processedWeight)} t</dd>
          </div>
        )}
        {closedBatchValue !== undefined && (
          <div className="northstar__meta-row">
            <dt>Closed-batch basis</dt>
            <dd>{formatAUDPerT(closedBatchValue)}</dd>
          </div>
        )}
        <div className="northstar__meta-row">
          <dt>Evaluated at</dt>
          <dd>{formatAsOf(meta.as_of)}</dd>
        </div>
      </dl>
    </section>
  );
}
