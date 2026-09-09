/** Removable metadata chip — the one place a pill radius is correct. */
export interface TagProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Show a remove affordance and handle the click. */
  onRemove?: () => void;
}
export declare function Tag(props: TagProps): JSX.Element;
