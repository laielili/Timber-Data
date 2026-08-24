export interface Kpi {
  id: string;
  label: string;
  value: number;
  unit: string;
  basis: string;
  description: string;
}

export interface Chart {
  id: string;
  title: string;
  type: string;
  rows: Record<string, unknown>[];
}

export interface DashboardMeta {
  dataset_type: string;
  currency: string;
  weight_unit: string;
  empty: boolean;
  tables: Record<string, number>;
  total_rows: number;
  last_upload: { upload_id: string; table_name: string; row_count: number; created_at: string } | null;
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
  kpis: Kpi[];
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