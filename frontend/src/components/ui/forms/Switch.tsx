import React from "react";

export interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  id?: string;
  className?: string;
}

export function Switch({
  checked,
  onChange,
  label,
  disabled = false,
  id,
  className = "",
}: SwitchProps) {
  const switchId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <label
      htmlFor={switchId}
      className={[
        "inline-flex items-center gap-3 select-none cursor-pointer text-sm text-[var(--n-900,#161614)]",
        disabled ? "opacity-50 cursor-not-allowed" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <button
        id={switchId}
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={[
          "switch-fluer relative inline-flex h-[20px] w-[36px] shrink-0 rounded-full border border-transparent transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#17518c]/30",
          checked ? "bg-[#17518c]" : "bg-[var(--n-200,#c7c4bd)]",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <span
          className={[
            "pointer-events-none inline-block h-[16px] w-[16px] transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out my-auto ml-0.5",
            checked ? "translate-x-[16px]" : "translate-x-0",
          ]
            .filter(Boolean)
            .join(" ")}
        />
      </button>
      {label ? <span>{label}</span> : null}
    </label>
  );
}
