import React from "react";
import { Icon } from "../core/Icon.jsx";

const FIELD_LABEL = { display: "block", fontSize: "var(--text-xs)", fontWeight: "var(--fw-medium)", color: "var(--text-strong)", letterSpacing: "var(--tracking-label)", marginBottom: 6 };
const FIELD_HINT = { fontSize: "var(--text-2xs)", color: "var(--text-muted)", marginTop: 6 };
const FIELD_CONTROL = {
  width: "100%",
  height: 38,
  padding: "0 12px",
  fontFamily: "var(--font-sans)",
  fontSize: "var(--text-sm)",
  color: "var(--text-strong)",
  background: "var(--surface-card)",
  border: "1px solid var(--border-default)",
  borderRadius: "var(--radius-md)",
  boxShadow: "var(--shadow-inset-field)",
  outline: "none",
  transition: "var(--transition-control)",
};

export function Input({ label, hint, error, icon, multiline = false, rows = 4, style, ...rest }) {
  const [focus, setFocus] = React.useState(false);
  const border = error ? "var(--state-danger-fg)" : focus ? "var(--blue-400)" : "var(--border-default)";
  const Tag = multiline ? "textarea" : "input";
  return (
    <label style={{ display: "block", ...style }}>
      {label ? <span style={FIELD_LABEL}>{label}</span> : null}
      <span style={{ position: "relative", display: "block" }}>
        {icon && !multiline ? (
          <span style={{ position: "absolute", left: 11, top: 0, height: 38, display: "flex", alignItems: "center", color: "var(--text-faint)" }}>
            <Icon name={icon} size={15} />
          </span>
        ) : null}
        <Tag
          rows={multiline ? rows : undefined}
          onFocus={() => setFocus(true)}
          onBlur={() => setFocus(false)}
          {...rest}
          style={{
            ...FIELD_CONTROL,
            height: multiline ? "auto" : 38,
            padding: multiline ? "10px 12px" : icon ? "0 12px 0 32px" : "0 12px",
            lineHeight: multiline ? "var(--lh-normal)" : undefined,
            resize: multiline ? "vertical" : undefined,
            borderColor: border,
            boxShadow: focus ? "var(--ring-focus)" : "var(--shadow-inset-field)",
          }}
        />
      </span>
      {error ? <span style={{ ...FIELD_HINT, color: "var(--state-danger-fg)" }}>{error}</span> : hint ? <span style={FIELD_HINT}>{hint}</span> : null}
    </label>
  );
}
