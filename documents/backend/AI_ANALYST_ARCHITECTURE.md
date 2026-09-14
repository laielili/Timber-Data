# AI Analyst Architecture — Circular Timber Intelligence (Phase 02)

Real conversational analyst integration. A real LLM is connected to the approved,
deterministic analyst tool layer and turns the Ask Circular drawer into a genuine
management analyst.

> **The LLM interprets. Python calculates.** The model is never the source of truth
> for business numbers.

---

## Architecture

```text
User
  ↓  (free-text question + context)
Ask Circular (React drawer)
  ↓  POST /api/v1/analyst/query
AI Analyst endpoint (FastAPI)
  ↓
AnalystService
  ↓  orchestration loop
ModelProvider (OpenAI-compatible, server-side only)
  ↓  tool_call requests
Tool Registry  →  Python Analytics Services  →  SQLite (read-only)
  ↑  structured ToolExecutionResult
ModelProvider
  ↑  final structured JSON
AnalystService (evidence validation + audit)
  ↓  AnalystResponse (Pydantic-validated)
Ask Circular (structured card: Conclusion / Evidence / Business implication /
              Suggested investigation / Data limitation)
```

## Provider adapter

`backend/app/ai/provider.py` defines a `ModelProvider` Protocol with a single
`chat(system, messages, tools, response_format, temperature)` method. The only
concrete adapter shipped is `OpenAICompatibleProvider` (httpx async, OpenAI /
OpenRouter / Azure / local OpenAI-compatible servers). All provider-specific concerns
(auth header, base URL, error→type mapping) live inside the adapter; business and
orchestration logic stay provider-neutral.

## Tool orchestration

`backend/app/ai/orchestration.py` drives the multi-round loop:

1. Build provider tool definitions **from the live registry** (`tool_adapter.registry_to_provider_tools()`).
2. Call the model. If it returns `tool_calls`, validate each against the registered
   tool + Pydantic input schema, execute through `REGISTRY.execute` (read-only,
   audited), and feed the structured result back.
3. Repeat up to `AI_MAX_TOOL_ROUNDS` (default 6). Exceeding the cap raises
   `MaxToolRoundsExceeded` (clean error, no infinite loop).
4. When the model stops calling tools, its content is parsed as the structured
   `AnalystResponse` JSON (enforced with `response_format` json_schema).

Unknown tool names are never executed — they are returned to the model as a
structured `UnknownTool` error.

## System role

`backend/app/ai/prompts.py` holds the **Circular Timber Intelligence — Recovery
Intelligence Analyst** system instruction. It fixes the 10 core rules: no invented
numbers, use tools for facts, never compute core metrics independently, never treat
provisional economics as final, never claim safety/certification, always mark
synthetic prototype data, state insufficiency, separate observation from
interpretation, and frame recommendations as investigate/compare/review/consider
(not mandates).

## Evidence grounding

Every final `AnalystResponse.evidence` item is cross-checked against the deterministic
tool outputs actually executed this turn (`orchestration.validate_evidence`):

- a referenced `source_tool` must have been called;
- a referenced `batch_id` must appear in a tool result;
- a numeric `value` must match a number in that tool's output within tolerance;
- unsupported claims are dropped (not silently shown) and noted in `data_limitation`.

## Structured response

`backend/app/ai/schemas.py` defines `AnalystResponse` (Pydantic) with `answer_id`,
`question`, `conclusion`, `evidence[]`, `business_implication`,
`suggested_investigation`, `data_limitation`, `tools_used[]`, `entities[]`,
`confidence`, `prototype=True`, `conversation_id`. The frontend renders exactly this
shape — no raw model text is trusted.

## Conversation context

`AnalystService` keeps a short-lived, **in-memory** conversation store (UUID
`conversation_id`, capped at `AI_MAX_HISTORY` messages). Only compact user/assistant
text is retained — no tool JSON, no vector DB, no persistent long-term memory. The
frontend sends the same `conversation_id` on follow-ups.

## Error handling

All AI/provider failures are converted to clean `AnalystErrorResponse` bodies
(`code`, `message`, `prototype`) — never an API key, raw HTTP body, or stack trace.
Distinct internal types: `AIProviderTimeout`, `AIProviderRateLimit`,
`AIProviderAuth`, `AIProviderUnavailable`, `AIProviderMalformedResponse`,
`MaxToolRoundsExceeded`, `InvalidAnalystRequest`. A disabled server returns
`ai_disabled` (HTTP 503). **No silent fallback to fake AI.**

## Safety boundary

The model can only call the 12 approved read-only analyst tools. There is no tool for
`update_batch`, `delete_batch`, `approve_material`, `certify_timber`, or any write.
The analyst may recommend investigation; it cannot execute operational decisions or
assert structural/chemical safety.

## Prototype limitations

- Dataset is `synthetic_prototype`; every answer carries `prototype=True`.
- North Star stays 85.08 AUD/t; no metric is recomputed by the model.
- Provisional (open) batches are never ranked as final realised performance.
- `Net Sorting Benefit` is a prototype all-feedstock counterfactual, not an
  industry-standard ROI.

## Configuration

All credentials come from the environment (`backend/.env.example`). The frontend
never receives `AI_API_KEY`; model calls are server-side. Frontend mode is selected by
`VITE_ANALYST_MODE=real|mock`.
