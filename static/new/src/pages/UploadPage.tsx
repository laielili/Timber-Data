import { useEffect, useState } from 'react';
import { api, describeError } from '../api';
import { useI18n } from '../i18n';
import type { UploadResult } from '../types';

const TABLES = [
  'SourceProjects',
  'Batches',
  'Materials',
  'RecoveryOutputs',
  'CostLedger',
  'ProcessingEvents',
  'InspectionEvents',
];

export function UploadPage({ onDataChanged }: { onDataChanged: () => void }) {
  const { t } = useI18n();
  const [table, setTable] = useState('Batches');
  const [mode, setMode] = useState<'append' | 'replace'>('append');
  const [file, setFile] = useState<File | null>(null);
  const [bundleFile, setBundleFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hasData, setHasData] = useState<boolean | null>(null);

  useEffect(() => {
    api
      .health()
      .then((h) => setHasData(h.total_rows > 0))
      .catch(() => setHasData(false));
  }, []);

  const upload = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const isJson = file.name.toLowerCase().endsWith('.json');
      const r = isJson ? await api.uploadJson(file, table, mode) : await api.uploadCsv(file, table, mode);
      setResult(r);
      onDataChanged();
    } catch (e) {
      setError(describeError(e));
    } finally {
      setBusy(false);
    }
  };

  const uploadBundle = async () => {
    if (!bundleFile) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const r = await api.uploadBundle(bundleFile);
      setResult(r);
      onDataChanged();
    } catch (e) {
      setError(describeError(e));
    } finally {
      setBusy(false);
    }
  };

  const loadDemo = async () => {
    const reset = hasData === true;
    if (reset && !window.confirm(t('将清空工作台现有数据并载入示例数据，是否继续？'))) return;
    setBusy(true);
    setError(null);
    try {
      const r = await api.loadDemo(reset ? 'replace' : 'append');
      setHasData(true);
      setResult({
        upload_id: 'demo',
        table_name: 'demo',
        filename: 'synthetic',
        mode: reset ? 'replace' : 'append',
        row_count: r.tables?.reduce((n, t) => n + t.rows, 0) ?? 0,
        status: 'ok',
        errors: [],
        message: r.message,
      });
      onDataChanged();
    } catch (e) {
      setError(describeError(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="upload">
      <header className="page-head">
        <h1>{t('数据链接')}</h1>
        <p className="page-head__sub">
          {t('上传符合 timber schema 的数据（CSV / JSON），替换或扩充当前数据集。上传后看板与 AI 自动读取新数据。')}
        </p>
      </header>

      <section className="panel">
        <h2>{t('1. 上传文件')}</h2>
        <div className="upload-form">
          <div className="upload-form__row">
            <label>
              {t('目标表')}
              <select value={table} onChange={(e) => setTable(e.target.value)}>
                {TABLES.map((tbl) => (
                  <option key={tbl} value={tbl}>
                    {tbl}
                  </option>
                ))}
              </select>
            </label>
            <label>
              {t('写入模式')}
              <select value={mode} onChange={(e) => setMode(e.target.value as 'append' | 'replace')}>
                <option value="append">{t('append（按主键 upsert，保留已有数据）')}</option>
                <option value="replace">{t('replace（清空该表后写入）')}</option>
              </select>
            </label>
          </div>
          <div className="upload-form__row">
            <label className="file-label">
              {t('选择文件（.csv 或 .json）')}
              <input type="file" accept=".csv,.json" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            </label>
            <button className="btn btn--primary" onClick={upload} disabled={!file || busy}>
              {busy ? t('上传中…') : t('上传')}
            </button>
          </div>
        </div>
        {file && (
          <p className="upload-hint">
            {file.name.endsWith('.json')
              ? t('将解析为 JSON 行数据，忽略未知列，校验必填列与外键引用。')
              : t('将解析为 CSV，忽略未知列，校验必填列与外键引用。')}
          </p>
        )}
        {result && <div className="upload-result upload-result--ok">{result.message}</div>}
        {error && <div className="upload-result upload-result--err">{error}</div>}
      </section>

      <section className="panel">
        <h2>{t('2. 整包上传（bundle）')}</h2>
        <p className="panel__desc">
          {t('JSON 格式：{ "tables": { "Batches": { "rows": [...] }, ... } }。适合一次性导入多张表。')}
        </p>
        <div className="upload-form">
          <div className="upload-form__row">
            <label className="file-label">
              {t('选择 bundle 文件（.json）')}
              <input type="file" accept=".json" onChange={(e) => setBundleFile(e.target.files?.[0] ?? null)} />
            </label>
            <button className="btn btn--primary" onClick={uploadBundle} disabled={!bundleFile || busy}>
              {t('上传 bundle')}
            </button>
          </div>
        </div>
      </section>

      <section className="panel">
        <h2>{t('3. 载入示例数据（可选）')}</h2>
        <p className="panel__desc">
          {t('将合成示例数据集（36 批次 · 1239 物料）导入工作台，用于快速体验看板与 AI。这不是预设——由您决定是否载入。工作台已有数据时，按钮会切换为「重置为示例数据」（确认后清空现有数据并重新载入）。')}
        </p>
        <button className="btn" onClick={loadDemo} disabled={busy || hasData === null}>
          {hasData === true ? t('重置为示例数据') : t('载入示例数据')}
        </button>
      </section>
    </div>
  );
}