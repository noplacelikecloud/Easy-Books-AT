"""Austrian Invoice and Document Requirements Validation (AT-06, § 11 UStG, § 14 UGB).

Validates mandatory Austrian invoice elements:
- Kleinbetragsrechnung threshold (<= 400.00 EUR gross vs > 400.00 EUR)
- Large invoice customer UID threshold (> 10,000.00 EUR B2B)
- Mandatory legal notices for Reverse Charge, Kleinunternehmer, Intra-EU supply, Export
- Consecutive numbering and service period
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, List, Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from models import Customer, Invoice, InvoiceLine, Settings, Tenant
from services.money import D


KLEINBETRAG_THRESHOLD = Decimal("400.00")
LARGE_INVOICE_THRESHOLD = Decimal("10000.00")


def validate_at_invoice(session: Session, invoice: Invoice) -> None:
    """Validate that an invoice meets all Austrian statutory criteria under § 11 UStG / § 14 UGB."""
    tenant = session.get(Tenant, invoice.tenant_id)
    settings_rows = session.exec(
        select(Settings).where(Settings.tenant_id == invoice.tenant_id)
    ).all()
    settings_map = {s.key: s.value for s in settings_rows}

    # 1. Supplier details
    supplier_name = settings_map.get("company_name") or (tenant.name if tenant else "")
    if not supplier_name:
        raise HTTPException(422, "Rechnungsaussteller (Firmenname) ist ein gesetzliches Pflichtfeld (§ 11 UStG).")

    # 2. Customer details
    customer = session.get(Customer, invoice.customer_id) if invoice.customer_id else None
    customer_name = invoice.customer_name or (customer.name if customer else "")
    if not customer_name:
        raise HTTPException(422, "Rechnungsempfänger (Name/Firma) ist ein gesetzliches Pflichtfeld (§ 11 UStG).")

    # 3. Consecutive invoice number
    if not invoice.number:
        raise HTTPException(422, "Fortlaufende Rechnungsnummer fehlt (§ 11 Abs. 1 Z 6 UStG).")

    # 4. Issue date and Service date
    if not invoice.issue_date:
        raise HTTPException(422, "Ausstellungsdatum fehlt (§ 11 Abs. 1 Z 2 UStG).")

    lines = session.exec(
        select(InvoiceLine).where(InvoiceLine.invoice_id == invoice.id)
    ).all()
    if not lines:
        raise HTTPException(422, "Rechnung muss mindestens eine Leistungsposition enthalten.")

    has_service_date = bool(
        invoice.service_date_start
        or invoice.service_date_end
        or any(getattr(ln, "service_date", None) for ln in lines)
    )
    if not has_service_date:
        raise HTTPException(422, "Tag der Lieferung oder Zeitraum der Leistung fehlt (§ 11 Abs. 1 Z 4 UStG).")

    # 5. Kleinbetragsrechnung check (<= 400.00 EUR gross) vs Standard
    total_gross = D(str(invoice.total or 0))
    from localizations.at.profile import get_active_profile
    prof = get_active_profile(session, invoice.tenant_id, invoice.issue_date)
    supplier_uid = (prof.vat_id if prof else None) or settings_map.get("vat_id") or settings_map.get("uid")

    if total_gross > KLEINBETRAG_THRESHOLD:
        if not supplier_uid and (not prof or prof.vat_status != "small_business_exempt"):
            raise HTTPException(
                422,
                f"Bei Rechnungsbeträgen über {KLEINBETRAG_THRESHOLD} EUR ist die UID des leistenden Unternehmers verpflichtend (§ 11 Abs. 1 Z 3 lit. a UStG).",
            )

    # 6. B2B Large Invoice (> 10,000.00 EUR) customer UID requirement
    if total_gross > LARGE_INVOICE_THRESHOLD:
        is_b2b = customer.is_business if customer else True
        if is_b2b:
            cust_uid = getattr(customer, "uid", None) or getattr(customer, "gstin", None)
            if not cust_uid:
                raise HTTPException(
                    422,
                    f"Bei Rechnungen über {LARGE_INVOICE_THRESHOLD} EUR an andere Unternehmer ist die UID des Kunden verpflichtend (§ 11 Abs. 1 Z 3 lit. b UStG).",
                )

    # 7. Check line tax treatment codes and mandatory legal notices
    for ln in lines:
        code = getattr(ln, "tax_treatment_code", None)
        notes = (invoice.notes or "") + (invoice.description or "")
        
        if code in ("AT_RC_DOMESTIC", "AT_RC_EU_SERVICE_OUT", "reverse_charge"):
            if "reverse charge" not in notes.lower() and "steuerschuldnerschaft" not in notes.lower():
                raise HTTPException(
                    422,
                    "Bei Übergang der Steuerschuld (Reverse Charge) ist der gesetzliche Hinweis 'Steuerschuldnerschaft des Leistungsempfängers' verpflichtend (§ 11 Abs. 1a UStG).",
                )

        if code in ("AT_ZERO_IG_SUPPLY", "intra_eu_supply"):
            cust_uid = getattr(customer, "uid", None) or getattr(customer, "gstin", None)
            if not cust_uid:
                raise HTTPException(
                    422,
                    "Für eine steuerfreie innergemeinschaftliche Lieferung ist eine gültige UID des Empfängers erforderlich (Art. 6 UStG).",
                )
            if "innergemeinschaft" not in notes.lower():
                raise HTTPException(
                    422,
                    "Hinweis auf 'steuerfreie innergemeinschaftliche Lieferung' ist verpflichtend (Art. 11 UStG).",
                )

        if code in ("AT_EXEMPT_KU", "small_business_exempt"):
            if "kleinunternehmer" not in notes.lower() and "§ 6 abs. 1 z 27" not in notes.lower():
                raise HTTPException(
                    422,
                    "Hinweis 'Umsatzsteuerbefreit aufgrund der Kleinunternehmerregelung gem. § 6 Abs. 1 Z 27 UStG' ist verpflichtend.",
                )
