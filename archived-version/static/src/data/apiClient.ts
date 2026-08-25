// Minimal HTTP client for the FastAPI data service (Backend Phase 01).
// Responsibilities: base URL, GET, JSON parsing, HTTP error handling, AbortSignal.
// No business calculations live here.

export class ApiConnectionError extends Error {
  constructor(message = 'Unable to connect to the data service.') {
    super(message);
    this.name = 'ApiConnectionError';
  }
}

export class ApiHttpError extends Error {
  constructor(public readonly status: number, message = 'The data service returned an invalid response.') {
    super(message);
    this.name = 'ApiHttpError';
  }
}

export class ApiContractError extends Error {
  constructor(message = 'The data service returned an invalid response.') {
    super(message);
    this.name = 'ApiContractError';
  }
}

export interface ApiClientOptions {
  baseUrl: string;
  signal?: AbortSignal;
}

/** GET a JSON resource from the data service, classifying failures clearly. */
export async function apiGet<T>(path: string, { baseUrl, signal }: ApiClientOptions): Promise<T> {
  const url = `${baseUrl.replace(/\/+$/, '')}${path}`;
  let res: Response;
  try {
    res = await fetch(url, { signal, headers: { Accept: 'application/json' } });
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err;
    throw new ApiConnectionError();
  }
  if (!res.ok) {
    throw new ApiHttpError(res.status);
  }
  try {
    return (await res.json()) as T;
  } catch {
    throw new ApiContractError('The data service returned a non-JSON response.');
  }
}

/** User-facing message for a load failure (technical details stay in dev console). */
export function describeError(err: unknown): string {
  if (err instanceof ApiConnectionError) return 'Unable to connect to the data service.';
  if (err instanceof ApiHttpError || err instanceof ApiContractError) {
    return 'The data service returned an invalid response.';
  }
  if (err instanceof DOMException && err.name === 'AbortError') return 'The request was aborted.';
  return err instanceof Error ? err.message : 'An unexpected error occurred.';
}

/** Error raised by the AI analyst endpoint (structured backend error, never a raw
 *  stack trace or API key). */
export class AnalystQueryError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = 'AnalystQueryError';
  }
}

/** POST a JSON body to the data service, classifying failures clearly. */
export async function apiPost<T>(
  path: string,
  body: unknown,
  { baseUrl, signal }: ApiClientOptions,
): Promise<T> {
  const url = `${baseUrl.replace(/\/+$/, '')}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err;
    throw new ApiConnectionError();
  }
  if (!res.ok) {
    let code = 'error';
    let message = `The analyst service returned HTTP ${res.status}.`;
    try {
      const data = (await res.json()) as { detail?: { code?: string; message?: string } };
      code = data.detail?.code ?? code;
      message = data.detail?.message ?? message;
    } catch {
      /* keep defaults */
    }
    throw new AnalystQueryError(code, message, res.status);
  }
  try {
    return (await res.json()) as T;
  } catch {
    throw new ApiContractError('The analyst service returned a non-JSON response.');
  }
}
