import { useEffect, useMemo, useState } from 'react';
import { api, describeError } from '../api';
import { useI18n } from '../i18n';
import type { ApiEndpoint, TableSchemaInfo, UploadResult } from '../types';

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
  const [tables, setTables] = useState<TableSchemaInfo[]>([]);
  const [table, setTable] = useState('Batches');
  const [mode, setMode] = useState<'append' | 'replace'>('append');
  const [file, setFile] = useState<File | null>(null);
  const [bundleFile, setBundleFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hasData, setHasData] = useState<boolean | null>(null);

  const [endpoints, setEndpoints] = useState<ApiEndpoint[]>([]);
  const [selectedPath, setSelectedPath] = useState('/api/new/dashboard');
  const [consoleOutput, setConsoleOutput] = useState<string>('');
  const [consoleFile, setConsoleFile] = useState<File | null>(null);
  const [consoleFields, setConsoleFields] = useState<Record<string, string>>({});

  useEffect(() => {
    api.uploadTables().then(setTables).catch(() => undefined);
    api
      .meta()
      .then((m) => setEndpoints(m.api_reference))
      .catch(() => undefined);
    api
      .health()
      .then((h) => setHasData(h.total_rows > 0))
      .catch(() => setHasData(false));
  }, []);

  const selected = useMemo(
    () => endpoints.find((e) => e.path === selectedPath) ?? null,
    [endpoints, selectedPath],
  );

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

  const runConsole = async () => {
    if (!selected) return;
      setConsoleOutput(t('执行中…'));
    try {
      let out: unknown;
      if (selected.path.includes('/upload/csv')) {
        out = await api.uploadCsv(consoleFile!, consoleFields.table || 'Batches', consoleFields.mode || 'append');
        onDataChanged();
      } else if (selected.path.includes('/upload/json')) {
        out = await api.uploadJson(consoleFile!, consoleFields.table || 'Batches', consoleFields.mode || 'append');
        onDataChanged();
      } else if (selected.path.includes('/upload/bundle')) {
        out = await api.uploadBundle(consoleFile!);
        onDataChanged();
      } else if (selected.path === '/api/new/dashboard') {
        out = await api.dashboard({
          period_start: consoleFields.period_start || undefined,
          period_end: consoleFields.period_end || undefined,
          source_type: consoleFields.source_type || undefined,
          region: consoleFields.region || undefined,
          species: consoleFields.species || undefined,
          recovery_route: consoleFields.recovery_route || undefined,
          batch_status: consoleFields.batch_status || undefined,
          current_stage: consoleFields.current_stage || undefined,
        });
      } else if (selected.path === '/api/new/ai/chat') {
        let messages: { role: 'user'; content: string }[];
        try {
          messages = JSON.parse(consoleFields.messages || '[{"role":"user","content":"hello"}]');
        } catch {
          messages = [{ role: 'user', content: consoleFields.messages || 'hello' }];
        }
        out = await api.chat(messages);
      } else if (selected.path === '/api/new/demo') {
        out = await api.loadDemo();
        onDataChanged();
      } else if (selected.path === '/api/new/ai/test') {
        out = await api.testAiConnection();
      } else {
        out = await api.endpoint(selected.method, selected.path);
      }
      setConsoleOutput(JSON.stringify(out, null, 2));
    } catch (e) {
       setConsoleOutput(`${t('错误：')}${describeError(e)}`);
    }
  };

  return (
    <div className="upload">
      <header className="page-head">
        <h1>{t('数据上传')}</h1>
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

      <section className="panel">
        <h2>{t('4. 表结构参考')}</h2>
        <div className="table-schemas">
          {tables.map((tbl) => (
            <details key={tbl.table_name} className="table-schema">
              <summary>
                {tbl.table_name} <span className="muted">{t('主键：')}{tbl.primary_key}</span>
              </summary>
              <table className="schema-table">
                <thead>
                  <tr>
                    <th>{t('字段')}</th>
                    <th>{t('类型')}</th>
                    <th>{t('必填')}</th>
                  </tr>
                </thead>
                <tbody>
                  {tbl.columns.map((c) => (
                    <tr key={c.name}>
                      <td>{c.name}</td>
                      <td>{c.type}</td>
                      <td>{c.required ? t('是') : t('否')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>{t('5. API 接口 · 文档与测试台')}</h2>
        <p className="panel__desc">
          {t('工作台提供真实 REST 端点（文档见 Swagger UI）。下面可直接选择端点并调用。')}
        </p>
        <div className="console">
          <div className="console__row">
            <label>
              {t('端点')}
              <select value={selectedPath} onChange={(e) => setSelectedPath(e.target.value)}>
                {endpoints.map((e) => (
                  <option key={e.path} value={e.path}>
                    {e.method} {e.path} — {t(e.summary)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {selected && (
            <div className="console__fields">
              {selected.path.includes('/upload/') && (
                <label className="file-label">
                  {t('文件')}
                  <input type="file" onChange={(e) => setConsoleFile(e.target.files?.[0] ?? null)} />
                </label>
              )}
              {selected.fields
                .filter((f) => f.type !== 'file')
                .map((f) => (
                  <label key={f.name}>
                    {f.name} {f.required ? '*' : ''}
                    <input
                      type={f.type === 'json' ? 'text' : f.name.includes('date') ? 'date' : 'text'}
                      placeholder={t(f.description)}
                      value={consoleFields[f.name] ?? ''}
                      onChange={(e) =>
                        setConsoleFields((d) => ({ ...d, [f.name]: e.target.value }))
                      }
                    />
                  </label>
                ))}
              <div className="console__example">
                <span className="muted">{t('curl 示例：')}</span>
                <pre>{selected.example}</pre>
              </div>
              <button className="btn btn--primary" onClick={runConsole}>
                {t('调用')}
              </button>
            </div>
          )}

          <div className="console__output">
            <pre>{consoleOutput || t('（点击“调用”查看返回结果）')}</pre>
          </div>
        </div>
      </section>
    </div>
  );
}