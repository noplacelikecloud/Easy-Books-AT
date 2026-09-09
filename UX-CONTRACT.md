# UX Contract

## Product context

- Audience: Austrian SMEs, bookkeepers, accountants, and tax advisers.
- Primary jobs: record evidence, finalize documents, reconcile VAT, prepare filing files, and produce UGB/EAR workpapers.
- Target market: Austria.
- Active locales: `de-AT` with English fallback.
- Native review: statutory and tax copy requires review by an Austrian accounting professional before release.
- Timezone/calendar: `Europe/Vienna`, Gregorian calendar, ISO dates in APIs, localized dates in UI.
- Accessibility target: WCAG 2.2 AA.

## Business-context sources

| Domain / scope | Authoritative source | Source type | Reviewed date |
|---|---|---|---|
| Permission model | `CLAUDE.md`, `backend/services/permissions.py` | Repository contract | 2026-09-09 |
| Data lifecycle | `docs/superpowers/plans/2026-09-08-austria-compliance-implementation.md` | Domain plan | 2026-09-09 |
| Deletion / retention | `docs/OESTERREICH_GAP_ANALYSE.md` | Legal gap analysis | 2026-09-09 |
| Tax and filing | `docs/OESTERREICH_COMPLIANCE_MATRIX.md` | Compliance matrix | 2026-09-09 |
| Legal copy | Austrian UGB, BAO, UStG and official BMF/USP form specifications referenced by the matrix | Primary law/guidance | 2026-09-09 |
| Market conventions | `DESIGN.md` | Product design contract | 2026-09-09 |

## Visual contract

- Project `DESIGN.md`: root `DESIGN.md`.
- Token ownership: existing runtime canonical.
- Runtime source: `frontend/src/app/globals.css` and shared components.
- Drift gate: frontend lint/build plus frontend-design-premium audit.
- Supported themes: existing light/dark theme behavior.
- Review policy: UI owner and Austrian domain reviewer approve compliance copy.

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Table Selection | shared table/list pages | existing frontend patterns | page selection | component/E2E |
| Select/Listbox | native `select` | existing forms | native | keyboard/browser |
| Date | native date input | existing forms | native | locale/E2E |
| Form | Invoice/Bill forms | shared form classes | create/edit | validation E2E |
| Scrollbar | global CSS | `globals.css` | stable gutter where needed | computed style |
| Toast | `MessageContext` | `MessageContext.tsx` | success/warning/info/error | live region |
| CRUD | owning list/detail page | existing sibling flow | return/stay | full flow |

## Component behavior

| Component | Default | Hover | Focus | Active | Disabled | Busy | Error |
|---|---|---|---|---|---|---|---|
| Button | labeled intent | tone shift | visible ring | pressed | dimmed + reason | fixed size label | inline message |
| Icon button | accessible name | surface shift | visible ring | pressed | dimmed | spinner | inline message |
| Input | bordered surface | border shift | primary ring | n/a | dimmed | read-only during submit | message below |
| Secret input | masked | border shift | primary ring | n/a | dimmed | unchanged | message below |
| Search | clear + 300ms debounce | border shift | primary ring | n/a | dimmed | stable result area | retry guidance |
| Textarea | existing resize policy | border shift | primary ring | n/a | dimmed | read-only | message below |
| Table/list | bounded dataset | row surface | action focus | selected state | n/a | stable loader | retry/empty state |

## Dataset navigation

- Admin tables: server pagination, normally 50 rows per page.
- Exploratory lists: server pagination or a bounded report period.
- URL state: committed period, filters, sort, page, and page size when the existing route supports it.
- Empty/no-results/error/loading: stable panel with a direct next action or retry.
- Back/scroll restoration: Next.js route history; create/edit returns to its owning list or detail.
- Bulk actions: page scope, visible selected count, confirmation for destructive actions, clear selection after success.

## Flow ledger

| Operation | Trigger | Pending | Success destination | Success feedback | Failure recovery | Focus outcome | Source ref |
|---|---|---|---|---|---|---|---|
| Create | Save | fixed busy button | owning detail/list | toast | retain form | summary/error | implementation plan §2.3 |
| Edit | Save changes | fixed busy button | owning detail | toast | retain changes | error/heading | implementation plan §2.3 |
| Finalize | Finalize | disable duplicate submit | same detail | toast + final number | show server blocker | status/action | implementation plan §2.3 |
| Cancel document | app dialog | danger action busy | same detail | toast | document unchanged | status/action | implementation plan §2.3 |
| Filing export | Finalize filing | action busy | same period | toast + download available | retain period/data | filing status | implementation plan PR 10 |
| Search | typed query | stable results | same list | result count | retry | search/results | `CLAUDE.md` |
| Bulk action | toolbar | disable toolbar | same list | affected count | keep failed selection | toolbar | `CLAUDE.md` |
| Upload/background job | choose file/start | progress | owning page | toast/result | retry same file | result | implementation plan PR 1 |
| Cancel/back | Cancel/Back | none | owning list | none | n/a | restored trigger | sibling forms |
| Soft-delete | Delete dialog | danger busy | owning list | toast | object retained | list heading | retention plan |
| Hard-delete | unavailable for retained AT records | n/a | n/a | reason shown | n/a | trigger | BAO retention model |

## Navigation and responsive behavior

- Document titles come from `frontend/src/lib/navTitles.ts`.
- Route errors stay in the page; permission failures use the existing API/route handling.
- Sidebar route state follows `frontend/src/lib/nav.ts`; breadcrumbs and tabs follow the dashboard shell.
- Mobile uses the existing drawer/more navigation.
- Tables scroll horizontally on their own surface and use the global sticky header convention.
- Truncated identifiers expose the full value through visible detail text or a title/copy action.
- Sticky surfaces must not cover focused controls.

## Overlays and feedback

- Dialog primitive: `MessageContext` confirmation dialog.
- Destructive confirmations: named object, consequence, explicit verb, least-destructive initial focus.
- Toast: shared `MessageContext`, semantic tone, deduplicated live announcement.
- Alerts: local to the owning workflow and persistent until resolved or dismissed.
- Tooltips: supplement visible labels; never carry the only critical instruction.
- Unsaved changes: preserve server-rejected values; use existing navigation behavior pending a shared dirty-form guard.
- Layer order: dialog above drawer, popover, and toast according to existing global components.

## Async and resilience

- Mutations are pessimistic and disable duplicate submit.
- Finalization and filing endpoints are idempotent or versioned server-side.
- Draft documents are the recovery unit; no UI claim of offline write support.
- API timeout is 30 seconds with actionable retry text.
- A version conflict leaves the current view intact and requires reload.
- Session expiry follows the central authentication handler.
- Long-running work reports status on the owning page.
- Effects ignore or cancel stale requests where period/input changes can race.

## Validation

- Pydantic/API schemas are authoritative; client validation covers required fields and obvious combinations.
- Validate on submit and after a touched invalid field changes.
- Show an inline summary for server blockers and retain entered data.
- Never echo secrets in toast or logs.
- Prevent duplicate submit and focus the first actionable error where the shared form supports it.

## Permission and clipboard

- Hide unavailable module navigation; show a disabled action with reason when the user can resolve a missing profile or reconciliation.
- Copy actions show truncated preview and copy the full non-secret value.
- Permission policy remains in backend permission services; the UI does not infer authorization.

## Migration status

- Migration ledger: `docs/OESTERREICH_UMSETZUNGSPRUEFUNG.md`.
- Canonical primitives: global CSS, `MessageContext`, `StatusBadge`, shared form/table components.
- Current slice: Austrian profile, document lifecycle, tax reconciliation, and filing workbench.
- Rollback gate: Alembic downgrade plus frontend build; removal waits until no AT profile depends on the feature.

## Verification

- Static commands: backend pytest, frontend lint/build, `git diff --check`, frontend-design-premium audit.
- Browser matrix: desktop/mobile widths, German/English, light/dark, keyboard navigation.
- Accessibility: headings, labels, focus, dialog behavior, status text, and contrast.
- Native/domain review: Austrian tax adviser or Bilanzbuchhalter before release.
- Visual regression: profile form, reconciliation blockers, filing actions, invoice/bill lifecycle controls.
- Canonical sibling: existing invoice and bill detail/form flows.
- CRUD/failure evidence: automated tests for draft/finalize/cancel/correction and server validation blockers.
