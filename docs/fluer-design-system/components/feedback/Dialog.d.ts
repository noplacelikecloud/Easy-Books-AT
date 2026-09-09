/** Modal for decisions and short focused forms. */
export interface DialogProps {
  open?: boolean;
  title?: React.ReactNode;
  description?: React.ReactNode;
  children?: React.ReactNode;
  /** Action row, right-aligned: secondary then primary. */
  footer?: React.ReactNode;
  onClose?: () => void;
  /** Width in px. Default 460. */
  width?: number;
  style?: React.CSSProperties;
}
export declare function Dialog(props: DialogProps): JSX.Element | null;
