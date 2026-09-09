import React from "react";
import { Icon } from "../core/Icon.jsx";

const TOAST_TONES = {
  neutral: { icon: "info", fg: "var(--text-strong)", accent: "var(--n-400)" },
  success: { icon: "check-circle", fg: "var(--state-success-fg)", accent: "var(--moss-500)" },
  warning: { icon: "alert-triangle", fg: "var(--state-warning-fg)", accent: "var(--amber-500)" },
  danger: { icon: "alert-octagon", fg: "var(--state-danger-fg)", accent: "var(--red-500)" },
};

export function Toast({ title, description, tone = "neutral", action, onClose, style, ...rest }) {
  const t = TOAST_TONES[tone] || TOAST_TONES.neutral;
  return (
    <div
      role="status"
      {...rest}
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 10,
        minWidth: 300,
        maxWidth: 420,
        padding: "12px 14px",
        borderRadius: "var(--radius-md)",
        background: "var(--surface-glass)",
        backdropFilter: "blur(var(--blur-glass))",
        WebkitBackdropFilter: "blur(var(--blur-glass))",
        border: "1px solid var(--border-default)",
        boxShadow: "var(--shadow-lg)",
        ...style,
      }}
    >
      <span style={{ color: t.accent, marginTop: 1 }}><Icon name={t.icon} size={16} /></span>
      <div style={{ display: "grid", gap: 2, flex: 1 }}>
        <span style={{ fontSize: "var(--text-sm)", fontWeight: "var(--fw-medium)", color: "var(--text-strong)" }}>{title}</span>
        {description ? <span style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>{description}</span> : null}
        {action ? <div style={{ marginTop: 6 }}>{action}</div> : null}
      </div>
      {onClose ? (
        <button type="button" onClick={onClose} aria-label="Schließen" style={{ border: "none", background: "transparent", color: "var(--text-faint)", cursor: "pointer", padding: 2, display: "inline-flex" }}>
          <Icon name="x" size={14} />
        </button>
      ) : null}
    </div>
  );
}
