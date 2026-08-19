// Ask Circular — conversational management analyst surface (right-side drawer, ~440px).
//
// Two modes:
//  - 'mock' : deterministic Q&A from the approved synthetic data (no AI / LLM).
//             Preserves the original shortcut-select behaviour.
//  - 'real' : free-text questions sent to POST /api/v1/analyst/query. The model may
//             call only the 12 approved analyst tools; the structured, validated
//             AnalystResponse is rendered. Shortcuts remain as quick-send buttons.

import { useEffect, useRef, useState } from 'react';
import type { MockQuestion } from '../data/mockAnswers';
import type { AnalystContext, AnalystQueryRequest, AnalystResponse } from '../types/analyst';
import { IconClose, IconSpark } from './icons';

interface Props {
  open: boolean;
  onClose: () => void;
  mode: 'real' | 'mock';
  questions: MockQuestion[];
  /** Only used in 'real' mode. */
  onAnalystQuery?: (req: AnalystQueryRequest) => Promise<AnalystResponse>;
  context?: AnalystContext;
}

interface Turn {
  id: string;
  question: string;
  response?: AnalystResponse;
  error?: string;
  loading: boolean;
}

const SUBTITLE = {
  mock: 'Prototype Q&A · deterministic answers from the approved synthetic dataset · no AI connection yet',
  real: 'AI-assisted analysis · grounded in approved recovery data',
} as const;

const LOADING_TEXT = 'Analysing recovery data…';
const ERROR_TEXT =
  'Ask Circular could not complete the analysis. The deterministic dashboard data remains available.';

function uid(): string {
  return `t_${Math.random().toString(36).slice(2, 9)}`;
}

export function AskCircularDrawer({ open, onClose, mode, questions, onAnalystQuery, context }: Props) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) {
      const t = window.setTimeout(() => closeRef.current?.focus(), 30);
      return () => window.clearTimeout(t);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="drawer-layer">
      <div className="drawer-overlay" onClick={onClose} aria-hidden="true" />
      <aside className="drawer" role="dialog" aria-modal="true" aria-label="Ask Circular">
        <header className="drawer__head">
          <div className="drawer__titles">
            <span className="drawer__eyebrow">
              <IconSpark size={13} /> Ask Circular
            </span>
            <p className="drawer__sub">{SUBTITLE[mode]}</p>
          </div>
          <button ref={closeRef} type="button" className="btn-icon" onClick={onClose} aria-label="Close Ask Circular">
            <IconClose size={17} />
          </button>
        </header>

        {mode === 'mock' ? (
          <MockBody questions={questions} />
        ) : (
          <RealBody questions={questions} onAnalystQuery={onAnalystQuery} context={context} />
        )}

        <footer className="drawer__foot">Synthetic prototype — not an industry financial model.</footer>
      </aside>
    </div>
  );
}

// --------------------------------------------------------------------------- mock mode

function MockBody({ questions }: { questions: MockQuestion[] }) {
  const [selectedId, setSelectedId] = useState<string | null>(questions[0]?.id ?? null);
  const selected = questions.find((q) => q.id === selectedId) ?? questions[0];

  return (
    <>
      <nav className="drawer__questions" aria-label="Example questions">
        {questions.map((q) => (
          <button
            key={q.id}
            type="button"
            className={`drawer__q ${q.id === selected?.id ? 'drawer__q--active' : ''}`}
            onClick={() => setSelectedId(q.id)}
            aria-pressed={q.id === selected?.id}
          >
            {q.question}
          </button>
        ))}
      </nav>

      {selected ? (
        <div className="answer" key={selected.id}>
          <h3 className="answer__q">{selected.question}</h3>
          <AnswerBlock label="Conclusion" text={selected.answer.conclusion} />
          <section className="answer__block">
            <h4 className="answer__label">Evidence</h4>
            <dl className="answer__evidence">
              {selected.answer.evidence.map((row) => (
                <div key={row.label} className="answer__evidence-row">
                  <dt>{row.label}</dt>
                  <dd>{row.value}</dd>
                </div>
              ))}
            </dl>
          </section>
          <AnswerBlock label="Business implication" text={selected.answer.businessImplication} />
          <AnswerBlock label="Suggested investigation" text={selected.answer.suggestedInvestigation} />
          <AnswerBlock label="Data limitation" text={selected.answer.dataLimitation} muted />
        </div>
      ) : (
        <div className="answer answer--empty">Choose a question to see the structured prototype response.</div>
      )}
    </>
  );
}

// --------------------------------------------------------------------------- real mode

function RealBody({
  questions,
  onAnalystQuery,
  context,
}: {
  questions: MockQuestion[];
  onAnalystQuery?: (req: AnalystQueryRequest) => Promise<AnalystResponse>;
  context?: AnalystContext;
}) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [turns]);

  async function send(question: string) {
    const q = question.trim();
    if (!q || submitting || !onAnalystQuery) return;
    const id = uid();
    setSubmitting(true);
    setTurns((prev) => [...prev, { id, question: q, loading: true }]);
    setInput('');
    try {
      const response = await onAnalystQuery({ question: q, context, conversation_id: conversationId });
      setConversationId(response.conversation_id);
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, response, loading: false } : t)));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred.';
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, error: message, loading: false } : t)));
    } finally {
      setSubmitting(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  }

  return (
    <>
      <nav className="drawer__questions" aria-label="Example questions">
        {questions.map((q) => (
          <button
            key={q.id}
            type="button"
            className="drawer__q"
            onClick={() => send(q.question)}
            disabled={submitting}
          >
            {q.question}
          </button>
        ))}
      </nav>

      <div className="answer ask-history" ref={scrollRef}>
        {turns.length === 0 ? (
          <div className="answer--empty">
            Ask a free-text question, or pick a shortcut above. The analyst answers using only approved recovery data.
          </div>
        ) : (
          turns.map((t) => (
            <div className="ask-turn" key={t.id}>
              <p className="ask-turn__q">{t.question}</p>
              {t.loading && <p className="drawer__loading">{LOADING_TEXT}</p>}
              {t.error && !t.response && <p className="drawer__error">{ERROR_TEXT}</p>}
              {t.response && <AnalystCard response={t.response} />}
            </div>
          ))
        )}
      </div>

      <div className="drawer__compose">
        <textarea
          className="drawer__input"
          placeholder="Ask a question…"
          value={input}
          rows={2}
          disabled={submitting}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          aria-label="Ask the analyst a question"
        />
        <button
          type="button"
          className="btn--ask"
          onClick={() => send(input)}
          disabled={submitting || !input.trim()}
        >
          {submitting ? 'Analysing…' : 'Ask'}
        </button>
      </div>
    </>
  );
}

// --------------------------------------------------------------------------- shared

function AnswerBlock({ label, text, muted }: { label: string; text: string; muted?: boolean }) {
  return (
    <section className="answer__block">
      <h4 className="answer__label">{label}</h4>
      <p className={`answer__text ${muted ? 'answer__text--muted' : ''}`}>{text}</p>
    </section>
  );
}

function AnalystCard({ response }: { response: AnalystResponse }) {
  return (
    <div className="analyst-card">
      <AnswerBlock label="Conclusion" text={response.conclusion} />
      <section className="answer__block">
        <h4 className="answer__label">Evidence</h4>
        <dl className="answer__evidence">
          {response.evidence.map((row, i) => (
            <div key={`${row.label}-${i}`} className="answer__evidence-row">
              <dt>{row.label}</dt>
              <dd>{row.value}</dd>
            </div>
          ))}
        </dl>
      </section>
      <AnswerBlock label="Business implication" text={response.business_implication} />
      <AnswerBlock label="Suggested investigation" text={response.suggested_investigation} />
      <AnswerBlock label="Data limitation" text={response.data_limitation} muted />

      <div className="analyst-card__meta">
        <span className={`confidence confidence--${response.confidence}`}>
          Confidence: {response.confidence}
        </span>
        {response.tools_used.length > 0 && (
          <details className="evidence-sources">
            <summary>Evidence sources ({response.tools_used.length})</summary>
            <ul>
              {response.tools_used.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}
