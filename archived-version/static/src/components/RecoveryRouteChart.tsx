// Chart 01 — Recovery Route Distribution (donut). Selected period.

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import type { TooltipProps } from 'recharts';
import type { RecoveryRoute, RecoveryRouteRow } from '../types/contract';
import { formatPercent, formatWeight } from '../lib/format';
import { palette } from '../lib/palette';

const ROUTE_COLORS: Record<RecoveryRoute, string> = {
  'Higher-value Recovery': palette.brand,
  'Board Feedstock': '#C9A079',
  'Special Handling': palette.peach,
  'Residual / Disposal': palette.taupe,
};

function RouteTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  const row = payload[0].payload as RecoveryRouteRow;
  return (
    <div className="tooltip">
      <div className="tooltip__title">{row.recovery_route}</div>
      <dl className="tooltip__rows">
        <div>
          <dt>Weight</dt>
          <dd>{formatWeight(row.weight_t)} t</dd>
        </div>
        <div>
          <dt>Share</dt>
          <dd>{formatPercent(row.percentage)}</dd>
        </div>
      </dl>
    </div>
  );
}

export function RecoveryRouteChart({ rows }: { rows: RecoveryRouteRow[] }) {
  const total = rows.reduce((sum, r) => sum + r.weight_t, 0);
  return (
    <div className="route-chart">
      <div className="route-chart__plot">
        <ResponsiveContainer width="100%" height={230}>
          <PieChart>
            <Pie
              data={rows}
              dataKey="weight_t"
              nameKey="recovery_route"
              innerRadius="60%"
              outerRadius="92%"
              paddingAngle={2}
              stroke={palette.panel}
              strokeWidth={2}
            >
              {rows.map((r) => (
                <Cell key={r.recovery_route} fill={ROUTE_COLORS[r.recovery_route]} />
              ))}
            </Pie>
            <Tooltip content={<RouteTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="route-chart__center" aria-hidden="true">
          <span className="route-chart__center-value">{formatWeight(total)}</span>
          <span className="route-chart__center-unit">t processed</span>
        </div>
      </div>
      <ul className="route-chart__legend">
        {rows.map((r) => (
          <li key={r.recovery_route} className="route-chart__legend-row">
            <span className="route-chart__swatch" style={{ background: ROUTE_COLORS[r.recovery_route] }} />
            <span className="route-chart__legend-name">{r.recovery_route}</span>
            <span className="route-chart__legend-w">{formatWeight(r.weight_t)} t</span>
            <span className="route-chart__legend-p">{formatPercent(r.percentage)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
