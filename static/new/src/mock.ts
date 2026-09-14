// Static-prototype mock data.
//
// This module powers the standalone `docs/` build so the product can be demoed
// without a running backend. Wire it in via the `USE_MOCK` flag in api.ts:
// flip it to `false` to talk to a real backend again. Filters are acknowledged
// but the dataset is intentionally static for the prototype.

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
  'Residential Demolition',
  'Commercial Strip-out',
  'Construction Offcut',
  'Pallet & Crate',
  'Orchard Removal',
];
const REGIONS = ['North', 'South', 'East', 'West', 'Central'];
const SPECIES = ['Pine', 'Hardwood Mix', 'Oregon', 'Plywood', 'MDF'];
const MATERIAL_FORMS = ['Beam', 'Board', 'Pallet', 'Crate', 'Offcut'];
const RECOVERY_ROUTES = ['Reuse', 'Mulch', 'Bioenergy', 'Panel Product', 'Landfill'];
const BATCH_STATUSES = ['Received', 'Sorted', 'Processing', 'Recovered', 'Unresolved'];
const CURRENT_STAGES = ['Intake', 'Assessment', 'Processing', 'Dispatch', 'Unresolved'];

export function mockDimensions(): Dimensions {
  return {
    period_start: '2026-01-01',
    period_end: '2026-08-31',
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
    id: 'kpi_incoming',
    label: '入库量',
    value: 1286.4,
    unit: 't',
    basis: '期间内到达批次',
    description: '所选维度下，期间内到达批次的总入库重量。',
  },
  {
    id: 'kpi_processed',
    label: '处理量',
    value: 1042.7,
    unit: 't',
    basis: '期间内产出',
    description: '所选维度下，期间内回收产出的总重量。',
  },
  {
    id: 'kpi_hvrr',
    label: '高值回收率',
    value: 63.2,
    unit: '%',
    basis: '快照',
    description: '所选维度下，期间内产出中高值回收去向的重量占比。',
  },
  {
    id: 'kpi_value',
    label: '回收价值/吨',
    value: 184.5,
    unit: '¥/t',
    basis: '快照',
    description: '毛回收价值 / 处理量。',
  },
  {
    id: 'kpi_cost',
    label: '成本/吨',
    value: 92.3,
    unit: '¥/t',
    basis: '快照',
    description: '成本台账总成本 / 处理量。',
  },
  {
    id: 'kpi_unresolved',
    label: '未解决物料',
    value: 38.6,
    unit: 't',
    basis: '快照',
    description: '快照：状态为 Unresolved 的物料总重量。',
  },
];

const CHARTS: Chart[] = [
  {
    id: 'chart_monthly',
    title: '月度趋势',
    type: 'bar',
    rows: [
      { month: '2026-01', incoming_t: 142, processed_t: 118, recovery_value: 21.6 },
      { month: '2026-02', incoming_t: 158, processed_t: 129, recovery_value: 23.8 },
      { month: '2026-03', incoming_t: 171, processed_t: 140, recovery_value: 26.1 },
      { month: '2026-04', incoming_t: 165, processed_t: 134, recovery_value: 24.7 },
      { month: '2026-05', incoming_t: 183, processed_t: 149, recovery_value: 27.9 },
      { month: '2026-06', incoming_t: 172, processed_t: 141, recovery_value: 25.9 },
      { month: '2026-07', incoming_t: 161, processed_t: 132, recovery_value: 24.3 },
      { month: '2026-08', incoming_t: 134, processed_t: 99, recovery_value: 18.2 },
    ],
  },
  {
    id: 'chart_routes',
    title: '回收去向分布',
    type: 'pie',
    rows: [
      { key: 'Reuse', weight_t: 412.3 },
      { key: 'Mulch', weight_t: 268.1 },
      { key: 'Bioenergy', weight_t: 191.5 },
      { key: 'Panel Product', weight_t: 130.8 },
      { key: 'Landfill', weight_t: 40.0 },
    ],
  },
  {
    id: 'chart_econ',
    title: '批次经济性',
    type: 'scatter',
    rows: [
      { cost_per_t: 88, value_per_t: 176, incoming_t: 42 },
      { cost_per_t: 102, value_per_t: 151, incoming_t: 58 },
      { cost_per_t: 79, value_per_t: 203, incoming_t: 35 },
      { cost_per_t: 115, value_per_t: 138, incoming_t: 61 },
      { cost_per_t: 94, value_per_t: 189, incoming_t: 47 },
      { cost_per_t: 71, value_per_t: 221, incoming_t: 29 },
      { cost_per_t: 108, value_per_t: 144, incoming_t: 53 },
      { cost_per_t: 85, value_per_t: 198, incoming_t: 44 },
    ],
  },
  {
    id: 'chart_sources',
    title: '来源结构',
    type: 'bar',
    rows: [
      { key: 'Residential Demolition', weight_t: 486.2 },
      { key: 'Commercial Strip-out', weight_t: 312.4 },
      { key: 'Construction Offcut', weight_t: 201.8 },
      { key: 'Pallet & Crate', weight_t: 88.5 },
      { key: 'Orchard Removal', weight_t: 57.3 },
    ],
  },
  {
    id: 'chart_materials',
    title: '物料组成',
    type: 'pie',
    rows: [
      { key: 'Beam', weight_t: 298.4 },
      { key: 'Board', weight_t: 256.1 },
      { key: 'Pallet', weight_t: 142.7 },
      { key: 'Crate', weight_t: 98.3 },
      { key: 'Offcut', weight_t: 247.2 },
    ],
  },
  {
    id: 'chart_status',
    title: '物料状态',
    type: 'bar',
    rows: [
      { key: 'Received', weight_t: 184.2 },
      { key: 'Sorted', weight_t: 256.8 },
      { key: 'Processing', weight_t: 312.5 },
      { key: 'Recovered', weight_t: 509.6 },
      { key: 'Unresolved', weight_t: 38.6 },
    ],
  },
];

export function mockDashboard(): DashboardResponse {
  return {
    meta: {
      dataset_type: 'timber',
      currency: 'CNY',
      weight_unit: 't',
      empty: false,
      tables: {
        SourceProjects: 5,
        Batches: 36,
        Materials: 1239,
        RecoveryOutputs: 612,
        CostLedger: 318,
        ProcessingEvents: 894,
        InspectionEvents: 277,
      },
      total_rows: 3381,
      last_upload: {
        upload_id: 'u_20260831',
        table_name: 'Batches',
        row_count: 36,
        created_at: '2026-08-31T09:14:00',
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
      tables: {
        SourceProjects: 5,
        Batches: 36,
        Materials: 1239,
        RecoveryOutputs: 612,
        CostLedger: 318,
        ProcessingEvents: 894,
        InspectionEvents: 277,
      },
      total_rows: 3381,
      last_upload: {
        upload_id: 'u_20260831',
        table_name: 'Batches',
        row_count: 36,
        created_at: '2026-08-31T09:14:00',
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
    total_rows: 3381,
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
