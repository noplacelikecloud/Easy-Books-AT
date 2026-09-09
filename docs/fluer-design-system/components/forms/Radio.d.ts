/** One-of-many choice; group by shared `name`. */
export interface RadioProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: React.ReactNode;
  description?: React.ReactNode;
  checked?: boolean;
  name?: string;
}
export declare function Radio(props: RadioProps): JSX.Element;
