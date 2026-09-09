import React from "react";

export interface TableProps extends React.TableHTMLAttributes<HTMLTableElement> {
  containerClassName?: string;
  children: React.ReactNode;
}

export function Table({
  children,
  className = "",
  containerClassName = "",
  ...rest
}: TableProps) {
  return (
    <div
      className={[
        "table-fluer-container w-full overflow-x-auto rounded-[14px] border border-[var(--border-hairline,#dedcd7)] bg-[var(--bg-card,#ffffff)] shadow-[0_1px_2px_rgba(22,22,20,0.04)]",
        containerClassName,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <table
        className={[
          "table-fluer w-full text-left border-collapse",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        {...rest}
      >
        {children}
      </table>
    </div>
  );
}

export function TableHeader({
  children,
  className = "",
  ...rest
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead
      className={[
        "bg-[var(--n-25,#fbfbf9)] border-b border-[var(--border-hairline,#dedcd7)]",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {children}
    </thead>
  );
}

export function TableBody({
  children,
  className = "",
  ...rest
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody
      className={["divide-y divide-[var(--border-hairline,#dedcd7)]", className]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {children}
    </tbody>
  );
}

export function TableRow({
  children,
  className = "",
  ...rest
}: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={[
        "transition-colors duration-100 hover:bg-[var(--n-50,#f4f3f0)]/80 dark:hover:bg-[#252118]",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {children}
    </tr>
  );
}

export function TableHead({
  children,
  align = "left",
  className = "",
  ...rest
}: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={[
        "px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-[var(--n-600,#57544d)] whitespace-nowrap select-none",
        align === "right" ? "text-right" : align === "center" ? "text-center" : "text-left",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {children}
    </th>
  );
}

export interface TableCellProps extends React.TdHTMLAttributes<HTMLTableCellElement> {
  mono?: boolean;
}

export function TableCell({
  children,
  align = "left",
  mono = false,
  className = "",
  ...rest
}: TableCellProps) {
  return (
    <td
      className={[
        "px-4 py-3 text-sm text-[var(--n-800,#282724)] whitespace-nowrap",
        mono ? "font-mono tabular-nums text-[13px] text-[var(--n-900,#161614)]" : "",
        align === "right" ? "text-right" : align === "center" ? "text-center" : "text-left",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {children}
    </td>
  );
}
