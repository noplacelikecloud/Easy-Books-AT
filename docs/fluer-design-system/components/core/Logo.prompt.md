One-line: das Markenzeichen — Wolke (Cloud) mit ausgestanztem Prompt-Zeichen `›_` (Development), immer als Vektor, nie als Bilddatei mit fester Farbe.

```jsx
<Logo size={28} showWordmark />
```

Die Wortmarke lautet immer „Fluer Development" — „Fluer" in Semibold, „Development" in Regular und `--text-muted`. Die Wolke nimmt `--text-brand`, die Wortmarke die Textfarbe des Elternelements. Auf dunklem Grund: `style={{ color: "var(--text-inverse)" }}` am Logo setzen und die Wolke über `--blue-300` aufhellen. Minimale Höhe 22px — darunter wird die Aussparung `›_` unleserlich; unter 22px stattdessen nur die Wortmarke setzen. Nie verzerren, nie einfärben außer Markenblau, Weiß oder Tinte.
