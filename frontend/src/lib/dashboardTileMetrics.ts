import type { DashboardSummary } from "@/lib/dashboardWidgets"
import type { TFunction } from "i18next"

export type MetricTone = "normal" | "warn" | "danger"
export interface TileMetric { value: string; badge?: string; tone?: MetricTone }

type Fmt = (n: number) => string
type Resolver = (s: DashboardSummary, fmt: Fmt, t?: TFunction) => TileMetric

// href → resolver. Routes not listed here have no metric (plain shortcut tile).
const TILE_METRICS: Record<string, Resolver> = {
  "/invoices": (s, fmt, t) => ({
    value: fmt(s.ar_outstanding),
    badge: s.overdue_invoices > 0 ? `${s.overdue_invoices} ${t ? t('common.overdue', 'overdue') : 'overdue'}` : undefined,
    tone: s.overdue_invoices > 0 ? "danger" : "normal",
  }),
  "/bills": (s, fmt, t) => ({
    value: fmt(s.ap_outstanding),
    badge: s.unpaid_bills > 0 ? `${s.unpaid_bills} ${t ? t('common.unpaid', 'unpaid') : 'unpaid'}` : undefined,
    tone: s.unpaid_bills > 0 ? "warn" : "normal",
  }),
  "/products": (s, _fmt, t) => ({
    value: `${s.low_stock_items}`,
    badge: s.low_stock_items > 0 ? (t ? t('dashboard.lowStock', 'low stock') : 'low stock') : undefined,
    tone: s.low_stock_items > 0 ? "warn" : "normal",
  }),
  "/bank-accounts": (s, fmt) => ({ value: fmt(s.cash_balance) }),
  "/cash-book": (s, fmt) => ({ value: fmt(s.cash_balance) }),
  "/aging/receivable": (s, fmt, t) => ({
    value: fmt(s.ar_outstanding),
    badge: s.overdue_invoices > 0 ? `${s.overdue_invoices} ${t ? t('common.overdue', 'overdue') : 'overdue'}` : undefined,
    tone: s.overdue_invoices > 0 ? "danger" : "normal",
  }),
  "/aging/payable": (s, fmt) => ({ value: fmt(s.ap_outstanding) }),
}

/** Resolve the metric for a shortcut href, or null if the route has no mapped
 *  metric or the summary hasn't loaded yet. Pure. */
export function resolveTileMetric(
  href: string, summary: DashboardSummary | undefined, fmt: Fmt, t?: TFunction,
): TileMetric | null {
  if (!summary) return null
  const resolver = TILE_METRICS[href]
  return resolver ? resolver(summary, fmt, t) : null
}
