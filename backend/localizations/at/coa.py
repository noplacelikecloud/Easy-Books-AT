"""Austrian KMU Chart of Accounts (Einheitskontenrahmen EKR) Seed & Mappings (PR 4, AT-05, AT-11).

Provides:
- Standard Austrian KMU account structure (Classes 0-9)
- AccountRoleBinding configuration (§ 190 UGB)
- Statutory UGB and E1a report line mappings (§ 224, 231 UGB, § 4 Abs. 3 EStG)
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sqlmodel import Session, select

from fastapi import HTTPException

from models import Account, JournalEntry, Settings
from models_at import AccountRoleBinding, ReportLineMapping
from services.account_roles import bind_account_role


# Austrian Einheitskontenrahmen (EKR), KMU subset.
#
# Codes follow the EKR class structure, which is what every Austrian
# accountant, tax adviser and Finanzamt form expects:
#   0 Anlagevermögen · 1 Vorräte · 2 sonstiges Umlaufvermögen + ARA
#   3 Rückstellungen/Verbindlichkeiten/PRA · 4 betriebliche Erträge
#   5 Materialaufwand · 6 Personalaufwand
#   7 Abschreibungen + sonstige betriebliche Aufwendungen
#   8 Finanzerträge/-aufwendungen + Steuern · 9 Eigenkapital
#
# Getting the class right is not cosmetic: localizations/at/ugb_reports.py and
# localizations/at/ear.py derive the § 231 UGB GuV positions and the E1a
# Kennzahlen from these numbers, so an account in the wrong class lands in the
# wrong line of the statutory statements.
#
# Accounts marked "(EKR-Erweiterung)" are not in the official chart — they are
# rate splits and exemption buckets this app needs. They are deliberately
# placed on free sub-numbers under their official collective account so they
# never collide with a real EKR account (e.g. Vorsteuer 2500 → 2501/2502/2503,
# never 2540, which the EKR assigns to KESt).
#
# (code, name, type, is_group, parent_code)
AT_KMU_COA_TEMPLATE: List[Tuple[str, str, str, bool, str | None]] = [
    # ── Klasse 0: Anlagevermögen ──────────────────────────────────────────
    ("0100", "Konzessionen", "Asset", False, None),
    ("0110", "Patent- und Lizenzrechte", "Asset", False, None),
    ("0120", "DV-Programme", "Asset", False, None),
    ("0190", "Kumulierte Abschreibungen immaterielle Vermögensgegenstände", "Asset", False, None),
    ("0200", "Unbebaute Grundstücke", "Asset", False, None),
    ("0210", "Bebaute Grundstücke (Grundwert)", "Asset", False, None),
    ("0300", "Betriebs- und Geschäftsgebäude auf eigenem Grund", "Asset", False, None),
    ("0390", "Kumulierte Abschreibungen Betriebs- und Geschäftsgebäude", "Asset", False, None),
    ("0400", "Maschinen und maschinelle Anlagen", "Asset", False, None),
    ("0450", "Geringwertige Maschinen", "Asset", False, None),
    ("0490", "Kumulierte Abschreibungen Maschinen", "Asset", False, None),
    ("0510", "Werkzeuge allgemein", "Asset", False, None),
    ("0590", "Kumulierte Abschreibungen Werkzeuge", "Asset", False, None),
    ("0620", "Büromaschinen, EDV", "Asset", False, None),
    ("0630", "PKW und Kombi", "Asset", False, None),
    ("0640", "LKW", "Asset", False, None),
    ("0660", "Betriebs- und Geschäftsausstattung", "Asset", False, None),
    ("0680", "Geringwertige Vermögensgegenstände", "Asset", False, None),
    ("0690", "Kumulierte Abschreibungen Betriebs- und Geschäftsausstattung", "Asset", False, None),
    ("0700", "Geleistete Anzahlungen für Sachanlagen", "Asset", False, None),
    ("0710", "Anlagen im Bau", "Asset", False, None),
    ("0800", "Beteiligungen an verbundenen Unternehmen", "Asset", False, None),
    ("0830", "Sonstige Beteiligungen", "Asset", False, None),
    ("0990", "Kumulierte Abschreibungen Beteiligungen", "Asset", False, None),

    # ── Klasse 1: Vorräte ─────────────────────────────────────────────────
    ("1000", "Bezugsverrechnung", "Asset", False, None),
    ("1100", "Rohstoffvorrat", "Asset", False, None),
    ("1200", "Bezogene Teile", "Asset", False, None),
    ("1300", "Hilfsstoffvorrat", "Asset", False, None),
    ("1350", "Vorrat Betriebsstoffe", "Asset", False, None),
    ("1400", "Unfertige Erzeugnisse", "Asset", False, None),
    ("1500", "Fertigerzeugnisse", "Asset", False, None),
    ("1600", "Handelswarenvorrat", "Asset", False, None),
    ("1700", "Noch nicht abrechenbare Leistungen", "Asset", False, None),
    ("1800", "Geleistete Anzahlungen auf Vorräte", "Asset", False, None),

    # ── Klasse 2: Sonstiges Umlaufvermögen, Forderungen, Kassa, Bank ──────
    ("2000", "Forderungen aus Lieferungen und Leistungen Inland", "Asset", False, None),
    ("2100", "Forderungen aus Lieferungen und Leistungen Währungsunion", "Asset", False, None),
    ("2150", "Forderungen aus Lieferungen und Leistungen sonstiges Ausland", "Asset", False, None),
    ("2300", "Sonstige Forderungen", "Asset", False, None),
    ("2500", "Vorsteuer 20%", "Asset", False, None),
    ("2501", "Vorsteuer 10% (EKR-Erweiterung)", "Asset", False, None),
    ("2502", "Vorsteuer 13% (EKR-Erweiterung)", "Asset", False, None),
    ("2503", "Vorsteuer 4,9% (EKR-Erweiterung)", "Asset", False, None),
    ("2505", "Vorsteuer Erwerb / Reverse Charge (EKR-Erweiterung)", "Asset", False, None),
    ("2540", "KESt (auf KöSt anrechenbar)", "Asset", False, None),
    ("2550", "KöSt (Vorauszahlungen, Guthaben)", "Asset", False, None),
    ("2700", "Kassa", "Asset", False, None),
    ("2770", "Verrechnungskonto Kassa-Bank", "Asset", False, None),
    ("2785", "Forderungen Kreditkarten", "Asset", False, None),
    ("2800", "Bank", "Asset", False, None),
    ("2900", "Aktive Rechnungsabgrenzung (ARA)", "Asset", False, None),

    # ── Klasse 3: Rückstellungen, Verbindlichkeiten, PRA ──────────────────
    ("3000", "Rückstellung für Abfertigungen", "Liability", False, None),
    ("3030", "Rückstellung für Körperschaftsteuer", "Liability", False, None),
    ("3090", "Sonstige Rückstellungen", "Liability", False, None),
    ("3110", "Bank (Kreditrahmen)", "Liability", False, None),
    ("3150", "Darlehen", "Liability", False, None),
    ("3185", "Verbindlichkeiten Kreditkarten", "Liability", False, None),
    ("3200", "Erhaltene Anzahlungen auf Bestellungen", "Liability", False, None),
    ("3300", "Verbindlichkeiten aus Lieferungen und Leistungen Inland", "Liability", False, None),
    ("3500", "Umsatzsteuer 20%", "Liability", False, None),
    ("3501", "Umsatzsteuer 10% (EKR-Erweiterung)", "Liability", False, None),
    ("3502", "Umsatzsteuer 13% (EKR-Erweiterung)", "Liability", False, None),
    ("3503", "Umsatzsteuer 4,9% (EKR-Erweiterung)", "Liability", False, None),
    ("3505", "Umsatzsteuer Erwerb / Reverse Charge (EKR-Erweiterung)", "Liability", False, None),
    ("3520", "Finanzamt-Zahllast", "Liability", False, None),
    ("3540", "Finanzamt-Lohnsteuer, DB, DZ", "Liability", False, None),
    ("3550", "Verbindlichkeiten Kommunalsteuer", "Liability", False, None),
    ("3560", "Verbindlichkeiten Finanzamt", "Liability", False, None),
    ("3600", "Verbindlichkeiten Sozialversicherung", "Liability", False, None),
    ("3700", "Sonstige Verbindlichkeiten", "Liability", False, None),
    ("3750", "Verbindlichkeiten gegenüber Mitarbeitern", "Liability", False, None),
    ("3900", "Passive Rechnungsabgrenzung (PRA)", "Liability", False, None),

    # ── Klasse 4: Betriebliche Erträge ────────────────────────────────────
    ("4000", "Umsatzerlöse Inland 20% USt", "Revenue", False, None),
    ("4010", "Umsatzerlöse Inland 10% USt", "Revenue", False, None),
    ("4020", "Umsatzerlöse Inland 13% USt (EKR-Erweiterung)", "Revenue", False, None),
    ("4030", "Umsatzerlöse Inland 4,9% USt (EKR-Erweiterung)", "Revenue", False, None),
    ("4040", "Steuerfreie Erlöse Kleinunternehmer § 6 Abs. 1 Z 27 (EKR-Erweiterung)", "Revenue", False, None),
    ("4050", "Steuerfreie innergemeinschaftliche Lieferungen Art. 6 (EKR-Erweiterung)", "Revenue", False, None),
    ("4060", "Steuerfreie Ausfuhren Drittland § 6 Abs. 1 Z 1 (EKR-Erweiterung)", "Revenue", False, None),
    ("4400", "Erlösberichtigungen Inland 20% USt", "Revenue", False, None),
    ("4401", "Erlösberichtigungen Inland 10% USt", "Revenue", False, None),
    ("4440", "Skontoaufwand Inland (Kundenskonti 20% USt)", "Revenue", False, None),
    ("4441", "Skontoaufwand Inland (Kundenskonti 10% USt)", "Revenue", False, None),
    ("4500", "Bestandsveränderungen unfertige Erzeugnisse", "Revenue", False, None),
    ("4550", "Bestandsveränderungen Fertigerzeugnisse", "Revenue", False, None),
    ("4580", "Aktivierte Eigenleistungen", "Revenue", False, None),
    ("4600", "Erlöse Anlagenverkauf", "Revenue", False, None),
    ("4630", "Erträge aus dem Abgang von Anlagen", "Revenue", False, None),
    ("4800", "Sonstige betriebliche Erträge", "Revenue", False, None),
    ("4820", "Eigenverbrauch (Sachbezug) 20 %", "Revenue", False, None),
    ("4830", "Mieterträge", "Revenue", False, None),

    # ── Klasse 5: Materialaufwand und bezogene Leistungen ─────────────────
    ("5000", "Bezugsverrechnung", "Expense", False, None),
    ("5010", "Handelswaren-Verbrauch", "Expense", False, None),
    ("5100", "Verbrauch Rohstoffe", "Expense", False, None),
    ("5200", "Verbrauch von bezogenen Teilen", "Expense", False, None),
    ("5300", "Verbrauch von Hilfsstoffen", "Expense", False, None),
    ("5340", "Verbrauch von Verpackungsmaterial", "Expense", False, None),
    ("5400", "Verbrauch von Betriebsstoffen", "Expense", False, None),
    ("5600", "Verbrauch von Brenn- und Treibstoffen, Energie und Wasser", "Expense", False, None),
    ("5700", "Bezogene Leistungen (Fremdleistungen)", "Expense", False, None),
    ("5800", "Abschreibung und Wertberichtigung von Vorräten", "Expense", False, None),
    ("5880", "Skontoertrag (Lieferantenskonti 20% USt)", "Expense", False, None),
    ("5881", "Skontoertrag (Lieferantenskonti 10% USt)", "Expense", False, None),

    # ── Klasse 6: Personalaufwand ─────────────────────────────────────────
    ("6000", "Löhne", "Expense", False, None),
    ("6200", "Gehälter", "Expense", False, None),
    ("6400", "Abfertigungszahlungen", "Expense", False, None),
    ("6410", "Betriebliche Mitarbeitervorsorge", "Expense", False, None),
    ("6500", "Gesetzlicher Sozialaufwand Arbeiter", "Expense", False, None),
    ("6560", "Gesetzlicher Sozialaufwand Angestellte", "Expense", False, None),
    ("6600", "Dienstgeberbeitrag zur Familienbeihilfe (DB)", "Expense", False, None),
    ("6610", "Zuschlag zum Dienstgeberbeitrag (DZ)", "Expense", False, None),
    ("6620", "Kommunalsteuer", "Expense", False, None),
    ("6700", "Freiwilliger Sozialaufwand", "Expense", False, None),

    # ── Klasse 7: Abschreibungen und sonstige betriebliche Aufwendungen ───
    ("7000", "Planmäßige Abschreibung immaterieller Anlagengegenstände", "Expense", False, None),
    ("7020", "Planmäßige Abschreibung von Sachanlagen (AfA)", "Expense", False, None),
    ("7030", "Außerplanmäßige Abschreibung von Sachanlagen", "Expense", False, None),
    ("7040", "Geringwertige Wirtschaftsgüter (Sofortabschreibung)", "Expense", False, None),
    ("7180", "Gebühren", "Expense", False, None),
    ("7200", "Instandhaltung durch Dritte", "Expense", False, None),
    ("7300", "Transporte durch Dritte", "Expense", False, None),
    ("7320", "PKW-Betriebsaufwand", "Expense", False, None),
    ("7350", "Kilometergeld", "Expense", False, None),
    ("7360", "Aufwand für Verpflegung (Tagesgeld) - Inland", "Expense", False, None),
    ("7370", "Aufwand für Nächtigung - Inland", "Expense", False, None),
    ("7380", "Portogebühren", "Expense", False, None),
    ("7381", "Telefon- und Internetgebühren", "Expense", False, None),
    ("7400", "Miete, Pacht und Leasing", "Expense", False, None),
    ("7540", "Provisionen an Dritte", "Expense", False, None),
    ("7600", "Büromaterial", "Expense", False, None),
    ("7630", "Fachliteratur", "Expense", False, None),
    ("7650", "Werbeaufwand", "Expense", False, None),
    ("7680", "Bewirtung - Inland - abzugsfähiger Betrag", "Expense", False, None),
    ("7682", "Bewirtung - Inland - nicht abzugsfähiger Betrag", "Expense", False, None),
    ("7700", "Versicherungsaufwand", "Expense", False, None),
    ("7750", "Rechts- und Beratungsaufwand", "Expense", False, None),
    ("7780", "Kammerumlage", "Expense", False, None),
    ("7790", "Spesen des Geldverkehrs", "Expense", False, None),
    ("7812", "Abschreibung Inlandsforderungen", "Expense", False, None),
    ("7818", "Fremdwährungs-Kursverlust", "Expense", False, None),
    ("7820", "Buchwert abgegangener Anlagen", "Expense", False, None),
    ("7830", "Verluste aus dem Abgang von Anlagen", "Expense", False, None),
    ("7850", "Sonstiger betrieblicher Aufwand", "Expense", False, None),

    # ── Klasse 8: Finanzerträge, Finanzaufwendungen, Ertragsteuern ────────
    ("8000", "Erträge aus Beteiligungen", "Revenue", False, None),
    ("8100", "Zinserträge aus Bankguthaben", "Revenue", False, None),
    ("8130", "Verzugszinsenerträge", "Revenue", False, None),
    ("8280", "Zinsaufwand für Bankkredite", "Expense", False, None),
    ("8290", "Zinsaufwand für Darlehen", "Expense", False, None),
    ("8320", "Verzugszinsen-Aufwand", "Expense", False, None),
    ("8500", "Körperschaftsteuer", "Expense", False, None),
    ("8510", "Kapitalertragsteuer (KESt)", "Expense", False, None),

    # ── Klasse 9: Eigenkapital und Rücklagen ──────────────────────────────
    ("9000", "Eigenkapital", "Equity", False, None),
    ("9100", "Kapitalrücklage", "Equity", False, None),
    ("9200", "Gewinnrücklage", "Equity", False, None),
    ("9390", "Bilanzgewinn / Bilanzverlust", "Equity", False, None),
    ("9600", "Privat", "Equity", False, None),
]


# Semantic roles → EKR accounts. Everything downstream (tax catalog, document
# lifecycle, UVA) resolves accounts through these keys, never through codes,
# so this mapping is the single place where "which account carries the
# receivable" is decided.
AT_ROLE_BINDINGS = {
    "accounts_receivable": "2000",
    "accounts_payable": "3300",
    "cash": "2700",
    "bank": "2800",
    "inventory": "1600",          # Handelswarenvorrat (EKR 1300 is Hilfsstoffe)
    "revenue": "4000",
    "expense": "7850",            # unclassified expense → GuV Z 8
    "cogs": "5010",               # Handelswaren-Verbrauch (EKR 5000 is Bezugsverrechnung)
    "retained_earnings": "9390",
    "vat_output": "3500",
    "vat_output_20": "3500",
    "vat_output_10": "3501",
    "vat_output_13": "3502",
    "vat_output_4_9": "3503",
    "vat_input": "2500",
    "vat_input_20": "2500",
    "vat_input_10": "2501",
    "vat_input_13": "2502",
    "vat_input_4_9": "2503",
    "vat_rc_output": "3505",
    "vat_rc_input": "2505",
    "vat_rc_eu_payable": "3505",
    "vat_ig_acquisition_tax": "3505",
    "vat_ig_acquisition_input": "2505",
    "customer_advances": "3200",
}


def ekr_number(code: str) -> int | None:
    """The EKR number a code belongs to, or ``None`` if it carries no class.

    ``"4000"`` → 4000. Custom codes are not always four clean digits, and a
    tenant may well add ``"4A-REV"`` for a bespoke revenue account; those must
    still land in the statutory statements rather than being silently dropped,
    so the leading digits decide and the rest is padded: ``"4A-REV"`` → 4000,
    ``"45"`` → 4500. A code that starts with a letter has no EKR class to
    honour and returns ``None``.

    The padding means a one-digit custom code lands at the *start* of its
    class, which for class 7 is the Abschreibungen range — imprecise, but a
    custom account in a neighbouring position beats one missing from the GuV.
    """
    digits = ""
    for ch in code:
        if not ch.isdigit():
            break
        digits += ch
    if not digits:
        return None
    return int(digits.ljust(4, "0")[:4])


def _posted_account_ids(session: Session, tenant_id: int) -> set[int]:
    """Account ids that already carry at least one journal entry."""
    rows = session.exec(
        select(JournalEntry.account_id).where(JournalEntry.tenant_id == tenant_id)
    ).all()
    return {int(r) for r in rows}


def install_at_kmu_coa(session: Session, tenant_id: int) -> Dict[str, Any]:
    """Switch the tenant onto the Austrian EKR chart of accounts.

    This is a *replacement*, not an addition. Every tenant is seeded with the
    generic English chart at signup, and its codes overlap the EKR with wholly
    different meanings — 2000 is Accounts Payable there and Forderungen aus
    Lieferungen und Leistungen here, 1100 is Accounts Receivable there and
    Rohstoffvorrat here. Simply creating "the codes that don't exist yet" left
    those English accounts in place and then bound the semantic roles to them,
    so ``accounts_receivable`` pointed at a liability account called Accounts
    Payable and every finalized Austrian invoice debited the wrong side of the
    balance sheet.

    So each code in the template is brought to its EKR definition:

    * missing        → created
    * present, same  → left alone (re-running this is idempotent)
    * present, other → **renamed and retyped in place**, which keeps every
      foreign key (role bindings, defaults, existing documents) intact
    * present, other, *and already posted to* → refused, because renaming an
      account under existing journal entries would silently reinterpret them

    Legacy accounts outside the template that were never posted to are
    deactivated so the Austrian chart is what the user actually sees; ones
    that carry postings are kept and reported back, since they are real
    bookkeeping history.
    """
    posted = _posted_account_ids(session, tenant_id)
    existing = {
        acc.code: acc
        for acc in session.exec(select(Account).where(Account.tenant_id == tenant_id)).all()
    }

    template_codes = {code for code, *_ in AT_KMU_COA_TEMPLATE}

    # Refuse before touching anything, and name every offending account.
    blocked = [
        f"{acc.code} '{acc.name}' → '{name}'"
        for code, name, acc_type, _is_group, _parent in AT_KMU_COA_TEMPLATE
        if (acc := existing.get(code)) is not None
        and (acc.name != name or acc.type != acc_type)
        and acc.id in posted
    ]
    if blocked:
        raise HTTPException(
            409,
            "Der österreichische Kontenrahmen kann nicht installiert werden: "
            "folgende Konten sind bereits bebucht und hätten eine andere "
            "Bedeutung erhalten — " + "; ".join(sorted(blocked)) + ". "
            "Bitte den Kontenrahmen auf einem Mandanten ohne Buchungen "
            "einrichten oder diese Buchungen zuvor umbuchen.",
        )

    created_accounts: Dict[str, Account] = {}
    created = renamed = 0
    for code, name, acc_type, is_group, _parent in AT_KMU_COA_TEMPLATE:
        acc = existing.get(code)
        if acc is None:
            acc = Account(
                tenant_id=tenant_id, code=code, name=name, type=acc_type, is_group=is_group,
            )
            session.add(acc)
            session.flush()
            created += 1
        elif acc.name != name or acc.type != acc_type:
            acc.name, acc.type, acc.is_group = name, acc_type, is_group
            acc.is_active = True
            session.add(acc)
            renamed += 1
        created_accounts[code] = acc

    # Retire the leftovers of the generic chart; keep anything already posted.
    deactivated: List[str] = []
    kept_with_history: List[str] = []
    for code, acc in existing.items():
        if code in template_codes:
            continue
        if acc.id in posted:
            kept_with_history.append(code)
        elif acc.is_active:
            acc.is_active = False
            session.add(acc)
            deactivated.append(code)

    # Bind semantic roles
    for role_key, acc_code in AT_ROLE_BINDINGS.items():
        if acc_code in created_accounts:
            bind_account_role(
                session=session,
                tenant_id=tenant_id,
                role_key=role_key,
                account_id=created_accounts[acc_code].id,
            )

    # Set party types for subledger
    if "2000" in created_accounts:
        created_accounts["2000"].party_type = "customer"
        session.add(created_accounts["2000"])
    if "3300" in created_accounts:
        created_accounts["3300"].party_type = "vendor"
        session.add(created_accounts["3300"])

    # Point the generic "default account" settings at their EKR counterparts so
    # any non-Austrian code path resolves an EKR account instead of recreating
    # an English one by code.
    for setting_key, role_key in (
        ("default_ar_account", "accounts_receivable"),
        ("default_ap_account", "accounts_payable"),
        ("default_revenue_account", "revenue"),
        ("default_cogs_account", "cogs"),
    ):
        _upsert_setting(session, tenant_id, setting_key, AT_ROLE_BINDINGS[role_key])

    session.flush()
    return {
        "installed": True,
        "accounts_count": len(created_accounts),
        "accounts_created": created,
        "accounts_realigned": renamed,
        "legacy_deactivated": sorted(deactivated),
        "legacy_kept_with_history": sorted(kept_with_history),
        "roles_bound": len(AT_ROLE_BINDINGS),
    }


def _upsert_setting(session: Session, tenant_id: int, key: str, value: str) -> None:
    row = session.exec(
        select(Settings).where(Settings.tenant_id == tenant_id, Settings.key == key)
    ).first()
    if row:
        row.value = value
    else:
        row = Settings(tenant_id=tenant_id, key=key, value=value)
    session.add(row)
