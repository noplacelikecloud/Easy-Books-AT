/** Small status marker — state, not decoration. */
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: "neutral" | "brand" | "success" | "warning" | "danger" | "info";
  /** Leading status dot. */
  dot?: boolean;
}
export declare function Badge(props: BadgeProps): JSX.Element;
