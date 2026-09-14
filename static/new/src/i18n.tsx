import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

export type Lang = 'zh' | 'en';

const ZH_TO_EN: Record<string, string> = {
  // ---- App nav ----
  '数据看板': 'Data Dashboard',
  '数据链接': 'Data Connection',
  'AI 助手': 'AI Assistant',
  '指标与图表，右侧筛选维度': 'Metrics & charts, filter on the right',
  '数据链接与 API 接口': 'Data Connection & API endpoints',
  '基于已上传数据的对话': 'Chat grounded on your uploaded data',
  '用户数据驱动': 'User-data driven',
  '数据存于 data/workbench.db': 'Data stored in data/workbench.db',

  // ---- Dashboard page (DashboardPage) ----
  '加载失败': 'Failed to load',
  '重试': 'Retry',
  '加载中…': 'Loading…',
  '尚未数据链接——看板会随您的数据实时更新。':
    'No data uploaded yet — the dashboard updates live as your data arrives.',
  '更新中…': 'Updating…',
  '数据集为空': 'Dataset is empty',
  '上传符合 timber schema 的数据后，看板与 AI 将自动读取；也可以先载入示例数据体验完整流程。':
    'After uploading data conforming to the timber schema, the dashboard and AI read it automatically. Or load the sample dataset first to explore the full flow.',
  '去数据链接': 'Go to Data Connection',
  '载入示例数据': 'Load Sample Data',
  '共': 'Total',
  '行': 'rows',
  '已应用筛选': 'filters applied',
  '显示全量数据': 'showing all data',

  // ---- KPI labels (from API) ----
  '入库量': 'Incoming Volume',
  '处理量': 'Processed Volume',
  '高值回收率': 'Higher-value Recovery Rate',
  '回收价值/吨': 'Recovered Value / t',
  '成本/吨': 'Cost / t',
  '未解决物料': 'Unresolved Materials',

  // ---- KPI basis (from API) ----
  '期间内到达批次': 'Batches arriving in period',
  '快照': 'Snapshot',
  '期间内产出': 'Output in period',

  // ---- KPI descriptions (from API) ----
  '所选维度下，期间内到达批次的总入库重量。':
    'Total incoming weight of batches arriving within the selected dimensions.',
  '所选维度下，期间内回收产出的总重量。':
    'Total recovered output weight within the selected dimensions.',
  '所选维度下，期间内产出中高值回收去向的重量占比。':
    'Share of higher-value recovery route within processed output, for the selected dimensions.',
  '毛回收价值 / 处理量。': 'Gross recovered value / processed volume.',
  '成本台账总成本 / 处理量。': 'Total cost ledger / processed volume.',
  '快照：状态为 Unresolved 的物料总重量。':
    'Snapshot: total weight of materials in the Unresolved state.',

  // ---- Chart titles (from API) ----
  '月度趋势': 'Monthly Trend',
  '回收去向分布': 'Recovery Route Distribution',
  '批次经济性': 'Batch Economics',
  '来源结构': 'Source Composition',
  '物料组成': 'Material Composition',
  '物料状态': 'Material State',

  // ---- Chart (ChartCard) ----
  '该维度下暂无数据': 'No data under the current filters',
  '价值/吨': 'Value / t',
  '入库(t)': 'Incoming (t)',

  // ---- Filter rail (FilterRail) ----
  '数据维度筛选': 'Data Dimension Filters',
  '来源类型': 'Source Type',
  '区域': 'Region',
  '树种': 'Species',
  '物料形态': 'Material Form',
  '回收去向': 'Recovery Route',
  '批次状态': 'Batch Status',
  '当前阶段': 'Current Stage',
  '起始日期': 'Start date',
  '结束日期': 'End date',
  '全部': 'All',
  '应用筛选': 'Apply filters',
  '重置': 'Reset',
  '筛选': 'Filters',
  '收起筛选栏': 'Collapse filters',
  '展开筛选栏': 'Expand filters',

  // ---- KPI (backend, extra strings) ----
  '期间内回收产出': 'Output recovered in period',
  '高值回收去向重量占处理量的比例。': 'Share of higher-value recovery route weight within processed volume.',
  '状态为 Unresolved 的物料总重量。': 'Total weight of materials in the Unresolved state.',

  // ---- API reference (backend meta) ----
  '上传 CSV 到指定表': 'Upload CSV to a table',
  '上传 JSON 行数据到指定表': 'Upload JSON row data to a table',
  '上传多表 JSON bundle': 'Upload multi-table JSON bundle',
  '载入合成示例数据（可选，非预设）': 'Load synthetic sample data (optional, not a preset)',
  '可上传的表及字段定义': 'Uploadable tables and field definitions',
  '数据看板（支持维度筛选查询参数）': 'Data dashboard (supports dimension filter params)',
  'AI 对话（基于已上传数据的问答）': 'AI chat (Q&A on your uploaded data)',
  '测试 AI 服务连接': 'Test AI service connection',
  'UTF-8 编码的 CSV，首行为表头': 'UTF-8 CSV with a header row',
  '目标表名，如 Batches': 'Target table name, e.g. Batches',
  'append（默认，按主键 upsert）或 replace（清空后写入）': 'append (default, upsert by primary key) or replace (clear then write)',
  'JSON 文件：{"rows": [...]} 或直接是行数组': 'JSON file: {"rows": [...]} or a raw array of rows',
  '目标表名': 'Target table name',
  '会话 ID（可选）': 'Conversation ID (optional)',

  // ---- Upload page ----
  '数据工作台': 'Data Workbench',
  '上传符合 timber schema 的数据（CSV / JSON），替换或扩充当前数据集。上传后看板与 AI 自动读取新数据。':
    'Upload data conforming to the timber schema (CSV / JSON) to replace or extend the current dataset. After upload, the dashboard and AI read the new data automatically.',
  '1. 上传文件': '1. Upload file',
  '目标表': 'Target table',
  '写入模式': 'Write mode',
  'append（按主键 upsert，保留已有数据）': 'append (upsert by primary key, keep existing data)',
  'replace（清空该表后写入）': 'replace (clear table then write)',
  '选择文件（.csv 或 .json）': 'Choose file (.csv or .json)',
  '上传中…': 'Uploading…',
  '上传': 'Upload',
  '将解析为 JSON 行数据，忽略未知列，校验必填列与外键引用。': 'Will be parsed as JSON rows, ignoring unknown columns and validating required columns and foreign keys.',
  '将解析为 CSV，忽略未知列，校验必填列与外键引用。': 'Will be parsed as CSV, ignoring unknown columns and validating required columns and foreign keys.',
  '2. 整包上传（bundle）': '2. Bundle upload',
  'JSON 格式：{ "tables": { "Batches": { "rows": [...] }, ... } }。适合一次性导入多张表。':
    'JSON format: { "tables": { "Batches": { "rows": [...] }, ... } }. Good for importing multiple tables at once.',
  '选择 bundle 文件（.json）': 'Choose bundle file (.json)',
  '上传 bundle': 'Upload bundle',
  '3. 载入示例数据（可选）': '3. Load sample data (optional)',
  '将合成示例数据集（36 批次 · 1239 物料）导入工作台，用于快速体验看板与 AI。这不是预设——由您决定是否载入。工作台已有数据时，按钮会切换为「重置为示例数据」（确认后清空现有数据并重新载入）。':
    'Imports a synthetic sample dataset (36 batches · 1239 materials) into the workbench to quickly explore the dashboard and AI. This is not a preset — you decide whether to load it. When data already exists, the button switches to “Reset to sample data” (clears existing data and reloads after confirmation).',
  '重置为示例数据': 'Reset to sample data',
  '4. 表结构参考': '4. Table schema reference',
  '主键：': 'Primary key: ',
  '字段': 'Field',
  '类型': 'Type',
  '必填': 'Required',
  '是': 'Yes',
  '否': 'No',
  '5. API 接口 · 文档与测试台': '5. API endpoints · docs & console',
  '工作台提供真实 REST 端点（文档见 Swagger UI）。下面可直接选择端点并调用。':
    'The workbench exposes real REST endpoints (docs at Swagger UI). Select and call an endpoint directly below.',
  '端点': 'Endpoint',
  '文件': 'File',
  'curl 示例：': 'curl example: ',
  '调用': 'Call',
  '（点击“调用”查看返回结果）': '(click “Call” to see the response)',
  '执行中…': 'Running…',
  '错误：': 'Error: ',
  '将清空工作台现有数据并载入示例数据，是否继续？': 'This will clear the workbench’s current data and load the sample data. Continue?',

  // ---- Chat page ----
  '已保存（API Key 已配置）': 'Saved (API Key configured)',
  '已保存（未配置 API Key）': 'Saved (API Key not configured)',
  '保存失败：': 'Save failed: ',
  '测试中…': 'Testing…',
  '连接成功：': 'Connected: ',
  '连接失败：': 'Connection failed: ',
  '测试出错：': 'Test error: ',
  '已连接': 'Connected',
  '未指定模型': 'unspecified model',
  '未配置模型。点击右上角“配置”连接 OpenAI 兼容接口。': 'No model configured. Click “Config” at the top-right to connect an OpenAI-compatible endpoint.',
  '收起配置': 'Hide config',
  '配置': 'Config',
  '模型配置（OpenAI 兼容）': 'Model config (OpenAI-compatible)',
  '模型（model）': 'Model',
  '已配置（留空保持不变）': 'Configured (leave blank to keep)',
  '启用 AI 对话': 'Enable AI chat',
  '保存中…': 'Saving…',
  '保存配置': 'Save config',
  '测试连接': 'Test connection',
  'API Key 仅保存在服务端（src/new/.secrets/），不会发送到浏览器，也不会在配置中回显。':
    'The API Key is stored only on the server (src/new/.secrets/) — it is never sent to the browser and is not echoed back in config.',
  '向 AI 提问关于您已上传数据的问题，例如：': 'Ask the AI about your uploaded data, e.g.:',
  '“总入库量是多少？高值回收率呢？”': '“What is the total incoming volume? And the higher-value recovery rate?”',
  '“哪个批次的成本/吨最高？”': '“Which batch has the highest cost/t?”',
  '“Residential Demolition 来源的净价值如何？”': '“What is the net value of the Residential Demolition source?”',
  '“分月展示处理量与回收价值的变化”': '“Show monthly processing volume and recovered value.”',
  '调用了工具：': 'Called tools: ',
  '思考中…': 'Thinking…',
  '输入问题…（Enter 发送，Shift+Enter 换行）': 'Type a question… (Enter to send, Shift+Enter for newline)',
  '请先完成模型配置': 'Complete model configuration first',
  '发送': 'Send',
};

interface I18nValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (s: string) => string;
}

const I18nContext = createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    const saved = localStorage.getItem('wb-lang');
    return saved === 'en' || saved === 'zh' ? (saved as Lang) : 'en';
  });

  useEffect(() => {
    localStorage.setItem('wb-lang', lang);
    document.documentElement.lang = lang === 'en' ? 'en' : 'zh-CN';
  }, [lang]);

  const setLang = (l: Lang) => setLangState(l);
  const t = (s: string) => (lang === 'en' && s in ZH_TO_EN ? ZH_TO_EN[s] : s);

  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within I18nProvider');
  return ctx;
}
