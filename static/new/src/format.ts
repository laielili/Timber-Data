/**
 * Number formatting for the metric system.
 *
 * The rule is derived from the unit, not from taste:
 * - ratios (`%`) and per-tonne rates (`AUD/处理t`) always show **two** decimals,
 *   because that is the precision the identity is written in
 *   (`320.00 × 80.00% − 186.00 = 70.00`) — dropping them makes the panel disagree
 *   with `documents/data/metric_system.md` on sight.
 * - absolute amounts keep up to two decimals and gain thousands separators.
 */
export function fmtMetric(v: number, unit: string): string {
  if (!Number.isFinite(v)) return '—';
  const isRatio = unit === '%' || unit.includes('/');
  return v.toLocaleString('en-US', {
    minimumFractionDigits: isRatio ? 2 : 0,
    maximumFractionDigits: isRatio ? 2 : 2,
  });
}

/** Tonnage: one decimal, so `1,240.0 t` matches the design baseline. */
export function fmtTonnes(v: number): string {
  if (!Number.isFinite(v)) return '—';
  return v.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}

/** `ChartColumn.format` values used by matrix tables. */
export function fmtByFormat(v: unknown, format: string | undefined): string {
  if (typeof v !== 'number' || !Number.isFinite(v)) return '—';
  switch (format) {
    case 'per_t':
      return v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    case 'weight':
      return v.toLocaleString('en-US', { maximumFractionDigits: 2 });
    case 'money':
    case undefined:
      return v.toLocaleString('en-US', { maximumFractionDigits: 2 });
    default:
      return v.toLocaleString('en-US', { maximumFractionDigits: 2 });
  }
}
