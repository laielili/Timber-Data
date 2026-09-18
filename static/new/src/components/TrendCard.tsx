import { useEffect, useMemo, useRef, useState } from 'react';
import type { Chart } from '../types';
import { ComposedSeriesChart } from './ChartCard';
import { useI18n } from '../i18n';

/**
 * Opening window, in months. Defaults to everything the data holds, because this
 * card exists to show a *trend* — opening on a single month renders one bar and
 * no line at all, which is the one thing a trend chart must not do. Ctrl + wheel
 * zooms in to as little as one month and back out again.
 *
 * Set `OPENING_WINDOW_MONTHS` to a number to open on the last N months instead.
 */
const OPENING_WINDOW_MONTHS: number | null = null;
const MIN_WINDOW_MONTHS = 1;

/**
 * The North Star trend, sitting beside the North Star card.
 *
 * Ctrl + wheel zooms the time range instead of the browser page. The listener is
 * attached natively with `{ passive: false }` because React's `onWheel` is
 * passive — calling `preventDefault()` from a passive listener does nothing, and
 * the browser would zoom the whole page on top of our zoom.
 */
export function TrendCard({ chart }: { chart: Chart }) {
  const { t } = useI18n();
  const rows = chart.rows as Record<string, unknown>[];
  const total = rows.length;
  const [span, setSpan] = useState(() => OPENING_WINDOW_MONTHS ?? Math.max(total, MIN_WINDOW_MONTHS));
  const hostRef = useRef<HTMLDivElement>(null);

  // keep the window inside the data when a filter changes the row count,
  // without resetting a zoom the reader has already set
  useEffect(() => {
    setSpan((s) => Math.min(Math.max(s, MIN_WINDOW_MONTHS), Math.max(total, MIN_WINDOW_MONTHS)));
  }, [total]);

  const visible = useMemo(() => rows.slice(Math.max(0, total - span)), [rows, total, span]);

  useEffect(() => {
    const el = hostRef.current;
    if (!el || total <= MIN_WINDOW_MONTHS) return;
    const onWheel = (e: WheelEvent) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      setSpan((s) => Math.min(total, Math.max(MIN_WINDOW_MONTHS, s + (e.deltaY > 0 ? 1 : -1))));
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, [total]);

  return (
    <section className="trend-card">
      <header className="trend-card__head">
        <h2 className="trend-card__title">{t(chart.title)}</h2>
        <span className="trend-card__hint">{t('按住 Ctrl + 滚轮可缩放时间维度')}</span>
      </header>
      <div className="trend-card__body" ref={hostRef}>
        {visible.length > 0 ? (
          <ComposedSeriesChart chart={chart} rows={visible} />
        ) : (
          <div className="chart-empty">{t('该维度下暂无数据')}</div>
        )}
      </div>
    </section>
  );
}
