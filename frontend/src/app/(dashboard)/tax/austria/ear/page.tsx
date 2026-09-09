"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { ChevronLeft, RefreshCw } from "lucide-react"
import { apiFetch } from "@/lib/api"
import { useFmt } from "@/context/SettingsContext"

type Position = { kz: string | null; title: string; amount: number; is_subtotal?: boolean; is_total?: boolean }
type Report = { year: number; legal_basis: string; form_version: string; positions: Position[]; taxable_profit: number }

export default function EarReportPage() {
  const fmt = useFmt()
  const [year, setYear] = useState(new Date().getFullYear())
  const [report, setReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try { setReport(await apiFetch<Report>(`/api/at/ear?year=${year}`)) }
    catch (reason) { setError(reason instanceof Error ? reason.message : "E/A-Rechnung konnte nicht geladen werden.") }
    finally { setLoading(false) }
  }, [year])
  useEffect(() => { void load() }, [load])

  return <main className="mx-auto max-w-4xl space-y-4 pb-10">
    <Link href="/tax/austria" className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--text-link)] hover:underline"><ChevronLeft className="h-4 w-4" aria-hidden="true" /> Österreich-Übersicht</Link>
    <header className="qb-card flex flex-wrap items-start justify-between gap-4 border-l-4 border-l-[var(--primary)] p-5"><div><p className="text-xs font-bold uppercase tracking-wider text-[var(--primary-dark)]">{report?.form_version ?? "E1a"}</p><h1 className="mt-1 text-2xl font-bold">Einnahmen-Ausgaben-Rechnung</h1><p className="mt-1 text-sm text-[var(--text-muted)]">Zufluss-/Abflussauswertung und Arbeitszuordnung für die Beilage E1a · § 4 Abs. 3 EStG</p></div><div className="flex items-end gap-2"><label className="text-xs font-bold text-[var(--text-muted)]">Jahr<input type="number" min="2000" max="2100" value={year} onChange={(event) => setYear(Number(event.target.value))} className="mt-1 block w-28 rounded-lg border border-[var(--border)] px-3 py-2 text-sm" /></label><button type="button" aria-label="Bericht aktualisieren" onClick={() => void load()} disabled={loading} className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-[var(--border)] hover:bg-[var(--bg-page)] disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} aria-hidden="true" /></button></div></header>
    {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>}
    {loading ? <div className="qb-card p-6 text-sm text-[var(--text-muted)]" role="status">Zahlungsströme werden ausgewertet …</div> : report && <section className="qb-card overflow-hidden"><div className="overflow-x-auto"><table className="w-full min-w-[560px] text-sm"><thead className="bg-[var(--bg-page)] text-xs uppercase tracking-wider text-[var(--text-muted)]"><tr><th className="px-4 py-2 text-left">Kennzahl</th><th className="px-4 py-2 text-left">Position</th><th className="px-4 py-2 text-right">Betrag EUR</th></tr></thead><tbody className="divide-y divide-[var(--border-light)]">{report.positions.map((position, index) => <tr key={`${position.kz ?? "sum"}-${index}`} className={position.is_total ? "bg-[var(--primary-light)] font-bold" : position.is_subtotal ? "bg-[var(--bg-page)] font-bold" : ""}><td className="px-4 py-2 font-mono text-[var(--text-muted)]">{position.kz ?? "—"}</td><th scope="row" className="px-4 py-2 text-left font-inherit">{position.title}</th><td className="px-4 py-2 text-right font-mono">{fmt(position.amount)}</td></tr>)}</tbody></table></div></section>}
    <p className="text-xs text-[var(--text-muted)]">Arbeitsunterlage; die fachliche Einordnung besonderer Betriebseinnahmen und -ausgaben muss vor Einreichung geprüft werden.</p>
  </main>
}
