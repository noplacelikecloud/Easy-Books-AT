import React from "react";

export function Radio({ label, description, checked, onChange, name, disabled = false, style, ...rest }) {
  return (
    <label style={{ display: "flex", gap: 10, alignItems: "flex-start", cursor: disabled ? "not-allowed" : "pointer", opacity: disabled ? 0.5 : 1, ...style }}>
      <input type="radio" name={name} checked={checked} onChange={onChange} disabled={disabled} {...rest} style={{ position: "absolute", opacity: 0, width: 0, height: 0 }} />
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          width: 18,
          height: 18,
          marginTop: 1,
          flex: "0 0 auto",
          borderRadius: "var(--radius-pill)",
          background: "var(--surface-card)",
          border: `1px solid ${checked ? "var(--blue-500)" : "var(--border-strong)"}`,
          boxShadow: checked ? "none" : "var(--shadow-inset-field)",
          transition: "var(--transition-control)",
        }}
      >
        {checked ? <span style={{ width: 8, height: 8, borderRadius: "var(--radius-pill)", background: "var(--surface-brand)" }} /> : null}
      </span>
      <span style={{ display: "grid", gap: 2 }}>
        <span style={{ fontSize: "var(--text-sm)", color: "var(--text-strong)" }}>{label}</span>
        {description ? <span style={{ fontSize: "var(--text-2xs)", color: "var(--text-muted)" }}>{description}</span> : null}
      </span>
    </label>
  );
}
