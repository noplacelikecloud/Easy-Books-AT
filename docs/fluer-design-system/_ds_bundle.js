/* @ds-bundle: {"format":4,"namespace":"FluerDesignSystem_fde5f8","components":[{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"Icon","sourcePath":"components/core/Icon.jsx"},{"name":"IconButton","sourcePath":"components/core/IconButton.jsx"},{"name":"Logo","sourcePath":"components/core/Logo.jsx"},{"name":"Tag","sourcePath":"components/core/Tag.jsx"},{"name":"Dialog","sourcePath":"components/feedback/Dialog.jsx"},{"name":"Toast","sourcePath":"components/feedback/Toast.jsx"},{"name":"Tooltip","sourcePath":"components/feedback/Tooltip.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Checkbox.jsx"},{"name":"Input","sourcePath":"components/forms/Input.jsx"},{"name":"Radio","sourcePath":"components/forms/Radio.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Switch","sourcePath":"components/forms/Switch.jsx"},{"name":"Tabs","sourcePath":"components/navigation/Tabs.jsx"}],"sourceHashes":{"components/core/Badge.jsx":"1aa38ee55849","components/core/Button.jsx":"02ad815cb3cb","components/core/Card.jsx":"8b57714e514d","components/core/Icon.jsx":"e82ef4c31c16","components/core/IconButton.jsx":"945e715e784f","components/core/Logo.jsx":"5266d013b81c","components/core/Tag.jsx":"db70a89a6651","components/feedback/Dialog.jsx":"f61d3c44432d","components/feedback/Toast.jsx":"1e38d6e4e6cd","components/feedback/Tooltip.jsx":"2253269d2244","components/forms/Checkbox.jsx":"86631e46a4c5","components/forms/Input.jsx":"ebd3da64a26b","components/forms/Radio.jsx":"0a88f44968f3","components/forms/Select.jsx":"33746ed97de2","components/forms/Switch.jsx":"fed97c3ad266","components/navigation/Tabs.jsx":"19bdb301a642","ui_kits/console/AppShell.jsx":"69ce07e31975","ui_kits/console/screens.jsx":"9f30d7d1717e","ui_kits/website/HomePage.jsx":"52787ac1bca1","ui_kits/website/SiteChrome.jsx":"1b2e59fcc298"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.FluerDesignSystem_fde5f8 = window.FluerDesignSystem_fde5f8 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/core/Badge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const BADGE_TONES = {
  neutral: {
    bg: "var(--n-50)",
    fg: "var(--text-body)",
    bd: "var(--border-default)"
  },
  brand: {
    bg: "var(--surface-brand-soft)",
    fg: "var(--blue-600)",
    bd: "var(--border-brand)"
  },
  success: {
    bg: "var(--state-success-bg)",
    fg: "var(--state-success-fg)",
    bd: "rgba(74,122,82,0.22)"
  },
  warning: {
    bg: "var(--state-warning-bg)",
    fg: "var(--state-warning-fg)",
    bd: "rgba(180,114,26,0.22)"
  },
  danger: {
    bg: "var(--state-danger-bg)",
    fg: "var(--state-danger-fg)",
    bd: "rgba(163,50,39,0.2)"
  },
  info: {
    bg: "var(--state-info-bg)",
    fg: "var(--state-info-fg)",
    bd: "rgba(47,93,140,0.2)"
  }
};
function Badge({
  children,
  tone = "neutral",
  dot = false,
  style,
  ...rest
}) {
  const t = BADGE_TONES[tone] || BADGE_TONES.neutral;
  return /*#__PURE__*/React.createElement("span", _extends({}, rest, {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      height: 22,
      padding: "0 8px",
      borderRadius: "var(--radius-xs)",
      background: t.bg,
      color: t.fg,
      border: `1px solid ${t.bd}`,
      fontSize: "var(--text-2xs)",
      fontWeight: "var(--fw-medium)",
      letterSpacing: "var(--tracking-label)",
      whiteSpace: "nowrap",
      ...style
    }
  }), dot ? /*#__PURE__*/React.createElement("span", {
    style: {
      width: 5,
      height: 5,
      borderRadius: "var(--radius-pill)",
      background: "currentColor"
    }
  }) : null, children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const CARD_PADS = {
  sm: "var(--space-6)",
  md: "var(--space-8)",
  lg: "var(--space-9)"
};
function Card({
  children,
  title,
  subtitle,
  actions,
  footer,
  padding = "md",
  interactive = false,
  tone = "default",
  style,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const pad = CARD_PADS[padding] || CARD_PADS.md;
  const lifted = interactive && hover;
  return /*#__PURE__*/React.createElement("section", _extends({
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false)
  }, rest, {
    style: {
      background: tone === "sunken" ? "var(--surface-sunken)" : "var(--surface-card)",
      border: `1px solid ${lifted ? "var(--border-default)" : "var(--border-hairline)"}`,
      borderRadius: "var(--radius-lg)",
      boxShadow: tone === "sunken" ? "none" : lifted ? "var(--shadow-md)" : "var(--shadow-sm)",
      transition: "var(--transition-control)",
      overflow: "hidden",
      ...style
    }
  }), title || actions ? /*#__PURE__*/React.createElement("header", {
    style: {
      display: "flex",
      alignItems: "flex-start",
      justifyContent: "space-between",
      gap: "var(--space-6)",
      padding: `${pad} ${pad} 0`
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: 4
    }
  }, title ? /*#__PURE__*/React.createElement("h3", {
    style: {
      fontSize: "var(--text-lg)",
      fontWeight: "var(--fw-semibold)",
      color: "var(--text-strong)",
      letterSpacing: "var(--tracking-heading)",
      margin: 0
    }
  }, title) : null, subtitle ? /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)",
      margin: 0
    }
  }, subtitle) : null), actions ? /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-3)",
      flex: "0 0 auto"
    }
  }, actions) : null) : null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: pad
    }
  }, children), footer ? /*#__PURE__*/React.createElement("footer", {
    style: {
      padding: `var(--space-5) ${pad}`,
      borderTop: "1px solid var(--border-hairline)",
      background: "var(--n-25)",
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, footer) : null);
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/Icon.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const ICON_BASE = "https://unpkg.com/lucide-static@0.544.0/icons/";
const ICON_CACHE = {};

/* Lucide (CDN) inlined as SVG so it inherits currentColor and rasterises in exports. */
function Icon({
  name = "circle",
  size = 18,
  style,
  ...rest
}) {
  const [markup, setMarkup] = React.useState(ICON_CACHE[name] || null);
  React.useEffect(() => {
    let alive = true;
    if (ICON_CACHE[name]) {
      setMarkup(ICON_CACHE[name]);
      return;
    }
    fetch(ICON_BASE + name + ".svg").then(r => r.ok ? r.text() : "").then(t => {
      const svg = t.replace(/width="24"/, 'width="100%"').replace(/height="24"/, 'height="100%"').replace(/stroke="currentColor"/, 'stroke="currentColor"');
      ICON_CACHE[name] = svg;
      if (alive) setMarkup(svg);
    }).catch(() => {});
    return () => {
      alive = false;
    };
  }, [name]);
  return /*#__PURE__*/React.createElement("span", _extends({
    "aria-hidden": "true"
  }, rest, {
    dangerouslySetInnerHTML: markup ? {
      __html: markup
    } : undefined,
    style: {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: size,
      height: size,
      flex: "0 0 auto",
      color: "inherit",
      ...style
    }
  }));
}
Object.assign(__ds_scope, { Icon });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Icon.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const BTN_SIZES = {
  sm: {
    height: 30,
    padding: "0 12px",
    font: "var(--text-xs)",
    radius: "var(--radius-sm)",
    gap: 6,
    icon: 14
  },
  md: {
    height: 38,
    padding: "0 16px",
    font: "var(--text-sm)",
    radius: "var(--radius-md)",
    gap: 8,
    icon: 16
  },
  lg: {
    height: 46,
    padding: "0 22px",
    font: "var(--text-md)",
    radius: "var(--radius-md)",
    gap: 9,
    icon: 18
  }
};
const BTN_VARIANTS = {
  primary: {
    rest: {
      background: "var(--surface-brand)",
      color: "var(--text-on-brand)",
      border: "1px solid var(--blue-600)",
      boxShadow: "var(--shadow-sm)"
    },
    hover: {
      background: "var(--blue-600)",
      boxShadow: "var(--shadow-brand)"
    }
  },
  secondary: {
    rest: {
      background: "var(--surface-card)",
      color: "var(--text-strong)",
      border: "1px solid var(--border-default)",
      boxShadow: "var(--shadow-xs)"
    },
    hover: {
      background: "var(--n-25)",
      border: "1px solid var(--border-strong)"
    }
  },
  ghost: {
    rest: {
      background: "transparent",
      color: "var(--text-body)",
      border: "1px solid transparent",
      boxShadow: "none"
    },
    hover: {
      background: "var(--n-50)",
      color: "var(--text-strong)"
    }
  },
  danger: {
    rest: {
      background: "var(--surface-card)",
      color: "var(--state-danger-fg)",
      border: "1px solid var(--red-100)",
      boxShadow: "var(--shadow-xs)"
    },
    hover: {
      background: "var(--state-danger-bg)",
      border: "1px solid rgba(163,50,39,0.28)"
    }
  }
};
function Button({
  children,
  variant = "primary",
  size = "md",
  icon,
  iconAfter,
  fullWidth = false,
  disabled = false,
  style,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const [press, setPress] = React.useState(false);
  const s = BTN_SIZES[size] || BTN_SIZES.md;
  const v = BTN_VARIANTS[variant] || BTN_VARIANTS.primary;
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    disabled: disabled,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => {
      setHover(false);
      setPress(false);
    },
    onMouseDown: () => setPress(true),
    onMouseUp: () => setPress(false)
  }, rest, {
    style: {
      display: fullWidth ? "flex" : "inline-flex",
      width: fullWidth ? "100%" : undefined,
      alignItems: "center",
      justifyContent: "center",
      gap: s.gap,
      height: s.height,
      padding: s.padding,
      borderRadius: s.radius,
      fontFamily: "var(--font-sans)",
      fontSize: s.font,
      fontWeight: "var(--fw-medium)",
      letterSpacing: "var(--tracking-label)",
      whiteSpace: "nowrap",
      flexShrink: 0,
      cursor: disabled ? "not-allowed" : "pointer",
      transition: "var(--transition-control), transform var(--dur-instant) var(--ease-standard)",
      opacity: disabled ? 0.45 : 1,
      transform: press && !disabled ? "translateY(0.5px)" : "none",
      ...v.rest,
      ...(hover && !disabled ? v.hover : null),
      ...style
    }
  }), icon ? /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: s.icon
  }) : null, children, iconAfter ? /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: iconAfter,
    size: s.icon
  }) : null);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/IconButton.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const IB_SIZES = {
  sm: {
    box: 28,
    icon: 14
  },
  md: {
    box: 34,
    icon: 16
  },
  lg: {
    box: 40,
    icon: 18
  }
};
function IconButton({
  icon = "more-horizontal",
  size = "md",
  variant = "ghost",
  label,
  disabled = false,
  style,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const s = IB_SIZES[size] || IB_SIZES.md;
  const outlined = variant === "outline";
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    "aria-label": label,
    title: label,
    disabled: disabled,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false)
  }, rest, {
    style: {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: s.box,
      height: s.box,
      borderRadius: "var(--radius-sm)",
      background: outlined ? "var(--surface-card)" : hover ? "var(--n-50)" : "transparent",
      border: outlined ? "1px solid var(--border-default)" : "1px solid transparent",
      color: hover && !disabled ? "var(--text-strong)" : "var(--text-muted)",
      boxShadow: outlined ? "var(--shadow-xs)" : "none",
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.4 : 1,
      transition: "var(--transition-control)",
      ...style
    }
  }), /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: s.icon
  }));
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/core/Logo.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/* Marke: Wolke (Cloud) mit ausgestanztem Prompt-Zeichen ›_ (Development). */
function Logo({
  size = 28,
  showWordmark = false,
  style,
  ...rest
}) {
  const uid = React.useId().replace(/:/g, "");
  const h = size;
  const w = 48 / 32 * h;
  return /*#__PURE__*/React.createElement("span", _extends({}, rest, {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: h * 0.32,
      color: "var(--text-strong)",
      ...style
    }
  }), /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 48 32",
    width: w,
    height: h,
    role: "img",
    "aria-label": "Fluer Development",
    style: {
      display: "block",
      color: "var(--text-brand)",
      flex: "0 0 auto"
    }
  }, /*#__PURE__*/React.createElement("mask", {
    id: "fluerCut" + uid
  }, /*#__PURE__*/React.createElement("rect", {
    x: "0",
    y: "0",
    width: "48",
    height: "32",
    fill: "#fff"
  }), /*#__PURE__*/React.createElement("g", {
    fill: "none",
    stroke: "#000",
    strokeWidth: "3",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M17.6 13.4 L22.6 18.2 L17.6 23"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M25.6 23 H32.4"
  }))), /*#__PURE__*/React.createElement("g", {
    mask: `url(#fluerCut${uid})`,
    fill: "currentColor"
  }, /*#__PURE__*/React.createElement("rect", {
    x: "7",
    y: "15",
    width: "34",
    height: "10",
    rx: "5"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "17",
    cy: "15",
    r: "8"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "29",
    cy: "13",
    r: "10"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "38",
    cy: "18",
    r: "6"
  }))), showWordmark ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: h * 0.78,
      fontWeight: "var(--fw-semibold)",
      letterSpacing: "-0.03em",
      color: "inherit",
      whiteSpace: "nowrap"
    }
  }, "Fluer ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: "var(--fw-regular)",
      color: "var(--text-muted)"
    }
  }, "Development")) : null);
}
Object.assign(__ds_scope, { Logo });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Logo.jsx", error: String((e && e.message) || e) }); }

// components/core/Tag.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function Tag({
  children,
  onRemove,
  style,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  return /*#__PURE__*/React.createElement("span", _extends({
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false)
  }, rest, {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      height: 26,
      padding: onRemove ? "0 6px 0 10px" : "0 10px",
      borderRadius: "var(--radius-pill)",
      background: "var(--surface-card)",
      border: `1px solid ${hover ? "var(--border-strong)" : "var(--border-default)"}`,
      color: "var(--text-body)",
      fontSize: "var(--text-xs)",
      transition: "var(--transition-control)",
      ...style
    }
  }), children, onRemove ? /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: onRemove,
    "aria-label": "Entfernen",
    style: {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: 16,
      height: 16,
      padding: 0,
      border: "none",
      background: "transparent",
      color: "var(--text-faint)",
      cursor: "pointer"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "x",
    size: 12
  })) : null);
}
Object.assign(__ds_scope, { Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Tag.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Dialog.jsx
try { (() => {
function Dialog({
  open = true,
  title,
  description,
  children,
  footer,
  onClose,
  width = 460,
  style
}) {
  if (!open) return null;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      inset: 0,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "var(--space-8)",
      background: "var(--overlay-scrim)",
      backdropFilter: "blur(var(--blur-scrim))",
      WebkitBackdropFilter: "blur(var(--blur-scrim))",
      zIndex: 60
    },
    onClick: onClose
  }, /*#__PURE__*/React.createElement("div", {
    role: "dialog",
    "aria-modal": "true",
    onClick: e => e.stopPropagation(),
    style: {
      width,
      maxWidth: "100%",
      background: "var(--surface-card)",
      border: "1px solid var(--border-hairline)",
      borderRadius: "var(--radius-xl)",
      boxShadow: "var(--shadow-lg)",
      overflow: "hidden",
      animation: "none",
      ...style
    }
  }, /*#__PURE__*/React.createElement("header", {
    style: {
      display: "flex",
      alignItems: "flex-start",
      gap: "var(--space-6)",
      padding: "var(--space-8) var(--space-8) 0"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: 5,
      flex: 1
    }
  }, title ? /*#__PURE__*/React.createElement("h3", {
    style: {
      margin: 0,
      fontSize: "var(--text-xl)",
      fontWeight: "var(--fw-semibold)",
      color: "var(--text-strong)",
      letterSpacing: "var(--tracking-heading)"
    }
  }, title) : null, description ? /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, description) : null), onClose ? /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: onClose,
    "aria-label": "Schlie\xDFen",
    style: {
      border: "none",
      background: "transparent",
      color: "var(--text-faint)",
      cursor: "pointer",
      padding: 3,
      display: "inline-flex"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "x",
    size: 16
  })) : null), children ? /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-7) var(--space-8)"
    }
  }, children) : /*#__PURE__*/React.createElement("div", {
    style: {
      height: "var(--space-7)"
    }
  }), footer ? /*#__PURE__*/React.createElement("footer", {
    style: {
      display: "flex",
      justifyContent: "flex-end",
      gap: "var(--space-4)",
      padding: "var(--space-6) var(--space-8)",
      borderTop: "1px solid var(--border-hairline)",
      background: "var(--n-25)"
    }
  }, footer) : null));
}
Object.assign(__ds_scope, { Dialog });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Dialog.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Toast.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const TOAST_TONES = {
  neutral: {
    icon: "info",
    fg: "var(--text-strong)",
    accent: "var(--n-400)"
  },
  success: {
    icon: "check-circle",
    fg: "var(--state-success-fg)",
    accent: "var(--moss-500)"
  },
  warning: {
    icon: "alert-triangle",
    fg: "var(--state-warning-fg)",
    accent: "var(--amber-500)"
  },
  danger: {
    icon: "alert-octagon",
    fg: "var(--state-danger-fg)",
    accent: "var(--red-500)"
  }
};
function Toast({
  title,
  description,
  tone = "neutral",
  action,
  onClose,
  style,
  ...rest
}) {
  const t = TOAST_TONES[tone] || TOAST_TONES.neutral;
  return /*#__PURE__*/React.createElement("div", _extends({
    role: "status"
  }, rest, {
    style: {
      display: "flex",
      alignItems: "flex-start",
      gap: 10,
      minWidth: 300,
      maxWidth: 420,
      padding: "12px 14px",
      borderRadius: "var(--radius-md)",
      background: "var(--surface-glass)",
      backdropFilter: "blur(var(--blur-glass))",
      WebkitBackdropFilter: "blur(var(--blur-glass))",
      border: "1px solid var(--border-default)",
      boxShadow: "var(--shadow-lg)",
      ...style
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      color: t.accent,
      marginTop: 1
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: t.icon,
    size: 16
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: 2,
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)",
      fontWeight: "var(--fw-medium)",
      color: "var(--text-strong)"
    }
  }, title), description ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, description) : null, action ? /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 6
    }
  }, action) : null), onClose ? /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: onClose,
    "aria-label": "Schlie\xDFen",
    style: {
      border: "none",
      background: "transparent",
      color: "var(--text-faint)",
      cursor: "pointer",
      padding: 2,
      display: "inline-flex"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "x",
    size: 14
  })) : null);
}
Object.assign(__ds_scope, { Toast });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Toast.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Tooltip.jsx
try { (() => {
function Tooltip({
  children,
  content,
  side = "top",
  style
}) {
  const [open, setOpen] = React.useState(false);
  const pos = {
    top: {
      bottom: "calc(100% + 7px)",
      left: "50%",
      transform: "translateX(-50%)"
    },
    bottom: {
      top: "calc(100% + 7px)",
      left: "50%",
      transform: "translateX(-50%)"
    },
    right: {
      left: "calc(100% + 7px)",
      top: "50%",
      transform: "translateY(-50%)"
    },
    left: {
      right: "calc(100% + 7px)",
      top: "50%",
      transform: "translateY(-50%)"
    }
  }[side];
  return /*#__PURE__*/React.createElement("span", {
    onMouseEnter: () => setOpen(true),
    onMouseLeave: () => setOpen(false),
    onFocus: () => setOpen(true),
    onBlur: () => setOpen(false),
    style: {
      position: "relative",
      display: "inline-flex",
      ...style
    }
  }, children, /*#__PURE__*/React.createElement("span", {
    role: "tooltip",
    style: {
      position: "absolute",
      zIndex: 40,
      ...pos,
      padding: "5px 9px",
      borderRadius: "var(--radius-sm)",
      background: "var(--surface-inverse)",
      color: "var(--text-inverse)",
      border: "1px solid var(--border-inverse)",
      boxShadow: "var(--shadow-md)",
      fontSize: "var(--text-2xs)",
      lineHeight: 1.35,
      whiteSpace: "nowrap",
      pointerEvents: "none",
      opacity: open ? 1 : 0,
      transition: "opacity var(--dur-fast) var(--ease-standard)"
    }
  }, content));
}
Object.assign(__ds_scope, { Tooltip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Tooltip.jsx", error: String((e && e.message) || e) }); }

// components/forms/Checkbox.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function Checkbox({
  label,
  description,
  checked,
  onChange,
  disabled = false,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: "flex",
      gap: 10,
      alignItems: "flex-start",
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.5 : 1,
      ...style
    }
  }, /*#__PURE__*/React.createElement("input", _extends({
    type: "checkbox",
    checked: checked,
    onChange: onChange,
    disabled: disabled
  }, rest, {
    style: {
      position: "absolute",
      opacity: 0,
      width: 0,
      height: 0
    }
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: 18,
      height: 18,
      marginTop: 1,
      flex: "0 0 auto",
      borderRadius: "var(--radius-xs)",
      background: checked ? "var(--surface-brand)" : "var(--surface-card)",
      border: `1px solid ${checked ? "var(--blue-600)" : "var(--border-strong)"}`,
      color: "var(--text-on-brand)",
      boxShadow: checked ? "none" : "var(--shadow-inset-field)",
      transition: "var(--transition-control)"
    }
  }, checked ? /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "check",
    size: 12
  }) : null), /*#__PURE__*/React.createElement("span", {
    style: {
      display: "grid",
      gap: 2
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-strong)"
    }
  }, label), description ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-2xs)",
      color: "var(--text-muted)"
    }
  }, description) : null));
}
Object.assign(__ds_scope, { Checkbox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Checkbox.jsx", error: String((e && e.message) || e) }); }

// components/forms/Input.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const FIELD_LABEL = {
  display: "block",
  fontSize: "var(--text-xs)",
  fontWeight: "var(--fw-medium)",
  color: "var(--text-strong)",
  letterSpacing: "var(--tracking-label)",
  marginBottom: 6
};
const FIELD_HINT = {
  fontSize: "var(--text-2xs)",
  color: "var(--text-muted)",
  marginTop: 6
};
const FIELD_CONTROL = {
  width: "100%",
  height: 38,
  padding: "0 12px",
  fontFamily: "var(--font-sans)",
  fontSize: "var(--text-sm)",
  color: "var(--text-strong)",
  background: "var(--surface-card)",
  border: "1px solid var(--border-default)",
  borderRadius: "var(--radius-md)",
  boxShadow: "var(--shadow-inset-field)",
  outline: "none",
  transition: "var(--transition-control)"
};
function Input({
  label,
  hint,
  error,
  icon,
  multiline = false,
  rows = 4,
  style,
  ...rest
}) {
  const [focus, setFocus] = React.useState(false);
  const border = error ? "var(--state-danger-fg)" : focus ? "var(--blue-400)" : "var(--border-default)";
  const Tag = multiline ? "textarea" : "input";
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: "block",
      ...style
    }
  }, label ? /*#__PURE__*/React.createElement("span", {
    style: FIELD_LABEL
  }, label) : null, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "relative",
      display: "block"
    }
  }, icon && !multiline ? /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      left: 11,
      top: 0,
      height: 38,
      display: "flex",
      alignItems: "center",
      color: "var(--text-faint)"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: 15
  })) : null, /*#__PURE__*/React.createElement(Tag, _extends({
    rows: multiline ? rows : undefined,
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false)
  }, rest, {
    style: {
      ...FIELD_CONTROL,
      height: multiline ? "auto" : 38,
      padding: multiline ? "10px 12px" : icon ? "0 12px 0 32px" : "0 12px",
      lineHeight: multiline ? "var(--lh-normal)" : undefined,
      resize: multiline ? "vertical" : undefined,
      borderColor: border,
      boxShadow: focus ? "var(--ring-focus)" : "var(--shadow-inset-field)"
    }
  }))), error ? /*#__PURE__*/React.createElement("span", {
    style: {
      ...FIELD_HINT,
      color: "var(--state-danger-fg)"
    }
  }, error) : hint ? /*#__PURE__*/React.createElement("span", {
    style: FIELD_HINT
  }, hint) : null);
}
Object.assign(__ds_scope, { Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Input.jsx", error: String((e && e.message) || e) }); }

// components/forms/Radio.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function Radio({
  label,
  description,
  checked,
  onChange,
  name,
  disabled = false,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: "flex",
      gap: 10,
      alignItems: "flex-start",
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.5 : 1,
      ...style
    }
  }, /*#__PURE__*/React.createElement("input", _extends({
    type: "radio",
    name: name,
    checked: checked,
    onChange: onChange,
    disabled: disabled
  }, rest, {
    style: {
      position: "absolute",
      opacity: 0,
      width: 0,
      height: 0
    }
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: 18,
      height: 18,
      marginTop: 1,
      flex: "0 0 auto",
      borderRadius: "var(--radius-pill)",
      background: "var(--surface-card)",
      border: `1px solid ${checked ? "var(--blue-500)" : "var(--border-strong)"}`,
      boxShadow: checked ? "none" : "var(--shadow-inset-field)",
      transition: "var(--transition-control)"
    }
  }, checked ? /*#__PURE__*/React.createElement("span", {
    style: {
      width: 8,
      height: 8,
      borderRadius: "var(--radius-pill)",
      background: "var(--surface-brand)"
    }
  }) : null), /*#__PURE__*/React.createElement("span", {
    style: {
      display: "grid",
      gap: 2
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-strong)"
    }
  }, label), description ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-2xs)",
      color: "var(--text-muted)"
    }
  }, description) : null));
}
Object.assign(__ds_scope, { Radio });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Radio.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const FIELD_LABEL = {
  display: "block",
  fontSize: "var(--text-xs)",
  fontWeight: "var(--fw-medium)",
  color: "var(--text-strong)",
  letterSpacing: "var(--tracking-label)",
  marginBottom: 6
};
const FIELD_HINT = {
  fontSize: "var(--text-2xs)",
  color: "var(--text-muted)",
  marginTop: 6
};
const FIELD_CONTROL = {
  width: "100%",
  height: 38,
  padding: "0 12px",
  fontFamily: "var(--font-sans)",
  fontSize: "var(--text-sm)",
  color: "var(--text-strong)",
  background: "var(--surface-card)",
  border: "1px solid var(--border-default)",
  borderRadius: "var(--radius-md)",
  boxShadow: "var(--shadow-inset-field)",
  outline: "none",
  transition: "var(--transition-control)"
};
function Select({
  label,
  hint,
  options = [],
  style,
  ...rest
}) {
  const [focus, setFocus] = React.useState(false);
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: "block",
      ...style
    }
  }, label ? /*#__PURE__*/React.createElement("span", {
    style: FIELD_LABEL
  }, label) : null, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "relative",
      display: "block"
    }
  }, /*#__PURE__*/React.createElement("select", _extends({
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false)
  }, rest, {
    style: {
      ...FIELD_CONTROL,
      appearance: "none",
      paddingRight: 34,
      cursor: "pointer",
      borderColor: focus ? "var(--blue-400)" : "var(--border-default)",
      boxShadow: focus ? "var(--ring-focus)" : "var(--shadow-inset-field)"
    }
  }), options.map(o => {
    const value = typeof o === "string" ? o : o.value;
    const text = typeof o === "string" ? o : o.label;
    return /*#__PURE__*/React.createElement("option", {
      key: value,
      value: value
    }, text);
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      right: 11,
      top: 0,
      height: 38,
      display: "flex",
      alignItems: "center",
      color: "var(--text-faint)",
      pointerEvents: "none"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "chevron-down",
    size: 15
  }))), hint ? /*#__PURE__*/React.createElement("span", {
    style: FIELD_HINT
  }, hint) : null);
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/Switch.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function Switch({
  label,
  description,
  checked = false,
  onChange,
  disabled = false,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "var(--space-6)",
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.5 : 1,
      ...style
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "grid",
      gap: 2
    }
  }, label ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-strong)"
    }
  }, label) : null, description ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-2xs)",
      color: "var(--text-muted)"
    }
  }, description) : null), /*#__PURE__*/React.createElement("span", {
    role: "switch",
    "aria-checked": checked,
    onClick: () => !disabled && onChange && onChange(!checked),
    style: {
      position: "relative",
      flex: "0 0 auto",
      width: 38,
      height: 22,
      borderRadius: "var(--radius-pill)",
      background: checked ? "var(--surface-brand)" : "var(--n-200)",
      border: `1px solid ${checked ? "var(--blue-600)" : "var(--border-strong)"}`,
      transition: "background-color var(--dur-base) var(--ease-standard), border-color var(--dur-base) var(--ease-standard)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      top: 2,
      left: checked ? 18 : 2,
      width: 16,
      height: 16,
      borderRadius: "var(--radius-pill)",
      background: "var(--n-0)",
      boxShadow: "var(--shadow-sm)",
      transition: "left var(--dur-base) var(--ease-out)"
    }
  })), /*#__PURE__*/React.createElement("input", _extends({
    type: "checkbox",
    checked: checked,
    disabled: disabled,
    onChange: () => onChange && onChange(!checked)
  }, rest, {
    style: {
      position: "absolute",
      opacity: 0,
      width: 0,
      height: 0
    }
  })));
}
Object.assign(__ds_scope, { Switch });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Switch.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Tabs.jsx
try { (() => {
function Tabs({
  items = [],
  value,
  onChange,
  style
}) {
  const [internal, setInternal] = React.useState(value ?? (items[0] && (items[0].value || items[0])));
  const active = value ?? internal;
  const select = v => {
    setInternal(v);
    onChange && onChange(v);
  };
  return /*#__PURE__*/React.createElement("div", {
    role: "tablist",
    style: {
      display: "flex",
      gap: "var(--space-7)",
      borderBottom: "1px solid var(--border-hairline)",
      ...style
    }
  }, items.map(raw => {
    const item = typeof raw === "string" ? {
      value: raw,
      label: raw
    } : raw;
    const on = item.value === active;
    return /*#__PURE__*/React.createElement("button", {
      key: item.value,
      role: "tab",
      "aria-selected": on,
      onClick: () => select(item.value),
      style: {
        display: "inline-flex",
        alignItems: "center",
        gap: 7,
        padding: "0 2px 11px",
        border: "none",
        background: "transparent",
        cursor: "pointer",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--text-sm)",
        fontWeight: on ? "var(--fw-medium)" : "var(--fw-regular)",
        color: on ? "var(--text-strong)" : "var(--text-muted)",
        boxShadow: on ? "inset 0 -2px 0 var(--blue-500)" : "none",
        transition: "var(--transition-control)"
      }
    }, item.icon ? /*#__PURE__*/React.createElement(__ds_scope.Icon, {
      name: item.icon,
      size: 15
    }) : null, item.label, item.count != null ? /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: "var(--font-mono)",
        fontSize: "var(--text-3xs)",
        color: "var(--text-faint)"
      }
    }, item.count) : null);
  }));
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Tabs.jsx", error: String((e && e.message) || e) }); }

// ui_kits/console/AppShell.jsx
try { (() => {
function ShellWordmark({
  size = 24
}) {
  return /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: size * 0.86,
      fontWeight: 600,
      letterSpacing: "-0.03em",
      color: "var(--text-strong)"
    }
  }, "Fluer ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 400,
      color: "var(--text-muted)"
    }
  }, "Development"));
}
const DSShell = window.FluerDesignSystem_fde5f8;
const ShLogo = DSShell.Logo || ShellWordmark,
  ShIcon = DSShell.Icon,
  ShIconButton = DSShell.IconButton,
  ShBadge = DSShell.Badge,
  ShTooltip = DSShell.Tooltip;
const NAV = [["overview", "Übersicht", "layout-dashboard"], ["deployments", "Deployments", "rocket"], ["logs", "Logs", "scroll-text"], ["settings", "Einstellungen", "settings"]];
function SideNav({
  view,
  onNav
}) {
  return /*#__PURE__*/React.createElement("aside", {
    style: {
      width: 264,
      flex: "0 0 auto",
      borderRight: "1px solid var(--border-hairline)",
      background: "var(--n-25)",
      display: "flex",
      flexDirection: "column",
      padding: "var(--space-6)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: 10,
      justifyItems: "start",
      padding: "var(--space-3) var(--space-3) var(--space-7)"
    }
  }, /*#__PURE__*/React.createElement(ShLogo, {
    size: 24,
    showWordmark: true
  }), /*#__PURE__*/React.createElement(ShBadge, {
    tone: "brand"
  }, "Console")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: 2
    }
  }, NAV.map(([k, l, icon]) => {
    const on = view === k;
    return /*#__PURE__*/React.createElement("button", {
      key: k,
      onClick: () => onNav(k),
      style: {
        display: "flex",
        alignItems: "center",
        gap: 10,
        height: 34,
        padding: "0 10px",
        border: "1px solid " + (on ? "var(--border-hairline)" : "transparent"),
        borderRadius: "var(--radius-sm)",
        background: on ? "var(--surface-card)" : "transparent",
        boxShadow: on ? "var(--shadow-xs)" : "none",
        cursor: "pointer",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--text-sm)",
        fontWeight: on ? 500 : 400,
        color: on ? "var(--text-strong)" : "var(--text-muted)",
        textAlign: "left",
        transition: "var(--transition-control)"
      }
    }, /*#__PURE__*/React.createElement(ShIcon, {
      name: icon,
      size: 16
    }), l);
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "auto",
      padding: "var(--space-5) var(--space-3)",
      borderTop: "1px solid var(--border-hairline)",
      display: "flex",
      alignItems: "center",
      gap: 9
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 26,
      height: 26,
      borderRadius: "var(--radius-pill)",
      background: "var(--blue-100)",
      border: "1px solid var(--border-brand)",
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: 11,
      fontWeight: 600,
      color: "var(--blue-600)"
    }
  }, "FD"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: 1,
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-xs)",
      color: "var(--text-strong)"
    }
  }, "Fluer Development"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-3xs)",
      color: "var(--text-faint)"
    }
  }, "Team-Plan")), /*#__PURE__*/React.createElement(ShIconButton, {
    icon: "chevrons-up-down",
    size: "sm",
    label: "Konto wechseln"
  })));
}
function TopBar({
  title,
  breadcrumb,
  actions
}) {
  return /*#__PURE__*/React.createElement("header", {
    style: {
      height: 60,
      flex: "0 0 auto",
      borderBottom: "1px solid var(--border-hairline)",
      background: "var(--surface-glass)",
      backdropFilter: "blur(var(--blur-glass))",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 var(--space-9)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 9
    }
  }, breadcrumb ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-faint)"
    }
  }, breadcrumb), /*#__PURE__*/React.createElement(ShIcon, {
    name: "chevron-right",
    size: 14,
    style: {
      color: "var(--text-faint)"
    }
  })) : null, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-md)",
      fontWeight: 500,
      color: "var(--text-strong)"
    }
  }, title)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-4)"
    }
  }, /*#__PURE__*/React.createElement(ShTooltip, {
    content: "Dokumentation"
  }, /*#__PURE__*/React.createElement(ShIconButton, {
    icon: "book-open",
    label: "Dokumentation"
  })), /*#__PURE__*/React.createElement(ShTooltip, {
    content: "Keine neuen Hinweise"
  }, /*#__PURE__*/React.createElement(ShIconButton, {
    icon: "bell",
    label: "Hinweise"
  })), actions));
}
Object.assign(window, {
  SideNav,
  TopBar
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/console/AppShell.jsx", error: String((e && e.message) || e) }); }

// ui_kits/console/screens.jsx
try { (() => {
function ScreenWordmark({
  size = 24
}) {
  return /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: size * 0.86,
      fontWeight: 600,
      letterSpacing: "-0.03em",
      color: "var(--text-strong)"
    }
  }, "Fluer ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 400,
      color: "var(--text-muted)"
    }
  }, "Development"));
}
const DS = window.FluerDesignSystem_fde5f8;
const ScButton = DS.Button,
  ScIconButton = DS.IconButton,
  ScBadge = DS.Badge,
  ScTag = DS.Tag,
  ScCard = DS.Card,
  ScIcon = DS.Icon,
  ScInput = DS.Input,
  ScSelect = DS.Select,
  ScCheckbox = DS.Checkbox,
  ScLogo = DS.Logo || ScreenWordmark,
  ScSwitch = DS.Switch,
  ScTabs = DS.Tabs,
  ScTooltip = DS.Tooltip,
  ScDialog = DS.Dialog,
  ScToast = DS.Toast;
const PAGE = {
  padding: "var(--space-10) var(--space-9) var(--space-12)",
  maxWidth: 1040,
  margin: "0 auto"
};
function StatRow({
  items
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: `repeat(${items.length},1fr)`,
      border: "1px solid var(--border-hairline)",
      borderRadius: "var(--radius-lg)",
      background: "var(--surface-card)",
      boxShadow: "var(--shadow-sm)",
      overflow: "hidden"
    }
  }, items.map(([label, value, sub], i) => /*#__PURE__*/React.createElement("div", {
    key: label,
    style: {
      padding: "var(--space-7) var(--space-8)",
      borderLeft: i ? "1px solid var(--border-hairline)" : "none"
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "fluer-eyebrow"
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-3xl)",
      fontWeight: 600,
      letterSpacing: "var(--tracking-display)",
      color: "var(--text-strong)",
      marginTop: 10,
      whiteSpace: "nowrap"
    }
  }, value), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-2xs)",
      color: "var(--text-muted)",
      marginTop: 4
    }
  }, sub))));
}
const DEPLOYS = [["deploy_8f2c41", "main", "success", "vor 4 Min.", "42 s"], ["deploy_7b1a09", "main", "success", "vor 3 Std.", "39 s"], ["deploy_6c88d2", "feat/billing", "failed", "vor 5 Std.", "18 s"], ["deploy_5a2f70", "main", "success", "gestern", "44 s"]];
const TONE = {
  success: ["success", "Erfolgreich"],
  failed: ["danger", "Fehlgeschlagen"],
  building: ["info", "Läuft"]
};
function DeployTable({
  rows = DEPLOYS,
  onOpen
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      border: "1px solid var(--border-hairline)",
      borderRadius: "var(--radius-lg)",
      background: "var(--surface-card)",
      boxShadow: "var(--shadow-sm)",
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1.3fr 1fr .9fr .8fr auto",
      gap: "var(--space-6)",
      padding: "var(--space-5) var(--space-8)",
      background: "var(--n-25)",
      borderBottom: "1px solid var(--border-hairline)"
    }
  }, ["Deployment", "Branch", "Status", "Dauer", ""].map(h => /*#__PURE__*/React.createElement("span", {
    key: h,
    className: "fluer-eyebrow"
  }, h))), rows.map(([id, branch, status, when, dur], i) => {
    const [tone, label] = TONE[status];
    return /*#__PURE__*/React.createElement("div", {
      key: id,
      style: {
        display: "grid",
        gridTemplateColumns: "1.3fr 1fr .9fr .8fr auto",
        gap: "var(--space-6)",
        alignItems: "center",
        padding: "var(--space-6) var(--space-8)",
        borderTop: i ? "1px solid var(--border-hairline)" : "none"
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: "grid",
        gap: 2
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: "var(--font-mono)",
        fontSize: "var(--text-xs)",
        color: "var(--text-strong)"
      }
    }, id), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: "var(--text-2xs)",
        color: "var(--text-faint)"
      }
    }, when)), /*#__PURE__*/React.createElement("span", {
      style: {
        display: "flex",
        alignItems: "center",
        gap: 6,
        fontSize: "var(--text-sm)",
        color: "var(--text-body)"
      }
    }, /*#__PURE__*/React.createElement(ScIcon, {
      name: "git-branch",
      size: 14,
      style: {
        color: "var(--text-faint)"
      }
    }), branch), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement(ScBadge, {
      tone: tone,
      dot: true
    }, label)), /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: "var(--font-mono)",
        fontSize: "var(--text-xs)",
        color: "var(--text-muted)"
      }
    }, dur), /*#__PURE__*/React.createElement("div", {
      style: {
        display: "flex",
        gap: 2
      }
    }, /*#__PURE__*/React.createElement(ScTooltip, {
      content: "Log \xF6ffnen"
    }, /*#__PURE__*/React.createElement(ScIconButton, {
      icon: "scroll-text",
      size: "sm",
      label: "Log",
      onClick: onOpen
    })), /*#__PURE__*/React.createElement(ScIconButton, {
      icon: "more-horizontal",
      size: "sm",
      label: "Mehr"
    })));
  }));
}
function OverviewScreen({
  onDeploy
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: PAGE
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-end",
      justifyContent: "space-between",
      gap: "var(--space-8)"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: "var(--text-3xl)"
    }
  }, "fluer-console"), /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: 8,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, "Produktion \xB7 eu-central-1 \xB7 zuletzt deployt vor 4 Minuten")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-4)"
    }
  }, /*#__PURE__*/React.createElement(ScButton, {
    variant: "secondary",
    icon: "external-link"
  }, "\xD6ffnen"), /*#__PURE__*/React.createElement(ScButton, {
    icon: "rocket",
    onClick: onDeploy
  }, "Deploy starten"))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "var(--space-9)"
    }
  }, /*#__PURE__*/React.createElement(StatRow, {
    items: [["Verfügbarkeit", "99,98 %", "letzte 30 Tage"], ["Antwortzeit", "128 ms", "p95"], ["Requests", "1,4 Mio.", "letzte 7 Tage"], ["Kosten", "84 €", "laufender Monat"]]
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1.6fr 1fr",
      gap: "var(--space-7)",
      marginTop: "var(--space-7)",
      alignItems: "start"
    }
  }, /*#__PURE__*/React.createElement(ScCard, {
    title: "Letzte Deployments",
    subtitle: "Vier von 128",
    padding: "sm",
    actions: /*#__PURE__*/React.createElement(ScIconButton, {
      icon: "more-horizontal",
      label: "Mehr"
    })
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: 0,
      margin: "-4px 0"
    }
  }, DEPLOYS.slice(0, 3).map(([id, branch, status, when]) => {
    const [tone, label] = TONE[status];
    return /*#__PURE__*/React.createElement("div", {
      key: id,
      style: {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
        padding: "11px 0",
        borderBottom: "1px solid var(--border-hairline)"
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: "grid",
        gap: 2
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: "var(--font-mono)",
        fontSize: "var(--text-xs)",
        color: "var(--text-strong)"
      }
    }, id), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: "var(--text-2xs)",
        color: "var(--text-faint)"
      }
    }, branch, " \xB7 ", when)), /*#__PURE__*/React.createElement(ScBadge, {
      tone: tone,
      dot: true
    }, label));
  }))), /*#__PURE__*/React.createElement(ScCard, {
    title: "Umgebung",
    padding: "sm"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(ScSwitch, {
    label: "Auto-Deploy",
    description: "Bei Push auf main.",
    checked: true,
    onChange: () => {}
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 1,
      background: "var(--border-hairline)"
    }
  }), /*#__PURE__*/React.createElement(ScSwitch, {
    label: "Vorschau-Umgebungen",
    description: "Pro Pull Request.",
    checked: false,
    onChange: () => {}
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 6,
      flexWrap: "wrap",
      marginTop: 2
    }
  }, /*#__PURE__*/React.createElement(ScTag, null, "eu-central-1"), /*#__PURE__*/React.createElement(ScTag, null, "node 22"), /*#__PURE__*/React.createElement(ScTag, null, "postgres 16"))))));
}
function DeploymentsScreen({
  onOpenLog
}) {
  const [tab, setTab] = React.useState("alle");
  return /*#__PURE__*/React.createElement("div", {
    style: PAGE
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "var(--space-8)"
    }
  }, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: "var(--text-3xl)"
    }
  }, "Deployments"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-4)",
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement(ScInput, {
    icon: "search",
    placeholder: "Suchen \u2026",
    style: {
      width: 220
    }
  }), /*#__PURE__*/React.createElement(ScSelect, {
    options: ["Alle Branches", "main", "feat/billing"],
    style: {
      width: 170
    }
  }))), /*#__PURE__*/React.createElement(ScTabs, {
    style: {
      marginTop: "var(--space-8)"
    },
    value: tab,
    onChange: setTab,
    items: [{
      value: "alle",
      label: "Alle",
      count: 128
    }, {
      value: "prod",
      label: "Produktion",
      count: 96
    }, {
      value: "preview",
      label: "Vorschau",
      count: 32
    }]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "var(--space-8)"
    }
  }, /*#__PURE__*/React.createElement(DeployTable, {
    onOpen: onOpenLog
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "var(--space-7)",
      background: "var(--surface-sunken)",
      border: "1px solid var(--border-hairline)",
      borderRadius: "var(--radius-lg)",
      padding: "var(--space-7) var(--space-8)",
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-xs)",
      lineHeight: 1.7,
      color: "var(--text-muted)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--text-strong)"
    }
  }, "\u203A deploy_8f2c41 \xB7 build log"), /*#__PURE__*/React.createElement("div", null, "14:02:11  install  \u2713 412 Pakete aus Cache"), /*#__PURE__*/React.createElement("div", null, "14:02:29  build    \u2713 18 Routen, 2,1 MB"), /*#__PURE__*/React.createElement("div", null, "14:02:48  deploy   \u2713 eu-central-1 aktiv")));
}
function SettingsScreen() {
  const [tab, setTab] = React.useState("allgemein");
  return /*#__PURE__*/React.createElement("div", {
    style: {
      ...PAGE,
      maxWidth: 820
    }
  }, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: "var(--text-3xl)"
    }
  }, "Einstellungen"), /*#__PURE__*/React.createElement(ScTabs, {
    style: {
      marginTop: "var(--space-8)"
    },
    value: tab,
    onChange: setTab,
    items: [{
      value: "allgemein",
      label: "Allgemein"
    }, {
      value: "env",
      label: "Variablen"
    }, {
      value: "team",
      label: "Team"
    }]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: "var(--space-7)",
      marginTop: "var(--space-9)"
    }
  }, /*#__PURE__*/React.createElement(ScCard, {
    title: "Projekt",
    padding: "md",
    footer: "\xC4nderungen wirken beim n\xE4chsten Deployment."
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: "var(--space-6)",
      maxWidth: 420
    }
  }, /*#__PURE__*/React.createElement(ScInput, {
    label: "Projektname",
    defaultValue: "fluer-console",
    hint: "Kleinbuchstaben und Bindestriche."
  }), /*#__PURE__*/React.createElement(ScSelect, {
    label: "Region",
    options: ["eu-central-1 · Frankfurt", "eu-west-1 · Dublin"]
  }), /*#__PURE__*/React.createElement(ScCheckbox, {
    label: "Build-Cache nutzen",
    description: "Beschleunigt Deployments deutlich.",
    checked: true,
    onChange: () => {}
  }))), /*#__PURE__*/React.createElement(ScCard, {
    title: "Gefahrenzone",
    subtitle: "Diese Aktionen sind endg\xFCltig.",
    padding: "md"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "var(--space-8)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)",
      maxWidth: "46ch"
    }
  }, "Projekt samt Deployments, Logs und Variablen l\xF6schen."), /*#__PURE__*/React.createElement(ScButton, {
    variant: "danger",
    icon: "trash-2"
  }, "Projekt l\xF6schen")))));
}
function LoginScreen({
  onLogin
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      minHeight: "100vh",
      display: "grid",
      gridTemplateColumns: "1fr 1fr"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "var(--space-11)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 340
    }
  }, /*#__PURE__*/React.createElement(ScLogo, {
    size: 26,
    showWordmark: true
  }), /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: "var(--text-2xl)",
      marginTop: "var(--space-9)"
    }
  }, "Anmelden"), /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: 8,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, "Console f\xFCr Projekte, Deployments und Logs."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: "var(--space-6)",
      marginTop: "var(--space-9)"
    }
  }, /*#__PURE__*/React.createElement(ScInput, {
    label: "E-Mail",
    defaultValue: "hallo@fluer.dev",
    icon: "mail"
  }), /*#__PURE__*/React.createElement(ScInput, {
    label: "Passwort",
    type: "password",
    defaultValue: "\xB7\xB7\xB7\xB7\xB7\xB7\xB7\xB7"
  }), /*#__PURE__*/React.createElement(ScButton, {
    fullWidth: true,
    size: "lg",
    onClick: onLogin,
    iconAfter: "arrow-right"
  }, "Weiter"), /*#__PURE__*/React.createElement(ScButton, {
    fullWidth: true,
    variant: "secondary",
    icon: "github"
  }, "Mit GitHub anmelden")), /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: "var(--space-8)",
      fontSize: "var(--text-2xs)",
      color: "var(--text-faint)"
    }
  }, "Hosting und Daten ausschlie\xDFlich in der EU."))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-inverse)",
      display: "flex",
      alignItems: "flex-end",
      padding: "var(--space-11)"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: "var(--text-xl)",
      color: "var(--text-inverse)",
      maxWidth: "26ch",
      lineHeight: 1.4
    }
  }, "\u201EEin Ansprechpartner von Entwurf bis Betrieb.\""), /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: "var(--space-6)",
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-2xs)",
      color: "rgba(255,255,255,.45)"
    }
  }, "Fluer Development \xB7 Cloud App Entwicklung"))));
}
Object.assign(window, {
  OverviewScreen,
  DeploymentsScreen,
  SettingsScreen,
  LoginScreen,
  DeployTable,
  StatRow
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/console/screens.jsx", error: String((e && e.message) || e) }); }

// ui_kits/website/HomePage.jsx
try { (() => {
const DSHome = window.FluerDesignSystem_fde5f8;
const HmBadge = DSHome.Badge,
  HmButton = DSHome.Button,
  HmCard = DSHome.Card,
  HmIcon = DSHome.Icon,
  HmTag = DSHome.Tag;
const SERVICES = [["cloud", "Cloud-Architektur", "Aufbau auf AWS oder Hetzner: Netzwerk, Datenhaltung, Deployment-Pfad. Dokumentiert und übergabefähig."], ["layout-dashboard", "App-Entwicklung", "Web-Anwendungen mit React und TypeScript, API in Node oder Go. Ein Ansprechpartner von Entwurf bis Release."], ["activity", "Betrieb & Monitoring", "Logging, Alerting, Backups. Monatlicher Bericht statt Blackbox."]];
const WORK = [["Logistik-Portal", "Sendungsverfolgung für 40 Standorte", "eu-central-1", "React · Go · Postgres"], ["Praxis-Terminsystem", "Buchung und Erinnerungen, DSGVO-konform", "eu-central-1", "React · Node · Redis"], ["Field-Service-App", "Offline-fähige Auftragserfassung", "eu-west-1", "React Native · Node"]];
function HomePage({
  onNav
}) {
  return /*#__PURE__*/React.createElement("main", null, /*#__PURE__*/React.createElement("section", {
    style: {
      maxWidth: "var(--container-wide)",
      margin: "0 auto",
      padding: "var(--space-14) var(--gutter-page) var(--space-13)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 660
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "fluer-eyebrow"
  }, "Cloud App Entwicklung"), /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: "var(--text-6xl)",
      lineHeight: 1.02,
      letterSpacing: "var(--tracking-display)",
      marginTop: "var(--space-6)"
    }
  }, "Cloud-Apps, sauber gebaut.")), /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: "var(--space-7)",
      maxWidth: "52ch",
      fontSize: "var(--text-lg)",
      lineHeight: "var(--lh-relaxed)",
      color: "var(--text-muted)"
    }
  }, "Fluer Development ist ein Einzelunternehmen. Sie sprechen mit der Person, die Ihre Anwendung entwirft, baut und betreibt."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-5)",
      marginTop: "var(--space-9)"
    }
  }, /*#__PURE__*/React.createElement(HmButton, {
    size: "lg",
    iconAfter: "arrow-right",
    onClick: () => onNav("kontakt")
  }, "Projekt anfragen"), /*#__PURE__*/React.createElement(HmButton, {
    size: "lg",
    variant: "ghost",
    onClick: () => onNav("arbeit")
  }, "Arbeiten ansehen")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-8)",
      marginTop: "var(--space-12)",
      paddingTop: "var(--space-7)",
      borderTop: "1px solid var(--border-hairline)",
      flexWrap: "wrap"
    }
  }, [["9 Jahre", "Erfahrung"], ["24", "ausgelieferte Anwendungen"], ["EU", "Hosting ausschließlich in der EU"]].map(([v, l]) => /*#__PURE__*/React.createElement("div", {
    key: l,
    style: {
      display: "grid",
      gap: 4,
      minWidth: 180
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-2xl)",
      fontWeight: 600,
      color: "var(--text-strong)",
      letterSpacing: "var(--tracking-heading)"
    }
  }, v), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, l))))), /*#__PURE__*/React.createElement("section", {
    id: "leistungen",
    style: {
      background: "var(--bg-page-alt)",
      borderTop: "1px solid var(--border-hairline)",
      borderBottom: "1px solid var(--border-hairline)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--container-wide)",
      margin: "0 auto",
      padding: "var(--space-13) var(--gutter-page)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "fluer-eyebrow"
  }, "Leistungen"), /*#__PURE__*/React.createElement("h2", {
    style: {
      marginTop: "var(--space-5)",
      maxWidth: "26ch"
    }
  }, "Drei Dinge, gr\xFCndlich statt vieles nebenbei."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(3,1fr)",
      gap: "var(--space-7)",
      marginTop: "var(--space-10)"
    }
  }, SERVICES.map(([icon, t, d]) => /*#__PURE__*/React.createElement("div", {
    key: t,
    style: {
      background: "var(--surface-card)",
      border: "1px solid var(--border-hairline)",
      borderRadius: "var(--radius-lg)",
      boxShadow: "var(--shadow-sm)",
      padding: "var(--space-8)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: 38,
      height: 38,
      borderRadius: "var(--radius-md)",
      background: "var(--surface-brand-soft)",
      border: "1px solid var(--border-brand)",
      color: "var(--text-brand)"
    }
  }, /*#__PURE__*/React.createElement(HmIcon, {
    name: icon,
    size: 19
  })), /*#__PURE__*/React.createElement("h3", {
    style: {
      marginTop: "var(--space-6)",
      fontSize: "var(--text-lg)"
    }
  }, t), /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: "var(--space-4)",
      fontSize: "var(--text-sm)",
      lineHeight: "var(--lh-relaxed)",
      color: "var(--text-muted)"
    }
  }, d)))))), /*#__PURE__*/React.createElement("section", {
    id: "arbeit",
    style: {
      maxWidth: "var(--container-wide)",
      margin: "0 auto",
      padding: "var(--space-13) var(--gutter-page) 0"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "fluer-eyebrow"
  }, "Arbeit"), /*#__PURE__*/React.createElement("h2", {
    style: {
      marginTop: "var(--space-5)"
    }
  }, "Ausgew\xE4hlte Projekte"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "var(--space-9)",
      border: "1px solid var(--border-hairline)",
      borderRadius: "var(--radius-lg)",
      background: "var(--surface-card)",
      boxShadow: "var(--shadow-sm)",
      overflow: "hidden"
    }
  }, WORK.map(([t, d, region, stack], i) => /*#__PURE__*/React.createElement("div", {
    key: t,
    style: {
      display: "grid",
      gridTemplateColumns: "1.1fr 1.4fr auto",
      gap: "var(--space-7)",
      alignItems: "center",
      padding: "var(--space-7) var(--space-8)",
      borderTop: i ? "1px solid var(--border-hairline)" : "none"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: 4
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-md)",
      fontWeight: 500,
      color: "var(--text-strong)"
    }
  }, t), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-2xs)",
      color: "var(--text-faint)"
    }
  }, region)), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, d), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-3)",
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement(HmTag, null, stack), /*#__PURE__*/React.createElement(HmIcon, {
    name: "arrow-up-right",
    size: 16,
    style: {
      color: "var(--text-faint)"
    }
  })))))), /*#__PURE__*/React.createElement("section", {
    id: "kontakt",
    style: {
      maxWidth: "var(--container-wide)",
      margin: "0 auto",
      padding: "var(--space-13) var(--gutter-page) 0"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-inverse)",
      borderRadius: "var(--radius-2xl)",
      padding: "var(--space-12) var(--space-11)",
      display: "grid",
      gridTemplateColumns: "1.3fr 1fr",
      gap: "var(--space-10)",
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h2", {
    style: {
      color: "var(--text-inverse)",
      maxWidth: "22ch",
      fontSize: "var(--text-3xl)"
    }
  }, "Erz\xE4hlen Sie mir vom Projekt."), /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: "var(--space-6)",
      fontSize: "var(--text-md)",
      color: "rgba(255,255,255,.66)",
      maxWidth: "44ch"
    }
  }, "Erstgespr\xE4ch, 30 Minuten, ohne Kosten. Danach erhalten Sie eine schriftliche Einsch\xE4tzung zu Aufwand und Vorgehen.")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: "var(--space-5)",
      justifyItems: "start"
    }
  }, /*#__PURE__*/React.createElement(HmButton, {
    size: "lg",
    icon: "mail"
  }, "hallo@fluer.dev"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-2xs)",
      color: "rgba(255,255,255,.5)"
    }
  }, "Antwort innerhalb eines Werktags")))));
}
Object.assign(window, {
  HomePage
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/website/HomePage.jsx", error: String((e && e.message) || e) }); }

// ui_kits/website/SiteChrome.jsx
try { (() => {
function SiteWordmark({
  size = 24
}) {
  return /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: size * 0.86,
      fontWeight: 600,
      letterSpacing: "-0.03em",
      color: "var(--text-strong)"
    }
  }, "Fluer ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 400,
      color: "var(--text-muted)"
    }
  }, "Development"));
}
const DSChrome = window.FluerDesignSystem_fde5f8;
const ChButton = DSChrome.Button,
  ChIcon = DSChrome.Icon,
  ChLogo = DSChrome.Logo || SiteWordmark;
function SiteHeader({
  view,
  onNav
}) {
  const items = [["leistungen", "Leistungen"], ["arbeit", "Arbeit"], ["kontakt", "Kontakt"]];
  return /*#__PURE__*/React.createElement("header", {
    style: {
      position: "sticky",
      top: 0,
      zIndex: 20,
      background: "var(--surface-glass)",
      backdropFilter: "blur(var(--blur-glass))",
      borderBottom: "1px solid var(--border-hairline)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--container-wide)",
      margin: "0 auto",
      padding: "0 var(--gutter-page)",
      height: 68,
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between"
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => onNav("start"),
    style: {
      border: "none",
      background: "none",
      cursor: "pointer",
      padding: 0,
      fontFamily: "var(--font-sans)",
      fontSize: 20,
      fontWeight: 600,
      letterSpacing: "-0.03em",
      color: "var(--text-strong)"
    }
  }, /*#__PURE__*/React.createElement(ChLogo, {
    size: 24,
    showWordmark: true
  })), /*#__PURE__*/React.createElement("nav", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-9)"
    }
  }, items.map(([k, l]) => /*#__PURE__*/React.createElement("button", {
    key: k,
    onClick: () => onNav(k),
    style: {
      border: "none",
      background: "none",
      cursor: "pointer",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--text-sm)",
      color: view === k ? "var(--text-strong)" : "var(--text-muted)",
      fontWeight: view === k ? 500 : 400
    }
  }, l)), /*#__PURE__*/React.createElement(ChButton, {
    size: "sm",
    variant: "secondary",
    iconAfter: "arrow-up-right",
    onClick: () => onNav("kontakt")
  }, "Projekt anfragen"))));
}
function SiteFooter() {
  return /*#__PURE__*/React.createElement("footer", {
    style: {
      borderTop: "1px solid var(--border-hairline)",
      background: "var(--n-25)",
      marginTop: "var(--space-13)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--container-wide)",
      margin: "0 auto",
      padding: "var(--space-11) var(--gutter-page) var(--space-9)",
      display: "grid",
      gridTemplateColumns: "1.4fr 1fr 1fr",
      gap: "var(--space-10)"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ChLogo, {
    size: 26,
    showWordmark: true
  }), /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: 10,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)",
      maxWidth: "34ch"
    }
  }, "Einzelunternehmen f\xFCr Cloud-App-Entwicklung. Architektur, Umsetzung, Betrieb.")), [["Leistungen", ["Cloud-Architektur", "App-Entwicklung", "Betrieb & Monitoring", "Audit"]], ["Kontakt", ["hallo@fluer.dev", "+49 …", "Impressum", "Datenschutz"]]].map(([t, ls]) => /*#__PURE__*/React.createElement("div", {
    key: t
  }, /*#__PURE__*/React.createElement("div", {
    className: "fluer-eyebrow"
  }, t), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: 8,
      marginTop: 14
    }
  }, ls.map(l => /*#__PURE__*/React.createElement("span", {
    key: l,
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-body)"
    }
  }, l)))))), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--container-wide)",
      margin: "0 auto",
      padding: "var(--space-6) var(--gutter-page)",
      borderTop: "1px solid var(--border-hairline)",
      display: "flex",
      justifyContent: "space-between",
      fontSize: "var(--text-2xs)",
      color: "var(--text-faint)"
    }
  }, /*#__PURE__*/React.createElement("span", null, "\xA9 2026 Fluer Development"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)"
    }
  }, "Frankfurt am Main")));
}
Object.assign(window, {
  SiteHeader,
  SiteFooter
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/website/SiteChrome.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.Icon = __ds_scope.Icon;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.Logo = __ds_scope.Logo;

__ds_ns.Tag = __ds_scope.Tag;

__ds_ns.Dialog = __ds_scope.Dialog;

__ds_ns.Toast = __ds_scope.Toast;

__ds_ns.Tooltip = __ds_scope.Tooltip;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.Radio = __ds_scope.Radio;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Switch = __ds_scope.Switch;

__ds_ns.Tabs = __ds_scope.Tabs;

})();
