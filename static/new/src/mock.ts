// Static-prototype mock data.
//
// This module powers the standalone `docs/` build so the product can be demoed
// without a running backend. Wire it in via the `USE_MOCK` flag in api.ts:
// flip it to `false` to talk to a real backend again. Filters are acknowledged
// but the dataset is intentionally static for the prototype.
//
// The numbers below are NOT invented: they are the verbatim response of
// `src/new/dashboard_service.get_dashboard()` run against the bundled sample
// dataset in `data/workbench.db` (36 batches, 2025-01-07 → 2025-12-21), so the
// dashboard, the API contract in `documents/frontend/FRONTEND_DATA_CONTRACT.md`
// and this prototype all agree. Currency is AUD; per-tonne rates render as $/t.
// Re-dump with `scripts/_dump_dashboard.py` if the sample dataset changes.

import type {
  ApiEndpoint,
  Chart,
  DashboardResponse,
  Dimensions,
  Kpi,
  MetaResponse,
  TableSchemaInfo,
} from './types';

const SOURCE_TYPES = [
  'Commercial Demolition',
  'Direct Salvage Purchase',
  'Industrial Renewal',
  'Infrastructure Salvage',
  'Residential Demolition',
  'Warehouse Deconstruction',
];
const REGIONS = [
  'New South Wales',
  'Queensland',
  'South Australia',
  'Tasmania',
  'Victoria',
  'Western Australia',
];
const SPECIES = [
  'Blackbutt',
  'Cypress Pine',
  'Ironbark',
  'Messmate',
  'Mixed Hardwood',
  'Mountain Ash',
  'Oregon',
  'Radiata Pine',
  'Spotted Gum',
  'Sydney Blue Gum',
  'Unknown / Mixed',
];
const MATERIAL_FORMS = [
  'Beam',
  'Board',
  'Cladding',
  'Flooring',
  'Mixed Salvage',
  'Other',
  'Post',
  'Structural Member',
];
const RECOVERY_ROUTES = [
  'Board Feedstock',
  'Higher-value Recovery',
  'Residual / Disposal',
  'Special Handling',
];
const BATCH_STATUSES = ['Completed', 'Partially Completed'];
const CURRENT_STAGES = ['Completed', 'Inspection', 'Processing', 'Sorting'];

export function mockDimensions(): Dimensions {
  return {
    period_start: '2025-01-07',
    period_end: '2025-12-21',
    source_types: SOURCE_TYPES,
    regions: REGIONS,
    species: SPECIES,
    material_forms: MATERIAL_FORMS,
    recovery_routes: RECOVERY_ROUTES,
    batch_statuses: BATCH_STATUSES,
    current_stages: CURRENT_STAGES,
  };
}

const KPIS: Kpi[] = [
  {
    id: 'incoming',
    label: '入库量',
    value: 1240.0,
    unit: 't',
    basis: '期间内到达批次',
    description: '所选维度下，期间内到达批次的总入库重量。',
  },
  {
    id: 'processed',
    label: '处理量',
    value: 992.0,
    unit: 't',
    basis: '期间内回收产出',
    description: '所选维度下，期间内回收产出的总重量。',
  },
  {
    id: 'hv_rate',
    label: '高值回收率',
    value: 35.69,
    unit: '%',
    basis: '期间内产出',
    description: '高值回收去向重量占处理量的比例。',
  },
  {
    id: 'value_per_t',
    label: '回收价值/吨',
    value: 320.0,
    unit: '$/t',
    basis: '期间内产出',
    description: '毛回收价值 / 处理量。',
  },
  {
    id: 'cost_per_t',
    label: '成本/吨',
    value: 208.5,
    unit: '$/t',
    basis: '期间内产出',
    description: '产出批次的成本台账总成本 / 处理量。',
  },
  {
    id: 'unresolved',
    label: '未解决物料',
    value: 24.8,
    unit: 't',
    basis: '快照',
    description: '快照：状态为 Unresolved 的物料总重量。',
  },
];

const CHARTS: Chart[] = [
  {
    id: 'monthly_trend',
    title: '月度趋势',
    type: 'bar',
    rows: [
      { month: '2025-01', incoming_t: 101.9, processed_t: 79.6, gross_value_aud: 26935.58, cost_aud: 21003.58 },
      { month: '2025-02', incoming_t: 97.7, processed_t: 93.4, gross_value_aud: 29039.98, cost_aud: 17327.24 },
      { month: '2025-03', incoming_t: 85.0, processed_t: 67.0, gross_value_aud: 21630.08, cost_aud: 18450.13 },
      { month: '2025-04', incoming_t: 96.6, processed_t: 113.6, gross_value_aud: 34945.84, cost_aud: 19375.27 },
      { month: '2025-05', incoming_t: 105.1, processed_t: 97.7, gross_value_aud: 34299.87, cost_aud: 20878.85 },
      { month: '2025-06', incoming_t: 107.3, processed_t: 72.2, gross_value_aud: 29098.79, cost_aud: 18416.12 },
      { month: '2025-07', incoming_t: 106.3, processed_t: 130.7, gross_value_aud: 33071.27, cost_aud: 29892.86 },
      { month: '2025-08', incoming_t: 98.8, processed_t: 85.0, gross_value_aud: 33203.67, cost_aud: 14190.69 },
      { month: '2025-09', incoming_t: 93.4, processed_t: 118.9, gross_value_aud: 38220.29, cost_aud: 22644.55 },
      { month: '2025-10', incoming_t: 144.8, processed_t: 64.8, gross_value_aud: 16891.17, cost_aud: 13356.05 },
      { month: '2025-11', incoming_t: 81.6, processed_t: 35.1, gross_value_aud: 10184.52, cost_aud: 10807.53 },
      { month: '2025-12', incoming_t: 121.5, processed_t: 34.0, gross_value_aud: 9918.98, cost_aud: 489.13 },
    ],
  },
  {
    id: 'route_distribution',
    title: '回收去向分布',
    type: 'pie',
    rows: [
      { route: 'Board Feedstock', weight_t: 546.0, gross_value_aud: 105140.02, percentage: 55.04 },
      { route: 'Higher-value Recovery', weight_t: 354.0, gross_value_aud: 194300.0, percentage: 35.69 },
      { route: 'Special Handling', weight_t: 48.0, gross_value_aud: 12499.99, percentage: 4.84 },
      { route: 'Residual / Disposal', weight_t: 44.0, gross_value_aud: 5500.03, percentage: 4.44 },
    ],
  },
  {
    id: 'batch_economics',
    title: '批次经济性',
    type: 'scatter',
    rows: [
      { batch_id: 'B001', source_type: 'Industrial Renewal', incoming_t: 32.9, processed_t: 32.9, gross_value_aud: 9546.11, cost_aud: 6792.78, net_value_aud: 2753.33, cost_per_t: 206.47, value_per_t: 290.16 },
      { batch_id: 'B002', source_type: 'Industrial Renewal', incoming_t: 46.7, processed_t: 46.7, gross_value_aud: 17389.47, cost_aud: 9741.18, net_value_aud: 7648.29, cost_per_t: 208.59, value_per_t: 372.37 },
      { batch_id: 'B003', source_type: 'Residential Demolition', incoming_t: 22.3, processed_t: 22.3, gross_value_aud: 4405.07, cost_aud: 4561.45, net_value_aud: -156.38, cost_per_t: 204.55, value_per_t: 197.54 },
      { batch_id: 'B004', source_type: 'Warehouse Deconstruction', incoming_t: 38.2, processed_t: 38.2, gross_value_aud: 11084.46, cost_aud: 7912.91, net_value_aud: 3171.55, cost_per_t: 207.14, value_per_t: 290.17 },
      { batch_id: 'B005', source_type: 'Infrastructure Salvage', incoming_t: 32.9, processed_t: 32.9, gross_value_aud: 13550.45, cost_aud: 6768.9, net_value_aud: 6781.55, cost_per_t: 205.74, value_per_t: 411.87 },
      { batch_id: 'B006', source_type: 'Residential Demolition', incoming_t: 26.6, processed_t: 26.6, gross_value_aud: 6586.45, cost_aud: 5666.51, net_value_aud: 919.94, cost_per_t: 213.03, value_per_t: 247.61 },
      { batch_id: 'B007', source_type: 'Industrial Renewal', incoming_t: 40.4, processed_t: 40.4, gross_value_aud: 15043.63, cost_aud: 8392.62, net_value_aud: 6651.01, cost_per_t: 207.74, value_per_t: 372.37 },
      { batch_id: 'B008', source_type: 'Warehouse Deconstruction', incoming_t: 25.5, processed_t: 25.5, gross_value_aud: 7398.89, cost_aud: 5240.91, net_value_aud: 2157.98, cost_per_t: 205.53, value_per_t: 290.15 },
      { batch_id: 'B009', source_type: 'Warehouse Deconstruction', incoming_t: 19.1, processed_t: 19.1, gross_value_aud: 5457.51, cost_aud: 4101.65, net_value_aud: 1355.86, cost_per_t: 214.75, value_per_t: 285.73 },
      { batch_id: 'B010', source_type: 'Commercial Demolition', incoming_t: 36.1, processed_t: 36.1, gross_value_aud: 15590.84, cost_aud: 7562.65, net_value_aud: 8028.19, cost_per_t: 209.49, value_per_t: 431.88 },
      { batch_id: 'B011', source_type: 'Residential Demolition', incoming_t: 32.9, processed_t: 32.9, gross_value_aud: 6498.6, cost_aud: 6765.06, net_value_aud: -266.46, cost_per_t: 205.62, value_per_t: 197.53 },
      { batch_id: 'B012', source_type: 'Direct Salvage Purchase', incoming_t: 27.6, processed_t: 27.6, gross_value_aud: 8008.29, cost_aud: 5680.02, net_value_aud: 2328.27, cost_per_t: 205.8, value_per_t: 290.16 },
      { batch_id: 'B013', source_type: 'Infrastructure Salvage', incoming_t: 48.9, processed_t: 48.9, gross_value_aud: 20140.36, cost_aud: 10142.89, net_value_aud: 9997.47, cost_per_t: 207.42, value_per_t: 411.87 },
      { batch_id: 'B014', source_type: 'Direct Salvage Purchase', incoming_t: 21.2, processed_t: 21.2, gross_value_aud: 6151.22, cost_aud: 4345.54, net_value_aud: 1805.68, cost_per_t: 204.98, value_per_t: 290.15 },
      { batch_id: 'B015', source_type: 'Industrial Renewal', incoming_t: 35.0, processed_t: 35.0, gross_value_aud: 13032.88, cost_aud: 7245.33, net_value_aud: 5787.55, cost_per_t: 207.01, value_per_t: 372.37 },
      { batch_id: 'B016', source_type: 'Commercial Demolition', incoming_t: 37.2, processed_t: 37.2, gross_value_aud: 16065.91, cost_aud: 7801.19, net_value_aud: 8264.72, cost_per_t: 209.71, value_per_t: 431.88 },
      { batch_id: 'B017', source_type: 'Residential Demolition', incoming_t: 44.6, processed_t: 44.6, gross_value_aud: 11043.41, cost_aud: 9755.31, net_value_aud: 1288.1, cost_per_t: 218.73, value_per_t: 247.61 },
      { batch_id: 'B018', source_type: 'Commercial Demolition', incoming_t: 25.5, processed_t: 25.5, gross_value_aud: 7398.89, cost_aud: 5240.91, net_value_aud: 2157.98, cost_per_t: 205.53, value_per_t: 290.15 },
      { batch_id: 'B019', source_type: 'Residential Demolition', incoming_t: 31.9, processed_t: 31.9, gross_value_aud: 6301.36, cost_aud: 6556.19, net_value_aud: -254.83, cost_per_t: 205.52, value_per_t: 197.53 },
      { batch_id: 'B020', source_type: 'Warehouse Deconstruction', incoming_t: 28.7, processed_t: 28.7, gross_value_aud: 8327.61, cost_aud: 5910.33, net_value_aud: 2417.28, cost_per_t: 205.93, value_per_t: 290.16 },
      { batch_id: 'B021', source_type: 'Industrial Renewal', incoming_t: 45.7, processed_t: 45.7, gross_value_aud: 17017.4, cost_aud: 9526.38, net_value_aud: 7491.02, cost_per_t: 208.45, value_per_t: 372.37 },
      { batch_id: 'B022', source_type: 'Infrastructure Salvage', incoming_t: 39.3, processed_t: 39.3, gross_value_aud: 16186.27, cost_aud: 8112.03, net_value_aud: 8074.24, cost_per_t: 206.41, value_per_t: 411.86 },
      { batch_id: 'B023', source_type: 'Residential Demolition', incoming_t: 26.6, processed_t: 26.6, gross_value_aud: 6586.45, cost_aud: 5666.51, net_value_aud: 919.94, cost_per_t: 213.03, value_per_t: 247.61 },
      { batch_id: 'B024', source_type: 'Commercial Demolition', incoming_t: 32.9, processed_t: 32.9, gross_value_aud: 9546.11, cost_aud: 6792.79, net_value_aud: 2753.32, cost_per_t: 206.47, value_per_t: 290.16 },
      { batch_id: 'B025', source_type: 'Commercial Demolition', incoming_t: 35.0, processed_t: 35.0, gross_value_aud: 15116.11, cost_aud: 7324.53, net_value_aud: 7791.58, cost_per_t: 209.27, value_per_t: 431.89 },
      { batch_id: 'B026', source_type: 'Warehouse Deconstruction', incoming_t: 24.4, processed_t: 24.4, gross_value_aud: 6971.62, cost_aud: 5308.72, net_value_aud: 1662.9, cost_per_t: 217.57, value_per_t: 285.72 },
      { batch_id: 'B027', source_type: 'Direct Salvage Purchase', incoming_t: 34.0, processed_t: 34.0, gross_value_aud: 9918.98, cost_aud: 7303.8, net_value_aud: 2615.18, cost_per_t: 214.82, value_per_t: 291.73 },
      { batch_id: 'B028', source_type: 'Residential Demolition', incoming_t: 41.4, processed_t: 41.4, gross_value_aud: 8177.86, cost_aud: 8548.68, net_value_aud: -370.82, cost_per_t: 206.49, value_per_t: 197.53 },
      { batch_id: 'B029', source_type: 'Industrial Renewal', incoming_t: 23.4, processed_t: 23.4, gross_value_aud: 8713.31, cost_aud: 4807.37, net_value_aud: 3905.94, cost_per_t: 205.44, value_per_t: 372.36 },
      { batch_id: 'B030', source_type: 'Direct Salvage Purchase', incoming_t: 80.0, processed_t: 0.0, gross_value_aud: 0.0, cost_aud: 7680.0, net_value_aud: -7680.0, cost_per_t: 96.0, value_per_t: 0.0 },
      { batch_id: 'B031', source_type: 'Commercial Demolition', incoming_t: 35.1, processed_t: 35.1, gross_value_aud: 10184.52, cost_aud: 7256.86, net_value_aud: 2927.66, cost_per_t: 206.75, value_per_t: 290.16 },
      { batch_id: 'B032', source_type: 'Infrastructure Salvage', incoming_t: 34.1, processed_t: 0.0, gross_value_aud: 0.0, cost_aud: 3273.6, net_value_aud: -3273.6, cost_per_t: 96.0, value_per_t: 0.0 },
      { batch_id: 'B033', source_type: 'Direct Salvage Purchase', incoming_t: 12.4, processed_t: 0.0, gross_value_aud: 0.0, cost_aud: 1190.4, net_value_aud: -1190.4, cost_per_t: 96.0, value_per_t: 0.0 },
      { batch_id: 'B034', source_type: 'Warehouse Deconstruction', incoming_t: 75.0, processed_t: 0.0, gross_value_aud: 0.0, cost_aud: 7200.0, net_value_aud: -7200.0, cost_per_t: 96.0, value_per_t: 0.0 },
      { batch_id: 'B035', source_type: 'Residential Demolition', incoming_t: 34.1, processed_t: 0.0, gross_value_aud: 0.0, cost_aud: 3273.6, net_value_aud: -3273.6, cost_per_t: 96.0, value_per_t: 0.0 },
      { batch_id: 'B036', source_type: 'Commercial Demolition', incoming_t: 12.4, processed_t: 0.0, gross_value_aud: 0.0, cost_aud: 1190.4, net_value_aud: -1190.4, cost_per_t: 96.0, value_per_t: 0.0 },
    ],
  },
  {
    id: 'source_distribution',
    title: '来源结构',
    type: 'bar',
    rows: [
      { key: 'Residential Demolition', count: 8, weight_t: 260.4 },
      { key: 'Industrial Renewal', count: 6, weight_t: 224.1 },
      { key: 'Commercial Demolition', count: 7, weight_t: 214.2 },
      { key: 'Warehouse Deconstruction', count: 6, weight_t: 210.9 },
      { key: 'Direct Salvage Purchase', count: 5, weight_t: 175.2 },
      { key: 'Infrastructure Salvage', count: 4, weight_t: 155.2 },
    ],
  },
  {
    id: 'species_distribution',
    title: '物料组成',
    type: 'bar',
    rows: [
      { key: 'Unknown / Mixed', count: 225, weight_t: 198.17 },
      { key: 'Oregon', count: 151, weight_t: 161.95 },
      { key: 'Cypress Pine', count: 157, weight_t: 157.16 },
      { key: 'Radiata Pine', count: 131, weight_t: 124.41 },
      { key: 'Ironbark', count: 84, weight_t: 93.84 },
      { key: 'Spotted Gum', count: 83, weight_t: 91.44 },
      { key: 'Mountain Ash', count: 93, weight_t: 91.37 },
      { key: 'Blackbutt', count: 81, weight_t: 90.69 },
      { key: 'Sydney Blue Gum', count: 84, weight_t: 84.83 },
      { key: 'Mixed Hardwood', count: 86, weight_t: 80.52 },
      { key: 'Messmate', count: 90, weight_t: 65.62 },
    ],
  },
  {
    id: 'material_state',
    title: '物料状态',
    type: 'pie',
    rows: [
      { key: 'Output', count: 1018, weight_t: 992.0 },
      { key: 'In Progress', count: 155, weight_t: 155.0 },
      { key: 'Pending Processing', count: 68, weight_t: 68.2 },
      { key: 'Unresolved', count: 24, weight_t: 24.8 },
    ],
  },
];

// Row counts of the bundled sample dataset (`data/workbench.db`).
const TABLE_COUNTS: Record<string, number> = {
  SourceProjects: 16,
  Batches: 36,
  Materials: 1265,
  RecoveryOutputs: 270,
  CostLedger: 162,
  ProcessingEvents: 195,
  InspectionEvents: 490,
};
const TOTAL_ROWS = 2434;

export function mockDashboard(): DashboardResponse {
  return {
    meta: {
      dataset_type: 'timber',
      currency: 'AUD',
      weight_unit: 't',
      empty: false,
      tables: TABLE_COUNTS,
      total_rows: TOTAL_ROWS,
      last_upload: {
        upload_id: 'demo_inspectionevents',
        table_name: 'InspectionEvents',
        row_count: 490,
        created_at: '2026-08-24 15:36:31',
      },
    },
    filters: {},
    dimensions: mockDimensions(),
    kpis: KPIS,
    charts: CHARTS,
  };
}

function endpoint(
  method: string,
  path: string,
  summary: string,
  fields: ApiEndpoint['fields'],
  example: string,
): ApiEndpoint {
  return { method, path, summary, content_type: 'application/json', fields, example };
}

export function mockMeta(): MetaResponse {
  return {
    dataset: {
      tables: TABLE_COUNTS,
      total_rows: TOTAL_ROWS,
      last_upload: {
        upload_id: 'demo_inspectionevents',
        table_name: 'InspectionEvents',
        row_count: 490,
        created_at: '2026-08-24 15:36:31',
      },
    },
    api_reference: [
      endpoint(
        'GET',
        '/api/new/dashboard',
        '数据看板（支持维度筛选查询参数）',
        [
          { name: 'source_type', type: 'string', required: false, description: '来源类型，如 Residential Demolition' },
          { name: 'region', type: 'string', required: false, description: '区域' },
          { name: 'species', type: 'string', required: false, description: '树种' },
          { name: 'recovery_route', type: 'string', required: false, description: '回收去向' },
          { name: 'period_start', type: 'date', required: false, description: '起始日期' },
          { name: 'period_end', type: 'date', required: false, description: '结束日期' },
        ],
        'curl -X GET "http://127.0.0.1:8100/api/new/dashboard?source_type=Residential%20Demolition"',
      ),
      endpoint(
        'POST',
        '/api/new/upload/csv',
        '上传 CSV 到指定表',
        [
          { name: 'file', type: 'file', required: true, description: 'UTF-8 编码的 CSV，首行为表头' },
          { name: 'table', type: 'string', required: true, description: '目标表名，如 Batches' },
          { name: 'mode', type: 'string', required: true, description: 'append（默认，按主键 upsert）或 replace（清空后写入）' },
        ],
        'curl -X POST "http://127.0.0.1:8100/api/new/upload/csv" -F "file=@batches.csv" -F "table=Batches" -F "mode=append"',
      ),
      endpoint(
        'POST',
        '/api/new/upload/json',
        '上传 JSON 行数据到指定表',
        [
          { name: 'file', type: 'file', required: true, description: 'JSON 文件：{"rows": [...]} 或直接是行数组' },
          { name: 'table', type: 'string', required: true, description: '目标表名' },
          { name: 'mode', type: 'string', required: true, description: '写入模式' },
        ],
        'curl -X POST "http://127.0.0.1:8100/api/new/upload/json" -F "file=@rows.json" -F "table=Materials" -F "mode=append"',
      ),
      endpoint(
        'POST',
        '/api/new/upload/bundle',
        '上传多表 JSON bundle',
        [{ name: 'file', type: 'file', required: true, description: '多表 JSON bundle' }],
        'curl -X POST "http://127.0.0.1:8100/api/new/upload/bundle" -F "file=@bundle.json"',
      ),
      endpoint(
        'POST',
        '/api/new/demo',
        '载入合成示例数据（可选，非预设）',
        [{ name: 'mode', type: 'string', required: false, description: 'append 或 replace' }],
        'curl -X POST "http://127.0.0.1:8100/api/new/demo?mode=append"',
      ),
      endpoint(
        'POST',
        '/api/new/ai/chat',
        'AI 对话（基于已上传数据的问答）',
        [
          { name: 'messages', type: 'json', required: true, description: '对话消息数组' },
          { name: 'conversation_id', type: 'string', required: false, description: '会话 ID（可选）' },
        ],
        'curl -X POST "http://127.0.0.1:8100/api/new/ai/chat" -H "Content-Type: application/json" -d \'{"messages":[{"role":"user","content":"总入库量是多少？"}]}\'',
      ),
      endpoint(
        'POST',
        '/api/new/ai/test',
        '测试 AI 服务连接',
        [{ name: 'api_key', type: 'string', required: false, description: '可选，覆盖服务端配置' }],
        'curl -X POST "http://127.0.0.1:8100/api/new/ai/test"',
      ),
    ],
  };
}

export function mockHealth() {
  return {
    status: 'ok',
    database: 'sqlite',
    dataset_type: 'timber',
    total_rows: TOTAL_ROWS,
  };
}

export function mockUploadTables(): TableSchemaInfo[] {
  return [
    {
      table_name: 'SourceProjects',
      primary_key: 'project_id',
      columns: [
        { name: 'project_id', type: 'string', nullable: false, required: true },
        { name: 'source_type', type: 'string', nullable: false, required: true },
        { name: 'region', type: 'string', nullable: true, required: false },
        { name: 'contact', type: 'string', nullable: true, required: false },
      ],
    },
    {
      table_name: 'Batches',
      primary_key: 'batch_id',
      columns: [
        { name: 'batch_id', type: 'string', nullable: false, required: true },
        { name: 'project_id', type: 'string', nullable: false, required: true },
        { name: 'arrival_date', type: 'date', nullable: false, required: true },
        { name: 'species', type: 'string', nullable: true, required: false },
        { name: 'incoming_t', type: 'float', nullable: false, required: true },
        { name: 'batch_status', type: 'string', nullable: false, required: true },
      ],
    },
    {
      table_name: 'Materials',
      primary_key: 'material_id',
      columns: [
        { name: 'material_id', type: 'string', nullable: false, required: true },
        { name: 'batch_id', type: 'string', nullable: false, required: true },
        { name: 'material_form', type: 'string', nullable: false, required: true },
        { name: 'weight_t', type: 'float', nullable: false, required: true },
        { name: 'current_stage', type: 'string', nullable: false, required: true },
      ],
    },
    {
      table_name: 'RecoveryOutputs',
      primary_key: 'output_id',
      columns: [
        { name: 'output_id', type: 'string', nullable: false, required: true },
        { name: 'material_id', type: 'string', nullable: false, required: true },
        { name: 'recovery_route', type: 'string', nullable: false, required: true },
        { name: 'weight_t', type: 'float', nullable: false, required: true },
        { name: 'gross_value', type: 'float', nullable: true, required: false },
      ],
    },
    {
      table_name: 'CostLedger',
      primary_key: 'cost_id',
      columns: [
        { name: 'cost_id', type: 'string', nullable: false, required: true },
        { name: 'batch_id', type: 'string', nullable: false, required: true },
        { name: 'cost_category', type: 'string', nullable: false, required: true },
        { name: 'amount', type: 'float', nullable: false, required: true },
      ],
    },
    {
      table_name: 'ProcessingEvents',
      primary_key: 'event_id',
      columns: [
        { name: 'event_id', type: 'string', nullable: false, required: true },
        { name: 'batch_id', type: 'string', nullable: false, required: true },
        { name: 'stage', type: 'string', nullable: false, required: true },
        { name: 'timestamp', type: 'datetime', nullable: false, required: true },
      ],
    },
    {
      table_name: 'InspectionEvents',
      primary_key: 'inspection_id',
      columns: [
        { name: 'inspection_id', type: 'string', nullable: false, required: true },
        { name: 'material_id', type: 'string', nullable: false, required: true },
        { name: 'result', type: 'string', nullable: false, required: true },
        { name: 'inspector', type: 'string', nullable: true, required: false },
      ],
    },
  ];
}
