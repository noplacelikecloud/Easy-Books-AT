import React from "react";
import { Icon } from "../core/Icon.jsx";

export function Dialog({ open = true, title, description, children, footer, onClose, width = 460, style }) {
  if (!open) return null;
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "var(--space-8)",
        background: "var(--overlay-scrim)",
        backdropFilter: "blur(var(--blur-scrim))",
        WebkitBackdropFilter: "blur(var(--blur-scrim))",
        zIndex: 60,
      }}
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
        style={{
          width,
          maxWidth: "100%",
          background: "var(--surface-card)",
          border: "1px solid var(--border-hairline)",
          borderRadius: "var(--radius-xl)",
          boxShadow: "var(--shadow-lg)",
          overflow: "hidden",
          animation: "none",
          ...style,
        }}
      >
        <header style={{ display: "flex", alignItems: "flex-start", gap: "var(--space-6)", padding: "var(--space-8) var(--space-8) 0" }}>
          <div style={{ display: "grid", gap: 5, flex: 1 }}>
            {title ? <h3 style={{ margin: 0, fontSize: "var(--text-xl)", fontWeight: "var(--fw-semibold)", color: "var(--text-strong)", letterSpacing: "var(--tracking-heading)" }}>{title}</h3> : null}
            {description ? <p style={{ margin: 0, fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>{description}</p> : null}
          </div>
          {onClose ? (
            <button type="button" onClick={onClose} aria-label="Schließen" style={{ border: "none", background: "transparent", color: "var(--text-faint)", cursor: "pointer", padding: 3, display: "inline-flex" }}>
              <Icon name="x" size={16} />
            </button>
          ) : null}
        </header>
        {children ? <div style={{ padding: "var(--space-7) var(--space-8)" }}>{children}</div> : <div style={{ height: "var(--space-7)" }} />}
        {footer ? (
          <footer style={{ display: "flex", justifyContent: "flex-end", gap: "var(--space-4)", padding: "var(--space-6) var(--space-8)", borderTop: "1px solid var(--border-hairline)", background: "var(--n-25)" }}>{footer}</footer>
        ) : null}
      </div>
    </div>
  );
}
