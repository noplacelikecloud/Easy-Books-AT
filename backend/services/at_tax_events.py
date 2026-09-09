"""Immutable Austrian VAT events derived from finalized documents and payments."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from localizations.at.profile import get_active_profile
from localizations.at.tax_catalog import init_at_tax_treatments, resolve_tax_treatment
from models import Bill, BillLine, Customer, Invoice, InvoiceLine, Product, Vendor
from models_at import DocumentVersion, TaxAdjustment, TaxEvent
from services.money import D, ZERO, money


def compute_tax_period(tax_date: str, frequency: str = "monthly") -> str:
    date_str = str(tax_date)[:10]
    year = date_str[:4]
    month = int(date_str[5:7])
    if frequency == "quarterly":
        return f"{year}-Q{(month - 1) // 3 + 1}"
    return f"{year}-{month:02d}"


def _line_treatment(
    session: Session,
    tenant_id: int,
    line: Any,
    header_code: Optional[str],
    on_date: str,
    direction: str,
    profile: Any,
):
    code = getattr(line, "tax_treatment_code", None) or header_code
    if not code:
        rate = D(getattr(line, "tax_rate", ZERO) or ZERO)
        if rate == D("10"):
            code = "AT_REDUCED_10"
        elif rate == D("13"):
            code = "AT_REDUCED_13"
        elif rate == D("4.9"):
            code = "AT_REDUCED_4_9"
        elif rate == ZERO:
            code = "AT_EXEMPT_KU" if profile.vat_status == "small_business_exempt" else "AT_ZERO_EXPORT"
        else:
            code = "AT_STANDARD_20"

    if profile.vat_status == "small_business_exempt" and direction == "sales" and code not in {
        "AT_EXEMPT_KU", "AT_ZERO_EXPORT", "AT_ZERO_IG_SUPPLY", "AT_RC_EU_SERVICE_OUT",
    }:
        raise HTTPException(422, "Kleinunternehmer dürfen keine reguläre Umsatzsteuer ausweisen.")

    classification = None
    if getattr(line, "product_id", None):
        product = session.exec(
            select(Product).where(Product.id == line.product_id, Product.tenant_id == tenant_id)
        ).first()
        if not product:
            raise HTTPException(404, "Produkt der Belegzeile nicht gefunden.")
        classification = product.pct_code

    treatment = resolve_tax_treatment(
        session=session,
        tenant_id=tenant_id,
        code=code,
        on_date=on_date,
        product_classification=classification,
        direction=direction,
    )
    if (
        direction == "sales"
        and treatment.treatment_type == "small_business_exempt"
        and profile.vat_status != "small_business_exempt"
    ):
        raise HTTPException(
            422,
            "Die Kleinunternehmerbefreiung ist für das Leistungsdatum nicht anwendbar; die Position muss mit der zutreffenden Regelbesteuerung neu klassifiziert werden.",
        )
    return code, treatment


def resolve_invoice_line_treatments(
    session: Session, invoice: Invoice, lines: List[InvoiceLine]
) -> list[tuple[InvoiceLine, str, Any]]:
    """Resolve and validate all sales treatments before any posting mutation."""
    profile = get_active_profile(session, invoice.tenant_id, invoice.issue_date)
    if not profile:
        return []
    init_at_tax_treatments(session, invoice.tenant_id)
    return [
        (
            line,
            *_line_treatment(
                session, invoice.tenant_id, line, invoice.tax_treatment_code,
                invoice.issue_date, "sales", profile,
            ),
        )
        for line in lines
    ]


def resolve_bill_line_treatments(
    session: Session, bill: Bill, lines: List[BillLine]
) -> list[tuple[BillLine, str, Any]]:
    """Resolve and validate all purchase treatments before any posting mutation."""
    profile = get_active_profile(session, bill.tenant_id, bill.bill_date)
    if not profile:
        return []
    init_at_tax_treatments(session, bill.tenant_id)
    return [
        (
            line,
            *_line_treatment(
                session, bill.tenant_id, line, bill.tax_treatment_code,
                bill.bill_date, "purchases", profile,
            ),
        )
        for line in lines
    ]


def purchase_treatment_rate(treatment: Any) -> Decimal:
    """Domestic reverse charge uses the normal rate when catalog base rate is zero."""
    if treatment.treatment_type == "reverse_charge" and D(treatment.rate) == ZERO:
        return D("20")
    return D(treatment.rate)


def _latest_version(
    session: Session, tenant_id: int, document_type: str, document_id: int
) -> Optional[DocumentVersion]:
    return session.exec(
        select(DocumentVersion).where(
            DocumentVersion.tenant_id == tenant_id,
            DocumentVersion.document_type == document_type,
            DocumentVersion.document_id == document_id,
        ).order_by(DocumentVersion.version.desc())
    ).first()


def create_tax_events_for_invoice(
    session: Session,
    invoice: Invoice,
    lines: List[InvoiceLine],
    customer: Optional[Customer] = None,
    *,
    document_version_id: Optional[int] = None,
    transaction_id: Optional[int] = None,
    source_doc_type: str = "invoice",
    source_doc_id: Optional[int] = None,
    event_type: str = "invoice",
    tax_date_override: Optional[str] = None,
    allocation_ratio: Decimal = Decimal("1"),
    idempotency_prefix: Optional[str] = None,
) -> List[TaxEvent]:
    """Create sales VAT events. Cash-method invoices are recognised at payment."""
    prof = get_active_profile(session, invoice.tenant_id, tax_date_override or invoice.issue_date)
    if not prof:
        return []
    resolved = resolve_invoice_line_treatments(session, invoice, lines)
    if prof.vat_method == "cash" and event_type != "payment":
        return []

    tax_date = tax_date_override or invoice.issue_date
    tax_period = compute_tax_period(tax_date, prof.vat_filing_frequency)
    fx = D(invoice.exchange_rate or 1)
    events: List[TaxEvent] = []
    for idx, (line, code, treatment) in enumerate(resolved):
        base = money(D(line.amount) * allocation_ratio)
        tax = money(base * D(treatment.rate) / D("100"))
        base_eur = money(base * fx)
        tax_eur = money(tax * fx)
        output = (
            tax_eur
            if treatment.treatment_type not in {
                "reverse_charge", "export", "intra_eu_supply", "small_business_exempt", "exempt",
            }
            else ZERO
        )
        key = f"{idempotency_prefix or f'inv-{invoice.id}'}-ln-{line.id or idx}"
        existing = session.exec(
            select(TaxEvent).where(TaxEvent.tenant_id == invoice.tenant_id, TaxEvent.idempotency_key == key)
        ).first()
        if existing:
            events.append(existing)
            continue
        event = TaxEvent(
            tenant_id=invoice.tenant_id,
            document_version_id=document_version_id,
            transaction_id=transaction_id,
            treatment_version_id=treatment.id,
            profile_version_id=prof.id,
            direction="sales",
            source_doc_type=source_doc_type,
            source_doc_id=source_doc_id or invoice.id,
            event_type=event_type,
            service_date=invoice.service_date_start or invoice.issue_date,
            invoice_date=invoice.issue_date,
            payment_date=tax_date if event_type == "payment" else None,
            booking_date=tax_date,
            tax_date=tax_date,
            tax_period=tax_period,
            treatment_code=code,
            currency=invoice.currency or "EUR",
            exchange_rate=fx,
            base_amount=base,
            tax_amount=tax,
            base_amount_eur=base_eur,
            tax_amount_eur=tax_eur,
            output_tax=output,
            reverse_charge_tax=ZERO,
            uva_base_kz=treatment.uva_base_kz,
            uva_tax_kz=treatment.uva_tax_kz,
            zm_relevant=treatment.zm_relevant,
            partner_country=(customer.address_country if customer else "AT") or "AT",
            partner_vat_id=customer.uid if customer else None,
            state="final",
            idempotency_key=key,
        )
        session.add(event)
        events.append(event)
    session.flush()
    return events


def create_tax_events_for_bill(
    session: Session,
    bill: Bill,
    lines: List[BillLine],
    vendor: Optional[Vendor] = None,
    *,
    document_version_id: Optional[int] = None,
    transaction_id: Optional[int] = None,
) -> List[TaxEvent]:
    prof = get_active_profile(session, bill.tenant_id, bill.bill_date)
    if not prof:
        return []
    resolved = resolve_bill_line_treatments(session, bill, lines)
    period = compute_tax_period(bill.bill_date, prof.vat_filing_frequency)
    fx = D(bill.exchange_rate or 1)
    events: List[TaxEvent] = []
    for idx, (line, code, treatment) in enumerate(resolved):
        base = D(line.amount)
        tax = money(base * purchase_treatment_rate(treatment) / D("100"))
        base_eur = money(base * fx)
        tax_eur = money(tax * fx)
        rc = tax_eur if treatment.treatment_type == "reverse_charge" else ZERO
        output = tax_eur if treatment.treatment_type == "intra_eu_acquisition" else ZERO
        deductible = ZERO if prof.vat_status == "small_business_exempt" else money(tax_eur * treatment.deductibility_rate)
        non_deductible = money(tax_eur - deductible)
        key = f"bil-{bill.id}-ln-{line.id or idx}"
        existing = session.exec(
            select(TaxEvent).where(TaxEvent.tenant_id == bill.tenant_id, TaxEvent.idempotency_key == key)
        ).first()
        if existing:
            events.append(existing)
            continue
        event = TaxEvent(
            tenant_id=bill.tenant_id,
            document_version_id=document_version_id,
            transaction_id=transaction_id,
            treatment_version_id=treatment.id,
            profile_version_id=prof.id,
            direction="purchases",
            source_doc_type="bill",
            source_doc_id=bill.id,
            event_type="bill",
            service_date=bill.service_date_start or bill.bill_date,
            invoice_date=bill.bill_date,
            booking_date=bill.bill_date,
            tax_date=bill.bill_date,
            tax_period=period,
            treatment_code=code,
            currency=bill.currency or "EUR",
            exchange_rate=fx,
            base_amount=base,
            tax_amount=tax,
            base_amount_eur=base_eur,
            tax_amount_eur=tax_eur,
            output_tax=output,
            reverse_charge_tax=rc,
            input_tax_deductible=deductible,
            input_tax_non_deductible=non_deductible,
            uva_base_kz=treatment.uva_base_kz,
            uva_tax_kz=treatment.uva_tax_kz,
            zm_relevant=treatment.zm_relevant,
            partner_country=(vendor.address_country if vendor else "AT") or "AT",
            partner_vat_id=vendor.uid if vendor else None,
            state="final",
            idempotency_key=key,
        )
        session.add(event)
        events.append(event)
    session.flush()
    return events


def create_tax_events_for_invoice_payment(
    session: Session,
    invoice: Invoice,
    payment_id: int,
    allocation_id: int,
    allocation_amount: Decimal,
    payment_date: str,
    transaction_id: Optional[int],
) -> List[TaxEvent]:
    prof = get_active_profile(session, invoice.tenant_id, payment_date)
    if not prof or prof.vat_method != "cash":
        return []
    if invoice.lifecycle_status != "finalized":
        raise HTTPException(409, "Zahlungen dürfen steuerlich nur finalisierten Rechnungen zugeordnet werden.")
    if D(invoice.total) <= ZERO:
        raise HTTPException(422, "Ungültige Rechnungssumme für die Zahlungsaufteilung.")
    lines = session.exec(select(InvoiceLine).where(InvoiceLine.invoice_id == invoice.id)).all()
    customer = session.get(Customer, invoice.customer_id) if invoice.customer_id else None
    version = _latest_version(session, invoice.tenant_id, "invoice", invoice.id)
    return create_tax_events_for_invoice(
        session, invoice, lines, customer,
        document_version_id=version.id if version else None,
        transaction_id=transaction_id,
        source_doc_type="payment",
        source_doc_id=payment_id,
        event_type="payment",
        tax_date_override=payment_date,
        allocation_ratio=D(allocation_amount) / D(invoice.total),
        idempotency_prefix=f"payment-allocation-{allocation_id}",
    )


def reverse_tax_events_for_doc(
    session: Session,
    doc_type: str,
    doc_id: int,
    reason: str,
    tenant_id: Optional[int] = None,
) -> List[TaxEvent]:
    """Append correction events without modifying historical originals."""
    query = select(TaxEvent).where(
        TaxEvent.source_doc_type == doc_type,
        TaxEvent.source_doc_id == doc_id,
        TaxEvent.state == "final",
        TaxEvent.original_event_id == None,  # noqa: E711
    )
    if tenant_id is not None:
        query = query.where(TaxEvent.tenant_id == tenant_id)
    originals = session.exec(query).all()
    now = datetime.utcnow().date().isoformat()
    reversals: List[TaxEvent] = []
    for original in originals:
        key = f"rev-{original.id}"
        if session.exec(select(TaxEvent).where(TaxEvent.tenant_id == original.tenant_id, TaxEvent.idempotency_key == key)).first():
            continue
        profile = get_active_profile(session, original.tenant_id, now)
        reversal = TaxEvent(
            tenant_id=original.tenant_id,
            document_version_id=original.document_version_id,
            transaction_id=None,
            treatment_version_id=original.treatment_version_id,
            profile_version_id=profile.id if profile else original.profile_version_id,
            direction=original.direction,
            source_doc_type=doc_type,
            source_doc_id=doc_id,
            event_type="adjustment",
            original_event_id=original.id,
            service_date=original.service_date,
            invoice_date=original.invoice_date,
            booking_date=now,
            tax_date=now,
            tax_period=compute_tax_period(now, profile.vat_filing_frequency if profile else "monthly"),
            treatment_code=original.treatment_code,
            currency=original.currency,
            exchange_rate=original.exchange_rate,
            base_amount=-original.base_amount,
            tax_amount=-original.tax_amount,
            base_amount_eur=-original.base_amount_eur,
            tax_amount_eur=-original.tax_amount_eur,
            output_tax=-original.output_tax,
            reverse_charge_tax=-original.reverse_charge_tax,
            input_tax_deductible=-original.input_tax_deductible,
            input_tax_non_deductible=-original.input_tax_non_deductible,
            uva_base_kz=original.uva_base_kz,
            uva_tax_kz=original.uva_tax_kz,
            zm_relevant=original.zm_relevant,
            partner_country=original.partner_country,
            partner_vat_id=original.partner_vat_id,
            state="final",
            idempotency_key=key,
        )
        session.add(reversal)
        session.flush()
        session.add(TaxAdjustment(
            tenant_id=original.tenant_id,
            original_event_id=original.id,
            new_event_id=reversal.id,
            reason=reason,
            adjustment_type="correction",
        ))
        reversals.append(reversal)
    session.flush()
    return reversals
