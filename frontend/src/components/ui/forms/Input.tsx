import React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, error, icon, className = "", id, ...rest }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="w-full flex flex-col gap-1.5">
        {label ? (
          <label
            htmlFor={inputId}
            className="text-xs font-medium text-[var(--n-800,#282724)] select-none"
          >
            {label}
          </label>
        ) : null}

        <div className="relative flex items-center">
          {icon ? (
            <span className="absolute left-3 text-[var(--n-400,#8c887f)] pointer-events-none shrink-0">
              {icon}
            </span>
          ) : null}

          <input
            ref={ref}
            id={inputId}
            className={[
              "input-fluer w-full h-[38px] px-3.5 text-sm rounded-[10px] bg-[var(--n-0,#ffffff)] text-[var(--n-900,#161614)] border transition-all duration-150 outline-none",
              error
                ? "border-[#a33227] focus:ring-2 focus:ring-[#a33227]/20 focus:border-[#a33227]"
                : "border-[var(--n-200,#c7c4bd)] focus:border-[#17518c] focus:ring-2 focus:ring-[#17518c]/20 hover:border-[var(--n-400,#8c887f)]",
              icon ? "pl-9" : "",
              "disabled:bg-[var(--n-50,#f4f3f0)] disabled:text-[var(--n-400,#8c887f)] disabled:cursor-not-allowed",
              className,
            ]
              .filter(Boolean)
              .join(" ")}
            {...rest}
          />
        </div>

        {error ? (
          <p className="text-xs text-[#a33227] m-0">{error}</p>
        ) : hint ? (
          <p className="text-xs text-[var(--n-600,#57544d)] m-0">{hint}</p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = "Input";
