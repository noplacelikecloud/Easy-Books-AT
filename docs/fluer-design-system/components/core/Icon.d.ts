/** Lucide icon rendered as a currentColor mask. */
export interface IconProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Lucide icon slug, e.g. "arrow-right", "cloud", "settings". */
  name?: string;
  /** Square size in px. Default 18. */
  size?: number;
  style?: React.CSSProperties;
}
export declare function Icon(props: IconProps): JSX.Element;
