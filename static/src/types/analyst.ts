// Analyst response types — mirror the backend `AnalystResponse` Pydantic model.
// The frontend renders ONLY this structured shape; it never trusts raw model text.

export type AnalystConfidence = "high" | "medium" | "low";

export interface AnalystEvidence {
  label: string;
  value: string;
  unit?: string | null;
  source_tool?: string | null;
  batch_id?: string | null;
  time_basis?: string | null;
}

export interface AnalystContext {
  period_start?: string | null;
  period_end?: string | null;
  as_of?: string | null;
  current_page?: string | null;
  selected_batch_id?: string | null;
}

export interface AnalystQueryRequest {
  question: string;
  context?: AnalystContext;
  conversation_id?: string | null;
}

export interface AnalystResponse {
  answer_id: string;
  question: string;
  conclusion: string;
  evidence: AnalystEvidence[];
  business_implication: string;
  suggested_investigation: string;
  data_limitation: string;
  tools_used: string[];
  entities: string[];
  confidence: AnalystConfidence;
  prototype: true;
  conversation_id: string;
  model?: string | null;
  provider?: string | null;
  tool_rounds?: number | null;
}

/** Clean structured error returned by the backend when AI analysis fails. */
export interface AnalystError {
  status: "error";
  code: string;
  message: string;
  conversation_id?: string | null;
  prototype: true;
}
