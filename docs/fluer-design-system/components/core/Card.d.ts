/** Quiet container: hairline border, 14px radius, soft shadow. */
export interface CardProps extends React.HTMLAttributes<HTMLElement> {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  /** Buttons / IconButtons aligned right in the header. */
  actions?: React.ReactNode;
  footer?: React.ReactNode;
  padding?: "sm" | "md" | "lg";
  /** Adds a hover lift for clickable cards. */
  interactive?: boolean;
  tone?: "default" | "sunken";
}
export declare function Card(props: CardProps): JSX.Element;
