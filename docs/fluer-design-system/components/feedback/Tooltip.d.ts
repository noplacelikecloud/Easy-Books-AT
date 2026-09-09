/** Dark hint on hover / focus. Label only — never interactive content. */
export interface TooltipProps {
  children?: React.ReactNode;
  content?: React.ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  style?: React.CSSProperties;
}
export declare function Tooltip(props: TooltipProps): JSX.Element;
