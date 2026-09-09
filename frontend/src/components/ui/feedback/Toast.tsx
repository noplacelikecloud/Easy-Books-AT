import React from "react";
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from "lucide-react";

export type ToastTone = "info" | "success" | "warning" | "danger";

export interface ToastProps {
  id?: string;
  tone?: ToastTone;
  title: string;
  message?: string;
  onDismiss?: () => void;
}

const ICONS = {
  info: <Info className="w-4 h-4 text-[#156170]" />,
  success: <CheckCircle2 className="w-4 h-4 text-[#246e2a]" />,
  warning: <AlertTriangle className="w-4 h-4 text-[#8c5d08]" />,
  danger: <AlertCircle className="w-4 h-4 text-[#a33227]" />,
};

export function Toast({
  tone = "info",
  title,
  message,
  onDismiss,
}: ToastProps) {
  return (
    <div
      role="status"
      className={[
        "toast-fluer flex items-start gap-3 w-full max-w-sm p-4 rounded-[10px]",
        "bg-white/85 dark:bg-[#1e1e1b]/85 backdrop-blur-[14px] border border-[var(--border-hairline,#dedcd7)]",
        "shadow-[0_6px_12px_-2px_rgba(22,22,20,0.08),0_2px_4px_rgba(22,22,20,0.04)] select-none",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span className="shrink-0 mt-0.5">{ICONS[tone]}</span>
      <div className="flex-1 grid gap-0.5">
        <h4 className="text-sm font-medium text-[var(--text-strong,#161614)] m-0">{title}</h4>
        {message ? (
          <p className="text-xs text-[var(--text-muted,#57544d)] m-0">{message}</p>
        ) : null}
      </div>
      {onDismiss ? (
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Schließen"
          className="shrink-0 p-1 -mr-1 -mt-1 rounded-[6px] text-[var(--n-600,#57544d)] hover:bg-[var(--n-50,#f4f3f0)] hover:text-[var(--n-900,#161614)] transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      ) : null}
    </div>
  );
}
