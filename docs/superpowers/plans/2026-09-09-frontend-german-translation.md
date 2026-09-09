# Frontend German (Austria) Translation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Translate remaining hardcoded English text in reports (Trial Balance, Balance Sheet, P&L, Ledger, Cash/Bank Book), DateRangePicker presets, and Dashboard widgets into Austrian German (UGB compliant) with matching English keys.

**Architecture:** Extend `de.json` and `en.json` translation files; wire `useTranslation` hook into components; ensure all user-visible strings resolve through `t()`.

**Tech Stack:** Next.js 16 (App Router), React 19, TypeScript, i18next / react-i18next, Tailwind CSS.

**Spec:** file:///Users/fluriancancom/.gemini/antigravity-ide/brain/7af927df-c3fa-4a87-8711-9893a33a4187/implementation_plan.md

## Global Constraints
- Maintain Austrian accounting terminology (UGB compliant: *Erlöse*, *Aufwendungen*, *Jahresüberschuss*, *Verbindlichkeiten*, *Forderungen*, *Summen- und Saldenliste*).
- Never break numeric formatting or date string parsers (`YYYY-MM-DD`).
- Keep `en.json` in sync with `de.json` for all newly introduced keys.

---

### Task 1: Consolidate and expand `de.json` and `en.json`

**Files:**
- Modify: `frontend/src/i18n/locales/de.json`
- Modify: `frontend/src/i18n/locales/en.json`

- [ ] **Step 1: Merge duplicate `"dashboard"` sections and add missing keys to `de.json`**
- [ ] **Step 2: Add matching keys to `en.json`**
- [ ] **Step 3: Validate JSON syntax with `node -e "JSON.parse(fs.readFileSync(...))"`**

---

### Task 2: Localize Financial Reports & Ledger Components

**Files:**
- Modify: `frontend/src/app/(dashboard)/trial-balance/page.tsx`
- Modify: `frontend/src/app/(dashboard)/balance/page.tsx`
- Modify: `frontend/src/app/(dashboard)/pl/page.tsx`
- Modify: `frontend/src/app/(dashboard)/ledger/page.tsx`
- Modify: `frontend/src/app/(dashboard)/cash-book/page.tsx`
- Modify: `frontend/src/app/(dashboard)/bank-book/page.tsx`
- Modify: `frontend/src/components/LedgerEntriesTable.tsx`
- Modify: `frontend/src/app/(dashboard)/aging/receivable/page.tsx`
- Modify: `frontend/src/app/(dashboard)/aging/payable/page.tsx`

- [ ] **Step 1: Update `trial-balance/page.tsx` with warning translation**
- [ ] **Step 2: Update `balance/page.tsx` with warning, asOf, and button translations**
- [ ] **Step 3: Update `pl/page.tsx` with button tooltips**
- [ ] **Step 4: Update `ledger/page.tsx` with full table header, view toggle, and empty state translations**
- [ ] **Step 5: Update `cash-book/page.tsx` and `bank-book/page.tsx`**
- [ ] **Step 6: Update `components/LedgerEntriesTable.tsx`**
- [ ] **Step 7: Update `aging/receivable/page.tsx` and `aging/payable/page.tsx`**

---

### Task 3: Localize DateRangePicker & Presets

**Files:**
- Modify: `frontend/src/components/DateRangePicker.tsx`

- [ ] **Step 1: Wire `useTranslation` into `DateRangePicker.tsx` for preset labels, "to" separator, hints, and aria labels**

---

### Task 4: Localize Dashboard Trend, Overview & Action Widgets

**Files:**
- Modify: `frontend/src/components/dashboard/widgets/trends/common.tsx`
- Modify: `frontend/src/components/dashboard/widgets/trends/CashFlowTrendWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/trends/DayBookWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/trends/ArApTrendWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/trends/ExpenseTrendWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/trends/SalesPurchasesWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/trends/ApAgingWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/trends/InvoiceStatusWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/trends/CashBalanceTrendWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/trends/CollectionsTrendWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/trends/ProfitMarginWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/trends/RevenueBreakdownWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/trends/TopVendorsWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/BankBalancesWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/TopProductsWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/InventorySummaryWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/HRMSummaryWidget.tsx`
- Modify: `frontend/src/components/dashboard/widgets/QuickActionsWidget.tsx`
- Modify: `frontend/src/components/dashboard/ShortcutTile.tsx`
- Modify: `frontend/src/components/dashboard/AddWidgetPanel.tsx`
- Modify: `frontend/src/lib/dashboardWidgets.tsx`

- [ ] **Step 1: Wire `TrendShell` with default localized strings**
- [ ] **Step 2: Update all trend widgets with localized titles, subtitles, and series**
- [ ] **Step 3: Update overview widgets (BankBalances, TopProducts, InventorySummary, HRMSummary)**
- [ ] **Step 4: Update QuickActionsWidget, ShortcutTile, AddWidgetPanel, and dashboardWidgets alerts/checklists**

---

### Task 5: Build & Docker Verification

- [ ] **Step 1: Run `npm run build` in `frontend/`**
- [ ] **Step 2: Rebuild & deploy Docker frontend container**
- [ ] **Step 3: Verify HTTP 200 on application routes**
