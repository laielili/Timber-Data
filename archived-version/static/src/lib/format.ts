// Presentation-only formatting utilities. No business logic.
// All values come from the approved contract / mock data.

const numFmt2 = new Intl.NumberFormat('en-AU', { maximumFractionDigits: 2 });
const numFmt1 = new Intl.NumberFormat('en-AU', { maximumFractionDigits: 1 });

/** Weight in tonnes: 1,240 / 1,013.37 / 47.4 */
export function formatWeight(t: number): string {
  return numFmt2.format(t);
}

/**
 * Currency with unit suffix: "1,240 t" / "1,013.37 t".
 */
export function formatWeightWithUnit(t: number, unit = 't'): string {
  return `${formatWeight(t)} ${unit}`;
}

/**
 * Compact AUD: $85.08 / $12.4k / -$6.2k / -$75.22.
 * Negative sign always precedes the dollar symbol.
 */
export function formatAUD(value: number): string {
  const sign = value < 0 ? '-' : '';
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `${sign}$${numFmt1.format(abs / 1_000_000)}M`;
  if (abs >= 1_000) return `${sign}$${numFmt1.format(abs / 1_000)}k`;
  return `${sign}$${numFmt2.format(abs)}`;
}

/** Currency with a unit suffix, e.g. $85.08/t or -$75.22/t */
export function formatAUDPerT(value: number, unit = 't'): string {
  return `${formatAUD(value)}/${unit}`;
}

/** Percentage: 39.1% / 10.7% / 100% */
export function formatPercent(pct: number): string {
  return `${numFmt1.format(pct)}%`;
}

/** "2025-01" -> "Jan" (short month label) */
export function monthShort(month: string): string {
  const m = Number(month.slice(5, 7));
  const names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return names[m - 1] ?? month;
}

/** "2025-01" -> "Jan 2025" */
export function monthLabel(month: string): string {
  return `${monthShort(month)} ${month.slice(0, 4)}`;
}

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** Accepts an ISO date ("2025-12-31") or ISO datetime ("2025-12-31T18:00:00"); returns null when unparseable. */
function parseDisplayDate(iso: string): Date | null {
  if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) {
    const d = new Date(`${iso}T00:00:00Z`);
    return Number.isNaN(d.getTime()) ? null : d;
  }
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** ISO date/datetime -> "31 Dec 2025". Never exposes raw ISO in UI copy. */
export function formatAsOf(iso: string): string {
  const d = parseDisplayDate(iso);
  if (!d) return iso;
  return `${d.getDate()} ${MONTH_NAMES[d.getMonth()]} ${d.getFullYear()}`;
}

/** Basis chip label */
export function basisLabel(basis: string): string {
  switch (basis) {
    case 'selected_period': return 'Period';
    case 'snapshot': return 'Snapshot';
    case 'comparison_period': return 'Comparison';
    default: return basis;
  }
}
