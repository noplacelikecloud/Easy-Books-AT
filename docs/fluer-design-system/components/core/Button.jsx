import React from "react";
import { Icon } from "./Icon.jsx";

const BTN_SIZES = {
  sm: { height: 30, padding: "0 12px", font: "var(--text-xs)", radius: "var(--radius-sm)", gap: 6, icon: 14 },
  md: { height: 38, padding: "0 16px", font: "var(--text-sm)", radius: "var(--radius-md)", gap: 8, icon: 16 },
  lg: { height: 46, padding: "0 22px", font: "var(--text-md)", radius: "var(--radius-md)", gap: 9, icon: 18 },
};

const BTN_VARIANTS = {
  primary: {
    rest: { background: "var(--surface-brand)", color: "var(--text-on-brand)", border: "1px solid var(--blue-600)", boxShadow: "var(--shadow-sm)" },
    hover: { background: "var(--blue-600)", boxShadow: "var(--shadow-brand)" },
  },
  secondary: {
    rest: { background: "var(--surface-card)", color: "var(--text-strong)", border: "1px solid var(--border-default)", boxShadow: "var(--shadow-xs)" },
    hover: { background: "var(--n-25)", border: "1px solid var(--border-strong)" },
  },
  ghost: {
    rest: { background: "transparent", color: "var(--text-body)", border: "1px solid transparent", boxShadow: "none" },
    hover: { background: "var(--n-50)", color: "var(--text-strong)" },
  },
  danger: {
    rest: { background: "var(--surface-card)", color: "var(--state-danger-fg)", border: "1px solid var(--red-100)", boxShadow: "var(--shadow-xs)" },
    hover: { background: "var(--state-danger-bg)", border: "1px solid rgba(163,50,39,0.28)" },
  },
};

export function Button({
  children,
  variant = "primary",
  size = "md",
  icon,
  iconAfter,
  fullWidth = false,
  disabled = false,
  style,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const [press, setPress] = React.useState(false);
  const s = BTN_SIZES[size] || BTN_SIZES.md;
  const v = BTN_VARIANTS[variant] || BTN_VARIANTS.primary;
  return (
    <button
      type="button"
      disabled={disabled}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => { setHover(false); setPress(false); }}
      onMouseDown={() => setPress(true)}
      onMouseUp={() => setPress(false)}
      {...rest}
      style={{
        display: fullWidth ? "flex" : "inline-flex",
        width: fullWidth ? "100%" : undefined,
        alignItems: "center",
        justifyContent: "center",
        gap: s.gap,
        height: s.height,
        padding: s.padding,
        borderRadius: s.radius,
        fontFamily: "var(--font-sans)",
        fontSize: s.font,
        fontWeight: "var(--fw-medium)",
        letterSpacing: "var(--tracking-label)",
        whiteSpace: "nowrap",
        flexShrink: 0,
        cursor: disabled ? "not-allowed" : "pointer",
        transition: "var(--transition-control), transform var(--dur-instant) var(--ease-standard)",
        opacity: disabled ? 0.45 : 1,
        transform: press && !disabled ? "translateY(0.5px)" : "none",
        ...v.rest,
        ...(hover && !disabled ? v.hover : null),
        ...style,
      }}
    >
      {icon ? <Icon name={icon} size={s.icon} /> : null}
      {children}
      {iconAfter ? <Icon name={iconAfter} size={s.icon} /> : null}
    </button>
  );
}
