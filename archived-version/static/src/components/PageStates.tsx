// Page-level loading / error / empty states (simple, backend-integration friendly).

export function LoadingScreen() {
  return (
    <div className="page-state" role="status" aria-live="polite">
      <div className="page-state__mark" aria-hidden="true">
        <span className="loader-dot" />
        <span className="loader-dot" />
        <span className="loader-dot" />
      </div>
      <p className="page-state__title">Loading Executive Overview</p>
      <p className="page-state__sub">Reading approved synthetic dataset…</p>
    </div>
  );
}

export function ErrorScreen({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="page-state" role="alert">
      <p className="page-state__title">Unable to load overview data</p>
      <p className="page-state__sub">{message}</p>
      <button type="button" className="btn btn--primary" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}

export function ChartEmpty({ label }: { label: string }) {
  return (
    <div className="chart-empty" role="status">
      <span className="chart-empty__dot" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
