// Lightweight runtime validation for the critical API responses.
// TypeScript types do NOT validate runtime JSON — these focused structural guards
// ensure the UI never renders silently-broken charts when the backend drifts from
// the approved contract. Failures raise ApiContractError (clear integration error).

import { ApiContractError } from './apiClient';

function isObj(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

const REQUIRED_OVERVIEW_KPIS = [
  'incoming_timber',
  'processed_timber',
  'higher_value_recovery_rate',
  'processing_cost_per_processed_t',
  'recovered_value_per_t',
  'unresolved_inspection_rate',
] as const;

const REQUIRED_OVERVIEW_CHARTS = [
  'recovery_route_distribution',
  'incoming_vs_processed',
  'operational_backlog',
  'net_sorting_benefit',
  'cost_vs_recovered_value',
  'batch_economics',
] as const;

/** Validate the shape of GET /api/v1/overview. */
export function assertOverviewResponse(v: unknown): void {
  if (!isObj(v) || !isObj(v.meta) || !isObj(v.north_star) || !isObj(v.kpis) || !isObj(v.charts)) {
    throw new ApiContractError('Overview response is missing required sections.');
  }
  for (const k of REQUIRED_OVERVIEW_KPIS) {
    const kpi = (v.kpis as Record<string, unknown>)[k];
    if (!isObj(kpi) || typeof kpi.value !== 'number') {
      throw new ApiContractError(`Overview KPI '${k}' is missing or invalid.`);
    }
  }
  for (const k of REQUIRED_OVERVIEW_CHARTS) {
    if (!Array.isArray((v.charts as Record<string, unknown>)[k])) {
      throw new ApiContractError(`Overview chart '${k}' is not an array.`);
    }
  }
  const ns = v.north_star as Record<string, unknown>;
  if (typeof ns.value !== 'number') {
    throw new ApiContractError("North Star value is missing or invalid.");
  }
}

/** Validate the shape of GET /api/v1/management-brief. */
export function assertManagementBriefResponse(v: unknown): void {
  if (!isObj(v) || !Array.isArray(v.briefs)) {
    throw new ApiContractError('Management brief response is invalid.');
  }
  for (const b of v.briefs) {
    if (
      !isObj(b) ||
      typeof b.id !== 'string' ||
      typeof b.title !== 'string' ||
      typeof b.detail !== 'string' ||
      !isObj(b.values)
    ) {
      throw new ApiContractError('Management brief item is missing required fields.');
    }
  }
}

/** Validate the shape of GET /api/v1/batches/{batch_id}. */
export function assertSingleBatchResponse(v: unknown): void {
  if (!isObj(v) || !isObj(v.batch)) {
    throw new ApiContractError('Single batch response is invalid.');
  }
  const b = v.batch as Record<string, unknown>;
  if (typeof b.batch_id !== 'string' || typeof b.economic_evaluation_status !== 'string') {
    throw new ApiContractError('Single batch response is missing required batch fields.');
  }
}
