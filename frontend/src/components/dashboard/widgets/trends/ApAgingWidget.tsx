"use client"

import { useTranslation } from "react-i18next"
import { Bar } from "react-chartjs-2"
import { useFmtCompact } from "@/context/SettingsContext"
import { TrendShell, moneyBarOpts, useTrends } from "./common"

// Same age-severity ramp the AR aging widget uses (green → dark red)
const BUCKET_COLORS = [
  "rgba(22,163,74,0.78)", "rgba(234,179,8,0.78)", "rgba(249,115,22,0.78)",
  "rgba(239,68,68,0.82)", "rgba(185,28,28,0.88)",
]

/** AP aging buckets — the payables mirror of the AR Aging widget. */
export default function ApAgingWidget() {
  const { t } = useTranslation()
  const fmt = useFmtCompact()
  const { data, error } = useTrends()

  const bucketLabels = [
    t('reports.bucketCurrent', 'Current'),
    t('reports.bucket1_30', '1–30d'),
    t('reports.bucket31_60', '31–60d'),
    t('reports.bucket61_90', '61–90d'),
    t('reports.bucket90Plus', '90d+'),
  ]

  const a = data?.ap_aging
  const values = a ? [a.current, a["1_30"], a["31_60"], a["61_90"], a.over_90].map(Number) : []
  const hasActivity = values.some(v => v !== 0)

  const chartData = {
    labels: bucketLabels,
    datasets: [{ data: values, backgroundColor: BUCKET_COLORS, borderRadius: 4 }],
  }

  return (
    <TrendShell
      title={t('widget.ap_aging', 'AP Aging (Payables)')} sub={t('dashboard.apAgingSub', 'Outstanding bill amounts by age bucket')}
      href="/bills" linkLabel={t('nav.bills', 'Bills')}
      loading={!data} error={error} empty={!hasActivity} emptyText={t('dashboard.noOutstandingBills', 'No outstanding bills.')}
      footer={
        <div className="flex items-center gap-4 mt-2 flex-wrap">
          {bucketLabels.map((label, i) => (
            <span key={label} className="flex items-center gap-1 text-[10px] text-[var(--text-primary)]/55">
              <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: BUCKET_COLORS[i] }} />
              {label}: <span className="font-semibold text-[var(--text-primary)]/75">{fmt(values[i] ?? 0)}</span>
            </span>
          ))}
        </div>
      }
    >
      <Bar data={chartData} options={moneyBarOpts(fmt)} />
    </TrendShell>
  )
}
