"""Austrian Tax Treatment Catalog and Effective-Dated Rules (PR 6: AT-05).

Defines statutory tax rates and rules under Austrian UStG 1994:
- 20 % Normalsteuersatz (§ 10 Abs. 1 UStG)
- 10 % Ermäßigter Steuersatz (§ 10 Abs. 2 UStG - Vermietung, Bücher, etc.)
- 13 % Ermäßigter Steuersatz (§ 10 Abs. 3 UStG - Kunst, Beherbergung, etc.)
- 4,9 % Ermäßigter Steuersatz (ab 01.07.2026 für Anlage-3-Grundnahrungsmittel;
  nicht für Gastronomie, Alkohol oder Mischleistungen)
- 0 % Steuerfreie Lieferungen mit Vorsteuerabzug (Ausfuhr, ig. Lieferung)
- Reverse Charge (§ 19 Abs. 1/1a UStG)
- Kleinunternehmerbefreiung (§ 6 Abs. 1 Z 27 UStG)
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from models_at import TaxTreatmentVersion
from services.money import D, ZERO


# Anlage 3 approved classifications for 4.9% essential food goods
ANLAGE_3_APPROVED = {
    "staple_food",
    "bread_grain",
    "dairy_milk",
    "basic_groceries",
    "essential_food",
}

EXCLUDED_4_9_CLASSIFICATIONS = {
    "gastronomy",
    "restaurant",
    "prepared_meals",
    "alcohol",
    "tobacco",
    "luxury",
}


AT_TAX_TREATMENTS_CATALOG: List[Dict[str, Any]] = [
    {
        "code": "AT_STANDARD_20",
        "name": "Normalsteuersatz 20 % (§ 10 Abs. 1 UStG)",
        "direction": "both",
        "treatment_type": "standard",
        "rate": Decimal("20.00"),
        "valid_from": "1995-01-01",
        "valid_to": None,
        "uva_base_kz": "022",
        "uva_tax_kz": "022",
        "output_account_role": "vat_output_20",
        "input_account_role": "vat_input_20",
        "zm_relevant": False,
        "deductibility_rate": Decimal("1.0"),
    },
    {
        "code": "AT_REDUCED_10",
        "name": "Ermäßigter Steuersatz 10 % (§ 10 Abs. 2 UStG)",
        "direction": "both",
        "treatment_type": "reduced_10",
        "rate": Decimal("10.00"),
        "valid_from": "1995-01-01",
        "valid_to": None,
        "uva_base_kz": "029",
        "uva_tax_kz": "029",
        "output_account_role": "vat_output_10",
        "input_account_role": "vat_input_10",
        "zm_relevant": False,
        "deductibility_rate": Decimal("1.0"),
    },
    {
        "code": "AT_REDUCED_13",
        "name": "Ermäßigter Steuersatz 13 % (§ 10 Abs. 3 UStG)",
        "direction": "both",
        "treatment_type": "reduced_13",
        "rate": Decimal("13.00"),
        "valid_from": "2016-01-01",
        "valid_to": None,
        "uva_base_kz": "006",
        "uva_tax_kz": "006",
        "output_account_role": "vat_output_13",
        "input_account_role": "vat_input_13",
        "zm_relevant": False,
        "deductibility_rate": Decimal("1.0"),
    },
    {
        "code": "AT_REDUCED_4_9",
        "name": "Ermäßigter Steuersatz 4,9 % (Grundnahrungsmittel ab 01.07.2026)",
        "direction": "both",
        "treatment_type": "reduced_4_9",
        "rate": Decimal("4.90"),
        "valid_from": "2026-07-01",
        "valid_to": None,
        "uva_base_kz": "124",
        "uva_tax_kz": "125",
        "output_account_role": "vat_output_4_9",
        "input_account_role": "vat_input_4_9",
        "zm_relevant": False,
        "deductibility_rate": Decimal("1.0"),
    },
    {
        "code": "AT_ZERO_EXPORT",
        "name": "Steuerfreie Ausfuhrlieferung Drittland (§ 6 Abs. 1 Z 1 iVm § 7 UStG)",
        "direction": "sales",
        "treatment_type": "export",
        "rate": Decimal("0.00"),
        "valid_from": "1995-01-01",
        "valid_to": None,
        "uva_base_kz": "011",
        "uva_tax_kz": None,
        "output_account_role": "sales_tax_exempt",
        "zm_relevant": False,
        "legal_notice": "Steuerfreie Ausfuhrlieferung gem. § 6 Abs. 1 Z 1 UStG",
        "deductibility_rate": Decimal("1.0"),
    },
    {
        "code": "AT_ZERO_IG_SUPPLY",
        "name": "Steuerfreie innergemeinschaftliche Lieferung (Art. 6 Abs. 1 UStG)",
        "direction": "sales",
        "treatment_type": "intra_eu_supply",
        "rate": Decimal("0.00"),
        "valid_from": "1995-01-01",
        "valid_to": None,
        "uva_base_kz": "017",
        "uva_tax_kz": None,
        "output_account_role": "sales_tax_exempt",
        "zm_relevant": True,
        "legal_notice": "Steuerfreie innergemeinschaftliche Lieferung gem. Art. 6 UStG",
        "deductibility_rate": Decimal("1.0"),
    },
    {
        "code": "AT_IG_ACQUISITION_20",
        "name": "Innergemeinschaftlicher Erwerb 20 % (Art. 1 UStG)",
        "direction": "purchases",
        "treatment_type": "intra_eu_acquisition",
        "rate": Decimal("20.00"),
        "valid_from": "1995-01-01",
        "valid_to": None,
        "uva_base_kz": "070",
        "uva_tax_kz": "065",
        "output_account_role": "vat_ig_acquisition_tax",
        "input_account_role": "vat_ig_acquisition_input",
        "zm_relevant": False,
        "deductibility_rate": Decimal("1.0"),
    },
    {
        "code": "AT_IG_ACQUISITION_4_9",
        "name": "Innergemeinschaftlicher Erwerb 4,9 % (Anlage 3 ab 01.07.2026)",
        "direction": "purchases",
        "treatment_type": "intra_eu_acquisition",
        "rate": Decimal("4.90"),
        "valid_from": "2026-07-01",
        "valid_to": None,
        "uva_base_kz": "125",
        "uva_tax_kz": "125",
        "output_account_role": "vat_ig_acquisition_tax",
        "input_account_role": "vat_ig_acquisition_input",
        "zm_relevant": False,
        "deductibility_rate": Decimal("1.0"),
    },
    {
        "code": "AT_RC_DOMESTIC",
        "name": "Übergang der Steuerschuld - Bauleistungen (§ 19 Abs. 1a UStG)",
        "direction": "both",
        "treatment_type": "reverse_charge",
        "rate": Decimal("0.00"),
        "valid_from": "2002-10-01",
        "valid_to": None,
        "uva_base_kz": "021",
        "uva_tax_kz": None,
        "output_account_role": "vat_rc_output",
        "input_account_role": "vat_input_20",
        "zm_relevant": False,
        "legal_notice": "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge gem. § 19 Abs. 1a UStG)",
        "deductibility_rate": Decimal("1.0"),
    },
    {
        "code": "AT_RC_EU_SERVICE_OUT",
        "name": "Nicht steuerbare B2B-Dienstleistung an EU-Unternehmer (§ 3a Abs. 6 UStG)",
        "direction": "sales",
        "treatment_type": "reverse_charge",
        "rate": Decimal("0.00"),
        "valid_from": "2010-01-01",
        "valid_to": None,
        "uva_base_kz": "021",
        "uva_tax_kz": None,
        "output_account_role": "sales_rc_eu",
        "zm_relevant": True,
        "legal_notice": "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge gem. Art. 196 MwSt-SystRL / § 3a Abs. 6 UStG)",
        "deductibility_rate": Decimal("1.0"),
    },
    {
        "code": "AT_RC_EU_SERVICE_IN",
        "name": "Bezug von Dienstleistungen ausländischer Unternehmer (§ 19 Abs. 1 2. Satz UStG)",
        "direction": "purchases",
        "treatment_type": "reverse_charge",
        "rate": Decimal("20.00"),
        "valid_from": "2010-01-01",
        "valid_to": None,
        "uva_base_kz": "057",
        "uva_tax_kz": "066",
        "output_account_role": "vat_rc_eu_payable",
        "input_account_role": "vat_input_20",
        "zm_relevant": False,
        "deductibility_rate": Decimal("1.0"),
    },
    {
        "code": "AT_EXEMPT_KU",
        "name": "Steuerbefreit für Kleinunternehmer (§ 6 Abs. 1 Z 27 UStG)",
        "direction": "sales",
        "treatment_type": "small_business_exempt",
        "rate": Decimal("0.00"),
        "valid_from": "1995-01-01",
        "valid_to": None,
        "uva_base_kz": "016",
        "uva_tax_kz": None,
        "output_account_role": "sales_exempt_ku",
        "zm_relevant": False,
        "legal_notice": "Umsatzsteuerbefreit aufgrund der Kleinunternehmerregelung gem. § 6 Abs. 1 Z 27 UStG",
        "deductibility_rate": Decimal("0.0"),
    },
]


def init_at_tax_treatments(session: Session, tenant_id: int) -> None:
    """Seed or update statutory Austrian tax treatment versions for a tenant."""
    for item in AT_TAX_TREATMENTS_CATALOG:
        existing = session.exec(
            select(TaxTreatmentVersion).where(
                TaxTreatmentVersion.tenant_id == tenant_id,
                TaxTreatmentVersion.code == item["code"],
                TaxTreatmentVersion.valid_from == item["valid_from"],
            )
        ).first()
        if not existing:
            row = TaxTreatmentVersion(tenant_id=tenant_id, **item)
            session.add(row)
    session.flush()


def resolve_tax_treatment(
    session: Session,
    tenant_id: int,
    code: str,
    on_date: str,
    product_classification: Optional[str] = None,
    direction: Optional[str] = None,
) -> TaxTreatmentVersion:
    """Resolve active tax treatment for a code as of the given date.
    
    Enforces statutory validity dates and classification restrictions (§ 10 UStG).
    """
    date_str = str(on_date)[:10]

    # Special rule: 4.9% rate is strictly effective from 2026-07-01
    if code in {"AT_REDUCED_4_9", "AT_IG_ACQUISITION_4_9"}:
        if date_str < "2026-07-01":
            raise HTTPException(
                400,
                f"Der ermäßigte Steuersatz von 4,9 % gilt erst ab 01.07.2026. Vorheriger Beleg ({date_str}) unzulässig.",
            )
        if product_classification not in ANLAGE_3_APPROVED:
            raise HTTPException(
                400,
                "Der Steuersatz von 4,9 % erfordert eine positiv bestätigte "
                "Anlage-3-Warenklassifikation und ist insbesondere für Gastronomie nicht anwendbar; "
                f"erhalten: {product_classification or 'keine'}.",
            )

    # Fetch from DB or catalog
    row = session.exec(
        select(TaxTreatmentVersion).where(
            TaxTreatmentVersion.tenant_id == tenant_id,
            TaxTreatmentVersion.code == code,
            TaxTreatmentVersion.valid_from <= date_str,
        ).order_by(TaxTreatmentVersion.valid_from.desc())
    ).first()

    if not row:
        # Fallback to catalog definition if not seeded in DB yet
        for cat in AT_TAX_TREATMENTS_CATALOG:
            if cat["code"] == code and cat["valid_from"] <= date_str:
                row = TaxTreatmentVersion(tenant_id=tenant_id, **cat)
                session.add(row)
                session.flush()
                break

    if not row:
        raise HTTPException(
            422,
            f"Steuerbehandlung '{code}' für Datum {date_str} nicht gefunden oder noch nicht gültig.",
        )

    if row.valid_to and date_str > row.valid_to:
        raise HTTPException(
            400,
            f"Steuerbehandlung '{code}' ist seit {row.valid_to} abgelaufen.",
        )

    if direction and row.direction != "both" and row.direction != direction:
        raise HTTPException(
            400,
            f"Steuerbehandlung '{code}' ist nur für '{row.direction}' zulässig, nicht für '{direction}'.",
        )

    return row
