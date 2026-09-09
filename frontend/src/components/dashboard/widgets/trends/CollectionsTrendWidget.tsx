"use client"

import { useTranslation } from "react-i18next"
import { Line } from "react-chartjs-2"
import { useFmtCompact } from "@/context/SettingsContext"
import { monthLabel } from "@/lib/dashboardTrends"
import { TrendShell, moneyLineOpts, useTrends } from "./common"

/** Billing vs collection: amounts invoiced vs customer payments received per month. */
export default function CollectionsTrendWidget() {
  const { t } = useTranslation()
  const fmt = useFmtCompact()
  const { data, error } = useTrends()

  const hasActivity = !!data && (
    data.sales_purchases.sales.some(v => v !== 0) || data.collections.some(v => v !== 0)
  )

  const chartData = {
    labels: data?.months.map(monthLabel) ?? [],
    datasets: [
      {
        label: t('dashboard.invoiced', 'Invoiced'), data: data?.sales_purchases.sales.map(Number) ?? [],
        borderColor: "#2563eb", backgroundColor: "#2563eb",
        pointRadius: 3, pointHoverRadius: 5, borderWidth: 2, tension: 0.3,
      },
      {
        label: t('dashboard.collected', 'Collected'), data: data?.collections.map(Number) ?? [],
        borderColor: "#16a34a", backgroundColor: "rgba(22,163,74,0.10)",
        pointRadius: 3, pointHoverRadius: 5, borderWidth: 2, tension: 0.3, fill: true,
      },
    ],
  }

  return (
    <TrendShell
      title={t('widget.collections_trend', 'Collections')} sub={t('dashboard.collectionsSub', 'Invoiced vs payments received')}
      href="/payments-received" linkLabel={t('nav.payments', 'Payments')}
      loading={!data} error={error} empty={!hasActivity} emptyText={t('dashboard.noBillingActivity', 'No billing activity yet.')}
    >
      <Line data={chartData} options={moneyLineOpts(fmt, true)} />
    </TrendShell>
  )
}
