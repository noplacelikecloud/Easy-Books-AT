import React from "react";

export function Switch({ label, description, checked = false, onChange, disabled = false, style, ...rest }) {
  return (
    <label style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--space-6)", cursor: disabled ? "not-allowed" : "pointer", opacity: disabled ? 0.5 : 1, ...style }}>
      <span style={{ display: "grid", gap: 2 }}>
        {label ? <span style={{ fontSize: "var(--text-sm)", color: "var(--text-strong)" }}>{label}</span> : null}
        {description ? <span style={{ fontSize: "var(--text-2xs)", color: "var(--text-muted)" }}>{description}</span> : null}
      </span>
      <span
        role="switch"
        aria-checked={checked}
        onClick={() => !disabled && onChange && onChange(!checked)}
        style={{
          position: "relative",
          flex: "0 0 auto",
          width: 38,
          height: 22,
          borderRadius: "var(--radius-pill)",
          background: checked ? "var(--surface-brand)" : "var(--n-200)",
          border: `1px solid ${checked ? "var(--blue-600)" : "var(--border-strong)"}`,
          transition: "background-color var(--dur-base) var(--ease-standard), border-color var(--dur-base) var(--ease-standard)",
        }}
      >
        <span
          style={{
            position: "absolute",
            top: 2,
            left: checked ? 18 : 2,
            width: 16,
            height: 16,
            borderRadius: "var(--radius-pill)",
            background: "var(--n-0)",
            boxShadow: "var(--shadow-sm)",
            transition: "left var(--dur-base) var(--ease-out)",
          }}
        />
      </span>
      <input type="checkbox" checked={checked} disabled={disabled} onChange={() => onChange && onChange(!checked)} {...rest} style={{ position: "absolute", opacity: 0, width: 0, height: 0 }} />
    </label>
  );
}
