import React from "react";
import { Icon } from "../core/Icon.jsx";

export function Tabs({ items = [], value, onChange, style }) {
  const [internal, setInternal] = React.useState(value ?? (items[0] && (items[0].value || items[0])));
  const active = value ?? internal;
  const select = (v) => { setInternal(v); onChange && onChange(v); };
  return (
    <div role="tablist" style={{ display: "flex", gap: "var(--space-7)", borderBottom: "1px solid var(--border-hairline)", ...style }}>
      {items.map((raw) => {
        const item = typeof raw === "string" ? { value: raw, label: raw } : raw;
        const on = item.value === active;
        return (
          <button
            key={item.value}
            role="tab"
            aria-selected={on}
            onClick={() => select(item.value)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 7,
              padding: "0 2px 11px",
              border: "none",
              background: "transparent",
              cursor: "pointer",
              fontFamily: "var(--font-sans)",
              fontSize: "var(--text-sm)",
              fontWeight: on ? "var(--fw-medium)" : "var(--fw-regular)",
              color: on ? "var(--text-strong)" : "var(--text-muted)",
              boxShadow: on ? "inset 0 -2px 0 var(--blue-500)" : "none",
              transition: "var(--transition-control)",
            }}
          >
            {item.icon ? <Icon name={item.icon} size={15} /> : null}
            {item.label}
            {item.count != null ? (
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-3xs)", color: "var(--text-faint)" }}>{item.count}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
