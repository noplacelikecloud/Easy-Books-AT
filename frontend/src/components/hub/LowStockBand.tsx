import { useTranslation } from "react-i18next"

export interface LowStockItem {
  name: string
  on_hand: number
  reorder_level: number
}

export interface LowStockBandProps {
  items: LowStockItem[]
}

export default function LowStockBand({ items }: LowStockBandProps) {
  const { t } = useTranslation()

  if (items.length === 0)
    return (
      <div className="bg-white rounded-xl p-3 text-sm text-[var(--text-primary)]/40 text-center">
        {t("hub.allStockOk", "All products within stock levels")}
      </div>
    )
  return (
    <div className="bg-white rounded-xl p-3">
      <div className="text-[9px] font-bold uppercase tracking-[0.12em] text-amber-600 mb-2">
        {t("hub.lowStockAlerts", "⚠ Low Stock Alerts")}
      </div>
      <div className="flex flex-col gap-1.5">
        {items.slice(0, 3).map((item, i) => {
          const out = item.on_hand <= 0
          return (
            <div
              key={i}
              className={`flex justify-between items-center rounded-lg px-2.5 py-1.5 ${out ? "bg-red-50" : "bg-amber-50"}`}
            >
              <span className="text-xs text-[var(--text-primary)] truncate">{item.name}</span>
              <span className={`text-xs font-bold ml-2 shrink-0 ${out ? "text-red-600" : "text-amber-600"}`}>
                {out ? t("hub.Out of Stock", "Out of stock") : t("hub.unitsLeft", { count: item.on_hand, defaultValue: `${item.on_hand} left` })}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
