import React from "react";

export type BadgeTone = "neutral" | "brand" | "success" | "warning" | "danger" | "info";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
  dot?: boolean;
  children: React.ReactNode;
}

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral:
    "badge-neutral bg-[var(--n-50,#f4f3f0)] text-[var(--n-700,#3f3d38)] border-[var(--n-200,#c7c4bd)]",
  brand:
    "badge-brand bg-[var(--blue-50,#eaf1f7)] text-[var(--blue-600,#123d6a)] border-[var(--blue-200,#a2c2e0)]",
  success:
    "badge-success bg-[var(--moss-50,#eef5ed)] text-[var(--moss-600,#246e2a)] border-[rgba(36,110,42,0.25)]",
  warning:
    "badge-warning bg-[var(--amber-50,#fdf6e7)] text-[var(--amber-600,#8c5d08)] border-[rgba(140,93,8,0.25)]",
  danger:
    "badge-danger bg-[var(--red-50,#faeceb)] text-[var(--red-600,#a33227)] border-[rgba(163,50,39,0.25)]",
  info:
    "badge-info bg-[var(--petrol-50,#eaf3f5)] text-[var(--petrol-600,#156170)] border-[rgba(21,97,112,0.25)]",
};

export function Badge({
  children,
  tone = "neutral",
  dot = false,
  className = "",
  ...rest
}: BadgeProps) {
  const toneCls = TONE_CLASSES[tone] || TONE_CLASSES.neutral;

  return (
    <span
      className={[
        "badge-fluer inline-flex items-center gap-1.5 h-[22px] px-2 rounded-[3px] border text-[11px] font-medium tracking-tight whitespace-nowrap select-none shrink-0",
        toneCls,
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {dot ? (
        <span className="badge-dot w-[5px] h-[5px] rounded-full bg-current shrink-0" />
      ) : null}
      {children}
    </span>
  );
}
