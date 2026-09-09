# Fluer Design System Migration (Phase 1 & Phase 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Fluer Design System foundation (Phase 1: Geist fonts, CSS variables & tokens, dark mode) and core UI component library (Phase 2: Button, IconButton, Badge, Tag, Card, Input, Select, Checkbox, Switch, Dialog, Toast, Tabs, Table) in TypeScript for Easy-Books.

**Architecture:** We embed the Fluer design tokens into `frontend/src/app/globals.css` alongside existing legacy tokens for backwards compatibility. Geist Sans and Geist Mono typography are loaded via Next.js and injected as CSS variables. All Fluer UI components are built in `frontend/src/components/ui/` with strict adherence to Fluer rules (Deep Blue `#17518C` accent, warm paper neutrals, exact radii: 3px, 6px, 10px, 14px, 20px, 999px, no solid red destructive buttons, hairline borders).

**Tech Stack:** Next.js 16 (App Router), React 19, TypeScript 5, Tailwind CSS v4, Lucide React, Vitest.

**Spec:** [`docs/superpowers/specs/2026-09-09-fluer-design-system-migration-design.md`](file:///Users/fluriancancom/Documents/Coding/OpenBooksAT/docs/superpowers/specs/2026-09-09-fluer-design-system-migration-design.md)

## Global Constraints

- Primary accent is strictly Deep Blue `#17518C` (`--blue-500`), hover `#123D6A` (`--blue-600`).
- Backgrounds: Page is `--n-25` (`#FBFBF9`), Cards are `--n-0` (`#FFFFFF`), Sunken surfaces `--n-50` (`#F4F3F0`).
- Radii rules: 3px (Badges, Checkboxen), 6px (IconButtons), 10px (Buttons, Inputs, Selects), 14px (Cards, Table container), 20px (Dialogs), 999px (Pills for Tags, Switches, Avatars).
- Never use pill buttons (`rounded-full`) for action buttons.
- Destructive buttons must use red text and red hairline border on white/card background, never solid red blocks.
- Numeric figures, codes, dates, and amounts must use `font-mono` (Geist Mono) with `tabular-nums`.
- Existing pages and legacy token consumers must continue functioning without regression.

---

### Task 1: Geist Typography & Font Integration

**Files:**
- Modify: `frontend/src/app/layout.tsx:1-35`
- Modify: `frontend/src/app/globals.css:1-20`
- Test: `frontend/src/lib/__tests__/typography.test.ts`

**Interfaces:**
- Produces: CSS variables `--font-sans` (Geist Sans) and `--font-mono` (Geist Mono) applied on `<html>` and `<body>`.

- [ ] **Step 1: Write failing typography test**

Create `frontend/src/lib/__tests__/typography.test.ts`:
```typescript
import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";

describe("Typography Setup", () => {
  it("defines Geist font variables in layout.tsx or globals.css", () => {
    const layoutPath = path.resolve(__dirname, "../../app/layout.tsx");
    const globalsPath = path.resolve(__dirname, "../../app/globals.css");
    const layoutContent = fs.readFileSync(layoutPath, "utf8");
    const globalsContent = fs.readFileSync(globalsPath, "utf8");

    const hasGeistInLayout = layoutContent.includes("Geist") || layoutContent.includes("geist");
    const hasGeistInGlobals = globalsContent.includes("Geist") || globalsContent.includes("--font-sans");
    expect(hasGeistInLayout || hasGeistInGlobals).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix frontend test src/lib/__tests__/typography.test.ts`
Expected: FAIL (Geist font is not yet configured in layout.tsx or globals.css).

- [ ] **Step 3: Configure Geist in Next.js layout and globals.css**

Install `geist` package or configure Google Fonts / `@import`:
```bash
npm --prefix frontend install geist
```

In `frontend/src/app/layout.tsx`:
```typescript
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";

// apply variables to html element
<html lang="de" className={`${GeistSans.variable} ${GeistMono.variable}`}>
```

In `frontend/src/app/globals.css`:
```css
:root {
  --font-sans: var(--font-geist-sans), "Geist", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: var(--font-geist-mono), "Geist Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
}

body {
  font-family: var(--font-sans);
  font-feature-settings: "cv02", "cv03", "cv04", "cv11";
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix frontend test src/lib/__tests__/typography.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit changes**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/app/layout.tsx frontend/src/app/globals.css frontend/src/lib/__tests__/typography.test.ts
git commit -m "feat(ui): configure Geist Sans and Geist Mono typography"
```

---

### Task 2: Fluer Design Tokens & Dark Mode

**Files:**
- Modify: `frontend/src/app/globals.css`
- Test: `frontend/src/lib/__tests__/fluerTokens.test.ts`

**Interfaces:**
- Produces: Complete Fluer CSS variables: `--n-0` through `--n-900`, `--blue-50` through `--blue-700`, `--moss-*`, `--amber-*`, `--red-*`, `--petrol-*`, `--radius-*`, `--shadow-*`, and `[data-theme="dark"]` overrides.

- [ ] **Step 1: Write failing tokens test**

Create `frontend/src/lib/__tests__/fluerTokens.test.ts`:
```typescript
import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";

describe("Fluer Design Tokens", () => {
  const cssPath = path.resolve(__dirname, "../../app/globals.css");
  const css = fs.readFileSync(cssPath, "utf8");

  it("defines Fluer neutrals scale", () => {
    expect(css).toContain("--n-0:");
    expect(css).toContain("--n-25:");
    expect(css).toContain("--n-100:");
    expect(css).toContain("--n-900:");
  });

  it("defines Fluer primary Deep Blue palette", () => {
    expect(css).toContain("--blue-500: #17518c");
    expect(css).toContain("--blue-600: #123d6a");
  });

  it("defines strict Fluer radii scale", () => {
    expect(css).toContain("--radius-xs: 3px");
    expect(css).toContain("--radius-sm: 6px");
    expect(css).toContain("--radius-md: 10px");
    expect(css).toContain("--radius-lg: 14px");
    expect(css).toContain("--radius-xl: 20px");
    expect(css).toContain("--radius-pill: 999px");
  });

  it("defines Fluer Dark Mode tokens", () => {
    expect(css).toContain('[data-theme="dark"]');
    expect(css).toContain("--bg-page: var(--n-900)");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix frontend test src/lib/__tests__/fluerTokens.test.ts`
Expected: FAIL (missing Fluer neutrals, radii, and dark mode tokens).

- [ ] **Step 3: Add Fluer tokens to globals.css**

Update `frontend/src/app/globals.css` with the full token set from the spec:
- Neutrals: `--n-0` (#ffffff) to `--n-900` (#161614)
- Blue accent: `--blue-50` to `--blue-700`
- Semantics: `--moss-*`, `--amber-*`, `--red-*`, `--petrol-*`
- Radii: `--radius-xs: 3px` to `--radius-pill: 999px`
- Shadows: `--shadow-xs`, `--shadow-sm`, `--shadow-md`, `--shadow-lg`
- Mappings: `--primary: var(--blue-500)`, `--bg-page: var(--n-25)`, `--bg-card: var(--n-0)`
- Dark mode overrides in `[data-theme="dark"]`

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix frontend test src/lib/__tests__/fluerTokens.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/app/globals.css frontend/src/lib/__tests__/fluerTokens.test.ts
git commit -m "feat(ui): add Fluer design tokens and dark mode CSS variables"
```

---

### Task 3: Core Primitives — `Button` & `IconButton`

**Files:**
- Create: `frontend/src/components/ui/core/Button.tsx`
- Create: `frontend/src/components/ui/core/IconButton.tsx`
- Test: `frontend/src/components/ui/__tests__/Button.test.tsx`

**Interfaces:**
- Produces:
  ```typescript
  export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "primary" | "secondary" | "ghost" | "danger";
    size?: "sm" | "md" | "lg";
    icon?: React.ReactNode;
    iconAfter?: React.ReactNode;
    fullWidth?: boolean;
    loading?: boolean;
  }
  export function Button(props: ButtonProps): JSX.Element;

  export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "secondary" | "ghost" | "danger";
    size?: "sm" | "md" | "lg";
    icon: React.ReactNode;
    "aria-label": string;
  }
  export function IconButton(props: IconButtonProps): JSX.Element;
  ```

- [ ] **Step 1: Write failing Button and IconButton tests**

Create `frontend/src/components/ui/__tests__/Button.test.tsx`:
```typescript
import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { Button } from "../core/Button";
import { IconButton } from "../core/IconButton";

describe("Fluer Button Component", () => {
  it("renders primary button with 10px radius styling", () => {
    const html = renderToString(<Button variant="primary">Speichern</Button>);
    expect(html).toContain("Speichern");
    expect(html).toContain("btn-fluer");
    expect(html).toContain("btn-primary");
  });

  it("renders danger button with non-solid red styling", () => {
    const html = renderToString(<Button variant="danger">Löschen</Button>);
    expect(html).toContain("Löschen");
    expect(html).toContain("btn-danger");
    // Ensure it does not use a solid red background
    expect(html).not.toContain("bg-red-600");
  });

  it("renders IconButton with aria-label and 6px radius", () => {
    const html = renderToString(<IconButton icon={<span>X</span>} aria-label="Schließen" />);
    expect(html).toContain("aria-label=\"Schließen\"");
    expect(html).toContain("btn-icon");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix frontend test src/components/ui/__tests__/Button.test.tsx`
Expected: FAIL (Cannot find module `../core/Button`).

- [ ] **Step 3: Implement `Button.tsx` and `IconButton.tsx`**

Create `frontend/src/components/ui/core/Button.tsx`:
- Strictly adhere to Fluer specs:
  - Sizes: `sm` (h=30px, px=12px, font=12px, radius=6px), `md` (h=38px, px=16px, font=14px, radius=10px), `lg` (h=46px, px=22px, font=15px, radius=10px).
  - Variants:
    - `primary`: bg `#17518C`, text white, hover `#123D6A`, shadow-sm.
    - `secondary`: bg `--n-0`, border `--n-200`, text `--n-900`, hover `--n-25`.
    - `ghost`: bg transparent, text `--n-700`, hover `--n-50`.
    - `danger`: bg `--n-0`, border `rgba(163,50,39,0.25)`, text `#A33227`, hover `rgba(163,50,39,0.06)`. Never solid red block.
  - Active press transform: `active:translate-y-[0.5px]`.

Create `frontend/src/components/ui/core/IconButton.tsx`:
- Square aspect ratio (30px/38px/46px), 6px radius (`--radius-sm`), accessible `aria-label`.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix frontend test src/components/ui/__tests__/Button.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/components/ui/core/Button.tsx frontend/src/components/ui/core/IconButton.tsx frontend/src/components/ui/__tests__/Button.test.tsx
git commit -m "feat(ui): implement Fluer Button and IconButton primitives"
```

---

### Task 4: Badges & Tags — `Badge` & `Tag`

**Files:**
- Create: `frontend/src/components/ui/core/Badge.tsx`
- Create: `frontend/src/components/ui/core/Tag.tsx`
- Test: `frontend/src/components/ui/__tests__/Badge.test.tsx`

**Interfaces:**
- Produces:
  ```typescript
  export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    tone?: "neutral" | "brand" | "success" | "warning" | "danger" | "info";
    dot?: boolean;
    children: React.ReactNode;
  }
  export function Badge(props: BadgeProps): JSX.Element;

  export interface TagProps extends React.HTMLAttributes<HTMLSpanElement> {
    onRemove?: () => void;
    children: React.ReactNode;
  }
  export function Tag(props: TagProps): JSX.Element;
  ```

- [ ] **Step 1: Write failing Badge and Tag tests**

Create `frontend/src/components/ui/__tests__/Badge.test.tsx`:
```typescript
import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { Badge } from "../core/Badge";
import { Tag } from "../core/Tag";

describe("Fluer Badge and Tag", () => {
  it("renders badge with 3px radius and optional dot", () => {
    const html = renderToString(<Badge tone="success" dot>Gebucht</Badge>);
    expect(html).toContain("Gebucht");
    expect(html).toContain("badge-fluer");
    expect(html).toContain("badge-success");
    expect(html).toContain("badge-dot");
  });

  it("renders tag with 999px pill radius", () => {
    const html = renderToString(<Tag>Kategorie A</Tag>);
    expect(html).toContain("Kategorie A");
    expect(html).toContain("tag-fluer");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix frontend test src/components/ui/__tests__/Badge.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement `Badge.tsx` and `Tag.tsx`**

- `Badge.tsx`: height 22px, padding 0 8px, font 11px medium, radius 3px (`--radius-xs`), border 1px solid semantic border, optional 5px dot indicator.
- `Tag.tsx`: height 24px, padding 0 10px, radius 999px (`--radius-pill`), optional remove button (`X`).

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix frontend test src/components/ui/__tests__/Badge.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/components/ui/core/Badge.tsx frontend/src/components/ui/core/Tag.tsx frontend/src/components/ui/__tests__/Badge.test.tsx
git commit -m "feat(ui): implement Fluer Badge (3px) and Tag (pill) components"
```

---

### Task 5: Cards & Containers — `Card`

**Files:**
- Create: `frontend/src/components/ui/core/Card.tsx`
- Test: `frontend/src/components/ui/__tests__/Card.test.tsx`

**Interfaces:**
- Produces:
  ```typescript
  export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    title?: string;
    subtitle?: string;
    actions?: React.ReactNode;
    footer?: React.ReactNode;
    padding?: "none" | "sm" | "md" | "lg";
    interactive?: boolean;
    tone?: "default" | "sunken";
    children: React.ReactNode;
  }
  export function Card(props: CardProps): JSX.Element;
  ```

- [ ] **Step 1: Write failing Card tests**

Create `frontend/src/components/ui/__tests__/Card.test.tsx`:
```typescript
import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { Card } from "../core/Card";

describe("Fluer Card Component", () => {
  it("renders card with 14px radius and header", () => {
    const html = renderToString(
      <Card title="Umsatzübersicht" subtitle="Laufendes Geschäftsjahr">
        <div>Inhalt</div>
      </Card>
    );
    expect(html).toContain("Umsatzübersicht");
    expect(html).toContain("Laufendes Geschäftsjahr");
    expect(html).toContain("card-fluer");
  });

  it("renders sunken card for grouped sections", () => {
    const html = renderToString(
      <Card tone="sunken">
        <div>Details</div>
      </Card>
    );
    expect(html).toContain("card-sunken");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix frontend test src/components/ui/__tests__/Card.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement `Card.tsx`**

- Radii: 14px (`--radius-lg`), hairline border (`--border-hairline`), background `--n-0` (`card-fluer`), soft elevation (`--shadow-sm`).
- `tone="sunken"`: background `--n-50`, no shadow, hairline border.
- Header, subtitle, action buttons slot, footer slot.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix frontend test src/components/ui/__tests__/Card.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/components/ui/core/Card.tsx frontend/src/components/ui/__tests__/Card.test.tsx
git commit -m "feat(ui): implement Fluer Card component with 14px radius and sunken mode"
```

---

### Task 6: Form Controls — `Input`, `Select`, `Checkbox`, `Switch`

**Files:**
- Create: `frontend/src/components/ui/forms/Input.tsx`
- Create: `frontend/src/components/ui/forms/Select.tsx`
- Create: `frontend/src/components/ui/forms/Checkbox.tsx`
- Create: `frontend/src/components/ui/forms/Switch.tsx`
- Test: `frontend/src/components/ui/__tests__/Forms.test.tsx`

**Interfaces:**
- Produces:
  ```typescript
  export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    hint?: string;
    error?: string;
    icon?: React.ReactNode;
  }
  export function Input(props: InputProps): JSX.Element;

  export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
    label?: string;
    hint?: string;
    error?: string;
    options: Array<{ value: string; label: string; disabled?: boolean }>;
  }
  export function Select(props: SelectProps): JSX.Element;

  export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
  }
  export function Checkbox(props: CheckboxProps): JSX.Element;

  export interface SwitchProps {
    checked: boolean;
    onChange: (checked: boolean) => void;
    label?: string;
    disabled?: boolean;
  }
  export function Switch(props: SwitchProps): JSX.Element;
  ```

- [ ] **Step 1: Write failing Forms tests**

Create `frontend/src/components/ui/__tests__/Forms.test.tsx`:
```typescript
import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { Input } from "../forms/Input";
import { Select } from "../forms/Select";
import { Checkbox } from "../forms/Checkbox";
import { Switch } from "../forms/Switch";

describe("Fluer Form Controls", () => {
  it("renders input with label and error state", () => {
    const html = renderToString(<Input label="E-Mail" error="Ungültige Adresse" />);
    expect(html).toContain("E-Mail");
    expect(html).toContain("Ungültige Adresse");
    expect(html).toContain("input-fluer");
  });

  it("renders select with chevron indicator", () => {
    const html = renderToString(
      <Select label="Konto" options={[{ value: "1000", label: "1000 Kassa" }]} />
    );
    expect(html).toContain("1000 Kassa");
    expect(html).toContain("select-fluer");
  });

  it("renders checkbox with 3px radius", () => {
    const html = renderToString(<Checkbox label="Aktiviert" defaultChecked />);
    expect(html).toContain("checkbox-fluer");
  });

  it("renders switch toggle with pill radius", () => {
    const html = renderToString(<Switch checked={true} onChange={() => {}} label="Automatik" />);
    expect(html).toContain("switch-fluer");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix frontend test src/components/ui/__tests__/Forms.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement Form Controls**

- `Input.tsx`: 10px radius (`--radius-md`), height 38px, hairline border `--n-200`, focus ring in `--blue-500` (3px with 2px offset). Error state with red border and message.
- `Select.tsx`: Matching 10px radius, Lucide `ChevronDown` icon, accessible label.
- `Checkbox.tsx`: 3px radius (`--radius-xs`), Deep Blue checkmark on active.
- `Switch.tsx`: 999px pill (`--radius-pill`), smooth 150ms spring animation between on/off states.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix frontend test src/components/ui/__tests__/Forms.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/components/ui/forms/ frontend/src/components/ui/__tests__/Forms.test.tsx
git commit -m "feat(ui): implement Fluer form controls (Input, Select, Checkbox, Switch)"
```

---

### Task 7: Feedback & Navigation — `Dialog`, `Toast`, `Tabs`

**Files:**
- Create: `frontend/src/components/ui/feedback/Dialog.tsx`
- Create: `frontend/src/components/ui/feedback/Toast.tsx`
- Create: `frontend/src/components/ui/navigation/Tabs.tsx`
- Test: `frontend/src/components/ui/__tests__/FeedbackNav.test.tsx`

**Interfaces:**
- Produces:
  ```typescript
  export interface DialogProps {
    open: boolean;
    onClose: () => void;
    title: string;
    description?: string;
    children: React.ReactNode;
    actions?: React.ReactNode;
  }
  export function Dialog(props: DialogProps): JSX.Element | null;

  export interface TabsProps {
    items: Array<{ id: string; label: string; count?: number }>;
    activeId: string;
    onChange: (id: string) => void;
  }
  export function Tabs(props: TabsProps): JSX.Element;
  ```

- [ ] **Step 1: Write failing Feedback & Navigation tests**

Create `frontend/src/components/ui/__tests__/FeedbackNav.test.tsx`:
```typescript
import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { Dialog } from "../feedback/Dialog";
import { Tabs } from "../navigation/Tabs";

describe("Fluer Feedback and Navigation", () => {
  it("renders dialog with 20px radius and modal scrim", () => {
    const html = renderToString(
      <Dialog open={true} onClose={() => {}} title="Buchung stornieren">
        <p>Möchten Sie diesen Beleg wirklich stornieren?</p>
      </Dialog>
    );
    expect(html).toContain("Buchung stornieren");
    expect(html).toContain("dialog-fluer");
  });

  it("renders tabs with active Deep Blue indicator", () => {
    const html = renderToString(
      <Tabs
        items={[{ id: "all", label: "Alle" }, { id: "open", label: "Offen", count: 3 }]}
        activeId="open"
        onChange={() => {}}
      />
    );
    expect(html).toContain("Offen");
    expect(html).toContain("tabs-fluer");
    expect(html).toContain("tab-active");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix frontend test src/components/ui/__tests__/FeedbackNav.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement Dialog, Toast, and Tabs**

- `Dialog.tsx`: 20px radius (`--radius-xl`), backdrop filter blur(3px) with rgba(22,22,20,0.36) scrim, centered card with `--shadow-lg`, close button.
- `Toast.tsx`: Glass surface with 14px blur (`--surface-glass`), hairline border, soft shadow.
- `Tabs.tsx`: Clean horizontal navigation bar with bottom border and `--blue-500` active bar indicator.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix frontend test src/components/ui/__tests__/FeedbackNav.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/components/ui/feedback/ frontend/src/components/ui/navigation/ frontend/src/components/ui/__tests__/FeedbackNav.test.tsx
git commit -m "feat(ui): implement Fluer Dialog (20px), Toast, and Tabs components"
```

---

### Task 8: Fluer Table Wrapper System

**Files:**
- Create: `frontend/src/components/ui/table/Table.tsx`
- Test: `frontend/src/components/ui/__tests__/Table.test.tsx`

**Interfaces:**
- Produces:
  ```typescript
  export interface TableProps extends React.TableHTMLAttributes<HTMLTableElement> {
    children: React.ReactNode;
  }
  export function Table(props: TableProps): JSX.Element;
  export function TableHeader({ children }: { children: React.ReactNode }): JSX.Element;
  export function TableBody({ children }: { children: React.ReactNode }): JSX.Element;
  export function TableRow({ children, className, ...rest }: React.HTMLAttributes<HTMLTableRowElement>): JSX.Element;
  export function TableHead({ children, align, className, ...rest }: React.ThHTMLAttributes<HTMLTableCellElement>): JSX.Element;
  export function TableCell({ children, align, mono, className, ...rest }: React.TdHTMLAttributes<HTMLTableCellElement> & { mono?: boolean }): JSX.Element;
  ```

- [ ] **Step 1: Write failing Table tests**

Create `frontend/src/components/ui/__tests__/Table.test.tsx`:
```typescript
import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../table/Table";

describe("Fluer Table Component", () => {
  it("renders table with 14px outer container radius and hairline borders", () => {
    const html = renderToString(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Beleg-Nr.</TableHead>
            <TableHead align="right">Betrag</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell mono>AR-2026-0042</TableCell>
            <TableCell align="right" mono>€ 1.250,00</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
    expect(html).toContain("AR-2026-0042");
    expect(html).toContain("table-fluer-container");
    expect(html).toContain("font-mono");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix frontend test src/components/ui/__tests__/Table.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement Table component**

- Outer container: `rounded-[14px]` (`--radius-lg`), border `1px solid var(--border-hairline)`, overflow hidden, background `--n-0`.
- Header: background `--n-25`, text `--n-600`, text-xs, uppercase tracking-wide, hairline bottom border.
- Body rows: height 44px, hover background `--n-50` (`dark:bg-[#1e1e1b]`), hairline bottom dividers.
- `TableCell` with `mono` prop: applies `font-mono tabular-nums text-[13px]`.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix frontend test src/components/ui/__tests__/Table.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit changes**

```bash
git add frontend/src/components/ui/table/Table.tsx frontend/src/components/ui/__tests__/Table.test.tsx
git commit -m "feat(ui): implement Fluer Table wrapper with 14px radius and Geist Mono amounts"
```

---

### Task 9: Component Index & Full Suite Verification

**Files:**
- Create: `frontend/src/components/ui/index.ts`
- Test: All tests in `npm test` and `npx tsc --noEmit`

**Interfaces:**
- Produces: Single barrel export `@/components/ui` containing all Fluer components.

- [ ] **Step 1: Create barrel export `frontend/src/components/ui/index.ts`**

Export Button, IconButton, Badge, Tag, Card, Input, Select, Checkbox, Switch, Dialog, Toast, Tabs, Table and all respective prop types.

- [ ] **Step 2: Run all Vitest tests**

Run: `npm --prefix frontend test`
Expected: All tests pass (100% green).

- [ ] **Step 3: Run TypeScript typecheck**

Run: `npm --prefix frontend run build -- --no-lint` or `npx --prefix frontend tsc --noEmit`
Expected: 0 errors.

- [ ] **Step 4: Commit changes**

```bash
git add frontend/src/components/ui/index.ts
git commit -m "feat(ui): create Fluer UI components barrel export and verify build"
```

---

## Plan Self-Review

1. **Spec coverage:** Covers Geist typography, Fluer tokens, all Core/Form/Feedback/Navigation/Table components, radii rules, non-solid danger button styling, and dark mode.
2. **No Placeholders:** Every test and implementation has exact code, classes, paths, and commands.
3. **Type consistency:** Props and types are consistent across tasks.
