// Chart 06 — Batch Economics (scatter / bubble).
// X: Sorting + Inspection cost/t · Y: Recovered value/t · Size: incoming t.
// Quadrant classification comes from the contract (computed from realised batches
// only). Default view shows realised batches; in-progress points are optional and
// always unclassified (no quadrant).

import { useMemo, useState } from 'react';
import { Cell, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts';
import type { TooltipProps } from 'recharts';
import type { BatchEconomicsRow, EconomicQuadrant } from '../types/contract';
import { formatAUD, formatAUDPerT, formatWeight } from '../lib/format';
import { palette } from '../lib/palette';

const QUADRANT_COLORS: Record<EconomicQuadrant, string> = {
  Efficient: palette.olive,
  'High-value / High-cost': palette.amber,
  Commodity: palette.taupe,
  'Review Required': palette.terracotta,
};

const QUADRANT_ORDER: EconomicQuadrant[] = ['Efficient', 'High-value / High-cost', 'Commodity', 'Review Required'];

function EconTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  const row = payload[0].payload as BatchEconomicsRow;
  const provisional = !row.eligible_for_realised_comparison;
  return (
    <div className="tooltip">
      <div className="tooltip__title">
        {row.batch_id}
        <span className={`tooltip__tag ${provisional ? 'tooltip__tag--provisional' : ''}`}>
          {row.economic_evaluation_status}
        </span>
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
          <dt>Sorting + Inspection</dt>
          <dd>{formatAUDPerT(row.sorting_plus_inspection_cost_per_t)}</dd>
        </div>
        <div>
          <dt>Recovered Value</dt>
          <dd>{formatAUDPerT(row.recovered_value_per_t)}</dd>
        </div>
        <div>
          <dt>Quadrant</dt>
          <dd>{row.economic_quadrant ?? 'In progress — unclassified'}</dd>
        </div>
      </dl>
    </div>
  );
}

export function BatchEconomicsChart({ rows }: { rows: BatchEconomicsRow[] }) {
  const [showProvisional, setShowProvisional] = useState(false);

  const realised = useMemo(() => rows.filter((r) => r.eligible_for_realised_comparison), [rows]);
  const provisional = useMemo(() => rows.filter((r) => !r.eligible_for_realised_comparison), [rows]);

  return (
    <div className="econ-chart">
      <div className="econ-chart__actions">
        <span className="econ-chart__note">Quadrants benchmarked on realised batches only</span>
        <button type="button" className="btn btn--ghost" onClick={() => setShowProvisional((v) => !v)}>
          {showProvisional ? 'Hide in-progress' : `Show in-progress (${provisional.length})`}
        </button>
      </div>
      <ResponsiveContainer width="100%" height={270}>
        <ScatterChart margin={{ top: 10, right: 16, left: 0, bottom: 8 }}>
          <XAxis
            type="number"
            dataKey="sorting_plus_inspection_cost_per_t"
            name="Sorting + Inspection cost/t"
            tickFormatter={(v: number) => formatAUD(v)}
            tick={{ fill: palette.muted, fontSize: 11.5 }}
            axisLine={{ stroke: palette.line }}
            tickLine={false}
            domain={[0, 'auto']}
            unit=""
            label={{
              value: 'Sorting + Inspection Cost / t (AUD/t)',
              position: 'insideBottom',
              offset: -2,
              fill: palette.muted,
              fontSize: 10.5,
            }}
          />
          <YAxis
            type="number"
            dataKey="recovered_value_per_t"
            name="Recovered value/t"
            tickFormatter={(v: number) => formatAUD(v)}
            tick={{ fill: palette.muted, fontSize: 11.5 }}
            axisLine={false}
            tickLine={false}
            domain={[0, 'auto']}
            width={50}
            label={{
              value: 'Recovered Value / t (AUD/t)',
              angle: -90,
              position: 'insideLeft',
              offset: 2,
              fill: palette.muted,
              fontSize: 10.5,
            }}
          />
          <ZAxis type="number" dataKey="incoming_weight_t" name="Incoming weight" range={[60, 520]} />
          <Tooltip content={<EconTooltip />} cursor={{ strokeDasharray: '4 4', stroke: palette.taupe }} />

          {showProvisional && (
            <Scatter data={provisional} fill={palette.taupe} fillOpacity={0.16} stroke={palette.muted} strokeWidth={1.4} strokeDasharray="5 3" />
          )}
          <Scatter data={realised}>
            {realised.map((r) => (
              <Cell
                key={r.batch_id}
                fill={r.economic_quadrant ? QUADRANT_COLORS[r.economic_quadrant] : palette.taupe}
                fillOpacity={0.9}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <ul className="econ-chart__legend">
        {QUADRANT_ORDER.map((q) => (
          <li key={q} className="econ-chart__legend-row">
            <span className="econ-chart__swatch" style={{ background: QUADRANT_COLORS[q] }} />
            {q}
          </li>
        ))}
        <li className="econ-chart__legend-row econ-chart__legend-row--provisional">
          <span className="econ-chart__swatch econ-chart__swatch--hollow" aria-hidden="true" />
          In-progress (no quadrant)
        </li>
      </ul>
    </div>
  );
}
