import React from "react";
import { ChevronDown } from "lucide-react";

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  hint?: string;
  error?: string;
  options?: SelectOption[];
  children?: React.ReactNode;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, hint, error, options, children, className = "", id, ...rest }, ref) => {
    const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="w-full flex flex-col gap-1.5">
        {label ? (
          <label
            htmlFor={selectId}
            className="text-xs font-medium text-[var(--n-800,#282724)] select-none"
          >
            {label}
          </label>
        ) : null}

        <div className="relative flex items-center">
          <select
            ref={ref}
            id={selectId}
            className={[
              "select-fluer appearance-none w-full h-[38px] pl-3.5 pr-9 text-sm rounded-[10px] bg-[var(--n-0,#ffffff)] text-[var(--n-900,#161614)] border transition-all duration-150 outline-none cursor-pointer",
              error
                ? "border-[#a33227] focus:ring-2 focus:ring-[#a33227]/20 focus:border-[#a33227]"
                : "border-[var(--n-200,#c7c4bd)] focus:border-[#17518c] focus:ring-2 focus:ring-[#17518c]/20 hover:border-[var(--n-400,#8c887f)]",
              "disabled:bg-[var(--n-50,#f4f3f0)] disabled:text-[var(--n-400,#8c887f)] disabled:cursor-not-allowed",
              className,
            ]
              .filter(Boolean)
              .join(" ")}
            {...rest}
          >
            {options
              ? options.map((opt) => (
                  <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                    {opt.label}
                  </option>
                ))
              : children}
          </select>
          <ChevronDown className="w-4 h-4 text-[var(--n-600,#57544d)] absolute right-3 pointer-events-none shrink-0" />
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

Select.displayName = "Select";
