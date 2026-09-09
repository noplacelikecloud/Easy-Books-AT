"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { AlertTriangle, CheckCircle2, Download, FileCheck2, RefreshCw, Settings2, ShieldCheck, XCircle } from "lucide-react"
import { apiBase, apiFetch, networkErrorMessage } from "@/lib/api"
import { getAuthToken } from "@/lib/auth"
import { useFmt } from "@/context/SettingsContext"
import { useMessages } from "@/context/MessageContext"

type Profile = {
  legal_form: string
  profit_method: string
  vat_status: string
  vat_method: string
  vat_filing_frequency: string
  vat_id: string | null
  valid_from: string
}
type Uva = {
  event_count: number
  kz_000: number
  total_output_tax: number
  total_input_tax: number
  kz_095: number
}
type Reconciliation = {
  is_reconciled: boolean
  gl_output_tax: number
  events_output_tax: number
  diff_output: number
  gl_input_tax: number
  events_input_tax: number
  diff_input: number
  gl_net_payable: number
  events_net_payable: number
  diff_net: number
  discrepancies: string[]
}
type SmallBusiness = {
  qualifying_turnover?: number
  threshold_amount?: number
  tolerance_amount?: number
  remaining_to_threshold?: number
  is_exceeded?: boolean
}
type Filing = { id: number; filing_type: string; period_key: string; version: number; status: string }

function currentPeriod() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`
}

async function downloadAuthenticated(path: string, filename: string) {
  let response: Response
  try {
    const token = getAuthToken()
    response = await fetch(`${apiBase}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  } catch (reason) {
    throw new Error(networkErrorMessage(reason, "Download fehlgeschlagen"))
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({})) as { detail?: string }
    throw new Error(payload.detail || "Download fehlgeschlagen")
  }
  const url = URL.createObjectURL(await response.blob())
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export default function AustriaTaxPage() {
  const fmt = useFmt()
  const { toast } = useMessages()
  const [period, setPeriod] = useState(currentPeriod)
  const [year, setYear] = useState(new Date().getFullYear() - 1)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [uva, setUva] = useState<Uva | null>(null)
  const [reconciliation, setReconciliation] = useState<Reconciliation | null>(null)
  const [smallBusiness, setSmallBusiness] = useState<SmallBusiness | null>(null)
  const [filings, setFilings] = useState<Filing[]>([])
  const [loading, setLoading] = useState(true)
  const [busyAction, setBusyAction] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const profileResult = await apiFetch<{ active: boolean; profile: Profile | null }>("/api/at/profile")
      setProfile(profileResult.profile)
      if (!profileResult.active || !profileResult.profile) {
        setUva(null); setReconciliation(null); setSmallBusiness(null); setFilings([])
        return
      }
      const requests: Promise<unknown>[] = [
        apiFetch<Uva>(`/api/at/tax/uva?period=${encodeURIComponent(period)}`),
        apiFetch<Reconciliation>(`/api/at/tax/reconciliation?period=${encodeURIComponent(period)}`),
        apiFetch<Filing[]>("/api/at/tax/filings"),
      ]
      if (profileResult.profile.vat_status === "small_business_exempt") {
        requests.push(apiFetch<SmallBusiness>(`/api/at/small-business?year=${period.slice(0, 4)}`))
      }
      const results = await Promise.all(requests)
      setUva(results[0] as Uva)
      setReconciliation(results[1] as Reconciliation)
      setFilings(results[2] as Filing[])
      setSmallBusiness((results[3] as SmallBusiness | undefined) ?? null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Österreich-Daten konnten nicht geladen werden.")
    } finally {
      setLoading(false)
    }
  }, [period])

  useEffect(() => { void load() }, [load])

  const finalize = async (type: "uva" | "zm" | "u1") => {
    const key = type === "u1" ? String(year) : period
    setBusyAction(type)
    setError(null)
    try {
      const query = type === "u1" ? `year=${year}` : `period=${encodeURIComponent(period)}`
      await apiFetch(`/api/at/tax/${type}/finalize?${query}`, { method: "POST" })
      toast(`${type.toUpperCase()} ${key} finalisiert; XML wurde lokal erstellt`, "success")
      await load()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : `${type.toUpperCase()} konnte nicht finalisiert werden.`)
    } finally {
      setBusyAction(null)
    }
  }

  const download = async (type: "uva" | "zm" | "u1") => {
    const key = type === "u1" ? String(year) : period
    const query = type === "u1" ? `year=${year}` : `period=${encodeURIComponent(period)}`
    setBusyAction(`${type}-download`)
    setError(null)
    try {
      await downloadAuthenticated(`/api/at/tax/${type}/xml?${query}`, `${type.toUpperCase()}_${key}.xml`)
      toast(`${type.toUpperCase()}-XML heruntergeladen`, "success")
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Download fehlgeschlagen.")
    } finally {
      setBusyAction(null)
    }
  }

  const finalized = (type: string, key: string) => filings.some((filing) => filing.filing_type === type && filing.period_key === key && filing.status === "finalized")

  return (
    <main className="mx-auto max-w-6xl space-y-5 pb-10">
      <header className="qb-card overflow-hidden">
        <div className="border-l-4 border-[var(--primary)] p-5 sm:p-6">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
            <div className="flex gap-3">
              <ShieldCheck className="mt-0.5 h-7 w-7 shrink-0 text-[var(--primary)]" aria-hidden="true" />
              <div><p className="text-xs font-bold uppercase tracking-[0.18em] text-[var(--primary-dark)]">Steuer-Arbeitsbereich</p><h1 className="mt-1 text-2xl font-bold">Österreich-Compliance</h1><p className="mt-2 max-w-2xl text-sm text-[var(--text-muted)]">Steuerjournal, Hauptbuch und Meldungswerte für den gewählten Zeitraum gemeinsam prüfen.</p></div>
            </div>
            <Link href="/settings/austria" className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-[var(--border)] px-4 py-2 text-sm font-bold hover:bg-[var(--bg-page)] focus-visible:outline-2 focus-visible:outline-offset-2"><Settings2 className="h-4 w-4" aria-hidden="true" /> Profil und Konten</Link>
          </div>
        </div>
      </header>

      {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>}

      {!loading && !profile && (
        <section className="qb-card p-6 text-center"><AlertTriangle className="mx-auto h-8 w-8 text-amber-600" aria-hidden="true" /><h2 className="mt-2 text-lg font-bold">Österreich-Profil fehlt</h2><p className="mt-1 text-sm text-[var(--text-muted)]">Richten Sie Rechtsform, Gewinnermittlung und Umsatzsteuerstatus ein, bevor Belege festgeschrieben werden.</p><Link href="/settings/austria" className="mt-4 inline-flex rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-bold text-white hover:bg-[var(--primary-dark)]">Profil einrichten</Link></section>
      )}

      {profile && (
        <>
          <section className="qb-card flex flex-wrap items-center justify-between gap-4 p-4">
            <div><p className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">Aktives Profil seit {profile.valid_from}</p><p className="mt-1 font-semibold">{profile.legal_form.toUpperCase()} · {profile.profit_method === "ear" ? "E/A-Rechnung" : "UGB doppelte Buchführung"} · {profile.vat_status === "small_business_exempt" ? "Kleinunternehmer" : "umsatzsteuerpflichtig"}</p></div>
            <div className="flex items-end gap-2"><label className="text-xs font-bold text-[var(--text-muted)]">UVA-Zeitraum<input type="month" value={period} onChange={(e) => setPeriod(e.target.value)} className="mt-1 block rounded-lg border border-[var(--border)] bg-[var(--bg-card)] px-3 py-2 text-sm text-[var(--text-primary)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20" /></label><button type="button" onClick={() => void load()} disabled={loading} aria-label="Daten aktualisieren" className="inline-flex h-10 w-10 cursor-pointer items-center justify-center rounded-lg border border-[var(--border)] hover:bg-[var(--bg-page)] focus-visible:outline-2 disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} aria-hidden="true" /></button></div>
          </section>

          {loading ? <div className="qb-card min-h-32 p-6 text-sm text-[var(--text-muted)]" role="status">Steuerwerte werden abgestimmt …</div> : (
            <>
              <section className={`qb-card overflow-hidden border-l-4 ${reconciliation?.is_reconciled ? "border-l-[var(--success)]" : "border-l-[var(--danger)]"}`}>
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border-light)] p-4"><div className="flex items-center gap-2">{reconciliation?.is_reconciled ? <CheckCircle2 className="h-5 w-5 text-[var(--success)]" aria-hidden="true" /> : <XCircle className="h-5 w-5 text-[var(--danger)]" aria-hidden="true" />}<div><h2 className="font-bold">Dreifachabstimmung {period}</h2><p className="text-sm text-[var(--text-muted)]">{reconciliation?.is_reconciled ? "Hauptbuch und Steuerjournal stimmen innerhalb von 0,05 EUR überein." : "Die Meldung bleibt bis zur Klärung der Differenz gesperrt."}</p></div></div><span className={`rounded-full px-3 py-1 text-xs font-bold ${reconciliation?.is_reconciled ? "bg-[var(--badge-green-bg)] text-[var(--success)]" : "bg-[var(--badge-red-bg)] text-[var(--danger)]"}`}>{reconciliation?.is_reconciled ? "Abgestimmt" : "Klärung erforderlich"}</span></div>
                <div className="overflow-x-auto"><table className="w-full min-w-[640px] text-sm"><thead className="bg-[var(--bg-page)] text-xs uppercase tracking-wider text-[var(--text-muted)]"><tr><th className="px-4 py-2 text-left">Position</th><th className="px-4 py-2 text-right">Hauptbuch</th><th className="px-4 py-2 text-right">Steuerjournal</th><th className="px-4 py-2 text-right">Differenz</th></tr></thead><tbody className="divide-y divide-[var(--border-light)]"><ReconRow label="Ausgangssteuer" gl={reconciliation?.gl_output_tax} events={reconciliation?.events_output_tax} diff={reconciliation?.diff_output} fmt={fmt} /><ReconRow label="Vorsteuer" gl={reconciliation?.gl_input_tax} events={reconciliation?.events_input_tax} diff={reconciliation?.diff_input} fmt={fmt} /><ReconRow label="Zahllast / Gutschrift" gl={reconciliation?.gl_net_payable} events={reconciliation?.events_net_payable} diff={reconciliation?.diff_net} fmt={fmt} /></tbody></table></div>
                {!!reconciliation?.discrepancies.length && <ul className="space-y-1 border-t border-red-100 bg-red-50 px-4 py-3 text-sm text-red-800">{reconciliation.discrepancies.map((item) => <li key={item}>• {item}</li>)}</ul>}
              </section>

              <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Metric label="Steuerbare Umsätze · KZ 000" value={uva?.kz_000} fmt={fmt} />
                <Metric label="Ausgangssteuer" value={uva?.total_output_tax} fmt={fmt} />
                <Metric label="Abziehbare Vorsteuer" value={uva?.total_input_tax} fmt={fmt} />
                <Metric label="KZ 095" value={uva?.kz_095} fmt={fmt} emphasized />
              </section>

              {smallBusiness && <section className="qb-card p-4"><div className="flex flex-wrap items-center justify-between gap-2"><div><h2 className="font-bold">Kleinunternehmergrenze</h2><p className="text-sm text-[var(--text-muted)]">Erfasster Umsatz {fmt(smallBusiness.qualifying_turnover ?? 0)} EUR · Grenze {fmt(smallBusiness.threshold_amount ?? 55000)} EUR · Toleranz bis {fmt(smallBusiness.tolerance_amount ?? 60500)} EUR</p></div><span className={`rounded-full px-3 py-1 text-xs font-bold ${smallBusiness.is_exceeded ? "bg-red-50 text-red-700" : "bg-green-50 text-green-700"}`}>{smallBusiness.is_exceeded ? "überschritten" : "innerhalb der Grenze"}</span></div></section>}

              <section className="grid gap-4 lg:grid-cols-3">
                <FilingCard title="UVA · U30" subtitle={`${period} · ${uva?.event_count ?? 0} Steuerereignisse`} finalized={finalized("uva", period)} disabled={!reconciliation?.is_reconciled} busy={busyAction === "uva" || busyAction === "uva-download"} onFinalize={() => void finalize("uva")} onDownload={() => void download("uva")} />
                <FilingCard title="Zusammenfassende Meldung" subtitle={`${period} · EU-Umsätze`} finalized={finalized("zm", period)} busy={busyAction === "zm" || busyAction === "zm-download"} onFinalize={() => void finalize("zm")} onDownload={() => void download("zm")} />
                <div className="qb-card p-4"><div className="flex items-start justify-between gap-3"><div><h2 className="font-bold">U1 Jahreserklärung</h2><p className="mt-1 text-sm text-[var(--text-muted)]">Amtliches Jahresschema für {year}</p></div><FileCheck2 className="h-5 w-5 text-[var(--primary)]" aria-hidden="true" /></div><label className="mt-4 block text-xs font-bold text-[var(--text-muted)]">Jahr<input type="number" min="2025" max={new Date().getFullYear()} value={year} onChange={(e) => setYear(Number(e.target.value))} className="mt-1 block w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm" /></label><div className="mt-4 flex gap-2"><button type="button" onClick={() => void finalize("u1")} disabled={!!busyAction} className="flex-1 rounded-lg bg-[var(--primary)] px-3 py-2 text-sm font-bold text-white hover:bg-[var(--primary-dark)] disabled:opacity-50">XML finalisieren</button><button type="button" onClick={() => void download("u1")} disabled={!finalized("u1", String(year)) || !!busyAction} aria-label="U1-XML herunterladen" className="rounded-lg border border-[var(--border)] px-3 py-2 hover:bg-[var(--bg-page)] disabled:opacity-40"><Download className="h-4 w-4" aria-hidden="true" /></button></div></div>
              </section>

              <section className="qb-card flex flex-wrap items-center justify-between gap-3 p-4"><div><h2 className="font-bold">Jahresabschluss und Nebenbücher</h2><p className="text-sm text-[var(--text-muted)]">{profile.profit_method === "ear" ? "E/A-Rechnung, E1a-Zuordnung, Anlagenverzeichnis und Wareneingangsbuch" : "UGB-Bilanz, GuV, Abschlusscheckliste und Anlagenbewegungen"}</p></div><div className="flex flex-wrap gap-2"><Link href={profile.profit_method === "ear" ? `/tax/austria/ear?year=${year}` : `/tax/austria/ugb?year=${year}`} className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm font-bold hover:bg-[var(--bg-page)]">Arbeitsunterlage öffnen</Link><Link href="/assets" className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm font-bold hover:bg-[var(--bg-page)]">Anlagen</Link></div></section>
            </>
          )}
        </>
      )}
    </main>
  )
}

function Metric({ label, value, fmt, emphasized = false }: { label: string; value?: number; fmt: (value: number) => string; emphasized?: boolean }) {
  return <div className={`qb-card p-4 ${emphasized ? "border-t-2 border-t-[var(--primary)]" : ""}`}><p className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{label}</p><p className="mt-2 font-mono text-xl font-bold">EUR {fmt(value ?? 0)}</p></div>
}

function ReconRow({ label, gl, events, diff, fmt }: { label: string; gl?: number; events?: number; diff?: number; fmt: (value: number) => string }) {
  const mismatch = Math.abs(diff ?? 0) > 0.05
  return <tr><th scope="row" className="px-4 py-3 text-left font-semibold">{label}</th><td className="px-4 py-3 text-right font-mono">{fmt(gl ?? 0)}</td><td className="px-4 py-3 text-right font-mono">{fmt(events ?? 0)}</td><td className={`px-4 py-3 text-right font-mono font-bold ${mismatch ? "text-[var(--danger)]" : "text-[var(--success)]"}`}>{fmt(diff ?? 0)}</td></tr>
}

function FilingCard({ title, subtitle, finalized, disabled = false, busy, onFinalize, onDownload }: { title: string; subtitle: string; finalized: boolean; disabled?: boolean; busy: boolean; onFinalize: () => void; onDownload: () => void }) {
  return <div className="qb-card p-4"><div className="flex items-start justify-between gap-3"><div><h2 className="font-bold">{title}</h2><p className="mt-1 text-sm text-[var(--text-muted)]">{subtitle}</p></div><span className={`rounded-full px-2 py-1 text-[10px] font-bold uppercase ${finalized ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-600"}`}>{finalized ? "finalisiert" : "offen"}</span></div><div className="mt-4 flex gap-2"><button type="button" onClick={onFinalize} disabled={disabled || busy} title={disabled ? "Die Hauptbuch-/Steuerjournal-Abstimmung muss zuerst stimmen." : undefined} className="flex-1 cursor-pointer rounded-lg bg-[var(--primary)] px-3 py-2 text-sm font-bold text-white hover:bg-[var(--primary-dark)] disabled:cursor-not-allowed disabled:opacity-40">{busy ? "Wird verarbeitet …" : "XML finalisieren"}</button><button type="button" onClick={onDownload} disabled={!finalized || busy} aria-label={`${title} XML herunterladen`} className="cursor-pointer rounded-lg border border-[var(--border)] px-3 py-2 hover:bg-[var(--bg-page)] disabled:cursor-not-allowed disabled:opacity-40"><Download className="h-4 w-4" aria-hidden="true" /></button></div></div>
}
