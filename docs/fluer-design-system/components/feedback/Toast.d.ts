/** Transient confirmation or failure notice, bottom-right of the viewport. */
export interface ToastProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: React.ReactNode;
  description?: React.ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger";
  /** Optional single Button, usually ghost/secondary. */
  action?: React.ReactNode;
  onClose?: () => void;
}
export declare function Toast(props: ToastProps): JSX.Element;
