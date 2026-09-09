"""Austrian Small Business Exemption and Threshold Monitoring (PR 9: AT-EAR-KU).

Under § 6 Abs. 1 Z 27 UStG 1994 (as amended from 2025):
- Annual turnover limit: 55,000.00 EUR agreed consideration
- 10% tolerance in the year of the breach (up to 60,500.00 EUR)
- The transaction crossing 60,500 EUR and all later transactions are taxable.
- Option for standard VAT under § 6 Abs. 3 UStG (Regelbesteuerungsantrag, binding for 5 years).
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from localizations.at.profile import create_profile_version, get_active_profile
from models import Invoice
from models_at import SmallBusinessThresholdLedger
from services.money import D, ZERO, money


KU_THRESHOLD = Decimal("55000.00")
KU_TOLERANCE = Decimal("60500.00")  # 55,000 + 10%


def get_or_create_ku_ledger(
    session: Session, tenant_id: int, year: int
) -> SmallBusinessThresholdLedger:
    ledger = session.exec(
        select(SmallBusinessThresholdLedger).where(
            SmallBusinessThresholdLedger.tenant_id == tenant_id,
            SmallBusinessThresholdLedger.year == year,
        )
    ).first()

    if not ledger:
        ledger = SmallBusinessThresholdLedger(
            tenant_id=tenant_id,
            year=year,
            qualifying_turnover=ZERO,
            threshold_amount=KU_THRESHOLD,
            tolerance_amount=KU_TOLERANCE,
            is_exceeded=False,
        )
        session.add(ledger)
        session.flush()

    return ledger


def record_turnover_for_invoice(
    session: Session,
    invoice: Invoice,
) -> SmallBusinessThresholdLedger:
    """Record an invoice against the annual small business threshold."""
    prof = get_active_profile(session, invoice.tenant_id, invoice.issue_date)
    if not prof or prof.vat_status != "small_business_exempt":
        # Only tracks tenants operating under small business exemption
        year = int(str(invoice.issue_date)[:4])
        return get_or_create_ku_ledger(session, invoice.tenant_id, year)

    year = int(str(invoice.issue_date)[:4])
    ledger = get_or_create_ku_ledger(session, invoice.tenant_id, year)

    inv_eur = money(D(invoice.total or invoice.subtotal or 0) * D(invoice.exchange_rate or 1.0))
    ledger.qualifying_turnover = money(ledger.qualifying_turnover + inv_eur)

    if ledger.qualifying_turnover > ledger.tolerance_amount and not ledger.is_exceeded:
        ledger.is_exceeded = True
        ledger.exceeded_on_date = invoice.issue_date
        ledger.exceeded_by_invoice_id = invoice.id

        # Automatically transition profile from exceeded date to standard VAT
        create_profile_version(
            session=session,
            tenant_id=invoice.tenant_id,
            user_id=getattr(invoice, "created_by_id", None),
            data={
                "valid_from": invoice.issue_date,
                "legal_form": prof.legal_form,
                "profit_method": prof.profit_method,
                "vat_status": "standard",
                "vat_method": prof.vat_method,
                "vat_filing_frequency": "monthly",
                "company_register_number": prof.company_register_number,
                "company_register_court": prof.company_register_court,
                "tax_number": prof.tax_number,
                "vat_id": prof.vat_id,
                "registered_seat": prof.registered_seat,
                "change_reason": (
                    f"Automatische Umstellung auf Regelbesteuerung: Kleinunternehmergrenze "
                    f"({ledger.tolerance_amount} EUR) durch Rechnung {invoice.number} am {invoice.issue_date} überschritten."
                ),
            },
        )

    session.add(ledger)
    session.flush()
    return ledger


def prepare_turnover_for_invoice(
    session: Session,
    invoice: Invoice,
    lines: list[Any],
) -> SmallBusinessThresholdLedger:
    """Record turnover before resolving the invoice's tax treatments.

    A crossing transaction must itself be taxable. Therefore an effective
    standard profile is created in the same transaction before validation and
    posting. Any later validation error rolls the entire transition back.
    """
    prof = get_active_profile(session, invoice.tenant_id, invoice.issue_date)
    year = int(str(invoice.issue_date)[:4])
    ledger = get_or_create_ku_ledger(session, invoice.tenant_id, year)
    if not prof or prof.vat_status != "small_business_exempt":
        return ledger

    qualifying = ZERO
    for line in lines:
        code = getattr(line, "tax_treatment_code", None) or invoice.tax_treatment_code
        if code == "AT_RC_EU_SERVICE_OUT":
            continue
        qualifying += D(getattr(line, "amount", ZERO) or ZERO)
    prospective = money(
        ledger.qualifying_turnover + qualifying * D(invoice.exchange_rate or 1)
    )
    prior = session.exec(select(SmallBusinessThresholdLedger).where(
        SmallBusinessThresholdLedger.tenant_id == invoice.tenant_id,
        SmallBusinessThresholdLedger.year == year - 1,
    )).first()
    prior_exceeded = bool(
        (prior and D(prior.qualifying_turnover) > KU_THRESHOLD)
        or D(prof.prior_year_turnover or ZERO) > KU_THRESHOLD
    )
    taxable_now = prior_exceeded or prospective > ledger.tolerance_amount

    ledger.qualifying_turnover = prospective
    if prospective > ledger.tolerance_amount:
        ledger.is_exceeded = True
        ledger.exceeded_on_date = ledger.exceeded_on_date or invoice.issue_date
        ledger.exceeded_by_invoice_id = ledger.exceeded_by_invoice_id or invoice.id
    session.add(ledger)

    if taxable_now:
        create_profile_version(
            session=session,
            tenant_id=invoice.tenant_id,
            user_id=getattr(invoice, "created_by_id", None),
            data={
                "valid_from": invoice.issue_date,
                "legal_form": prof.legal_form,
                "profit_method": prof.profit_method,
                "vat_status": "standard",
                "vat_method": prof.vat_method,
                "vat_filing_frequency": prof.vat_filing_frequency,
                "fiscal_year_start": prof.fiscal_year_start,
                "company_register_number": prof.company_register_number,
                "company_register_court": prof.company_register_court,
                "tax_number": prof.tax_number,
                "vat_id": prof.vat_id,
                "registered_seat": prof.registered_seat,
                "change_reason": (
                    "Automatische Umstellung gemäß § 6 Abs. 1 Z 27 UStG: "
                    + ("Vorjahresgrenze überschritten." if prior_exceeded else
                       f"10-%-Toleranz durch Rechnung {invoice.number} überschritten.")
                ),
            },
        )
    session.flush()
    return ledger


def get_small_business_status(session: Session, tenant_id: int, year: int) -> Dict[str, Any]:
    """Inspect current Kleinunternehmer limit status and warning tiers."""
    ledger = get_or_create_ku_ledger(session, tenant_id, year)

    turnover = ledger.qualifying_turnover
    threshold = ledger.threshold_amount
    tolerance = ledger.tolerance_amount

    remaining_to_threshold = money(max(ZERO, threshold - turnover))
    remaining_to_tolerance = money(max(ZERO, tolerance - turnover))
    percent = money((turnover / threshold) * D("100")) if threshold > 0 else ZERO

    if ledger.is_exceeded or turnover > tolerance:
        status = "exceeded"
    elif turnover > threshold:
        status = "tolerance_window"
    elif turnover >= threshold * D("0.85"):
        status = "warning_approaching"
    else:
        status = "ok"

    return {
        "year": year,
        "qualifying_turnover": float(turnover),
        "threshold": float(threshold),
        "tolerance": float(tolerance),
        "remaining_buffer": float(remaining_to_tolerance),
        "percentage_used": float(percent),
        "status": status,
        "is_exceeded": ledger.is_exceeded,
        "exceeded_on_date": ledger.exceeded_on_date,
        "exceeded_by_invoice_id": ledger.exceeded_by_invoice_id,
        "opted_into_standard_vat": ledger.opted_into_standard_vat,
        "option_valid_from": ledger.option_valid_from,
    }


def opt_into_standard_vat(
    session: Session,
    tenant_id: int,
    valid_from: str,
    user_id: int,
    reason: Optional[str] = None,
) -> SmallBusinessThresholdLedger:
    """Voluntary waiver of small business exemption (§ 6 Abs. 3 UStG - Regelbesteuerungsantrag)."""
    prof = get_active_profile(session, tenant_id, valid_from)
    year = int(str(valid_from)[:4])
    ledger = get_or_create_ku_ledger(session, tenant_id, year)

    ledger.opted_into_standard_vat = True
    ledger.option_valid_from = valid_from
    session.add(ledger)

    create_profile_version(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        data={
            "valid_from": valid_from,
            "legal_form": prof.legal_form if prof else "sole_proprietor",
            "profit_method": prof.profit_method if prof else "ear",
            "vat_status": "opted_in",
            "vat_method": prof.vat_method if prof else "cash",
            "vat_filing_frequency": "quarterly",
            "change_reason": reason or "Freiwilliger Verzicht auf Kleinunternehmerbefreiung gem. § 6 Abs. 3 UStG",
        },
    )

    session.flush()
    return ledger
