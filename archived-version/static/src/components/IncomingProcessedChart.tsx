// Chart 02 — Incoming vs Processed Timber (two-line, monthly). Selected period.

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { TooltipProps } from 'recharts';
import type { IncomingVsProcessedRow } from '../types/contract';
import { monthLabel, monthShort, formatWeight } from '../lib/format';
import { palette } from '../lib/palette';

function FlowTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="tooltip">
      <div className="tooltip__title">{monthLabel(String(label))}</div>
      <dl className="tooltip__rows">
        {payload.map((entry) => (
          <div key={String(entry.dataKey)}>
            <dt>
              <span className="tooltip__dot" style={{ background: entry.color }} />
              {entry.name}
            </dt>
            <dd>{formatWeight(Number(entry.value))} t</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export function IncomingProcessedChart({ rows }: { rows: IncomingVsProcessedRow[] }) {
  return (
    <ResponsiveContainer width="100%" height={270}>
      <LineChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 4 }}>
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
          tickFormatter={(v: number) => formatWeight(v)}
          tick={{ fill: palette.muted, fontSize: 11.5 }}
          axisLine={false}
          tickLine={false}
          width={44}
          label={{
            value: 't',
            angle: -90,
            position: 'insideLeft',
            offset: 4,
            fill: palette.muted,
            fontSize: 10.5,
          }}
        />
        <Tooltip content={<FlowTooltip />} />
        <Legend
          iconType="plainline"
          iconSize={18}
          wrapperStyle={{ fontSize: 12, color: palette.muted, paddingTop: 6 }}
        />
        <Line
          name="Incoming Timber"
          type="monotone"
          dataKey="incoming_timber_t"
          stroke={palette.amber}
          strokeWidth={2.5}
          dot={false}
          activeDot={{ r: 4.5, strokeWidth: 0 }}
        />
        <Line
          name="Processed Timber"
          type="monotone"
          dataKey="processed_timber_t"
          stroke={palette.darkBrown}
          strokeWidth={2.5}
          dot={false}
          activeDot={{ r: 4.5, strokeWidth: 0 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
