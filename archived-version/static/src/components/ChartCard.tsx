// ChartCard — shared shell for the six analytical chart modules.
// Carries title, business question, time-basis label and empty state.

import type { ReactNode } from 'react';
import { ChartEmpty } from './PageStates';

export type ChartTier = 'primary' | 'support' | 'wide';

interface ChartCardProps {
  title: string;
  question: string;
  basis: string;
  tier?: ChartTier;
  span?: number;
  empty?: boolean;
  emptyLabel?: string;
  actions?: ReactNode;
  children?: ReactNode;
}

export function ChartCard({
  title,
  question,
  basis,
  tier = 'support',
  span,
  empty = false,
  emptyLabel = 'No data in period',
  actions,
  children,
}: ChartCardProps) {
  return (
    <section
      className={`chart-card chart-card--${tier}`}
      style={span ? { gridColumn: `span ${span}` } : undefined}
      aria-label={title}
    >
      <header className="chart-card__head">
        <div className="chart-card__titles">
          <h3 className="chart-card__title">{title}</h3>
          <p className="chart-card__question">{question}</p>
        </div>
        <div className="chart-card__meta">
          <span className="chip chip--basis">{basis}</span>
          {actions}
        </div>
      </header>
      {empty ? <ChartEmpty label={emptyLabel} /> : <div className="chart-card__body">{children}</div>}
    </section>
  );
}
