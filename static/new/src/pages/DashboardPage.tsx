import { useCallback, useEffect, useState } from 'react';
import { api, describeError } from '../api';
import { ChartCard } from '../components/ChartCard';
import { FilterRail } from '../components/FilterRail';
import { KpiCard } from '../components/KpiCard';
import { useI18n } from '../i18n';
import type { DashboardResponse, Filters } from '../types';

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

  return (
    <div className="dashboard">
      <div className="dashboard__main">
        <header className="page-head">
          <h1>{t('数据看板')}</h1>
          <p className="page-head__sub">
            {empty
              ? t('尚未数据链接——看板会随您的数据实时更新。')
              : `${t('共')} ${data.meta.total_rows.toLocaleString()} ${t('行')} · ${applied ? t('已应用筛选') : t('显示全量数据')}`}
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
            <section className="kpi-grid">
              {data.kpis.map((k) => (
                <KpiCard key={k.id} kpi={k} />
              ))}
            </section>
            <section className="charts-grid">
              {data.charts.map((c) => (
                <ChartCard key={c.id} chart={c} />
              ))}
            </section>
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