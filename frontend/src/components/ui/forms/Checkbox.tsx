import React from "react";
import { Check } from "lucide-react";

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, className = "", id, checked, defaultChecked, onChange, disabled, ...rest }, ref) => {
    const checkboxId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);
    const [isChecked, setIsChecked] = React.useState(defaultChecked || false);
    const resolvedChecked = checked !== undefined ? checked : isChecked;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      if (checked === undefined) {
        setIsChecked(e.target.checked);
      }
      onChange?.(e);
    };

    return (
      <label
        htmlFor={checkboxId}
        className={[
          "inline-flex items-center gap-2.5 select-none cursor-pointer text-sm text-[var(--n-900,#161614)]",
          disabled ? "opacity-50 cursor-not-allowed" : "",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <div className="relative inline-flex items-center justify-center shrink-0">
          <input
            ref={ref}
            id={checkboxId}
            type="checkbox"
            checked={resolvedChecked}
            onChange={handleChange}
            disabled={disabled}
            className="peer sr-only"
            {...rest}
          />
          <div
            className={[
              "checkbox-fluer w-[18px] h-[18px] rounded-[3px] border transition-all duration-150 flex items-center justify-center",
              resolvedChecked
                ? "bg-[#17518c] border-[#17518c] text-white"
                : "bg-[var(--n-0,#ffffff)] border-[var(--n-200,#c7c4bd)] hover:border-[var(--n-400,#8c887f)]",
              "peer-focus-visible:ring-2 peer-focus-visible:ring-[#17518c]/30",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {resolvedChecked ? <Check className="w-3.5 h-3.5 stroke-[2.5]" /> : null}
          </div>
        </div>
        {label ? <span>{label}</span> : null}
      </label>
    );
  }
);

Checkbox.displayName = "Checkbox";
