import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
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
import { fmtByFormat } from '../format';
import { useI18n } from '../i18n';

const PALETTE = ['#DFA52A', '#3B2F21', '#5E7D4F', '#B0563B', '#9A8A74', '#C9A079', '#F8B99D', '#FCF551'];

const LABEL_KEYS = ['route', 'category', 'grade', 'state', 'key', 'month', 'batch_id'];

function labelKey(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return 'key';
  for (const k of LABEL_KEYS) {
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

/** Translate the data-carrying label column so the zh view reads as one language. */
function withTranslatedLabel(
  rows: Record<string, unknown>[],
  label: string,
  td: (s: string) => string,
): Record<string, unknown>[] {
  return rows.map((r) => ({ ...r, [label]: td(String(r[label] ?? '')) }));
}

/**
 * The bar/line renderer. Exported so the North Star trend card can reuse it with
 * a zoomed row window instead of reimplementing the same chart.
 *
 * Layout decisions (rotation, horizontal bars) are always taken from the chart's
 * full row set, never from a zoom window — otherwise scrolling the time axis
 * would flip the chart between layouts.
 */
export function ComposedSeriesChart({
  chart,
  rows: rowsOverride,
}: {
  chart: Chart;
  rows?: Record<string, unknown>[];
}) {
  const { t, td } = useI18n();
  const raw = chart.rows as Record<string, unknown>[];
  const label = labelKey(raw);
  const rows = withTranslatedLabel(rowsOverride ?? raw, label, td);
  // Explicit series when the backend supplies them; otherwise fall back to
  // "every numeric column" — mixing a count with a dollar figure is exactly the
  // mistake this guard prevents.
  const nums = numericKeys(raw, [label]);
  const lineKeys = chart.lines ?? (label === 'month' ? nums.filter((k) => k.includes('aud')) : []);
  const barKeys = chart.bars ?? nums.filter((k) => !lineKeys.includes(k));
  const dual = Boolean(chart.dual_axis && lineKeys.length);
  const name = (k: string) => t(chart.series_labels?.[k] ?? k);

  const maxLabelLen = raw.reduce((m, r) => Math.max(m, String(r[label] ?? '').length), 0);
  // Category labels that are long cannot be read at an angle without being
  // clipped, so those charts flip to horizontal bars with a wide category axis.
  const horizontal = maxLabelLen > 14 && lineKeys.length === 0;
  // Recharts silently drops ticks that do not fit, which on five long cost
  // categories left two bars unlabelled. Short labels just get angled instead.
  const rotate = !horizontal && (maxLabelLen > 12 || (raw.length > 6 && maxLabelLen > 8));

  if (horizontal) {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart layout="vertical" data={rows} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e8ecf2" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey={label} tick={{ fontSize: 11 }} width={128} interval={0} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {barKeys.map((k, i) => (
            <Bar key={k} dataKey={k} fill={PALETTE[i % PALETTE.length]} name={name(k)} />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart
        data={rows}
        margin={{ top: 8, right: dual ? 4 : 12, left: 0, bottom: rotate ? 6 : 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e8ecf2" />
        <XAxis
          dataKey={label}
          tick={{ fontSize: 11 }}
          interval={rotate ? 0 : 'preserveStartEnd'}
          angle={rotate ? -24 : 0}
          textAnchor={rotate ? 'end' : 'middle'}
          height={rotate ? 62 : 30}
        />
        <YAxis yAxisId="left" tick={{ fontSize: 11 }} width={52} />
        {dual && <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} width={56} />}
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {barKeys.map((k, i) => (
          <Bar key={k} yAxisId="left" dataKey={k} fill={PALETTE[i % PALETTE.length]} name={name(k)} />
        ))}
        {lineKeys.map((k, i) => (
          <Line
            key={k}
            yAxisId={dual ? 'right' : 'left'}
            type="monotone"
            dataKey={k}
            stroke={PALETTE[(barKeys.length + i + 2) % PALETTE.length]}
            strokeWidth={2}
            dot={false}
            name={name(k)}
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
}

function PieRenderer({ chart }: { chart: Chart }) {
  const { td } = useI18n();
  const raw = chart.rows as Record<string, unknown>[];
  const label = labelKey(raw);
  const rows = withTranslatedLabel(raw, label, td);
  const weightKey = 'weight_t' in (raw[0] ?? {}) ? 'weight_t' : numericKeys(raw, [label])[0];
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
      <ScatterChart margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e8ecf2" />
        <XAxis
          dataKey="cost_per_incoming_t"
          name={t('成本/入库t')}
          tick={{ fontSize: 11 }}
          minTickGap={28}
        />
        <YAxis
          dataKey="value_per_incoming_t"
          name={t('价值/入库t')}
          tick={{ fontSize: 11 }}
          width={52}
        />
        <ZAxis dataKey="incoming_t" range={[40, 320]} name={t('入库(t)')} />
        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
        <Scatter data={rows} fill={PALETTE[0]} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

/** The reconciliation table: four status rows that must sum back to M0. */
function MatrixRenderer({ chart }: { chart: Chart }) {
  const { t, td } = useI18n();
  const cols = chart.columns ?? [];
  const total = chart.total;

  return (
    <div className="matrix">
      <table className="matrix__table">
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c.key} className={c.type === 'num' ? 'num' : ''}>
                {t(c.label)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {(chart.rows as Record<string, unknown>[]).map((r, i) => (
            <tr key={i} className={String(r.state) === 'Output' ? 'matrix__row--output' : ''}>
              {cols.map((c) => (
                <td key={c.key} className={c.type === 'num' ? 'num' : ''}>
                  {c.type === 'num' ? fmtByFormat(r[c.key], c.format) : td(String(r[c.key] ?? ''))}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
        {total && (
          <tfoot>
            <tr>
              {cols.map((c) => (
                <td key={c.key} className={c.type === 'num' ? 'num' : ''}>
                  {c.key === 'state' ? t('合计') : fmtByFormat(total[c.key], c.format)}
                </td>
              ))}
            </tr>
          </tfoot>
        )}
      </table>
      {chart.note && <p className="matrix__note">{t(chart.note)}</p>}
    </div>
  );
}

export function ChartCard({ chart, wide = false }: { chart: Chart; wide?: boolean }) {
  const { t } = useI18n();
  const body =
    chart.rows.length === 0 ? (
      <div className="chart-empty">{t('该维度下暂无数据')}</div>
    ) : chart.type === 'matrix' ? (
      <MatrixRenderer chart={chart} />
    ) : chart.type === 'pie' ? (
      <PieRenderer chart={chart} />
    ) : chart.type === 'scatter' ? (
      <ScatterRenderer chart={chart} />
    ) : (
      <ComposedSeriesChart chart={chart} />
    );

  const isMatrix = chart.type === 'matrix';

  return (
    <div className={`chart-card${wide ? ' chart-card--wide' : ''}`}>
      <h3>{t(chart.title)}</h3>
      <div className={`chart-card__body${isMatrix ? ' chart-card__body--matrix' : ''}`}>{body}</div>
    </div>
  );
}
