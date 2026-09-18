interface Props {
  values: number[];
  /** Series colour; defaults to the card's dark-brown ink. */
  tone?: string;
  /** Accessible description, e.g. the metric name. */
  label: string;
}

const W = 100;
const H = 46;
const PAD_L = 5;
const PAD_R = 4;
const PAD_T = 6;
const PAD_B = 6;

/**
 * Card sparkline — shape only, no ticks, no labels. The card face already states
 * the current value; this exists purely so the eye can see where that value came
 * from (rising / flat / falling) without leaving the card.
 *
 * The vertical range is the series' own min/max rather than zero-based: these
 * metrics live in a narrow band (a processing rate around 80%, a unit cost
 * around 190), and anchoring at zero would flatten every one of them into a
 * straight line. That makes it a *shape* indicator, not a magnitude one — which
 * is the point, and why the reference axes stay neutral.
 */
export function Sparkline({ values, tone = '#3b2f21', label }: Props) {
  const pts = values.filter((v) => Number.isFinite(v));
  if (pts.length < 2) return null;

  const min = Math.min(...pts);
  const max = Math.max(...pts);
  const span = max - min || 1;
  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;

  const x = (i: number) => PAD_L + (i / (pts.length - 1)) * innerW;
  const y = (v: number) => PAD_T + (1 - (v - min) / span) * innerH;

  const line = pts.map((v, i) => `${x(i).toFixed(2)},${y(v).toFixed(2)}`).join(' ');
  const area = `${PAD_L},${H - PAD_B} ${line} ${W - PAD_R},${H - PAD_B}`;
  const lastX = x(pts.length - 1);
  const lastY = y(pts[pts.length - 1]);

  return (
    <svg
      className="sparkline"
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="none"
      role="img"
      aria-label={label}
    >
      {/* the L-shaped frame from the reference: bottom + left hairline */}
      <line x1={PAD_L} y1={3} x2={PAD_L} y2={H - PAD_B} stroke="#d3d1c7" strokeWidth="1" vectorEffect="non-scaling-stroke" />
      <line x1={PAD_L} y1={H - PAD_B} x2={W - 1} y2={H - PAD_B} stroke="#d3d1c7" strokeWidth="1" vectorEffect="non-scaling-stroke" />
      <polygon points={area} fill={tone} opacity="0.08" />
      <polyline
        points={line}
        fill="none"
        stroke={tone}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
      <circle cx={lastX} cy={lastY} r="2.4" fill={tone} />
    </svg>
  );
}
