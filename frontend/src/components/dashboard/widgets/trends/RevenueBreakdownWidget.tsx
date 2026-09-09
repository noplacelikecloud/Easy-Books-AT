"use client"

import { useTranslation } from "react-i18next"
import { Doughnut } from "react-chartjs-2"
import { useFmt } from "@/context/SettingsContext"
import { CATEGORICAL, TrendShell, doughnutOpts, useTrends } from "./common"

/** YTD revenue by account — the revenue mirror of the expense doughnut. */
export default function RevenueBreakdownWidget() {
  const { t } = useTranslation()
  const fmt = useFmt()
  const { data, error } = useTrends()

  const rows = data?.revenue_breakdown ?? []
  const chartData = {
    labels: rows.map(r => r.account),
    datasets: [{
      data: rows.map(r => Number(r.amount)),
      backgroundColor: CATEGORICAL, borderWidth: 2, borderColor: "#fff",
    }],
  }

  return (
    <TrendShell
      title={t('widget.revenue_breakdown', 'Revenue Breakdown (YTD)')} sub={t('dashboard.revenueByAccount', 'Revenue by GL account')}
      href="/pl" linkLabel={t('dashboard.pl', 'P&L')}
      loading={!data} error={error} empty={rows.length === 0} emptyText={t('dashboard.noRevenueData', 'No revenue data.')}
    >
      <Doughnut data={chartData} options={doughnutOpts(fmt)} />
    </TrendShell>
  )
}
