import React from "react";
import { Icon } from "./Icon.jsx";

const IB_SIZES = { sm: { box: 28, icon: 14 }, md: { box: 34, icon: 16 }, lg: { box: 40, icon: 18 } };

export function IconButton({ icon = "more-horizontal", size = "md", variant = "ghost", label, disabled = false, style, ...rest }) {
  const [hover, setHover] = React.useState(false);
  const s = IB_SIZES[size] || IB_SIZES.md;
  const outlined = variant === "outline";
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      disabled={disabled}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      {...rest}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: s.box,
        height: s.box,
        borderRadius: "var(--radius-sm)",
        background: outlined ? "var(--surface-card)" : hover ? "var(--n-50)" : "transparent",
        border: outlined ? "1px solid var(--border-default)" : "1px solid transparent",
        color: hover && !disabled ? "var(--text-strong)" : "var(--text-muted)",
        boxShadow: outlined ? "var(--shadow-xs)" : "none",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.4 : 1,
        transition: "var(--transition-control)",
        ...style,
      }}
    >
      <Icon name={icon} size={s.icon} />
    </button>
  );
}
