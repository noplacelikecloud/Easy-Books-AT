import React from "react";
import { Loader2 } from "lucide-react";

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  icon: React.ReactNode;
  "aria-label": string;
  loading?: boolean;
}

const ICON_SIZE_CLASSES = {
  sm: "w-[30px] h-[30px] rounded-[6px] text-xs",
  md: "w-[38px] h-[38px] rounded-[6px] text-sm",
  lg: "w-[46px] h-[46px] rounded-[6px] text-base",
};

const ICON_VARIANT_CLASSES = {
  secondary:
    "bg-[var(--n-0,#ffffff)] text-[var(--n-900,#161614)] border border-[var(--n-200,#c7c4bd)] hover:bg-[var(--n-25,#fbfbf9)] hover:border-[var(--n-400,#8c887f)] shadow-[0_1px_2px_rgba(22,22,20,0.04)] focus-visible:ring-2 focus-visible:ring-[#17518c]/20",
  ghost:
    "bg-transparent text-[var(--n-700,#3f3d38)] border border-transparent hover:bg-[var(--n-50,#f4f3f0)] hover:text-[var(--n-900,#161614)] focus-visible:ring-2 focus-visible:ring-[#17518c]/20",
  danger:
    "bg-[var(--n-0,#ffffff)] text-[#a33227] border border-[#a33227]/30 hover:bg-[#faeceb] hover:border-[#a33227]/50 shadow-[0_1px_2px_rgba(22,22,20,0.04)] focus-visible:ring-2 focus-visible:ring-[#a33227]/20",
};

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      variant = "secondary",
      size = "md",
      icon,
      "aria-label": ariaLabel,
      loading = false,
      disabled = false,
      className = "",
      type = "button",
      ...rest
    },
    ref
  ) => {
    const isDisabled = disabled || loading;
    const sizeCls = ICON_SIZE_CLASSES[size] || ICON_SIZE_CLASSES.md;
    const variantCls = ICON_VARIANT_CLASSES[variant] || ICON_VARIANT_CLASSES.secondary;

    return (
      <button
        ref={ref}
        type={type}
        aria-label={ariaLabel}
        disabled={isDisabled}
        className={[
          "btn-fluer btn-icon inline-flex items-center justify-center transition-all duration-150 select-none shrink-0",
          "active:translate-y-[0.5px] disabled:opacity-45 disabled:pointer-events-none disabled:cursor-not-allowed",
          sizeCls,
          variantCls,
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        {...rest}
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin shrink-0" /> : icon}
      </button>
    );
  }
);

IconButton.displayName = "IconButton";
