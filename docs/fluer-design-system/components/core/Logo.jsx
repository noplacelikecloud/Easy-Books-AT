import React from "react";

/* Marke: Wolke (Cloud) mit ausgestanztem Prompt-Zeichen ›_ (Development). */
export function Logo({ size = 28, showWordmark = false, style, ...rest }) {
  const uid = React.useId().replace(/:/g, "");
  const h = size;
  const w = (48 / 32) * h;
  return (
    <span {...rest} style={{ display: "inline-flex", alignItems: "center", gap: h * 0.32, color: "var(--text-strong)", ...style }}>
      <svg viewBox="0 0 48 32" width={w} height={h} role="img" aria-label="Fluer Development" style={{ display: "block", color: "var(--text-brand)", flex: "0 0 auto" }}>
        <mask id={"fluerCut" + uid}>
          <rect x="0" y="0" width="48" height="32" fill="#fff" />
          <g fill="none" stroke="#000" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17.6 13.4 L22.6 18.2 L17.6 23" />
            <path d="M25.6 23 H32.4" />
          </g>
        </mask>
        <g mask={`url(#fluerCut${uid})`} fill="currentColor">
          <rect x="7" y="15" width="34" height="10" rx="5" />
          <circle cx="17" cy="15" r="8" />
          <circle cx="29" cy="13" r="10" />
          <circle cx="38" cy="18" r="6" />
        </g>
      </svg>
      {showWordmark ? (
        <span style={{ fontFamily: "var(--font-sans)", fontSize: h * 0.78, fontWeight: "var(--fw-semibold)", letterSpacing: "-0.03em", color: "inherit", whiteSpace: "nowrap" }}>
          Fluer <span style={{ fontWeight: "var(--fw-regular)", color: "var(--text-muted)" }}>Development</span>
        </span>
      ) : null}
    </span>
  );
}
