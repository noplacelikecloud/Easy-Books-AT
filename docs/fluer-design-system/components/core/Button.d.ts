/**
 * Primary action control.
 */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  /** Lucide icon slug rendered before the label. */
  icon?: string;
  /** Lucide icon slug rendered after the label. */
  iconAfter?: string;
  fullWidth?: boolean;
  disabled?: boolean;
}
export declare function Button(props: ButtonProps): JSX.Element;
