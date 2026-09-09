"""Austrian KMU Chart of Accounts (Einheitskontenrahmen EKR) Seed & Mappings (PR 4, AT-05, AT-11).

Provides:
- Standard Austrian KMU account structure (Classes 0-9)
- AccountRoleBinding configuration (§ 190 UGB)
- Statutory UGB and E1a report line mappings (§ 224, 231 UGB, § 4 Abs. 3 EStG)
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sqlmodel import Session, select

from models import Account
from models_at import AccountRoleBinding, ReportLineMapping
from services.account_roles import bind_account_role


# (code, name, type, is_group, parent_code)
AT_KMU_COA_TEMPLATE: List[Tuple[str, str, str, bool, str | None]] = [
    # Klasse 0: Anlagevermögen
    ("0100", "Immaterielle Vermögensgegenstände", "Asset", False, None),
    ("0400", "Maschinen und maschinelle Anlagen", "Asset", False, None),
    ("0600", "Betriebs- und Geschäftsausstattung (BGA)", "Asset", False, None),
    ("0800", "Geringwertige Wirtschaftsgüter (GWG)", "Asset", False, None),

    # Klasse 1: Vorräte
    ("1100", "Roh-, Hilfs- und Betriebsstoffe", "Asset", False, None),
    ("1300", "Handelswarenvorrat", "Asset", False, None),

    # Klasse 2: Sonstiges Umlaufvermögen, Forderungen, Kassa, Bank
    ("2000", "Lieferforderungen (Inland)", "Asset", False, None),
    ("2300", "Sonstige Forderungen", "Asset", False, None),
    ("2500", "Vorsteuer 20%", "Asset", False, None),
    ("2510", "Vorsteuer 10%", "Asset", False, None),
    ("2520", "Vorsteuer 13%", "Asset", False, None),
    ("2530", "Vorsteuer 4,9%", "Asset", False, None),
    ("2540", "Vorsteuer Erwerb / Reverse Charge", "Asset", False, None),
    ("2700", "Kassa", "Asset", False, None),
    ("2800", "Bankguthaben (Girokonto)", "Asset", False, None),

    # Klasse 3: Rückstellungen und Verbindlichkeiten
    ("3000", "Rückstellungen", "Liability", False, None),
    ("3300", "Lieferverbindlichkeiten (Inland)", "Liability", False, None),
    ("3200", "Erhaltene Anzahlungen", "Liability", False, None),
    ("3500", "Umsatzsteuer 20%", "Liability", False, None),
    ("3510", "Umsatzsteuer 10%", "Liability", False, None),
    ("3520", "Umsatzsteuer 13%", "Liability", False, None),
    ("3530", "Umsatzsteuer 4,9%", "Liability", False, None),
    ("3540", "Umsatzsteuer Erwerb / Reverse Charge", "Liability", False, None),

    # Klasse 4: Betriebliche Erträge
    ("4000", "Umsatzerlöse 20%", "Revenue", False, None),
    ("4010", "Umsatzerlöse 10%", "Revenue", False, None),
    ("4020", "Umsatzerlöse 13%", "Revenue", False, None),
    ("4030", "Umsatzerlöse 4,9%", "Revenue", False, None),
    ("4040", "Steuerfreie Erlöse Kleinunternehmer gem. § 6(1)27", "Revenue", False, None),
    ("4050", "Steuerfreie ig. Lieferungen Art. 6", "Revenue", False, None),
    ("4060", "Steuerfreie Ausfuhren Drittland § 6(1)1", "Revenue", False, None),

    # Klasse 5: Material- und bezogene Leistungen
    ("5000", "Handelswareneinsatz / Materialaufwand", "Expense", False, None),
    ("5100", "Fremdleistungen", "Expense", False, None),

    # Klasse 7: Personalaufwand
    ("7000", "Löhne und Gehälter", "Expense", False, None),
    ("7100", "Gesetzlicher Sozialaufwand", "Expense", False, None),

    # Klasse 8: Abschreibungen, Zinsen, Steuern
    ("8000", "Abschreibungen auf Sachanlagen (AfA)", "Expense", False, None),
    ("8010", "Sofortabschreibung geringwertiger Wirtschaftsgüter", "Expense", False, None),
    ("8200", "Zinsaufwendungen", "Expense", False, None),
    ("8500", "Körperschaftsteuer (KöSt)", "Expense", False, None),

    # Klasse 9: Eigenkapital, Rücklagen, Abschluss
    ("9000", "Stammkapital / Gezeichnetes Kapital", "Equity", False, None),
    ("9300", "Bilanzgewinn / Gewinnvortrag", "Equity", False, None),
    ("9600", "Privatentnahmen", "Equity", False, None),
    ("9700", "Privateinlagen", "Equity", False, None),
]


AT_ROLE_BINDINGS = {
    "accounts_receivable": "2000",
    "accounts_payable": "3300",
    "cash": "2700",
    "bank": "2800",
    "inventory": "1300",
    "revenue": "4000",
    "expense": "5000",
    "cogs": "5000",
    "retained_earnings": "9300",
    "vat_output": "3500",
    "vat_output_20": "3500",
    "vat_output_10": "3510",
    "vat_output_13": "3520",
    "vat_output_4_9": "3530",
    "vat_input": "2500",
    "vat_input_20": "2500",
    "vat_input_10": "2510",
    "vat_input_13": "2520",
    "vat_input_4_9": "2530",
    "vat_rc_output": "3540",
    "vat_rc_input": "2540",
    "vat_rc_eu_payable": "3540",
    "vat_ig_acquisition_tax": "3540",
    "vat_ig_acquisition_input": "2540",
    "customer_advances": "3200",
}


def install_at_kmu_coa(session: Session, tenant_id: int) -> Dict[str, Any]:
    """Install the standard Austrian KMU Chart of Accounts and semantic role bindings."""
    created_accounts: Dict[str, Account] = {}
    for code, name, acc_type, is_group, _ in AT_KMU_COA_TEMPLATE:
        existing = session.exec(
            select(Account).where(Account.tenant_id == tenant_id, Account.code == code)
        ).first()
        if not existing:
            acc = Account(
                tenant_id=tenant_id,
                code=code,
                name=name,
                type=acc_type,
                is_group=is_group,
            )
            session.add(acc)
            session.flush()
            created_accounts[code] = acc
        else:
            created_accounts[code] = existing

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

    session.flush()
    return {
        "installed": True,
        "accounts_count": len(created_accounts),
        "roles_bound": len(AT_ROLE_BINDINGS),
    }
