import React from "react";
import { X } from "lucide-react";

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl";
}

const MAX_WIDTHS = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
};

export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  actions,
  maxWidth = "md",
}: DialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Fluer Scrim: 36% opacity with 3px blur */}
      <div
        className="fixed inset-0 bg-[#161614]/36 backdrop-blur-[3px] transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Fluer Modal Card: 20px radius, shadow-lg, hairline border */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        className={[
          "dialog-fluer relative z-10 w-full rounded-[20px] bg-[var(--bg-card,#ffffff)] border border-[var(--border-hairline,#dedcd7)]",
          "shadow-[0_12px_24px_-4px_rgba(22,22,20,0.12),0_4px_8px_rgba(22,22,20,0.06)] overflow-hidden",
          MAX_WIDTHS[maxWidth] || MAX_WIDTHS.md,
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <div className="flex items-start justify-between p-6 pb-4 border-b border-[var(--border-hairline,#dedcd7)]">
          <div>
            <h2 id="dialog-title" className="text-lg font-semibold text-[var(--text-strong,#161614)] tracking-tight m-0">
              {title}
            </h2>
            {description ? (
              <p className="text-sm text-[var(--text-muted,#57544d)] mt-1 mb-0">
                {description}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Schließen"
            className="p-1 rounded-[6px] text-[var(--n-600,#57544d)] hover:bg-[var(--n-50,#f4f3f0)] hover:text-[var(--n-900,#161614)] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">{children}</div>

        {actions ? (
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-[var(--border-hairline,#dedcd7)] bg-[var(--n-25,#fbfbf9)]">
            {actions}
          </div>
        ) : null}
      </div>
    </div>
  );
}
