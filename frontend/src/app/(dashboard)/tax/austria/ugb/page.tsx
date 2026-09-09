"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { CheckCircle2, ChevronLeft, RefreshCw, XCircle } from "lucide-react"
import { apiFetch } from "@/lib/api"
import { useFmt } from "@/context/SettingsContext"

type Line = { position?: string; code?: string; name: string; current: number; prior?: number; is_subtotal?: boolean; is_total?: boolean; subitems?: Line[] }
type Balance = { aktiva: Line[]; passiva: Line[]; total_aktiva: number; total_passiva: number; is_balanced: boolean; has_negative_equity: boolean }
type Income = { lines: Line[]; annual_profit: number }
type Checklist = { is_ready_for_closing: boolean; items: { id: string; title: string; legal_basis: string; status: string; detail: string }[] }

export default function UgbReportPage() {
  const fmt = useFmt()
  const [year, setYear] = useState(new Date().getFullYear())
  const [balance, setBalance] = useState<Balance | null>(null)
  const [income, setIncome] = useState<Income | null>(null)
  const [checklist, setChecklist] = useState<Checklist | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const [bs, pl, checks] = await Promise.all([
        apiFetch<Balance>(`/api/at/reports/balance-sheet?as_of_date=${year}-12-31&prior_date=${year - 1}-12-31`),
        apiFetch<Income>(`/api/at/reports/income-statement?start_date=${year}-01-01&end_date=${year}-12-31&prior_start_date=${year - 1}-01-01&prior_end_date=${year - 1}-12-31`),
        apiFetch<Checklist>(`/api/at/reports/closing-checklist?year=${year}`),
      ])
      setBalance(bs); setIncome(pl); setChecklist(checks)
    } catch (reason) { setError(reason instanceof Error ? reason.message : "UGB-Berichte konnten nicht geladen werden.") }
    finally { setLoading(false) }
  }, [year])
  useEffect(() => { void load() }, [load])

  return <main className="mx-auto max-w-6xl space-y-4 pb-10">
    <Link href="/tax/austria" className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--text-link)] hover:underline"><ChevronLeft className="h-4 w-4" aria-hidden="true" /> Österreich-Übersicht</Link>
    <header className="qb-card flex flex-wrap items-start justify-between gap-4 border-l-4 border-l-[var(--primary)] p-5"><div><p className="text-xs font-bold uppercase tracking-wider text-[var(--primary-dark)]">Jahresabschluss</p><h1 className="mt-1 text-2xl font-bold">UGB-Bilanz und GuV</h1><p className="mt-1 text-sm text-[var(--text-muted)]">Gliederung nach §§ 224 und 231 UGB mit Abschlusskontrollen.</p></div><div className="flex items-end gap-2"><label className="text-xs font-bold text-[var(--text-muted)]">Geschäftsjahr<input type="number" min="2000" max="2100" value={year} onChange={(event) => setYear(Number(event.target.value))} className="mt-1 block w-28 rounded-lg border border-[var(--border)] px-3 py-2 text-sm" /></label><button type="button" aria-label="Berichte aktualisieren" onClick={() => void load()} disabled={loading} className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-[var(--border)] hover:bg-[var(--bg-page)] disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} aria-hidden="true" /></button></div></header>
    {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>}
    {loading ? <div className="qb-card p-6 text-sm text-[var(--text-muted)]" role="status">Hauptbuch und Nebenbücher werden geprüft …</div> : balance && income && checklist && <>
      <section className={`qb-card flex flex-wrap items-center justify-between gap-3 border-l-4 p-4 ${checklist.is_ready_for_closing ? "border-l-[var(--success)]" : "border-l-[var(--danger)]"}`}><div className="flex items-center gap-2">{checklist.is_ready_for_closing ? <CheckCircle2 className="h-5 w-5 text-[var(--success)]" aria-hidden="true" /> : <XCircle className="h-5 w-5 text-[var(--danger)]" aria-hidden="true" />}<div><h2 className="font-bold">{checklist.is_ready_for_closing ? "Abschlusskontrollen bestanden" : "Abschluss noch gesperrt"}</h2><p className="text-sm text-[var(--text-muted)]">Bilanz, Kassa, offene Posten und Umsatzsteuerabstimmung</p></div></div><span className="font-mono text-sm">Bilanzdifferenz: {fmt(balance.total_aktiva - balance.total_passiva)} EUR</span></section>
      {balance.has_negative_equity && <div role="alert" className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">Negatives Eigenkapital: Der Ausweis und die erforderlichen Erläuterungen nach § 225 Abs. 1 UGB müssen geprüft werden.</div>}
      <section className="grid gap-4 lg:grid-cols-2"><Statement title="Aktiva" lines={balance.aktiva} total={balance.total_aktiva} year={year} fmt={fmt} /><Statement title="Passiva" lines={balance.passiva} total={balance.total_passiva} year={year} fmt={fmt} /></section>
      <section className="qb-card overflow-hidden"><h2 className="border-b border-[var(--border)] p-4 font-bold">Gewinn- und Verlustrechnung</h2><StatementTable lines={income.lines} year={year} fmt={fmt} /></section>
      <section className="qb-card overflow-hidden"><h2 className="border-b border-[var(--border)] p-4 font-bold">Abschlusscheckliste</h2><ul className="divide-y divide-[var(--border-light)]">{checklist.items.map((item) => <li key={item.id} className="flex gap-3 p-4">{item.status === "passed" ? <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-[var(--success)]" aria-hidden="true" /> : <XCircle className={`mt-0.5 h-5 w-5 shrink-0 ${item.status === "warning" ? "text-amber-600" : "text-[var(--danger)]"}`} aria-hidden="true" />}<div><p className="font-semibold">{item.title} <span className="font-normal text-[var(--text-muted)]">· {item.legal_basis}</span></p><p className="mt-0.5 text-sm text-[var(--text-muted)]">{item.detail}</p></div></li>)}</ul></section>
    </>}
  </main>
}

function flatten(lines: Line[]) { return lines.flatMap((line) => [line, ...(line.subitems ?? []).map((child) => ({ ...child, name: `↳ ${child.name}` }))]) }
function Statement({ title, lines, total, year, fmt }: { title: string; lines: Line[]; total: number; year: number; fmt: (value: number) => string }) { return <section className="qb-card overflow-hidden"><h2 className="border-b border-[var(--border)] p-4 font-bold">{title}</h2><StatementTable lines={flatten(lines)} year={year} fmt={fmt} /><div className="flex justify-between border-t-2 border-[var(--text-primary)] p-4 font-bold"><span>Summe {title}</span><span className="font-mono">{fmt(total)} EUR</span></div></section> }
function StatementTable({ lines, year, fmt }: { lines: Line[]; year: number; fmt: (value: number) => string }) { return <div className="overflow-x-auto"><table className="w-full min-w-[520px] text-sm"><thead className="bg-[var(--bg-page)] text-xs uppercase tracking-wider text-[var(--text-muted)]"><tr><th className="px-4 py-2 text-left">Position</th><th className="px-4 py-2 text-right">{year}</th><th className="px-4 py-2 text-right">{year - 1}</th></tr></thead><tbody className="divide-y divide-[var(--border-light)]">{lines.map((line, index) => <tr key={`${line.position ?? line.code ?? index}-${line.name}`} className={line.is_total || line.is_subtotal ? "bg-[var(--bg-page)] font-bold" : ""}><th scope="row" className="px-4 py-2 text-left font-inherit">{line.position ?? line.code} {line.name}</th><td className="px-4 py-2 text-right font-mono">{fmt(line.current)}</td><td className="px-4 py-2 text-right font-mono">{fmt(line.prior ?? 0)}</td></tr>)}</tbody></table></div> }
