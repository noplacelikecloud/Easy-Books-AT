/** Native select styled to match Input. */
export interface SelectOption { value: string; label: string }
export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  hint?: string;
  /** Strings or {value,label} pairs. */
  options?: (string | SelectOption)[];
}
export declare function Select(props: SelectProps): JSX.Element;
