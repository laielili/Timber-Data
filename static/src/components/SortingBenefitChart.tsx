// Chart 04 — Net Sorting Benefit by Batch (horizontal bar).
// Default ranking uses REALISED (Completed) batches only — provisional batches are
// never ranked against realised batches. Positive and negative values both shown.

import { useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { TooltipProps } from 'recharts';
import type { NetSortingBenefitRow } from '../types/contract';
import { formatAUD, formatWeight } from '../lib/format';
import { palette } from '../lib/palette';

function BenefitTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  const row = payload[0].payload as NetSortingBenefitRow;
  return (
    <div className="tooltip">
      <div className="tooltip__title">
        {row.batch_id}
        <span className="tooltip__tag">{row.economic_evaluation_status}</span>
      </div>
      <dl className="tooltip__rows">
        <div>
          <dt>Source</dt>
          <dd>{row.source_type}</dd>
        </div>
        <div>
          <dt>Incoming</dt>
          <dd>{formatWeight(row.incoming_weight_t)} t</dd>
        </div>
        <div>
          <dt>Net sorting benefit</dt>
          <dd>{formatAUD(row.net_sorting_benefit_aud)}</dd>
        </div>
        <div>
          <dt>Per tonne</dt>
          <dd>{formatAUD(row.net_sorting_benefit_per_t)}/t</dd>
        </div>
      </dl>
    </div>
  );
}

export function SortingBenefitChart({ rows }: { rows: NetSortingBenefitRow[] }) {
  const [viewAll, setViewAll] = useState(false);

  const realised = rows
    .filter((r) => r.eligible_for_realised_comparison)
    .sort((a, b) => b.net_sorting_benefit_aud - a.net_sorting_benefit_aud);

  const provisionalCount = rows.length - realised.length;
  const positivesTop = realised.filter((r) => r.net_sorting_benefit_aud > 0).slice(0, 5);
  const negativesBottom = realised.filter((r) => r.net_sorting_benefit_aud < 0);
  const negativeCount = negativesBottom.length;
  const bottomShown = negativesBottom.slice(-5);
  const display = viewAll ? realised : [...positivesTop, ...bottomShown];

  return (
    <div className="benefit-chart">
      <div className="benefit-chart__actions">
        <span className="benefit-chart__note">
          {viewAll
            ? `All realised batches shown (${realised.length})`
            : `Realised only · top ${positivesTop.length} positive + ${bottomShown.length} negative of ${negativeCount} · ${provisionalCount} in-progress excluded`}
        </span>
        <button type="button" className="btn btn--ghost" onClick={() => setViewAll((v) => !v)}>
          {viewAll ? 'Show top & bottom' : `View all realised (${realised.length})`}
        </button>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={display} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={palette.line} horizontal={false} />
          <XAxis
            type="number"
            tickFormatter={(v: number) => formatAUD(v)}
            tick={{ fill: palette.muted, fontSize: 11.5 }}
            axisLine={false}
            tickLine={false}
            label={{
              value: 'AUD',
              position: 'insideRight',
              offset: -4,
              fill: palette.muted,
              fontSize: 10.5,
            }}
          />
          <YAxis
            type="category"
            dataKey="batch_id"
            width={54}
            tick={{ fill: palette.ink, fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            interval={0}
          />
          <Tooltip content={<BenefitTooltip />} cursor={{ fill: 'rgba(35,32,26,0.05)' }} />
          <ReferenceLine x={0} stroke={palette.ink} strokeWidth={1.2} />
          <Bar dataKey="net_sorting_benefit_aud" radius={[0, 3, 3, 0]} barSize={17}>
            {display.map((r) => (
              <Cell
                key={r.batch_id}
                fill={r.net_sorting_benefit_aud >= 0 ? palette.olive : palette.terracotta}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
