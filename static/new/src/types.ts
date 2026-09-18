export interface Kpi {
  id: string;
  label: string;
  value: number;
  unit: string;
  /** Names the tonne denominator (per processed t for value, per incoming t for cost). */
  basis: string;
  description: string;
  /** s1 value | s2 cost | s3 conversion */
  group: string;
  group_label: string;
  /** Monthly series for the card sparkline. Empty for snapshot metrics. */
  trend: number[];
}

/** M0 — the one number every other metric has to explain. */
export interface NorthStar {
  id: string;
  label: string;
  value: number;
  unit: string;
  net_value_aud: number;
  incoming_t: number;
  processed_t: number;
  basis: string;
  description: string;
  identity: string;
  expression: {
    value_per_processed_t: number;
    processing_rate: number;
    cost_per_incoming_t: number;
  };
}

/** A counterweight metric: blocks a specific way of inflating the North Star. */
export interface Guardrail {
  id: string;
  label: string;
  value: number;
  unit: string;
  basis: string;
  /** ok 正常 | warn 预警 | severe 严重 */
  level: 'ok' | 'warn' | 'severe';
  description: string;
}

export interface ChartColumn {
  key: string;
  label: string;
  type: string;
  /** money | weight | per_t — drives decimal precision in matrix tables. */
  format?: string;
}

export interface Chart {
  id: string;
  title: string;
  type: string;
  /** matrix (reconciliation table) | drivers (identity decomposition) | slices (endowment) */
  group: string;
  rows: Record<string, unknown>[];
  bars?: string[];
  lines?: string[];
  dual_axis?: boolean;
  /** Legend text per series key, so raw column names never reach the reader. */
  series_labels?: Record<string, string>;
  columns?: ChartColumn[];
  note?: string;
  total?: Record<string, number>;
  output_wt?: number;
}

export interface LastUpload {
  upload_id: string;
  table_name: string;
  filename: string;
  mode: string;
  row_count: number;
  status: string;
  message: string;
  created_at: string;
}

export interface DashboardMeta {
  dataset_type: string;
  currency: string;
  weight_unit: string;
  empty: boolean;
  tables: Record<string, number>;
  total_rows: number;
  last_upload: LastUpload | null;
}

export interface Dimensions {
  period_start: string | null;
  period_end: string | null;
  source_types: string[];
  regions: string[];
  species: string[];
  material_forms: string[];
  recovery_routes: string[];
  batch_statuses: string[];
  current_stages: string[];
}

export interface Filters {
  period_start?: string;
  period_end?: string;
  source_type?: string;
  region?: string;
  species?: string;
  material_form?: string;
  recovery_route?: string;
  batch_status?: string;
  current_stage?: string;
}

export interface DashboardResponse {
  meta: DashboardMeta;
  filters: Filters;
  dimensions: Dimensions;
  north_star: NorthStar | null;
  kpis: Kpi[];
  guardrails: Guardrail[];
  charts: Chart[];
}

export interface TableColumn {
  name: string;
  type: string;
  nullable: boolean;
  required: boolean;
}

export interface TableSchemaInfo {
  table_name: string;
  primary_key: string;
  columns: TableColumn[];
}

export interface UploadResult {
  upload_id: string;
  table_name: string;
  filename: string;
  mode: string;
  row_count: number;
  status: string;
  message: string;
  errors: string[];
}

export interface ApiEndpoint {
  method: string;
  path: string;
  summary: string;
  content_type: string;
  fields: { name: string; type: string; required: boolean; description: string }[];
  example: string;
}

export interface MetaResponse {
  dataset: { tables: Record<string, number>; total_rows: number; last_upload: unknown };
  api_reference: ApiEndpoint[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  reply: string;
  conversation_id: string;
  tools_used: string[];
  model: string | null;
  provider: string | null;
}

export interface AISettings {
  enabled: boolean;
  provider: string;
  base_url: string;
  model: string;
  api_key_configured: boolean;
  source: string;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  code: string | null;
}