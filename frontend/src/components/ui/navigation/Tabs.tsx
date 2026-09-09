import React from "react";

export interface TabItem {
  id: string;
  label: string;
  count?: number;
  disabled?: boolean;
}

export interface TabsProps {
  items: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
}

export function Tabs({
  items,
  activeId,
  onChange,
  className = "",
}: TabsProps) {
  return (
    <nav
      className={[
        "tabs-fluer flex items-center gap-1 border-b border-[var(--border-hairline,#dedcd7)]",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="Tabs"
    >
      {items.map((tab) => {
        const isActive = tab.id === activeId;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            disabled={tab.disabled}
            onClick={() => !tab.disabled && onChange(tab.id)}
            className={[
              "relative px-4 py-2.5 text-sm font-medium transition-colors select-none whitespace-nowrap outline-none",
              isActive
                ? "tab-active text-[#17518c] font-semibold"
                : "text-[var(--n-600,#57544d)] hover:text-[var(--n-900,#161614)] hover:bg-[var(--n-50,#f4f3f0)]/50",
              tab.disabled ? "opacity-40 cursor-not-allowed" : "cursor-pointer",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            <span className="flex items-center gap-2">
              {tab.label}
              {tab.count !== undefined ? (
                <span
                  className={[
                    "text-[11px] px-1.5 py-0.5 rounded-[3px] font-mono",
                    isActive
                      ? "bg-[#eaf1f7] text-[#17518c]"
                      : "bg-[var(--n-100,#dedcd7)] text-[var(--n-700,#3f3d38)]",
                  ].join(" ")}
                >
                  {tab.count}
                </span>
              ) : null}
            </span>

            {isActive ? (
              <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-[#17518c] rounded-t-sm" />
            ) : null}
          </button>
        );
      })}
    </nav>
  );
}
