/** Square, label-less action for toolbars, table rows and card headers. */
export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Lucide icon slug. */
  icon?: string;
  size?: "sm" | "md" | "lg";
  variant?: "ghost" | "outline";
  /** Accessible label — also the tooltip title. */
  label?: string;
}
export declare function IconButton(props: IconButtonProps): JSX.Element;
