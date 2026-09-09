/** Immediate-effect toggle for settings rows. */
export interface SwitchProps {
  label?: React.ReactNode;
  description?: React.ReactNode;
  checked?: boolean;
  onChange?: (next: boolean) => void;
  disabled?: boolean;
  style?: React.CSSProperties;
}
export declare function Switch(props: SwitchProps): JSX.Element;
