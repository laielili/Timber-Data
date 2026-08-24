import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts';
import type { Chart } from '../types';
import { useI18n } from '../i18n';

const PALETTE = ['#DFA52A', '#3B2F21', '#5E7D4F', '#B0563B', '#9A8A74', '#C9A079', '#F8B99D', '#FCF551'];

function labelKey(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return 'key';
  for (const k of ['route', 'key', 'month', 'batch_id']) {
    if (k in rows[0]) return k;
  }
  return 'key';
}

function numericKeys(rows: Record<string, unknown>[], exclude: string[] = []): string[] {
  if (rows.length === 0) return [];
  return Object.keys(rows[0]).filter(
    (k) => typeof rows[0][k] === 'number' && !exclude.includes(k),
  );
}

function BarRenderer({ chart }: { chart: Chart }) {
  const rows = chart.rows as Record<string, unknown>[];
  const label = labelKey(rows);
  const exclude = label === 'month' ? [] : [];
  const nums = numericKeys(rows, [label, ...exclude]);
  const showLines = label === 'month';
  const lineKeys = showLines ? nums.filter((k) => k.includes('aud') || k.includes('value')) : [];
  const barKeys = nums.filter((k) => !lineKeys.includes(k));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e8ecf2" />
        <XAxis dataKey={label} tick={{ fontSize: 11 }} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 11 }} width={48} />
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {barKeys.map((k, i) => (
          <Bar key={k} dataKey={k} fill={PALETTE[i % PALETTE.length]} name={k} />
        ))}
        {lineKeys.map((k, i) => (
          <Line
            key={k}
            type="monotone"
            dataKey={k}
            stroke={PALETTE[(barKeys.length + i) % PALETTE.length]}
            strokeWidth={2}
            dot={false}
            name={k}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

function PieRenderer({ chart }: { chart: Chart }) {
  const rows = chart.rows as Record<string, unknown>[];
  const label = labelKey(rows);
  const weightKey = 'weight_t' in (rows[0] ?? {}) ? 'weight_t' : numericKeys(rows, [label])[0];
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={rows}
          dataKey={weightKey}
          nameKey={label}
          innerRadius="45%"
          outerRadius="80%"
          paddingAngle={2}
        >
          {rows.map((_r, i) => (
            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

function ScatterRenderer({ chart }: { chart: Chart }) {
  const { t } = useI18n();
  const rows = chart.rows as Record<string, unknown>[];
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e8ecf2" />
        <XAxis dataKey="cost_per_t" name={t('成本/吨')} tick={{ fontSize: 11 }} />
        <YAxis dataKey="value_per_t" name={t('价值/吨')} tick={{ fontSize: 11 }} width={48} />
        <ZAxis dataKey="incoming_t" range={[40, 320]} name={t('入库(t)')} />
        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
        <Scatter data={rows} fill={PALETTE[0]} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export function ChartCard({ chart }: { chart: Chart }) {
  const { t } = useI18n();
  const body =
    chart.rows.length === 0 ? (
      <div className="chart-empty">{t('该维度下暂无数据')}</div>
    ) : chart.type === 'pie' ? (
      <PieRenderer chart={chart} />
    ) : chart.type === 'scatter' ? (
      <ScatterRenderer chart={chart} />
    ) : (
      <BarRenderer chart={chart} />
    );

  return (
    <div className="chart-card">
      <h3>{t(chart.title)}</h3>
      <div className="chart-card__body">{body}</div>
    </div>
  );
}