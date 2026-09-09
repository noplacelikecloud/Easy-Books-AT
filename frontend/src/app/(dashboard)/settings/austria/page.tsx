"use client"

import { FormEvent, useEffect, useState } from "react"
import Link from "next/link"
import { CheckCircle2, ChevronLeft, Landmark, LockKeyhole, Save } from "lucide-react"
import { apiFetch } from "@/lib/api"
import { useMessages } from "@/context/MessageContext"

type Profile = {
  valid_from: string
  legal_form: string
  profit_method: string
  vat_status: string
  vat_method: string
  vat_filing_frequency: string
  fiscal_year_start: string
  tax_number: string | null
  vat_id: string | null
  company_register_number: string | null
  company_register_court: string | null
  registered_seat: string | null
  prior_year_turnover: number | null
}

const initialProfile: Profile = {
  valid_from: `${new Date().getFullYear()}-01-01`,
  legal_form: "gmbh",
  profit_method: "ugb_double_entry",
  vat_status: "standard",
  vat_method: "accrual",
  vat_filing_frequency: "monthly",
  fiscal_year_start: "01-01",
  tax_number: "",
  vat_id: "",
  company_register_number: "",
  company_register_court: "",
  registered_seat: "",
  prior_year_turnover: null,
}

const inputClass = "w-full rounded-lg border border-[var(--border)] bg-[var(--bg-card)] px-3 py-2 text-sm outline-none focus:border-[var(--primary)] focus:ring-2 focus:ring-[var(--primary)]/20 disabled:opacity-60"
const labelClass = "space-y-1 text-sm font-semibold text-[var(--text-primary)]"

export default function AustriaSettingsPage() {
  const { toast } = useMessages()
  const [profile, setProfile] = useState<Profile>(initialProfile)
  const [active, setActive] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [installing, setInstalling] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiFetch<{ active: boolean; profile: Profile | null }>("/api/at/profile")
      .then((result) => {
        setActive(result.active)
        if (result.profile) setProfile({ ...initialProfile, ...result.profile })
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Profil konnte nicht geladen werden."))
      .finally(() => setLoading(false))
  }, [])

  const update = (key: keyof Profile, value: string | number | null) => {
    setProfile((current) => ({ ...current, [key]: value }))
  }

  const save = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const result = await apiFetch<{ profile: Profile }>("/api/at/profile", {
        method: "POST",
        body: JSON.stringify({
          ...profile,
          tax_number: profile.tax_number || null,
          vat_id: profile.vat_id || null,
          company_register_number: profile.company_register_number || null,
          company_register_court: profile.company_register_court || null,
          registered_seat: profile.registered_seat || null,
          change_reason: active ? "Änderung über das Österreich-Onboarding" : "Ersteinrichtung Österreich",
        }),
      })
      setProfile({ ...initialProfile, ...result.profile })
      setActive(true)
      toast("Österreich-Profil gespeichert", "success")
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Profil konnte nicht gespeichert werden.")
    } finally {
      setSaving(false)
    }
  }

  const installAccounts = async () => {
    setInstalling(true)
    setError(null)
    try {
      const result = await apiFetch<{ accounts_count: number; roles_bound: number }>("/api/at/install-coa", { method: "POST" })
      toast(`${result.accounts_count} Konten und ${result.roles_bound} Kontenrollen geprüft`, "success")
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Kontenplan konnte nicht eingerichtet werden.")
    } finally {
      setInstalling(false)
    }
  }

  if (loading) return <div className="min-h-40 p-6 text-sm text-[var(--text-muted)]" role="status">Österreich-Profil wird geladen …</div>

  return (
    <main className="mx-auto max-w-5xl space-y-5 pb-10">
      <Link href="/tax/austria" className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--text-link)] hover:underline focus-visible:outline-2 focus-visible:outline-offset-2">
        <ChevronLeft className="h-4 w-4" aria-hidden="true" /> Zur Österreich-Übersicht
      </Link>

      <header className="qb-card overflow-hidden">
        <div className="border-l-4 border-[var(--primary)] p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-[var(--primary-dark)]">Mandantenprofil</p>
              <h1 className="mt-1 text-2xl font-bold text-[var(--text-primary)]">Österreich korrekt einrichten</h1>
              <p className="mt-2 max-w-2xl text-sm text-[var(--text-muted)]">Das wirksame Profil steuert Gewinnermittlung, Umsatzsteuer, Belegprüfung und verfügbare Meldungen.</p>
            </div>
            <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${active ? "bg-[var(--badge-green-bg)] text-[var(--success)]" : "bg-[var(--badge-yellow-bg)] text-amber-700"}`}>
              <CheckCircle2 className="h-4 w-4" aria-hidden="true" /> {active ? "Profil aktiv" : "Einrichtung offen"}
            </span>
          </div>
        </div>
      </header>

      {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>}

      <form onSubmit={save} noValidate className="space-y-5">
        <section className="qb-card p-5">
          <h2 className="text-lg font-bold">Rechtsform und Gewinnermittlung</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <label className={labelClass}>Gültig ab
              <input className={inputClass} type="date" required value={profile.valid_from} onChange={(e) => update("valid_from", e.target.value)} />
            </label>
            <label className={labelClass}>Rechtsform
              <select className={inputClass} value={profile.legal_form} onChange={(e) => update("legal_form", e.target.value)}>
                <option value="gmbh">GmbH</option><option value="flexco">FlexCo</option><option value="sole_proprietor">Einzelunternehmen</option><option value="og">OG</option><option value="kg">KG</option>
              </select>
            </label>
            <label className={labelClass}>Gewinnermittlung
              <select className={inputClass} value={profile.profit_method} onChange={(e) => update("profit_method", e.target.value)}>
                <option value="ugb_double_entry">Doppelte Buchführung nach UGB</option><option value="ear">Einnahmen-Ausgaben-Rechnung</option>
              </select>
            </label>
            <label className={labelClass}>Sitz
              <input className={inputClass} value={profile.registered_seat ?? ""} onChange={(e) => update("registered_seat", e.target.value)} placeholder="Wien" />
            </label>
            <label className={labelClass}>Firmenbuchnummer
              <input className={inputClass} value={profile.company_register_number ?? ""} onChange={(e) => update("company_register_number", e.target.value)} placeholder="FN 123456 a" />
            </label>
            <label className={labelClass}>Firmenbuchgericht
              <input className={inputClass} value={profile.company_register_court ?? ""} onChange={(e) => update("company_register_court", e.target.value)} placeholder="Handelsgericht Wien" />
            </label>
          </div>
        </section>

        <section className="qb-card p-5">
          <h2 className="text-lg font-bold">Umsatzsteuer</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <label className={labelClass}>USt-Status
              <select className={inputClass} value={profile.vat_status} onChange={(e) => update("vat_status", e.target.value)}>
                <option value="standard">Regelbesteuerung</option><option value="small_business_exempt">Kleinunternehmerbefreiung</option><option value="opted_in">Verzicht auf Kleinunternehmerbefreiung</option>
              </select>
            </label>
            <label className={labelClass}>Besteuerungsmethode
              <select className={inputClass} value={profile.vat_method} onChange={(e) => update("vat_method", e.target.value)}>
                <option value="accrual">Sollbesteuerung</option><option value="cash">Istbesteuerung</option>
              </select>
            </label>
            <label className={labelClass}>UVA-Zeitraum
              <select className={inputClass} value={profile.vat_filing_frequency} onChange={(e) => update("vat_filing_frequency", e.target.value)}>
                <option value="monthly">Monatlich</option><option value="quarterly">Vierteljährlich</option><option value="annual_only">Nur Jahreserklärung</option>
              </select>
            </label>
            <label className={labelClass}>Steuernummer
              <input className={inputClass} value={profile.tax_number ?? ""} onChange={(e) => update("tax_number", e.target.value)} inputMode="numeric" />
            </label>
            <label className={labelClass}>UID
              <input className={inputClass} value={profile.vat_id ?? ""} onChange={(e) => update("vat_id", e.target.value.toUpperCase())} placeholder="ATU12345678" />
            </label>
            <label className={labelClass}>Vorjahresumsatz in EUR
              <input className={inputClass} type="number" min="0" step="0.01" value={profile.prior_year_turnover ?? ""} onChange={(e) => update("prior_year_turnover", e.target.value === "" ? null : Number(e.target.value))} />
            </label>
          </div>
          {profile.vat_status === "small_business_exempt" && (
            <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">Die Anwendung überwacht die Grenze von 55.000 EUR und die 10-%-Toleranz. Der überschreitende Umsatz wird bei mehr als 60.500 EUR regelbesteuert.</p>
          )}
        </section>

        <section className="qb-card flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-3">
            <LockKeyhole className="mt-0.5 h-5 w-5 shrink-0 text-[var(--text-muted)]" aria-hidden="true" />
            <div><h2 className="font-bold">Bedingte Module</h2><p className="text-sm text-[var(--text-muted)]">RKSV, österreichische Bundese-Rechnung und Personalverrechnung bleiben bis zur technischen Freigabe serverseitig gesperrt.</p></div>
          </div>
          <button type="button" onClick={installAccounts} disabled={installing || !active} title={!active ? "Speichern Sie zuerst das Profil." : undefined} className="inline-flex shrink-0 cursor-pointer items-center justify-center gap-2 rounded-lg border border-[var(--border)] px-4 py-2 text-sm font-bold hover:bg-[var(--bg-page)] focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50">
            <Landmark className="h-4 w-4" aria-hidden="true" /> {installing ? "Konten werden geprüft …" : "AT-Kontenplan einrichten"}
          </button>
        </section>

        <div className="flex justify-end">
          <button type="submit" disabled={saving} className="inline-flex min-w-44 cursor-pointer items-center justify-center gap-2 rounded-lg bg-[var(--primary)] px-5 py-2.5 text-sm font-bold text-white hover:bg-[var(--primary-dark)] focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-60">
            <Save className="h-4 w-4" aria-hidden="true" /> {saving ? "Wird gespeichert …" : "Profil speichern"}
          </button>
        </div>
      </form>
    </main>
  )
}
