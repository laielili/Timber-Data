import { useCallback, useEffect, useState } from 'react';
import { api, describeError } from '../api';
import { ChartCard } from '../components/ChartCard';
import { FilterRail } from '../components/FilterRail';
import { GuardrailStrip } from '../components/GuardrailStrip';
import { KpiCard } from '../components/KpiCard';
import { NorthStarCard } from '../components/NorthStarCard';
import { TrendCard } from '../components/TrendCard';
import { useI18n } from '../i18n';
import type { DashboardResponse, Filters } from '../types';

/**
 * The three strategy groups, in identity order: M1 × M3 − M2. Only the plain
 * name is shown — the S-codes and M-code ranges are scaffolding for the design
 * layer (`documents/data/metric_system.md`), not for the panel.
 */
const KPI_GROUPS: { id: string; label: string }[] = [
  { id: 's1', label: '价值端' },
  { id: 's3', label: '转化端' },
  { id: 's2', label: '成本端' },
];

const CHART_SECTIONS: { group: string; title: string; hint: string }[] = [
  { group: 'drivers', title: '驱动分解', hint: '把三个驱动项逐层摊开' },
  { group: 'slices', title: '禀赋与切片', hint: '原料禀赋与批次分布' },
];

export function DashboardPage({ goUpload }: { goUpload: () => void }) {
  const { t } = useI18n();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [applied, setApplied] = useState<Filters>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [demoMsg, setDemoMsg] = useState<string | null>(null);

  const load = useCallback((filters: Filters) => {
    setLoading(true);
    setError(null);
    api
      .dashboard(filters)
      .then((d) => setData(d))
      .catch((e) => setError(describeError(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load(applied);
  }, [load, applied]);

  const handleDemo = async () => {
    setDemoMsg(null);
    try {
      const r = await api.loadDemo();
      setDemoMsg(r.message);
      load(applied);
    } catch (e) {
      setDemoMsg(describeError(e));
    }
  };

  if (!data) {
    return (
      <div className="page-state">
        {error ? (
          <>
            <h2>{t('加载失败')}</h2>
            <p>{error}</p>
            <button className="btn" onClick={() => load(applied)}>{t('重试')}</button>
          </>
        ) : (
          <p>{t('加载中…')}</p>
        )}
      </div>
    );
  }

  const empty = data.meta.empty;
  const activeFilters = Object.values(applied).filter(Boolean).length;
  const matrix = data.charts.filter((c) => c.group === 'matrix');
  // monthly_trend is promoted out of the chart grid to sit beside the North Star
  const trend = data.charts.find((c) => c.id === 'monthly_trend');

  return (
    <div className="dashboard">
      <div className="dashboard__main">
        <header className="page-head">
          <h1>{t('数据看板')}</h1>
          <p className="page-head__sub">
            {empty
              ? t('尚未数据链接——看板会随您的数据实时更新。')
              : `${t('共')} ${data.meta.total_rows.toLocaleString()} ${t('行')} · ${
                  activeFilters > 0 ? t('已应用筛选') : t('显示全量数据')
                }`}
          </p>
          {loading && <span className="loading-hint">{t('更新中…')}</span>}
        </header>

        {empty ? (
          <div className="empty-state">
            <h2>{t('数据集为空')}</h2>
            <p>{t('上传符合 timber schema 的数据后，看板与 AI 将自动读取；也可以先载入示例数据体验完整流程。')}</p>
            <div className="empty-state__actions">
              <button className="btn btn--primary" onClick={goUpload}>{t('去数据链接')}</button>
              <button className="btn" onClick={handleDemo}>{t('载入示例数据')}</button>
            </div>
            {demoMsg && <p className="demo-msg">{demoMsg}</p>}
          </div>
        ) : (
          <>
            {/* Anchor + its own trend, with the counterweights on their own row
                directly underneath. */}
            <div className="top-row">
              {data.north_star && <NorthStarCard ns={data.north_star} />}
              {trend && <TrendCard chart={trend} />}
            </div>

            <GuardrailStrip items={data.guardrails} />

            {KPI_GROUPS.map((group) => {
              const items = data.kpis.filter((k) => k.group === group.id);
              if (items.length === 0) return null;
              return (
                <section className="kpi-group" key={group.id}>
                  <div className="kpi-group__head">
                    <span
                      className={`kpi-group__accent kpi-group__accent--${group.id}`}
                      aria-hidden="true"
                    />
                    <span className="kpi-group__label">{t(group.label)}</span>
                    <span className="kpi-group__goal">{t(items[0].group_label)}</span>
                  </div>
                  <div className="kpi-grid">
                    {items.map((k) => (
                      <KpiCard key={k.id} kpi={k} />
                    ))}
                  </div>
                </section>
              );
            })}

            {matrix.map((c) => (
              <ChartCard key={c.id} chart={c} wide />
            ))}

            {CHART_SECTIONS.map((section) => {
              const items = data.charts.filter(
                (c) => c.group === section.group && c.id !== 'monthly_trend',
              );
              if (items.length === 0) return null;
              return (
                <section className="chart-section" key={section.group}>
                  <div className="chart-section__head">
                    <h2>{t(section.title)}</h2>
                    <span>{t(section.hint)}</span>
                  </div>
                  <div className="charts-grid">
                    {items.map((c) => (
                      <ChartCard key={c.id} chart={c} />
                    ))}
                  </div>
                </section>
              );
            })}
          </>
        )}
      </div>

      <FilterRail
        dimensions={data.dimensions}
        onApply={(f) => setApplied({ ...f })}
        onReset={() => setApplied({})}
      />
    </div>
  );
}
