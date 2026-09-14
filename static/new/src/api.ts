import type {
  AISettings,
  ApiEndpoint,
  ChatMessage,
  ChatResponse,
  ConnectionTestResult,
  DashboardResponse,
  Filters,
  MetaResponse,
  TableSchemaInfo,
  UploadResult,
} from './types';
import { mockDashboard, mockMeta, mockHealth, mockUploadTables, mockDimensions } from './mock';

const BASE = '/api';

// Static-prototype mode: when true, the frontend serves bundled mock data so the
// demo runs with no backend. Flip to false (and rebuild) to talk to a real API.
const USE_MOCK = true;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === 'string') detail = body.detail;
      else if (body.detail && typeof body.detail.message === 'string') detail = body.detail.message;
      else if (body.message) detail = body.message;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

function qs(filters: Filters): string {
  const params = new URLSearchParams();
  (Object.keys(filters) as (keyof Filters)[]).forEach((k) => {
    const v = filters[k];
    if (v) params.set(k, v);
  });
  const s = params.toString();
  return s ? `?${s}` : '';
}

export const api = {
  dashboard(filters: Filters = {}): Promise<DashboardResponse> {
    if (USE_MOCK) return Promise.resolve(mockDashboard());
    return request(`/new/dashboard${qs(filters)}`);
  },
  dimensions(): Promise<DashboardResponse['dimensions']> {
    if (USE_MOCK) return Promise.resolve(mockDimensions());
    return request('/new/dashboard/dimensions');
  },
  meta(): Promise<MetaResponse> {
    if (USE_MOCK) return Promise.resolve(mockMeta());
    return request('/new/meta');
  },
  uploadTables(): Promise<TableSchemaInfo[]> {
    if (USE_MOCK) return Promise.resolve(mockUploadTables());
    return request('/new/upload/tables');
  },
  uploadCsv(file: File, table: string, mode: string): Promise<UploadResult> {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('table', table);
    fd.append('mode', mode);
    return request('/new/upload/csv', { method: 'POST', body: fd });
  },
  uploadJson(file: File, table: string, mode: string): Promise<UploadResult> {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('table', table);
    fd.append('mode', mode);
    return request('/new/upload/json', { method: 'POST', body: fd });
  },
  uploadBundle(file: File): Promise<UploadResult> {
    const fd = new FormData();
    fd.append('file', file);
    return request('/new/upload/bundle', { method: 'POST', body: fd });
  },
  loadDemo(mode: 'append' | 'replace' = 'append'): Promise<{ loaded: boolean; message: string; tables?: { table: string; rows: number }[] }> {
    return request(`/new/demo?mode=${mode}`, { method: 'POST' });
  },
  health(): Promise<{ status: string; database: string; dataset_type: string; total_rows: number }> {
    if (USE_MOCK) return Promise.resolve(mockHealth());
    return request('/new/health');
  },
  getAiSettings(): Promise<AISettings> {
    return request('/new/ai/settings');
  },
  saveAiSettings(payload: { enabled: boolean; base_url: string; model: string; api_key?: string }): Promise<AISettings> {
    return request('/new/ai/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },
  testAiConnection(payload?: Partial<{ base_url: string; model: string; api_key: string }>): Promise<ConnectionTestResult> {
    return request('/new/ai/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload ?? {}),
    });
  },
  chat(messages: ChatMessage[], conversationId?: string | null): Promise<ChatResponse> {
    return request('/new/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, conversation_id: conversationId ?? undefined }),
    });
  },
  endpoint(method: string, path: string, body?: unknown): Promise<unknown> {
    const isGet = method.toUpperCase() === 'GET';
    return request(path.replace('/api', ''), {
      method,
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      ...(isGet ? {} : {}),
    });
  },
};

export function describeError(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

export const apiReferenceExamples: Record<string, ApiEndpoint[]> = {};
