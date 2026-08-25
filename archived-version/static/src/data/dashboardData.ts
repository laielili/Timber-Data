// Data access layer.
// UI components never touch file paths or raw JSON directly — they consume the typed
// DashboardData produced by a DashboardDataSource. Two interchangeable implementations:
//   - MockDashboardDataSource (local /data/*.json — offline demo / regression)
//   - ApiDashboardDataSource (FastAPI analytics service — primary integrated mode)
// createDashboardDataSource() selects the mode from VITE_DATA_SOURCE.
// The future Python/FastAPI backend replaces the mock without visual changes.

import { useEffect, useState } from 'react';
import type {
  BatchList,
  ManagementReportData,
  Meta,
  MonthlyPerformance,
  OverviewResponse,
  SingleBatch,
  SourcePerformanceList,
} from '../types/contract';
import { apiGet } from './apiClient';
import { assertManagementBriefResponse, assertOverviewResponse, assertSingleBatchResponse } from './validateContract';

/** AI Management Brief item — structured payload served by the data layer.
 *  React components only render this object; no business logic is derived in the UI. */
export interface ManagementBriefItem {
  id: string;
  title: string;
  detail: string;
  severity: 'attention' | 'positive' | 'neutral';
  related_batch_id: string | null;
  question_id: string | null;
  basis: 'selected_period' | 'snapshot' | 'comparison_period';
  values: Record<string, number | string | null>;
}

export interface ManagementBriefPayload {
  meta: Meta;
  briefs: ManagementBriefItem[];
}

export interface DashboardData {
  meta: Meta;
  overview: OverviewResponse;
  batchList: BatchList;
  singleBatches: Record<string, SingleBatch>;
  sourcePerformance: SourcePerformanceList;
  monthlyPerformance: MonthlyPerformance;
  managementReport: ManagementReportData;
  managementBrief: ManagementBriefPayload;
}

export interface DashboardDataSource {
  fetchAll(): Promise<DashboardData>;
}

const SINGLE_BATCH_IDS = ['B017', 'B022', 'B030'] as const;

/** Reads the approved mock JSON from the static data directory. */
export class MockDashboardDataSource implements DashboardDataSource {
  constructor(private readonly baseUrl = '/data') {}

  private async get<T>(file: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}/${file}`);
    if (!res.ok) {
      throw new Error(`Failed to load ${file} (HTTP ${res.status})`);
    }
    return (await res.json()) as T;
  }

  async fetchAll(): Promise<DashboardData> {
    const [overview, batchList, sourcePerformance, monthlyPerformance, managementReport, managementBrief] =
      await Promise.all([
        this.get<OverviewResponse>('overview.json'),
        this.get<BatchList>('batch_list.json'),
        this.get<SourcePerformanceList>('source_performance.json'),
        this.get<MonthlyPerformance>('monthly_performance.json'),
        this.get<ManagementReportData>('management_report_data.json'),
        this.get<ManagementBriefPayload>('management_brief.json'),
      ]);

    const singleEntries = await Promise.all(
      SINGLE_BATCH_IDS.map(async (id) => {
        const single = await this.get<SingleBatch>(`batch_${id}.json`);
        return [id, single] as const;
      }),
    );
    const singleBatches: Record<string, SingleBatch> = Object.fromEntries(singleEntries);

    return {
      meta: overview.meta,
      overview,
      batchList,
      singleBatches,
      sourcePerformance,
      monthlyPerformance,
      managementReport,
      managementBrief,
    };
  }
}

/** Reads the same DashboardData shape from the FastAPI analytics service.
 *  Parallel requests; runtime-validates the critical responses; no mock fallback —
 *  failures surface as clear integration errors. */
export class ApiDashboardDataSource implements DashboardDataSource {
  constructor(private readonly baseUrl: string) {}

  async fetchAll(): Promise<DashboardData> {
    const [overview, managementBrief, batchList, sourcePerformance, monthlyPerformance, managementReport] =
      await Promise.all([
        apiGet<OverviewResponse>('/api/v1/overview', { baseUrl: this.baseUrl }),
        apiGet<ManagementBriefPayload>('/api/v1/management-brief', { baseUrl: this.baseUrl }),
        apiGet<BatchList>('/api/v1/batches', { baseUrl: this.baseUrl }),
        apiGet<SourcePerformanceList>('/api/v1/source-performance', { baseUrl: this.baseUrl }),
        apiGet<MonthlyPerformance>('/api/v1/monthly-performance', { baseUrl: this.baseUrl }),
        apiGet<ManagementReportData>('/api/v1/management-report-data', { baseUrl: this.baseUrl }),
      ]);

    // runtime validation of the critical responses (compile-time types don't check JSON)
    assertOverviewResponse(overview);
    assertManagementBriefResponse(managementBrief);

    const singleEntries = await Promise.all(
      SINGLE_BATCH_IDS.map(async (id) => {
        const single = await apiGet<SingleBatch>(`/api/v1/batches/${id}`, { baseUrl: this.baseUrl });
        assertSingleBatchResponse(single);
        return [id, single] as const;
      }),
    );
    const singleBatches: Record<string, SingleBatch> = Object.fromEntries(singleEntries);

    return {
      meta: overview.meta,
      overview,
      batchList,
      singleBatches,
      sourcePerformance,
      monthlyPerformance,
      managementReport,
      managementBrief,
    };
  }
}

type DataSourceEnv = Record<string, string | undefined> & {
  VITE_DATA_SOURCE?: string;
  VITE_API_BASE_URL?: string;
};

/** Environment-driven factory: VITE_DATA_SOURCE=api → FastAPI; otherwise mock. */
export function createDashboardDataSource(env: DataSourceEnv = import.meta.env): DashboardDataSource {
  if (env.VITE_DATA_SOURCE === 'api') {
    const baseUrl = env.VITE_API_BASE_URL ?? 'http://localhost:8000';
    return new ApiDashboardDataSource(baseUrl);
  }
  return new MockDashboardDataSource();
}

export interface LoadState {
  data: DashboardData | null;
  loading: boolean;
  error: Error | null;
}

const DEFAULT_SOURCE: DashboardDataSource = createDashboardDataSource();

export function useDashboardData(source: DashboardDataSource = DEFAULT_SOURCE): LoadState {
  const [state, setState] = useState<LoadState>({ data: null, loading: true, error: null });

  useEffect(() => {
    let alive = true;
    setState({ data: null, loading: true, error: null });
    source
      .fetchAll()
      .then((data) => alive && setState({ data, loading: false, error: null }))
      .catch((err: unknown) => {
        if (alive) {
          setState({ data: null, loading: false, error: err instanceof Error ? err : new Error(String(err)) });
        }
      });
    return () => {
      alive = false;
    };
  }, [source]);

  return state;
}
