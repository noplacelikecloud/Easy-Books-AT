import React from "react";

export function Tooltip({ children, content, side = "top", style }) {
  const [open, setOpen] = React.useState(false);
  const pos = {
    top: { bottom: "calc(100% + 7px)", left: "50%", transform: "translateX(-50%)" },
    bottom: { top: "calc(100% + 7px)", left: "50%", transform: "translateX(-50%)" },
    right: { left: "calc(100% + 7px)", top: "50%", transform: "translateY(-50%)" },
    left: { right: "calc(100% + 7px)", top: "50%", transform: "translateY(-50%)" },
  }[side];
  return (
    <span
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
      style={{ position: "relative", display: "inline-flex", ...style }}
    >
      {children}
      <span
        role="tooltip"
        style={{
          position: "absolute",
          zIndex: 40,
          ...pos,
          padding: "5px 9px",
          borderRadius: "var(--radius-sm)",
          background: "var(--surface-inverse)",
          color: "var(--text-inverse)",
          border: "1px solid var(--border-inverse)",
          boxShadow: "var(--shadow-md)",
          fontSize: "var(--text-2xs)",
          lineHeight: 1.35,
          whiteSpace: "nowrap",
          pointerEvents: "none",
          opacity: open ? 1 : 0,
          transition: "opacity var(--dur-fast) var(--ease-standard)",
        }}
      >
        {content}
      </span>
    </span>
  );
}
