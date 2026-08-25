// Minimal inline icons (stroke-based, no icon library).

interface IconProps {
  size?: number;
  className?: string;
}

function Svg({ size = 16, className, children }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export function IconOverview(p: IconProps) {
  return (
    <Svg {...p}>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </Svg>
  );
}

export function IconTrend(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M3 17l5-5 4 3 6-8" />
      <path d="M15 7h4v4" />
    </Svg>
  );
}

export function IconShield(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6l7-3z" />
      <path d="M9.5 12l2 2 3.5-3.5" />
    </Svg>
  );
}

export function IconFlow(p: IconProps) {
  return (
    <Svg {...p}>
      <circle cx="5" cy="6" r="2.2" />
      <circle cx="19" cy="6" r="2.2" />
      <circle cx="12" cy="18" r="2.2" />
      <path d="M7.2 6h9.6M12 15.8v-6M5 8.2v4.3a2 2 0 002 2h7.5" />
    </Svg>
  );
}

export function IconCoin(p: IconProps) {
  return (
    <Svg {...p}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5v9M14.8 9.2c-.6-1-1.6-1.5-2.8-1.5-1.7 0-3 1-3 2.4 0 3.2 6 1.6 6 4.6 0 1.4-1.3 2.4-3 2.4-1.2 0-2.3-.5-2.9-1.6" />
    </Svg>
  );
}

export function IconStack(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M4 8l8-4 8 4-8 4-8-4z" />
      <path d="M4 12l8 4 8-4" />
      <path d="M4 16l8 4 8-4" />
    </Svg>
  );
}

export function IconDoc(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M7 3h7l5 5v13H7z" />
      <path d="M14 3v5h5" />
      <path d="M9.5 13h5M9.5 16.5h5" />
    </Svg>
  );
}

export function IconSpark(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M12 3l1.8 6.2L20 11l-6.2 1.8L12 19l-1.8-6.2L4 11l6.2-1.8L12 3z" />
    </Svg>
  );
}

export function IconClose(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M6 6l12 12M18 6L6 18" />
    </Svg>
  );
}

export function IconArrowRight(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M4 12h15M13 6l6 6-6 6" />
    </Svg>
  );
}
