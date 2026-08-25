// Chart 05 — Cost vs Recovered Value (grouped bars + net line). Monthly, selected period.
// Negative net-value months (Nov, Dec) are NOT hidden.

import { Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { TooltipProps } from 'recharts';
import type { CostVsRecoveredValueRow } from '../types/contract';
import { formatAUD, monthLabel, monthShort } from '../lib/format';
import { palette } from '../lib/palette';

const compact = (v: number) => formatAUD(v);

function CostValueTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  const row = payload[0].payload as CostVsRecoveredValueRow;
  return (
    <div className="tooltip">
      <div className="tooltip__title">{monthLabel(String(label))}</div>
      <dl className="tooltip__rows">
        <div>
          <dt>Recovery cost</dt>
          <dd>{formatAUD(row.total_recovery_cost_aud)}</dd>
        </div>
        <div>
          <dt>Recovered value</dt>
          <dd>{formatAUD(row.gross_recovered_value_aud)}</dd>
        </div>
        <div className={row.net_recovery_value_aud < 0 ? 'tooltip__neg' : ''}>
          <dt>Net value</dt>
          <dd>{formatAUD(row.net_recovery_value_aud)}</dd>
        </div>
      </dl>
    </div>
  );
}

export function CostValueChart({ rows }: { rows: CostVsRecoveredValueRow[] }) {
  return (
    <ResponsiveContainer width="100%" height={290}>
      <ComposedChart data={rows} margin={{ top: 8, right: 4, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={palette.line} vertical={false} />
        <XAxis
          dataKey="month"
          tickFormatter={monthShort}
          tick={{ fill: palette.muted, fontSize: 11.5 }}
          axisLine={{ stroke: palette.line }}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          yAxisId="left"
          tickFormatter={compact}
          tick={{ fill: palette.muted, fontSize: 11.5 }}
          axisLine={false}
          tickLine={false}
          width={52}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tickFormatter={compact}
          tick={{ fill: palette.muted, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={44}
        />
        <Tooltip content={<CostValueTooltip />} />
        <Legend
          iconType="square"
          iconSize={9}
          wrapperStyle={{ fontSize: 12, color: palette.muted, paddingTop: 6 }}
        />
        <Bar
          yAxisId="left"
          name="Recovery Cost"
          dataKey="total_recovery_cost_aud"
          fill={palette.taupe}
          radius={[2, 2, 0, 0]}
          barSize={14}
        />
        <Bar
          yAxisId="left"
          name="Recovered Value"
          dataKey="gross_recovered_value_aud"
          fill={palette.amber}
          radius={[2, 2, 0, 0]}
          barSize={14}
        />
        <Line
          yAxisId="right"
          name="Net Value"
          type="monotone"
          dataKey="net_recovery_value_aud"
          stroke={palette.darkBrown}
          strokeWidth={2}
          dot={{ r: 2.5, fill: palette.darkBrown, strokeWidth: 0 }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
