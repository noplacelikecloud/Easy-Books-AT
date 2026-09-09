import React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  footer?: React.ReactNode;
  padding?: "none" | "sm" | "md" | "lg";
  interactive?: boolean;
  tone?: "default" | "sunken";
  children: React.ReactNode;
}

const CARD_PADS = {
  none: "p-0",
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
};

export function Card({
  children,
  title,
  subtitle,
  actions,
  footer,
  padding = "md",
  interactive = false,
  tone = "default",
  className = "",
  ...rest
}: CardProps) {
  const isSunken = tone === "sunken";
  const padCls = CARD_PADS[padding] || CARD_PADS.md;

  return (
    <section
      className={[
        "card-fluer rounded-[14px] border overflow-hidden transition-all duration-150",
        isSunken
          ? "card-sunken bg-[var(--surface-sunken,#f4f3f0)] border-[var(--border-hairline,#dedcd7)] shadow-none"
          : "bg-[var(--bg-card,#ffffff)] border-[var(--border-hairline,#dedcd7)] shadow-[0_2px_4px_rgba(22,22,20,0.06),0_1px_2px_rgba(22,22,20,0.04)]",
        interactive && !isSunken
          ? "hover:shadow-[0_6px_12px_-2px_rgba(22,22,20,0.08),0_2px_4px_rgba(22,22,20,0.04)] hover:border-[var(--n-400,#8c887f)] cursor-pointer"
          : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {title || actions ? (
        <header className="flex items-start justify-between gap-4 px-6 pt-6 pb-2">
          <div className="grid gap-1">
            {title ? (
              <h3 className="text-base font-semibold text-[var(--text-strong,#161614)] tracking-tight m-0">
                {title}
              </h3>
            ) : null}
            {subtitle ? (
              <p className="text-sm text-[var(--text-muted,#57544d)] m-0">
                {subtitle}
              </p>
            ) : null}
          </div>
          {actions ? (
            <div className="flex items-center gap-2 shrink-0">{actions}</div>
          ) : null}
        </header>
      ) : null}

      <div className={padCls}>{children}</div>

      {footer ? (
        <footer className="px-6 py-3.5 border-t border-[var(--border-hairline,#dedcd7)] bg-[var(--n-25,#fbfbf9)] text-xs text-[var(--text-muted,#57544d)]">
          {footer}
        </footer>
      ) : null}
    </section>
  );
}
