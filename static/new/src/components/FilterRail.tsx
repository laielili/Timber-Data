import { useState } from 'react';
import type { Dimensions, Filters } from '../types';
import { IconChevronRight } from './icons';
import { useI18n } from '../i18n';

interface Props {
  dimensions: Dimensions;
  onApply: (f: Filters) => void;
  onReset: () => void;
}

const DIM_SELECTS: { key: keyof Dimensions; label: string; filterKey: keyof Filters }[] = [
  { key: 'source_types', label: '来源类型', filterKey: 'source_type' },
  { key: 'regions', label: '区域', filterKey: 'region' },
  { key: 'species', label: '树种', filterKey: 'species' },
  { key: 'material_forms', label: '物料形态', filterKey: 'material_form' },
  { key: 'recovery_routes', label: '回收去向', filterKey: 'recovery_route' },
  { key: 'batch_statuses', label: '批次状态', filterKey: 'batch_status' },
  { key: 'current_stages', label: '当前阶段', filterKey: 'current_stage' },
];

export function FilterRail({ dimensions, onApply, onReset }: Props) {
  const { t } = useI18n();
  const [draft, setDraft] = useState<Filters>({});
  const [open, setOpen] = useState(true);

  const set = (key: keyof Filters, value: string) =>
    setDraft((d) => ({ ...d, [key]: value || undefined }));

  const apply = () => onApply(draft);
  const reset = () => {
    setDraft({});
    onReset();
  };

  const activeCount = Object.values(draft).filter(Boolean).length;

  return (
    <aside className={`filter-rail${open ? '' : ' filter-rail--closed'}`}>
      {open ? (
        <>
          <div className="filter-rail__head">
            <span className="filter-rail__title">{t('数据维度筛选')}</span>
            {activeCount > 0 && <span className="filter-rail__badge">{activeCount}</span>}
            <button
              type="button"
              className="filter-rail__toggle"
              onClick={() => setOpen(false)}
              title={t('收起筛选栏')}
            >
              <IconChevronRight size={15} />
            </button>
          </div>

          <div className="filter-rail__body">
            <div className="filter-field">
              <label>{t('起始日期')}</label>
              <input
                type="date"
                value={draft.period_start ?? ''}
                min={dimensions.period_start ?? undefined}
                max={dimensions.period_end ?? undefined}
                onChange={(e) => set('period_start', e.target.value)}
              />
            </div>
            <div className="filter-field">
              <label>{t('结束日期')}</label>
              <input
                type="date"
                value={draft.period_end ?? ''}
                min={dimensions.period_start ?? undefined}
                max={dimensions.period_end ?? undefined}
                onChange={(e) => set('period_end', e.target.value)}
              />
            </div>

            {DIM_SELECTS.map(({ key, label, filterKey }) => (
              <div className="filter-field" key={key}>
                <label>{t(label)}</label>
                <select value={(draft[filterKey] as string) ?? ''} onChange={(e) => set(filterKey, e.target.value)}>
                  <option value="">{t('全部')}</option>
                  {(dimensions[key] as string[]).map((v) => (
                    <option key={v} value={v}>
                      {v}
                    </option>
                  ))}
                </select>
              </div>
            ))}

            <div className="filter-rail__actions">
              <button type="button" className="btn btn--primary" onClick={apply}>
                {t('应用筛选')}
              </button>
              <button type="button" className="btn" onClick={reset}>
                {t('重置')}
              </button>
            </div>
          </div>
        </>
      ) : (
        <button
          type="button"
          className="filter-rail__open"
          onClick={() => setOpen(true)}
          title={t('展开筛选栏')}
        >
          {t('筛选')}
        </button>
      )}
    </aside>
  );
}