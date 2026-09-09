import React from "react";
import { Loader2 } from "lucide-react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  icon?: React.ReactNode;
  iconAfter?: React.ReactNode;
  fullWidth?: boolean;
  loading?: boolean;
}

const SIZE_CLASSES = {
  sm: "h-[30px] px-3 text-xs rounded-[6px] gap-1.5",
  md: "h-[38px] px-4 text-sm rounded-[10px] gap-2",
  lg: "h-[46px] px-5 text-[15px] rounded-[10px] gap-2.5",
};

const VARIANT_CLASSES = {
  primary:
    "btn-primary bg-[#17518c] text-white border border-[#123d6a] hover:bg-[#123d6a] shadow-[0_1px_2px_rgba(22,22,20,0.06)] focus-visible:ring-2 focus-visible:ring-[#17518c]/30",
  secondary:
    "btn-secondary bg-[var(--n-0,#ffffff)] text-[var(--n-900,#161614)] border border-[var(--n-200,#c7c4bd)] hover:bg-[var(--n-25,#fbfbf9)] hover:border-[var(--n-400,#8c887f)] shadow-[0_1px_2px_rgba(22,22,20,0.04)] focus-visible:ring-2 focus-visible:ring-[#17518c]/20",
  ghost:
    "btn-ghost bg-transparent text-[var(--n-700,#3f3d38)] border border-transparent hover:bg-[var(--n-50,#f4f3f0)] hover:text-[var(--n-900,#161614)] focus-visible:ring-2 focus-visible:ring-[#17518c]/20",
  danger:
    "btn-danger bg-[var(--n-0,#ffffff)] text-[#a33227] border border-[#a33227]/30 hover:bg-[#faeceb] hover:border-[#a33227]/50 shadow-[0_1px_2px_rgba(22,22,20,0.04)] focus-visible:ring-2 focus-visible:ring-[#a33227]/20",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = "primary",
      size = "md",
      icon,
      iconAfter,
      fullWidth = false,
      loading = false,
      disabled = false,
      className = "",
      type = "button",
      ...rest
    },
    ref
  ) => {
    const isDisabled = disabled || loading;
    const sizeCls = SIZE_CLASSES[size] || SIZE_CLASSES.md;
    const variantCls = VARIANT_CLASSES[variant] || VARIANT_CLASSES.primary;

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        className={[
          "btn-fluer inline-flex items-center justify-center font-medium font-sans whitespace-nowrap transition-all duration-150 select-none",
          "active:translate-y-[0.5px] disabled:opacity-45 disabled:pointer-events-none disabled:cursor-not-allowed",
          fullWidth ? "w-full" : "",
          sizeCls,
          variantCls,
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        {...rest}
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin shrink-0" /> : icon ? <span className="shrink-0">{icon}</span> : null}
        {children}
        {!loading && iconAfter ? <span className="shrink-0">{iconAfter}</span> : null}
      </button>
    );
  }
);

Button.displayName = "Button";
