/** Underlined tab bar for switching views inside one page. */
export interface TabItem { value: string; label: string; icon?: string; count?: number }
export interface TabsProps {
  items?: (string | TabItem)[];
  /** Controlled value; omit for internal state. */
  value?: string;
  onChange?: (value: string) => void;
  style?: React.CSSProperties;
}
export declare function Tabs(props: TabsProps): JSX.Element;
