---
version: "2.0"
name: "OpenBooksAT"
description: "High-precision, calm B2B console for double-entry bookkeeping and Austrian statutory compliance."
colors:
  primary: "#17518C"
  primary-dark: "#123D6A"
  primary-light: "#EAF1F7"
  navigation: "#393A3D"
  background: "#FBFBF9"
  surface: "#FFFFFF"
  surface-sunken: "#F4F3F0"
  text: "#161614"
  text-muted: "#57544D"
  border: "#DEDCD7"
  border-default: "#C7C4BD"
  danger: "#A33227"
  warning: "#8C5D08"
  success: "#246E2A"
  info: "#156170"
typography:
  sans:
    fontFamily: "var(--font-geist-sans), 'Geist', system-ui, -apple-system, sans-serif"
  mono:
    fontFamily: "var(--font-geist-mono), 'Geist Mono', ui-monospace, SFMono-Regular, monospace"
rounded:
  xs: "3px"
  sm: "6px"
  md: "10px"
  lg: "14px"
  xl: "20px"
  pill: "999px"
spacing:
  section-gap: "2rem"
  page-max: "80rem"
components:
  ui-hub: "frontend/src/components/ui"
  primitives:
    - Button (10px radius; primary, secondary, ghost, danger)
    - IconButton (6px radius; accessible aria-label)
    - Badge (3px radius; semantic tones with optional dot)
    - Tag (999px pill; optional dismiss)
    - Card (14px radius; hairline border, soft shadow, sunken mode)
    - Input (10px radius; hairline border, 3px Deep Blue focus ring)
    - Select (10px radius; built-in chevron)
    - Checkbox (3px radius; Deep Blue checked state)
    - Switch (999px pill; smooth spring toggle)
    - Dialog (20px radius card; 36% scrim with 3px backdrop blur)
    - Toast (14px backdrop blur glass)
    - Tabs (Horizontal line with Deep Blue active indicator)
    - Table (14px container radius, hairline dividers, Geist Mono figures)
---

# Fluer Design System — OpenBooksAT / Easy-Books

## 1. Overview & North Star

### Creative North Star

The Fluer Design System establishes an uncompromisingly calm, high-precision, and tactile workspace for Austrian SME bookkeeping and tax compliance. 
Taking inspiration from modern engineering consoles (Linear, Vercel, Stripe), it trades arbitrary saturation and mixed radii for a singular primary accent, warm paper neutrals, hairline borders, and strict geometric discipline.

### Product Context & Core Principles

- **Audience & Primary Job:** Austrian SME owners, certified bookkeepers, accountants, and tax advisors recording journal entries, managing AP/AR, reconciling VAT (UVA/USt), and preparing statutory audit workpapers.
- **Single Primary Accent:** **Deep Blue `#17518C` (`--blue-500`)** is used exclusively for primary CTAs, active tab indicators, and keyboard focus rings.
- **Warm Paper Materiality:** Canvas sits on `--n-25` (`#FBFBF9`), cards on pure white `--n-0` (`#FFFFFF`), and grouped sub-sections on sunken `--n-50` (`#F4F3F0`).
- **Hairline Geometry:** Hierarchy is established through 1px hairline borders (`--n-100` `#DEDCD7` and `--n-200` `#C7C4BD`) paired with soft, low-intensity elevation shadows (`--shadow-sm`). Shadows never appear without a hairline boundary.
- **Strict Radien Scale:** Every component adheres to an exact mathematical radii tier.
- **No Pill Buttons:** Buttons always use 10px radius (`--radius-md`). Full pills (`rounded-full`) are strictly reserved for tags, switches, and avatars.
- **Restrained Danger Treatment:** Destructive actions (reversals, voids, deletes) use red text and a red hairline border on a white or card surface — never solid red blocks.
- **Canonical Implementation:** UI primitives reside in `frontend/src/components/ui/`. CSS variables in `frontend/src/app/globals.css` are the source of truth.

---

## 2. Color Palette & Semantics

### 2.1 Neutrals (Warm Paper Scale)
- `--n-0`: `#FFFFFF` — Cards and elevated popovers
- `--n-25`: `#FBFBF9` — Application canvas background
- `--n-50`: `#F4F3F0` — Sunken card surfaces, table hover states, subtle input backgrounds
- `--n-75`: `#E9E8E4` — Secondary dividers
- `--n-100`: `#DEDCD7` — Default hairline borders
- `--n-200`: `#C7C4BD` — Interactive borders (inputs, selects, default checkboxes)
- `--n-400`: `#8C887F` — Faint text, placeholders, disabled states
- `--n-600`: `#57544D` — Muted labels, secondary meta info
- `--n-700`: `#3F3D38` — Standard body text
- `--n-800`: `#282724` — Form field labels and strong text
- `--n-900`: `#161614` — Headings, titles, and high-emphasis data

### 2.2 Primary Accent (Deep Blue)
- `--blue-50`: `#EAF1F7` — Primary light tint / active badge background
- `--blue-100`: `#D0E0EF` — Focus ring aura
- `--blue-200`: `#A2C2E0` — Accent borders
- `--blue-500`: `#17518C` — **Primary brand accent** (Buttons, active tabs, focus borders)
- `--blue-600`: `#123D6A` — Primary hover state
- `--blue-700`: `#0D2C4C` — Primary active/pressed state

### 2.3 Semantic States
- **Success (Moss):** `--moss-50` (`#EEF5ED`), `--moss-600` (`#246E2A`) — Reconciled balances, posted vouchers, passed VAT checks.
- **Warning (Amber):** `--amber-50` (`#FDF6E7`), `--amber-600` (`#8C5D08`) — Unallocated payments, review items, approaching deadlines.
- **Danger (Red):** `--red-50` (`#FAECEB`), `--red-600` (`#A33227`) — Unbalanced entries, failed validation, voided vouchers, destructive confirmations.
- **Info (Petrol):** `--petrol-50` (`#EAF3F5`), `--petrol-600` (`#156170`) — System hints, statutory citations, non-blocking notices.

### 2.4 Dark Mode (Night Console)
Under `[data-theme="dark"]`:
- Background: `--bg-page: var(--n-900)` (`#161614`)
- Cards: `--bg-card: #1E1E1B`
- Sunken surface: `--surface-sunken: #121210`
- Hairlines: `--border-hairline: #2E2E2A`, `--border-default: #3F3D38`
- Primary: `--primary: #2373C4`, hover: `#2F86DE`

---

## 3. Typography

- **Geist Sans:** Used for all page titles, headers, navigation labels, and UI controls. Headlines apply subtle negative letter-spacing (`tracking-tight`).
- **Geist Mono:** Mandatory for amounts, balances, currency symbols, invoice numbers, tax codes (UVA Kennzahlen 000, 060, etc.), dates, and tabular data with `tabular-nums`.
- **Locale & Number Formatting:** Amounts formatted according to Austrian conventions (`1.250,00 €`). Negative values formatted as `(1.250,00 €)` or `-1.250,00 €`.

---

## 4. Radii & Spacing Rules

| Token | Value | Applied To |
|---|---|---|
| `--radius-xs` | **3px** | `Badge`, `Checkbox` |
| `--radius-sm` | **6px** | `IconButton`, small tags, menu items |
| `--radius-md` | **10px** | `Button`, `Input`, `Select`, `Toast` |
| `--radius-lg` | **14px** | `Card`, `Table` container |
| `--radius-xl` | **20px** | `Dialog` modal card |
| `--radius-pill` | **999px** | `Tag`, `Switch` track/knob, Avatars (**Never for Buttons**) |

---

## 5. UI Components & Patterns (`@/components/ui`)

### 5.1 Button & IconButton
- **Button:**
  - `primary`: Solid Deep Blue `#17518C`, white text, 10px radius.
  - `secondary`: White/card background, `--n-200` hairline border, `--n-900` text.
  - `ghost`: Transparent background, hover tint.
  - `danger`: Red text (`#A33227`), red hairline border on white card. **Never solid red.**
  - Sizes: `sm` (30px), `md` (38px), `lg` (46px).
- **IconButton:** Square proportion (30px, 38px, 46px), 6px radius, strictly requires `aria-label`.

### 5.2 Badge & Tag
- **Badge:** 3px radius, 22px height, semantic background tint with matching border. Supports optional 5px indicator dot.
- **Tag:** 999px pill radius, 24px height, optional dismiss `X` button.

### 5.3 Card
- 14px radius, 1px hairline border (`--border-hairline`), `--shadow-sm`.
- `tone="sunken"`: For grouped forms, sub-panels, and audit breakdowns without box shadow.
- Dedicated header (title, subtitle, actions) and footer slots.

### 5.4 Form Controls
- **Input & Select:** 10px radius, 38px height, hairline border. Focus produces a 3px ring in Deep Blue with 20% opacity.
- **Checkbox:** 3px radius, 18px box, Deep Blue check on active.
- **Switch:** 36px x 20px pill track, smooth 150ms spring sliding knob.

### 5.5 Dialog & Feedback
- **Dialog:** 20px radius card centered on page, protected by a 36% opacity dark scrim (`#161614/36`) and 3px backdrop blur.
- **Toast:** Glassmorphism card with 14px backdrop blur, hairline border, and semantic status icon.

### 5.6 Table Container
- Bounded container with 14px outer radius, hairline outer border, and overflow management.
- Subtle uppercase headers on `--n-25`.
- 44px height body rows with subtle hover highlight.
- `mono` cell prop enforces Geist Mono with `tabular-nums`.

---

## 6. Do's and Don'ts

- **Do:** Use Deep Blue `#17518C` for the primary focus of the page.
- **Do:** Use Geist Mono with `tabular-nums` for all financial figures, tax amounts, and voucher numbers.
- **Do:** Render destructive buttons with a red outline and red text on a card background.
- **Do:** Ensure all modal scrims use 36% opacity with 3px backdrop blur.
- **Don't:** Use rounded-full pill buttons for action buttons (keep buttons at 10px radius).
- **Don't:** Add colorful or saturated card backgrounds; keep cards white (`--n-0`) or sunken (`--n-50`).
- **Don't:** Render shadows without a defining hairline border.
- **Don't:** Introduce ad-hoc border radii outside the 3px / 6px / 10px / 14px / 20px / 999px scale.
