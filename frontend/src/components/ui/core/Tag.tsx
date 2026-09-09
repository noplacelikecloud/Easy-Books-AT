import React from "react";
import { X } from "lucide-react";

export interface TagProps extends React.HTMLAttributes<HTMLSpanElement> {
  onRemove?: () => void;
  children: React.ReactNode;
}

export function Tag({
  children,
  onRemove,
  className = "",
  ...rest
}: TagProps) {
  return (
    <span
      className={[
        "tag-fluer inline-flex items-center gap-1.5 h-[24px] px-2.5 rounded-full border border-[var(--n-200,#c7c4bd)] bg-[var(--n-50,#f4f3f0)] text-[var(--n-800,#282724)] text-xs font-medium tracking-tight whitespace-nowrap select-none",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {children}
      {onRemove ? (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="hover:bg-[var(--n-200,#c7c4bd)] rounded-full p-0.5 text-[var(--n-600,#57544d)] hover:text-[var(--n-900,#161614)] transition-colors -mr-1"
          aria-label="Entfernen"
        >
          <X className="w-3 h-3" />
        </button>
      ) : null}
    </span>
  );
}
