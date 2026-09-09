import React from "react";

const ICON_BASE = "https://unpkg.com/lucide-static@0.544.0/icons/";
const ICON_CACHE = {};

/* Lucide (CDN) inlined as SVG so it inherits currentColor and rasterises in exports. */
export function Icon({ name = "circle", size = 18, style, ...rest }) {
  const [markup, setMarkup] = React.useState(ICON_CACHE[name] || null);
  React.useEffect(() => {
    let alive = true;
    if (ICON_CACHE[name]) { setMarkup(ICON_CACHE[name]); return; }
    fetch(ICON_BASE + name + ".svg")
      .then((r) => (r.ok ? r.text() : ""))
      .then((t) => {
        const svg = t
          .replace(/width="24"/, 'width="100%"')
          .replace(/height="24"/, 'height="100%"')
          .replace(/stroke="currentColor"/, 'stroke="currentColor"');
        ICON_CACHE[name] = svg;
        if (alive) setMarkup(svg);
      })
      .catch(() => {});
    return () => { alive = false; };
  }, [name]);
  return (
    <span
      aria-hidden="true"
      {...rest}
      dangerouslySetInnerHTML={markup ? { __html: markup } : undefined}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: size,
        height: size,
        flex: "0 0 auto",
        color: "inherit",
        ...style,
      }}
    />
  );
}
