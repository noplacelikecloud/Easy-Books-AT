---
version: "1.0"
name: "OpenBooksAT"
description: "A dense, audit-oriented bookkeeping workspace for Austrian SMEs."
colors:
  primary: "#2CA01C"
  primary-dark: "#1A7510"
  primary-light: "#E8F5E4"
  navigation: "#393A3D"
  background: "#F4F6F8"
  surface: "#FFFFFF"
  text: "#1C2B36"
  muted: "#6C737A"
  border: "#D8DDE3"
  danger: "#D32F2F"
  warning: "#F59E0B"
  info: "#0077C5"
typography:
  sans:
    fontFamily: "var(--font-geist-sans), system-ui, -apple-system, sans-serif"
  mono:
    fontFamily: "var(--font-geist-mono), ui-monospace, monospace"
rounded:
  DEFAULT: "0.5rem"
  sm: "0.25rem"
  md: "0.5rem"
  lg: "0.75rem"
spacing:
  section-gap: "1rem"
  page-max: "72rem"
components:
  button: {}
  card: {}
  dialog: {}
  table: {}
  input: {}
---

# OpenBooksAT Design System

## Overview

### Creative North Star

The Austrian tax workpaper is the reference: restrained white sheets, clear totals, visible reconciliation state, and compact supporting evidence. The interface should feel calm during monthly bookkeeping and explicit at every irreversible filing or finalization boundary.

### Product context and register

- **Audience and primary job:** Austrian SME owners, bookkeepers, accountants, and tax advisers who record transactions, reconcile VAT, and prepare statutory workpapers.
- **Target market and evidence:** Austria, defined by `docs/OESTERREICH_GAP_ANALYSE.md` and the AT implementation plan.
- **Locales:** German (`de-AT`) and English fallback. Legal wording requires native professional review before product release.
- **Usage scene:** Repeated desktop work with dense financial data; responsive views support review and simple actions on smaller screens.
- **Register:** Product utility with a distinct Austrian compliance area at `/tax/austria` and `/settings/austria`.
- **Memorable signature:** A narrow green reconciliation rail shows whether ledger, tax journal, and filing agree.
- **Restraint:** Forms, tables, and destructive actions follow existing shared components and interaction patterns.
- **Anti-references:** Marketing dashboards and decorative tax imagery, because they obscure evidence and status.
- **Token ownership:** This file mirrors the runtime tokens in `frontend/src/app/globals.css`; the CSS remains canonical.

## Colors

White surfaces sit on `#F4F6F8`; `#D8DDE3` borders establish hierarchy. Green is reserved for primary actions and passed controls. Amber means review, red means blocking or destructive, and blue is informational. Focus must remain visible in light and dark themes.

## Typography

Geist Sans is the UI face. Geist Mono is used for amounts, identifiers, hashes, periods, and tax codes. Labels use sentence case; compact uppercase captions may identify stable table columns and statutory sections. German content uses normal German capitalization and locale formatting.

## Layout

Pages use the existing dashboard shell and a maximum working width near 72rem. Forms use one column on mobile and two columns where labels and controls remain readable. Tables own horizontal overflow. The runtime density tokens control cell and card spacing.

## Elevation & Depth

Hierarchy comes from surfaces, borders, and the existing low card shadow. Dialogs and drawers may rise above the page. Filing and accounting data should not use decorative blur or large shadows.

## Shapes

Controls and cards use the existing 0.5rem default radius; prominent panels may use 0.75rem. Status pills remain fully rounded. Dividers are one-pixel neutral borders.

## Components

### Foundational visual states

Enabled controls have hover and visible keyboard focus. Disabled controls explain unavailable statutory actions. Busy buttons retain their size. Errors stay near the failed action; the shared toast announces completion. Loading uses the existing stable text or spinner treatment.

### Buttons and actions

Green solid buttons commit safe primary actions. Neutral outlined buttons navigate or refresh. Destructive cancellation uses the shared app-owned confirmation dialog and a danger treatment. Icon-only buttons require accessible names.

### Navigation and data display

The sidebar owns global navigation. Native tables present filing histories and line data; cards present small sets of parallel totals. Status badges use semantic tokens and always include text.

### Forms and overlays

Inputs reuse the established border, padding, and focus ring. Server validation messages remain visible without clearing entered data. Confirmations use `MessageContext`, never browser dialogs.

### Iconography

Lucide React provides 16–24px outline icons. Commit, cancel, filing, and download actions retain text labels.

### Motion

Motion communicates loading, disclosure, or state change and respects reduced-motion preferences. Routine accounting pages avoid ambient animation.

### Content and data visualization

Copy names the accounting action directly. Amounts use `de-AT` formatting for German and English fallback otherwise. Reconciliation always exposes the compared values and variance, not color alone.

## Do's and Don'ts

- **Do:** Show the source period, filing version, and reconciliation result beside a filing action.
- **Do:** Reuse the same finalization and cancellation vocabulary on invoices and bills.
- **Don't:** Present an export as submitted to FinanzOnline when it is only generated locally.
- **Don't:** hide blocked controls without an accessible explanation when the user can resolve the issue.
