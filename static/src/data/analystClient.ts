// AI Analyst client — talks to POST /api/v1/analyst/query on the FastAPI service.
// All model calls happen server-side; this module only ships the question and
// receives the structured, validated AnalystResponse.

import { apiPost, AnalystQueryError } from './apiClient';
import type { AnalystQueryRequest, AnalystResponse } from '../types/analyst';

export { AnalystQueryError };

/** Send a free-text analyst question and get back a structured management answer. */
export async function postAnalystQuery(
  req: AnalystQueryRequest,
  baseUrl: string,
  signal?: AbortSignal,
): Promise<AnalystResponse> {
  return apiPost<AnalystResponse>('/api/v1/analyst/query', req, { baseUrl, signal });
}
