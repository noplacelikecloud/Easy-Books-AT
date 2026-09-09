/** Multi-select toggle with optional description line. */
export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: React.ReactNode;
  description?: React.ReactNode;
  checked?: boolean;
  disabled?: boolean;
}
export declare function Checkbox(props: CheckboxProps): JSX.Element;
