// Backend Phase 02 — integration tests for the data layer (vitest).
// 01-03: API data source loads overview / brief / B017.
// 04: API data source rejects HTTP failure (no silent fallback).
// 05: invalid backend response triggers contract failure.
// 06: mock mode still works.
// 07: API mode never falls back to mock (fetch failure → error; URLs are /api/v1 only).

import { afterEach, describe, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { ApiConnectionError, ApiContractError } from './apiClient';
import { ApiDashboardDataSource, MockDashboardDataSource, createDashboardDataSource } from './dashboardData';
import { assertOverviewResponse, assertManagementBriefResponse, assertSingleBatchResponse } from './validateContract';

// tests run from the frontend/ directory; mock JSON lives in the project root
const MOCK_DIR = resolve(process.cwd(), '..', 'data', 'mock');
const API_BASE = 'http://api.test:8000';

function loadFixture(name: string): unknown {
  return JSON.parse(readFileSync(resolve(MOCK_DIR, name), 'utf-8'));
}

/** Route a fetch URL to a fixture by filename, or throw when unknown.
 *  More specific fragments (longer) match first — e.g. /api/v1/batches/B017
 *  must win over /api/v1/batches. */
function fixtureFetch(files: Record<string, string>, fallbackUrl?: (url: string) => Response) {
  const sorted = Object.entries(files).sort((a, b) => b[0].length - a[0].length);
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    for (const [fragment, file] of sorted) {
      if (url.includes(fragment)) {
        return new Response(JSON.stringify(loadFixture(file)), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
    }
    if (fallbackUrl) return fallbackUrl(url);
    return new Response('{}', { status: 404 });
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('ApiDashboardDataSource', () => {
  it('01: loads Overview from the API (validated, typed)', async () => {
    vi.stubGlobal('fetch', fixtureFetch({
      '/api/v1/overview': 'overview.json',
      '/api/v1/management-brief': 'management_brief.json',
      '/api/v1/batches': 'batch_list.json',
      '/api/v1/source-performance': 'source_performance.json',
      '/api/v1/monthly-performance': 'monthly_performance.json',
      '/api/v1/management-report-data': 'management_report_data.json',
      '/api/v1/batches/B017': 'batch_B017.json',
      '/api/v1/batches/B022': 'batch_B022.json',
      '/api/v1/batches/B030': 'batch_B030.json',
    }));

    const ds = new ApiDashboardDataSource(API_BASE);
    const data = await ds.fetchAll();

    expect(data.overview.north_star.value).toBeCloseTo(85.08, 2);
    expect(data.overview.kpis.incoming_timber.value).toBe(1240);
    expect(data.overview.charts.batch_economics).toHaveLength(36);
    expect(data.meta.dataset_type).toBe('synthetic_prototype');
  });

  it('02: loads Management Brief from the API', async () => {
    vi.stubGlobal('fetch', fixtureFetch({
      '/api/v1/overview': 'overview.json',
      '/api/v1/management-brief': 'management_brief.json',
      '/api/v1/batches': 'batch_list.json',
      '/api/v1/source-performance': 'source_performance.json',
      '/api/v1/monthly-performance': 'monthly_performance.json',
      '/api/v1/management-report-data': 'management_report_data.json',
      '/api/v1/batches/B017': 'batch_B017.json',
      '/api/v1/batches/B022': 'batch_B022.json',
      '/api/v1/batches/B030': 'batch_B030.json',
    }));

    const data = await new ApiDashboardDataSource(API_BASE).fetchAll();
    expect(data.managementBrief.briefs).toHaveLength(3);
    expect(data.managementBrief.briefs[0].id).toBe('brief_batch_17');
    expect(data.managementBrief.briefs[1].values.inspection_backlog_growth_vs_nov_pct).toBeCloseTo(21.7, 1);
  });

  it('03: loads B017 single batch from the API', async () => {
    vi.stubGlobal('fetch', fixtureFetch({
      '/api/v1/overview': 'overview.json',
      '/api/v1/management-brief': 'management_brief.json',
      '/api/v1/batches': 'batch_list.json',
      '/api/v1/source-performance': 'source_performance.json',
      '/api/v1/monthly-performance': 'monthly_performance.json',
      '/api/v1/management-report-data': 'management_report_data.json',
      '/api/v1/batches/B017': 'batch_B017.json',
      '/api/v1/batches/B022': 'batch_B022.json',
      '/api/v1/batches/B030': 'batch_B030.json',
    }));

    const data = await new ApiDashboardDataSource(API_BASE).fetchAll();
    const b17 = data.singleBatches.B017?.batch;
    expect(b17?.economic_evaluation_status).toBe('Realised');
    expect(b17?.economic_quadrant).toBe('Review Required');
    expect(b17?.net_sorting_benefit_aud).toBeLessThan(0);
  });

  it('04: rejects an unreachable API (no silent mock fallback)', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => {
      throw new TypeError('fetch failed');
    }));
    await expect(new ApiDashboardDataSource(API_BASE).fetchAll()).rejects.toBeInstanceOf(ApiConnectionError);
  });

  it('05: invalid backend response triggers contract failure', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ hello: 'world' }), { status: 200 })));
    await expect(new ApiDashboardDataSource(API_BASE).fetchAll()).rejects.toBeInstanceOf(ApiContractError);
  });

  it('07: API mode only ever requests /api/v1/* (never /data/*)', async () => {
    const fetchMock = fixtureFetch({
      '/api/v1/overview': 'overview.json',
      '/api/v1/management-brief': 'management_brief.json',
      '/api/v1/batches': 'batch_list.json',
      '/api/v1/source-performance': 'source_performance.json',
      '/api/v1/monthly-performance': 'monthly_performance.json',
      '/api/v1/management-report-data': 'management_report_data.json',
      '/api/v1/batches/B017': 'batch_B017.json',
      '/api/v1/batches/B022': 'batch_B022.json',
      '/api/v1/batches/B030': 'batch_B030.json',
    });
    vi.stubGlobal('fetch', fetchMock);

    await new ApiDashboardDataSource(API_BASE).fetchAll();

    const urls = fetchMock.mock.calls.map((c) => String(c[0]));
    expect(urls.length).toBeGreaterThanOrEqual(9);
    expect(urls.every((u) => u.startsWith(API_BASE + '/api/v1/'))).toBe(true);
    expect(urls.some((u) => u.includes('/data/'))).toBe(false);
  });
});

describe('MockDashboardDataSource', () => {
  it('06: mock mode still loads the full DashboardData shape', async () => {
    vi.stubGlobal('fetch', fixtureFetch({
      '/data/overview.json': 'overview.json',
      '/data/batch_list.json': 'batch_list.json',
      '/data/source_performance.json': 'source_performance.json',
      '/data/monthly_performance.json': 'monthly_performance.json',
      '/data/management_report_data.json': 'management_report_data.json',
      '/data/management_brief.json': 'management_brief.json',
      '/data/batch_B017.json': 'batch_B017.json',
      '/data/batch_B022.json': 'batch_B022.json',
      '/data/batch_B030.json': 'batch_B030.json',
    }));

    const data = await new MockDashboardDataSource('/data').fetchAll();
    expect(data.overview.kpis.processed_timber.value).toBeCloseTo(1013.365, 3);
    expect(Object.keys(data.singleBatches)).toEqual(['B017', 'B022', 'B030']);
  });
});

describe('createDashboardDataSource', () => {
  it('selects api mode from VITE_DATA_SOURCE=api', () => {
    const ds = createDashboardDataSource({ VITE_DATA_SOURCE: 'api', VITE_API_BASE_URL: API_BASE });
    expect(ds).toBeInstanceOf(ApiDashboardDataSource);
  });

  it('defaults to mock mode', () => {
    expect(createDashboardDataSource({})).toBeInstanceOf(MockDashboardDataSource);
  });
});

describe('runtime contract validation', () => {
  it('accepts valid payloads', () => {
    expect(() => assertOverviewResponse(loadFixture('overview.json'))).not.toThrow();
    expect(() => assertManagementBriefResponse(loadFixture('management_brief.json'))).not.toThrow();
    expect(() => assertSingleBatchResponse(loadFixture('batch_B017.json'))).not.toThrow();
  });

  it('rejects malformed payloads', () => {
    expect(() => assertOverviewResponse({ meta: {} })).toThrow(ApiContractError);
    expect(() => assertManagementBriefResponse({ briefs: [{ id: 1 }] })).toThrow(ApiContractError);
    expect(() => assertSingleBatchResponse({ batch: {} })).toThrow(ApiContractError);
  });
});
