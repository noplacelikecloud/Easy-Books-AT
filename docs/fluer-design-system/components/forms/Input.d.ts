/** Text field, single- or multi-line, with label / hint / error. */
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  /** Replaces hint and turns the border red. */
  error?: string;
  /** Lucide slug for a leading glyph (single-line only). */
  icon?: string;
  multiline?: boolean;
  rows?: number;
}
export declare function Input(props: InputProps): JSX.Element;
