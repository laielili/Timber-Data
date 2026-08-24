import { useState } from 'react';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { ChatPage } from './pages/ChatPage';
import { IconGrid, IconSpark, IconUpload } from './components/icons';
import { useI18n } from './i18n';

export type Page = 'dashboard' | 'upload' | 'ai';

const NAV: { id: Page; label: string; hint: string; icon: (p: { size?: number; className?: string }) => React.ReactNode }[] = [
  { id: 'dashboard', label: '数据看板', hint: '指标与图表，右侧筛选维度', icon: IconGrid },
  { id: 'upload', label: '数据上传', hint: '上传数据与 API 接口', icon: IconUpload },
  { id: 'ai', label: 'AI 助手', hint: '基于已上传数据的对话', icon: IconSpark },
];

export default function App() {
  const [page, setPage] = useState<Page>('dashboard');
  const [dataVersion, setDataVersion] = useState(0);
  const { lang, setLang, t } = useI18n();

  const goUpload = () => setPage('upload');
  const onDataChanged = () => setDataVersion((v) => v + 1);

  return (
    <div className="app">
      <nav className="nav">
        <div className="nav__brand">
          <span className="nav__brand-mark">WB</span>
          <div className="nav__brand-text">
            <span className="nav__brand-name">Workbench</span>
            <span className="nav__brand-sub">{t('数据工作台')}</span>
          </div>
        </div>
        <ul className="nav__list">
          {NAV.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.id}>
                <button
                  type="button"
                  className={`nav__item${page === item.id ? ' nav__item--active' : ''}`}
                  onClick={() => setPage(item.id)}
                >
                  <Icon size={16} className="nav__icon" />
                  <span className="nav__item-text">
                    <span>{t(item.label)}</span>
                    <small>{t(item.hint)}</small>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
        <div className="nav__foot">
          <span className="nav__chip">{t('用户数据驱动')}</span>
          <p className="nav__note">{t('数据存于 data/workbench.db')}</p>
        </div>
      </nav>

      <main className="content">
        <div className="topbar">
          <button
            type="button"
            className="lang-switch"
            onClick={() => setLang(lang === 'zh' ? 'en' : 'zh')}
            aria-label="Language"
          >
            <span className="lang-switch__label">Language</span>
            <span className="lang-switch__code">{lang === 'zh' ? 'ZH' : 'EN'}</span>
          </button>
        </div>
        {page === 'dashboard' && (
          <DashboardPage key={dataVersion} goUpload={goUpload} />
        )}
        {page === 'upload' && <UploadPage onDataChanged={onDataChanged} />}
        {page === 'ai' && <ChatPage />}
      </main>
    </div>
  );
}