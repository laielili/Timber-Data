// Chart 03 — Operational Backlog (horizontal bar). SNAPSHOT chart.
// Stages are mutually exclusive (TIME_SEMANTICS: priority Unresolved > Inspection > Sorting > Processing).

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { TooltipProps } from 'recharts';
import type { OperationalBacklogRow } from '../types/contract';
import { formatPercent, formatWeight } from '../lib/format';
import { palette } from '../lib/palette';

const STAGE_COLORS: Record<string, string> = {
  Sorting: palette.amber,
  Inspection: palette.peach,
  Processing: '#A9835C',
  Unresolved: palette.taupe,
};

function BacklogTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  const row = payload[0].payload as OperationalBacklogRow;
  return (
    <div className="tooltip">
      <div className="tooltip__title">{row.backlog_stage}</div>
      <dl className="tooltip__rows">
        <div>
          <dt>Open weight</dt>
          <dd>{formatWeight(row.weight_t)} t</dd>
        </div>
        <div>
          <dt>Share of open</dt>
          <dd>{formatPercent(row.percentage_of_open_weight)}</dd>
        </div>
        <div>
          <dt>Snapshot</dt>
          <dd>{row.as_of_date}</dd>
        </div>
      </dl>
    </div>
  );
}

export function OperationalBacklogChart({ rows }: { rows: OperationalBacklogRow[] }) {
  const ordered = [...rows].sort(
    (a, b) =>
      ['Sorting', 'Inspection', 'Processing', 'Unresolved'].indexOf(a.backlog_stage) -
      ['Sorting', 'Inspection', 'Processing', 'Unresolved'].indexOf(b.backlog_stage),
  );
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={ordered} layout="vertical" margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={palette.line} horizontal={false} />
        <XAxis
          type="number"
          tickFormatter={(v: number) => formatWeight(v)}
          tick={{ fill: palette.muted, fontSize: 11.5 }}
          axisLine={false}
          tickLine={false}
          label={{
            value: 't',
            position: 'insideRight',
            offset: -4,
            fill: palette.muted,
            fontSize: 10.5,
          }}
        />
        <YAxis
          type="category"
          dataKey="backlog_stage"
          width={92}
          tick={{ fill: palette.ink, fontSize: 12.5 }}
          axisLine={false}
          tickLine={false}
          interval={0}
        />
        <Tooltip content={<BacklogTooltip />} cursor={{ fill: 'rgba(35,32,26,0.05)' }} />
        <Bar dataKey="weight_t" radius={[0, 4, 4, 0]} barSize={20}>
          {ordered.map((r) => (
            <Cell key={r.backlog_stage} fill={STAGE_COLORS[r.backlog_stage]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
