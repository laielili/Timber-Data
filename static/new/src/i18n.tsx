import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

export type Lang = 'zh' | 'en';

const ZH_TO_EN: Record<string, string> = {
  // ---- App nav ----
  '数据看板': 'Data Dashboard',
  '数据链接': 'Data Connection',
  'AI 助手': 'AI Assistant',
  '指标与图表，右侧筛选维度': 'Metrics & charts, filter on the right',
  '上传与示例数据': 'Upload & sample data',
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

  // ---- Metric system: North Star ----
  '净回收价值 / 入库吨': 'Net Recovery Value / incoming t',
  '北极星': 'North Star',
  '期间内产出与成本 ÷ 期间内到达': 'Output & cost in period ÷ arrived in period',
  '回收价值总额减去回收成本总额，再除以期间入库吨，即每一入库吨净赚多少。分子是至今累计（含已沉没成本），分母是期间入库 —— 这是运营管理度量，不是会计利润。':
    'Total recovered value minus total recovered cost, divided by incoming tonnes in the period — what each incoming tonne nets. The numerator is cumulative to date (including sunk cost); the denominator is the period intake. This is an operational measure, not accounting profit.',
  '平均单位价值': 'Avg unit value',
  '平均单位成本': 'Avg unit cost',
  '处理率': 'Processing rate',

  // ---- Metric system: strategy groups ----
  '价值端': 'Value',
  '成本端': 'Cost',
  '转化端': 'Conversion',
  '提高每一吨已处理木材的售价': 'Sell every processed tonne for more',
  '降低每一吨入库木材的核心回收成本': 'Spend less core cost per incoming tonne',
  '让更多入库吨成为已产出': 'Turn more incoming tonnes into output',

  // ---- Metric system: KPI labels ----
  '回收价值总额': 'Total Recovered Value',
  '回收成本总额 Core-5': 'Total Core-5 Cost',
  '最大成本项占比': 'Top Cost Line Share',
  '未决率': 'Unresolved Rate',
  '在途率': 'In-flight Rate',

  // ---- Metric system: KPI basis (names the tonne denominator) ----
  '期间内产出 ÷ 处理量': 'Output in period ÷ processed t',
  '期间内成本台账': 'Cost ledger in period',
  '期间内成本 ÷ 入库量': 'Cost in period ÷ incoming t',
  '期间内产出 ÷ 期间内到达': 'Output in period ÷ arrived in period',

  // ---- Metric system: KPI descriptions ----
  // Definitions only — no observed values, no M-codes. See MetricTip.tsx.
  '回收价值总额 ÷ 处理量，即每一处理吨平均卖出多少钱。基准是处理吨。':
    'Total recovered value ÷ processed tonnes — what a processed tonne sells for on average. The denominator is the processed tonne.',
  '期间内回收产出的毛价值合计，尚未扣减任何成本。':
    'Gross value of the output recovered in the period, before any cost is deducted.',
  '高值回收去向的重量 ÷ 处理量，衡量有多少吨卖出了高单价。':
    'Higher-value recovery weight ÷ processed tonnes — how much of the volume sells at a premium.',
  '回收成本总额 ÷ 入库量，即每一入库吨平均花了多少钱。基准是入库吨。':
    'Total recovered cost ÷ incoming tonnes — what an incoming tonne costs on average. The denominator is the incoming tonne.',
  'Core-5 成本合计：分拣、检验、处理、特殊处理、处置五类，不含运输与其他。':
    'Core-5 cost total: sorting, inspection, processing, special handling and disposal. Transport and Other are excluded.',
  '成本结构中占比最大的一类，占回收成本总额的比例。明细见成本结构图。':
    'The largest cost line, as a share of the total recovered cost. Full breakdown in the cost structure chart.',
  '处理量 ÷ 入库量，衡量收进来的吨有多少已经变成产出。':
    'Processed ÷ incoming tonnes — how much of the intake has become output.',
  '状态为未决的物料重量 ÷ 入库量。未决吨既没有实现价值，成本也已沉没。':
    'Weight of unresolved material ÷ incoming tonnes. Those tonnes have realised no value and their cost is already sunk.',
  '状态为在途或待处理的物料重量 ÷ 入库量。这些吨成本已付、价值尚未实现。':
    'Weight of material in progress or pending processing ÷ incoming tonnes. Their cost is paid; their value is not yet realised.',

  // ---- Metric system: guardrails ----
  '护栏指标 · 防止北极星被做高': 'Guardrails · stop the North Star from being gamed',
  '规模护栏 · 绝对净回收价值': 'Scale · absolute net recovery value',
  '分布护栏 · 亏损批次占比': 'Distribution · share of loss-making batches',
  '品质护栏 · 降级率': 'Quality · downgrade rate',
  '度量护栏 · 记录完整率': 'Measurement · record completeness',
  '履约护栏 · 应检未检率': 'Compliance · flagged-but-not-inspected rate',
  '期间内产出与成本': 'Output & cost in period',
  '期间内批次': 'Batches in period',
  '期间内到达批次物料': 'Materials of batches arriving in period',
  '北极星是比率，缩分母（少收货）就能把它抬高，但绝对净价值会掉，两者必须一起看。预警线按净额占回收价值的比例判定：低于 25% 转黄，归零或为负转红。':
    'The North Star is a ratio — shrinking the denominator lifts it while absolute net value falls, so the two must be read together. The band applies to net ÷ recovered value: below 25% turns amber, zero or negative turns red.',
  '均值掩盖结构：北极星为正不代表多数批次为正。绿灯 ≤ 20%，35% 以上转红。':
    'Averages hide structure: a positive North Star does not mean most batches are positive. Green ≤ 20%; above 35% turns red.',
  '为冲高值回收率而过度定级，会在实际定级时暴露为降级。绿灯 ≤ 10%，20% 以上转红。':
    'Over-grading to chase the higher-value rate shows up later as downgrades. Green ≤ 10%; above 20% turns red.',
  '记录不完整的吨越多，上面所有指标越不可审计。绿灯 ≥ 95%，低于 80% 转红。':
    'The more incomplete tonnes there are, the less auditable every metric above becomes. Green ≥ 95%; below 80% turns red.',
  '裁检验成本最直接的办法是漏检；本项盯住标记需检验却没有检验记录的物料。绿灯 = 0%，高于 2% 转红。':
    'The quickest way to cut inspection cost is to skip inspections; this watches materials flagged for inspection with no inspection record. Green = 0%; above 2% turns red.',

  // ---- Metric system: guardrail alert levels & trend hint ----
  '正常': 'Normal',
  '预警': 'Warning',
  '严重': 'Severe',
  '按住 Ctrl + 滚轮可缩放时间维度': 'Hold Ctrl + scroll to zoom the time range',

  // ---- Metric system: units that name their own tonne denominator ----
  'AUD/处理t': 'AUD/processed t',
  'AUD/入库t': 'AUD/incoming t',

  // ---- Metric system: hover annotations ----
  '计算口径': 'Basis',

  // ---- Metric system: chart series labels (from API) ----
  '入库量 (t)': 'Incoming (t)',
  '处理量 (t)': 'Processed (t)',
  '净回收价值 (AUD)': 'Net recovery value (AUD)',
  '成本 (AUD)': 'Cost (AUD)',
  '重量 (t)': 'Weight (t)',
  '单位价值 (AUD/t)': 'Unit value (AUD/t)',
  '物料重量 (t)': 'Material weight (t)',

  // ---- Metric system: chart sections & matrix ----
  '状态矩阵 · 三条策略的汇合点': 'Status Matrix · where the three strategies meet',
  '归属规则（方案 B）：分拣 + 检验由所有吨承担；处理/特殊处理/处置仅由已产出的 Output 承担；价值只在 Output 实现。四行合计必须回到北极星。':
    'Attribution (option B): sorting + inspection are borne by every tonne; processing / special handling / disposal only by tonnes that produced output; value is realised on Output alone. The four rows must sum back to the North Star.',
  '驱动分解': 'Driver decomposition',
  '禀赋与切片': 'Endowment & slices',
  '把三个驱动项逐层摊开': 'Unfold the three drivers layer by layer',
  '原料禀赋与批次分布': 'Feedstock endowment and batch spread',
  '合计': 'Total',
  '状态': 'State',
  '重量 t': 'Weight t',
  '归属成本 AUD': 'Attributed cost AUD',
  '归属价值 AUD': 'Attributed value AUD',
  '净贡献 AUD': 'Net contribution AUD',
  '每吨净 AUD': 'Net per t AUD',
  '成本结构': 'Cost Structure',
  '等级结构': 'Grade Structure',
  '成本/入库t': 'Cost / incoming t',
  '价值/入库t': 'Value / incoming t',

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
  '必填': 'Required',
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

/**
 * Reverse map for the categorical values that arrive *from the database* in
 * English. Proper nouns (species, source types, regions) are deliberately left
 * alone — only the controlled vocabularies that carry the metric story are
 * localised, so the zh view reads as one language instead of one-and-a-half.
 */
const EN_TO_ZH: Record<string, string> = {
  // Materials.resolution_status — the four rows of the status matrix
  Output: '已产出',
  'In Progress': '在途',
  'Pending Processing': '待处理',
  Unresolved: '未决',
  // recovery_grade
  Premium: '优级',
  Character: '纹理级',
  Rustic: '粗朴级',
  Feedstock: '原料级',
  // recovery_route
  'Board Feedstock': '板材原料',
  'Higher-value Recovery': '高值回收',
  'Special Handling': '特殊处理',
  'Residual / Disposal': '余料 / 处置',
  // CostLedger.cost_category
  Processing: '处理',
  'Sorting Labour': '分拣人工',
  Inspection: '检验',
  Disposal: '处置',
};

interface I18nValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (s: string) => string;
  /** Translate a value that came from the database (English → zh when in zh mode). */
  td: (s: string) => string;
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

  const t = (s: string) => {
    if (lang !== 'en') return s;
    if (s in ZH_TO_EN) return ZH_TO_EN[s];
    // Composite labels like "最大成本项占比 · Processing" carry a data value in
    // their tail; translate the head and leave the data value alone.
    const sep = s.indexOf(' · ');
    if (sep > 0) {
      const head = s.slice(0, sep);
      if (head in ZH_TO_EN) return ZH_TO_EN[head] + s.slice(sep);
    }
    return s;
  };

  const td = (s: string) => (lang === 'zh' ? EN_TO_ZH[s] ?? s : s);

  return (
    <I18nContext.Provider value={{ lang, setLang, t, td }}>{children}</I18nContext.Provider>
  );
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within I18nProvider');
  return ctx;
}
