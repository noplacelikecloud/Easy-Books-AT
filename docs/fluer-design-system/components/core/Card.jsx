import React from "react";

const CARD_PADS = { sm: "var(--space-6)", md: "var(--space-8)", lg: "var(--space-9)" };

export function Card({ children, title, subtitle, actions, footer, padding = "md", interactive = false, tone = "default", style, ...rest }) {
  const [hover, setHover] = React.useState(false);
  const pad = CARD_PADS[padding] || CARD_PADS.md;
  const lifted = interactive && hover;
  return (
    <section
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      {...rest}
      style={{
        background: tone === "sunken" ? "var(--surface-sunken)" : "var(--surface-card)",
        border: `1px solid ${lifted ? "var(--border-default)" : "var(--border-hairline)"}`,
        borderRadius: "var(--radius-lg)",
        boxShadow: tone === "sunken" ? "none" : lifted ? "var(--shadow-md)" : "var(--shadow-sm)",
        transition: "var(--transition-control)",
        overflow: "hidden",
        ...style,
      }}
    >
      {title || actions ? (
        <header style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--space-6)", padding: `${pad} ${pad} 0` }}>
          <div style={{ display: "grid", gap: 4 }}>
            {title ? <h3 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--fw-semibold)", color: "var(--text-strong)", letterSpacing: "var(--tracking-heading)", margin: 0 }}>{title}</h3> : null}
            {subtitle ? <p style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)", margin: 0 }}>{subtitle}</p> : null}
          </div>
          {actions ? <div style={{ display: "flex", gap: "var(--space-3)", flex: "0 0 auto" }}>{actions}</div> : null}
        </header>
      ) : null}
      <div style={{ padding: pad }}>{children}</div>
      {footer ? (
        <footer style={{ padding: `var(--space-5) ${pad}`, borderTop: "1px solid var(--border-hairline)", background: "var(--n-25)", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>{footer}</footer>
      ) : null}
    </section>
  );
}
