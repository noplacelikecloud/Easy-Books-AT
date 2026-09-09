import React from "react";
import { Icon } from "./Icon.jsx";

export function Tag({ children, onRemove, style, ...rest }) {
  const [hover, setHover] = React.useState(false);
  return (
    <span
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      {...rest}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        height: 26,
        padding: onRemove ? "0 6px 0 10px" : "0 10px",
        borderRadius: "var(--radius-pill)",
        background: "var(--surface-card)",
        border: `1px solid ${hover ? "var(--border-strong)" : "var(--border-default)"}`,
        color: "var(--text-body)",
        fontSize: "var(--text-xs)",
        transition: "var(--transition-control)",
        ...style,
      }}
    >
      {children}
      {onRemove ? (
        <button
          type="button"
          onClick={onRemove}
          aria-label="Entfernen"
          style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: 16, height: 16, padding: 0, border: "none", background: "transparent", color: "var(--text-faint)", cursor: "pointer" }}
        >
          <Icon name="x" size={12} />
        </button>
      ) : null}
    </span>
  );
}
