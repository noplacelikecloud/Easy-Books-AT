/** Markenzeichen: Wolke mit ausgestanztem Prompt-Zeichen `›_`. */
export interface LogoProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Höhe der Wolke in px. Default 28. Minimum 22. */
  size?: number;
  /** Wortmarke „Fluer" rechts neben dem Zeichen. */
  showWordmark?: boolean;
}
export declare function Logo(props: LogoProps): JSX.Element;
