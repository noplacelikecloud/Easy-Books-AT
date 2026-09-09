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

export function Select({ label, hint, options = [], style, ...rest }) {
  const [focus, setFocus] = React.useState(false);
  return (
    <label style={{ display: "block", ...style }}>
      {label ? <span style={FIELD_LABEL}>{label}</span> : null}
      <span style={{ position: "relative", display: "block" }}>
        <select
          onFocus={() => setFocus(true)}
          onBlur={() => setFocus(false)}
          {...rest}
          style={{
            ...FIELD_CONTROL,
            appearance: "none",
            paddingRight: 34,
            cursor: "pointer",
            borderColor: focus ? "var(--blue-400)" : "var(--border-default)",
            boxShadow: focus ? "var(--ring-focus)" : "var(--shadow-inset-field)",
          }}
        >
          {options.map((o) => {
            const value = typeof o === "string" ? o : o.value;
            const text = typeof o === "string" ? o : o.label;
            return <option key={value} value={value}>{text}</option>;
          })}
        </select>
        <span style={{ position: "absolute", right: 11, top: 0, height: 38, display: "flex", alignItems: "center", color: "var(--text-faint)", pointerEvents: "none" }}>
          <Icon name="chevron-down" size={15} />
        </span>
      </span>
      {hint ? <span style={FIELD_HINT}>{hint}</span> : null}
    </label>
  );
}
