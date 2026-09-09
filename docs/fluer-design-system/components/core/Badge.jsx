import React from "react";

const BADGE_TONES = {
  neutral: { bg: "var(--n-50)", fg: "var(--text-body)", bd: "var(--border-default)" },
  brand: { bg: "var(--surface-brand-soft)", fg: "var(--blue-600)", bd: "var(--border-brand)" },
  success: { bg: "var(--state-success-bg)", fg: "var(--state-success-fg)", bd: "rgba(74,122,82,0.22)" },
  warning: { bg: "var(--state-warning-bg)", fg: "var(--state-warning-fg)", bd: "rgba(180,114,26,0.22)" },
  danger: { bg: "var(--state-danger-bg)", fg: "var(--state-danger-fg)", bd: "rgba(163,50,39,0.2)" },
  info: { bg: "var(--state-info-bg)", fg: "var(--state-info-fg)", bd: "rgba(47,93,140,0.2)" },
};

export function Badge({ children, tone = "neutral", dot = false, style, ...rest }) {
  const t = BADGE_TONES[tone] || BADGE_TONES.neutral;
  return (
    <span
      {...rest}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        height: 22,
        padding: "0 8px",
        borderRadius: "var(--radius-xs)",
        background: t.bg,
        color: t.fg,
        border: `1px solid ${t.bd}`,
        fontSize: "var(--text-2xs)",
        fontWeight: "var(--fw-medium)",
        letterSpacing: "var(--tracking-label)",
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {dot ? <span style={{ width: 5, height: 5, borderRadius: "var(--radius-pill)", background: "currentColor" }} /> : null}
      {children}
    </span>
  );
}
