// Header: page title, time controls (display only), prototype indicator.

import type { Meta } from '../types/contract';
import { formatAsOf } from '../lib/format';

export function OverviewHeader({ meta }: { meta: Meta }) {
  const period = `Jan–Dec ${meta.period_start.slice(0, 4)}`;
  return (
    <header className="overview-header">
      <div>
        <h1 className="overview-header__title">Executive Overview</h1>
        <p className="overview-header__sub">Recovery economics · operational state · commercial value</p>
      </div>
      <div className="overview-header__controls">
        <span className="chip chip--time" title="Selected period — flow metrics (TIME_SEMANTICS)">
          Period <strong>{period}</strong>
        </span>
        <span className="chip chip--time" title="Snapshot — state metrics evaluated at as_of (TIME_SEMANTICS)">
          Snapshot <strong>{formatAsOf(meta.as_of)}</strong>
        </span>
        <span className="chip chip--proto" title="All values are synthetic prototype assumptions for product testing">
          Prototype data
        </span>
      </div>
    </header>
  );
}
