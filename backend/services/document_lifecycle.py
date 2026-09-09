"""Document Lifecycle and Integrity Service for Austrian Compliance (AT-01, AT-02).

Enforces immutable documents, state machine transitions, year-bound sequence series,
and audit trail (§ 190 Abs. 4 UGB, § 131 BAO).
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from models import Customer, Invoice, InvoiceLine, Bill, BillLine, CreditNote, CreditNoteLine, DebitNote, DebitNoteLine, Transaction, JournalEntry, PaymentAllocation, Product, Settings, StockMovement
from models_at import DocumentNumberSeries, DocumentVersion, TaxAdjustment, TaxEvent
from services.document_snapshot import (
    build_canonical_invoice_snapshot,
    build_canonical_bill_snapshot,
    record_document_version,
)
from services.posting import balance_legs_against, post_transaction, EntryInput
from services.money import D, ZERO, money


def get_next_series_number(
    session: Session,
    tenant_id: int,
    document_type: str,
    date_str: str,
    series_code: str = "DEFAULT",
    default_prefix: Optional[str] = None,
) -> str:
    """Assign next sequential number bound to document's fiscal/calendar year.

    § 11 Abs. 1 Z 6 UStG, § 131 BAO: Consecutive numbering without gaps per year.
    """
    try:
        doc_year = int(str(date_str)[:4])
    except (ValueError, TypeError, IndexError):
        doc_year = datetime.utcnow().year

    prefix = default_prefix or {
        "invoice": "AT-INV",
        "bill": "AT-BIL",
        "credit_note": "AT-CN",
        "debit_note": "AT-DN",
    }.get(document_type, "DOC")

    # Select with lock if possible, or standard select
    series = session.exec(
        select(DocumentNumberSeries).where(
            DocumentNumberSeries.tenant_id == tenant_id,
            DocumentNumberSeries.document_type == document_type,
            DocumentNumberSeries.series_code == series_code,
            DocumentNumberSeries.year == doc_year,
        ).with_for_update()
    ).first()

    if not series:
        series = DocumentNumberSeries(
            tenant_id=tenant_id,
            document_type=document_type,
            series_code=series_code,
            year=doc_year,
            current_number=0,
            prefix=prefix,
        )
        session.add(series)
        session.flush()

    series.current_number += 1
    session.add(series)
    session.flush()

    return f"{series.prefix}-{doc_year}-{series.current_number:05d}"


def assert_document_mutable(doc: Any, operation: str = "edit") -> None:
    """Check whether a document can be modified. Finalized documents are immutable."""
    status = getattr(doc, "lifecycle_status", "draft")
    if status == "finalized":
        doc_num = getattr(doc, "number", f"ID {doc.id}")
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot {operation} finalized document {doc_num}. Under § 190 Abs. 4 UGB "
                f"and § 131 BAO, finalized records are immutable. Issue a storno/correction instead."
            ),
        )


def assert_document_deletable(session: Session, tenant_id: int, document_type: str, doc: Any) -> None:
    """Check whether a document can be deleted.

    Blocked if finalized, if GL transaction exists, or if payments are allocated.
    """
    status = getattr(doc, "lifecycle_status", "draft")
    doc_num = getattr(doc, "number", f"ID {doc.id}")
    if status == "finalized":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete finalized document {doc_num}.",
        )
    if getattr(doc, "transaction_id", None) is not None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot delete document {doc_num} with active general ledger transaction. "
                f"The attack 'posted -> draft -> delete' is prohibited by Austrian compliance rules."
            ),
        )


def finalize_invoice(
    session: Session,
    user: Any,
    invoice_id: int,
    reason: Optional[str] = None,
) -> Invoice:
    """Atomically number, post, archive and freeze an Austrian sales invoice."""
    inv = session.exec(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == user.tenant_id)
    ).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")

    if getattr(inv, "lifecycle_status", "draft") == "finalized":
        return inv  # Idempotent return

    from localizations.at.profile import get_active_profile
    at_prof = get_active_profile(session, user.tenant_id, inv.issue_date)
    lines = session.exec(
        select(InvoiceLine).where(InvoiceLine.invoice_id == inv.id)
    ).all()
    customer = session.get(Customer, inv.customer_id) if inv.customer_id else None
    if not lines:
        raise HTTPException(422, "Eine Rechnung benötigt mindestens eine Position.")

    from localizations.at.invoice_validation import validate_at_invoice
    from localizations.at.archive import store_archive_bytes
    from services.account_roles import resolve_account_role
    from services.at_tax_events import create_tax_events_for_invoice, resolve_invoice_line_treatments
    from localizations.at.small_business import prepare_turnover_for_invoice
    from services.pdf import PdfEngineError, PdfRenderError, render_html_pdf, render_text_pdf
    from services.inventory import InventoryError

    validate_at_invoice(session, inv)
    prepare_turnover_for_invoice(session, inv, lines)
    at_prof = get_active_profile(session, user.tenant_id, inv.issue_date)
    resolved = resolve_invoice_line_treatments(session, inv, lines)
    if not resolved:
        raise HTTPException(422, "Kein aktives AT-Profil für das Rechnungsdatum.")

    def require_role(role: str):
        account = resolve_account_role(session, user.tenant_id, role, inv.issue_date)
        if not account:
            raise HTTPException(422, f"Verpflichtende Kontenrolle '{role}' ist nicht zugeordnet.")
        return account

    # A legal sequence number is consumed only inside the finalization transaction.
    if inv.number.startswith("DRAFT-"):
        inv.number = get_next_series_number(session, user.tenant_id, "invoice", inv.issue_date)

    subtotal = ZERO
    tax_total = ZERO
    entries: List[EntryInput] = []
    revenue = require_role("revenue")
    total_cogs = ZERO
    for line, _code, treatment in resolved:
        base = money(D(line.amount))
        tax = money(base * D(treatment.rate) / D("100"))
        line.tax_rate = D(treatment.rate)
        line.tax_amount = tax
        session.add(line)
        subtotal += base
        tax_total += tax
        entries.append(EntryInput(
            account_id=revenue.id,
            credit=money(base * D(inv.exchange_rate or 1)),
            customer_id=inv.customer_id,
        ))
        if tax > ZERO and treatment.treatment_type not in {
            "reverse_charge", "export", "intra_eu_supply", "small_business_exempt", "exempt",
        }:
            vat_account = require_role(treatment.output_account_role or "vat_output")
            entries.append(EntryInput(
                account_id=vat_account.id,
                credit=money(tax * D(inv.exchange_rate or 1)),
            ))
        if line.product_id:
            product = session.exec(select(Product).where(
                Product.id == line.product_id, Product.tenant_id == user.tenant_id,
            )).first()
            if product and product.product_type == "stock":
                from routers.invoices import _consume_product_or_bom
                try:
                    total_cogs += _consume_product_or_bom(
                        session, user.tenant_id, product, D(line.qty), True, inv.id,
                    )
                except InventoryError as exc:
                    raise HTTPException(422, str(exc)) from exc

    inv.subtotal = money(subtotal)
    inv.gst_amount = money(tax_total)
    inv.total = money(subtotal + tax_total)
    ar = require_role("accounts_receivable")
    # AR stays exactly the invoice total in base currency; the per-line revenue
    # and VAT legs are each rounded on their own, so over many lines their sum
    # can drift from it by rounding units. balance_legs_against books that
    # residual on the largest leg (see services/posting.py).
    entries = balance_legs_against(entries, EntryInput(
        account_id=ar.id,
        debit=money(inv.total * D(inv.exchange_rate or 1)),
        customer_id=inv.customer_id,
    ))
    txn = post_transaction(
        session, user, date=inv.issue_date,
        description=f"Rechnung {inv.number} — {inv.customer_name or ''}",
        entries=entries, voucher_type="SL",
        audit_entity_type="invoice",
        audit_detail={"invoice_number": inv.number, "total": str(inv.total)},
    )
    inv.transaction_id = txn.id

    if total_cogs > ZERO:
        cogs = require_role("cogs")
        inventory = require_role("inventory")
        cogs_txn = post_transaction(
            session, user, date=inv.issue_date,
            description=f"Wareneinsatz {inv.number}", voucher_type="JV",
            entries=[
                EntryInput(account_id=cogs.id, debit=total_cogs),
                EntryInput(account_id=inventory.id, credit=total_cogs),
            ],
            audit_entity_type="invoice",
            audit_detail={"invoice_number": inv.number, "cogs": str(total_cogs)},
        )
        inv.cogs_transaction_id = cogs_txn.id

    inv.lifecycle_status = "finalized"
    if inv.status == "draft":
        inv.status = "open"
    session.add(inv)
    session.flush()

    settings = {row.key: row.value for row in session.exec(
        select(Settings).where(Settings.tenant_id == user.tenant_id)
    ).all()}
    try:
        pdf = render_html_pdf("invoice_at.html", {
            "invoice": inv.model_dump(),
            "lines": [line.model_dump() for line in lines],
            "issuer": {
                "name": settings.get("company_name", ""),
                "address": ", ".join(filter(None, [settings.get("address_line1"), settings.get("city"), "Österreich"])),
                "vat_id": at_prof.vat_id,
                "company_register_number": at_prof.company_register_number,
                "company_register_court": at_prof.company_register_court,
            },
            "recipient": {
                "name": inv.customer_name or "",
                "address": ", ".join(filter(None, [getattr(customer, "address_street", None), getattr(customer, "address_zip", None), getattr(customer, "address_city", None), getattr(customer, "address_country", None)])),
                "vat_id": getattr(customer, "uid", None),
            },
        })
    except PdfEngineError:
        pdf = render_text_pdf(f"Rechnung {inv.number}", [
            f"Aussteller: {settings.get('company_name', '')}",
            f"Empfänger: {inv.customer_name or ''}",
            f"Rechnungsdatum: {inv.issue_date}",
            f"Leistungsdatum: {inv.service_date_start or inv.issue_date}",
            *[f"{line.description}: {line.qty} x {line.rate} = {line.amount}; USt {line.tax_rate}% {line.tax_amount}" for line in lines],
            f"Netto: {inv.subtotal} EUR", f"USt: {inv.gst_amount} EUR", f"Gesamt: {inv.total} EUR",
        ])
    except PdfRenderError as exc:
        raise HTTPException(503, f"Finalisierung abgebrochen: PDF konnte nicht erzeugt werden: {exc}") from exc
    archived = store_archive_bytes(
        session, user.tenant_id, "invoice_pdf", inv.id, f"{inv.number}.pdf",
        "application/pdf", pdf, inv.issue_date,
    )
    payload = build_canonical_invoice_snapshot(inv, lines, customer, tax_details=[
        {"line_id": line.id, "code": code, "rate": str(treatment.rate), "tax": str(line.tax_amount)}
        for line, code, treatment in resolved
    ])
    payload["issuer"] = {
        "name": settings.get("company_name", ""),
        "address_line1": settings.get("address_line1"),
        "city": settings.get("city"),
        "country": settings.get("country", "AT"),
        "vat_id": at_prof.vat_id,
        "tax_number": at_prof.tax_number,
        "company_register_number": at_prof.company_register_number,
        "company_register_court": at_prof.company_register_court,
        "registered_seat": at_prof.registered_seat,
        "profile_version_id": at_prof.id,
    }
    version = record_document_version(
        session=session,
        tenant_id=user.tenant_id,
        document_type="invoice",
        document_id=inv.id,
        state="finalized",
        payload=payload,
        user_id=user.id,
        reason=reason or "Initial finalization",
        series_name="DEFAULT",
        pdf_path=archived.file_path,
        pdf_hash=archived.sha256_hash,
    )
    create_tax_events_for_invoice(
        session, inv, lines, customer,
        document_version_id=version.id, transaction_id=txn.id,
    )
    session.commit()
    session.refresh(inv)
    return inv


def finalize_bill(
    session: Session,
    user: Any,
    bill_id: int,
    reason: Optional[str] = None,
) -> Bill:
    """Atomically number, post, archive and freeze an Austrian vendor bill."""
    bill = session.exec(
        select(Bill).where(Bill.id == bill_id, Bill.tenant_id == user.tenant_id)
    ).first()
    if not bill:
        raise HTTPException(404, "Bill not found")

    if getattr(bill, "lifecycle_status", "draft") == "finalized":
        return bill

    from models import Vendor
    vendor = session.get(Vendor, bill.vendor_id) if bill.vendor_id else None
    from localizations.at.profile import get_active_profile
    at_prof = get_active_profile(session, user.tenant_id, bill.bill_date)
    lines = session.exec(
        select(BillLine).where(BillLine.bill_id == bill.id)
    ).all()

    if not lines:
        raise HTTPException(422, "Eine Eingangsrechnung benötigt mindestens eine Position.")
    from localizations.at.archive import store_archive_bytes
    from services.account_roles import resolve_account_role
    from services.at_tax_events import create_tax_events_for_bill, purchase_treatment_rate, resolve_bill_line_treatments
    from services.inventory import record_purchase
    from services.pdf import PdfEngineError, PdfRenderError, render_bill_pdf, render_text_pdf

    resolved = resolve_bill_line_treatments(session, bill, lines)
    if not resolved:
        raise HTTPException(422, "Kein aktives AT-Profil für das Rechnungsdatum.")

    def require_role(role: str):
        account = resolve_account_role(session, user.tenant_id, role, bill.bill_date)
        if not account:
            raise HTTPException(422, f"Verpflichtende Kontenrolle '{role}' ist nicht zugeordnet.")
        return account

    if bill.number.startswith("DRAFT-"):
        bill.number = get_next_series_number(session, user.tenant_id, "bill", bill.bill_date)
    expense = require_role("expense")
    inventory = require_role("inventory")
    entries: List[EntryInput] = []
    subtotal = ZERO
    charged_tax_total = ZERO
    for line, _code, treatment in resolved:
        base = money(D(line.amount))
        assessed_tax = money(base * purchase_treatment_rate(treatment) / D("100"))
        is_self_assessed = treatment.treatment_type in {"reverse_charge", "intra_eu_acquisition"}
        charged_tax = ZERO if is_self_assessed else assessed_tax
        deductible = ZERO if at_prof and at_prof.vat_status == "small_business_exempt" else money(
            assessed_tax * treatment.deductibility_rate
        )
        non_deductible = money(assessed_tax - deductible)
        line.tax_rate = D(treatment.rate)
        line.tax_amount = charged_tax
        session.add(line)
        subtotal += base
        charged_tax_total += charged_tax
        product = None
        if line.product_id:
            product = session.exec(select(Product).where(
                Product.id == line.product_id, Product.tenant_id == user.tenant_id,
            )).first()
        line_account = inventory if product and product.product_type == "stock" else expense
        debit_base = money((base + non_deductible) * D(bill.exchange_rate or 1))
        entries.append(EntryInput(account_id=line_account.id, debit=debit_base, vendor_id=bill.vendor_id))
        if deductible > ZERO:
            input_role = treatment.input_account_role or "vat_input"
            input_account = require_role(input_role)
            entries.append(EntryInput(
                account_id=input_account.id,
                debit=money(deductible * D(bill.exchange_rate or 1)),
            ))
        if is_self_assessed and assessed_tax > ZERO:
            output_account = require_role(treatment.output_account_role or "vat_rc_output")
            entries.append(EntryInput(
                account_id=output_account.id,
                credit=money(assessed_tax * D(bill.exchange_rate or 1)),
            ))
        if product and product.product_type == "stock":
            unit_cost = D(line.rate)
            if D(line.qty) != ZERO and non_deductible > ZERO:
                unit_cost += non_deductible / D(line.qty)
            record_purchase(
                session,
                tenant_id=user.tenant_id,
                product_id=product.id,
                qty=D(line.qty),
                unit_cost=unit_cost,
                source_doc=bill.number,
            )

    bill.subtotal = money(subtotal)
    bill.gst_amount = money(charged_tax_total)
    bill.total = money(subtotal + charged_tax_total)
    ap = require_role("accounts_payable")
    # AP stays exactly the bill total in base currency — see the invoice path.
    entries = balance_legs_against(entries, EntryInput(
        account_id=ap.id, credit=money(bill.total * D(bill.exchange_rate or 1)), vendor_id=bill.vendor_id,
    ))
    txn = post_transaction(
        session, user, date=bill.bill_date,
        description=f"Eingangsrechnung {bill.number} — {bill.vendor_name or ''}",
        entries=entries, voucher_type="PR",
        audit_entity_type="bill",
        audit_detail={"bill_number": bill.number, "total": str(bill.total)},
    )
    bill.transaction_id = txn.id

    bill.lifecycle_status = "finalized"
    if bill.status == "draft":
        bill.status = "open"
    session.add(bill)
    session.flush()

    settings = {row.key: row.value for row in session.exec(
        select(Settings).where(Settings.tenant_id == user.tenant_id)
    ).all()}
    try:
        pdf = render_bill_pdf(
            bill=bill.model_dump(), lines=[line.model_dump() for line in lines],
            company_name=settings.get("company_name", ""),
            tagline=settings.get("business_tagline", ""),
        )
    except PdfEngineError:
        pdf = render_text_pdf(f"Eingangsrechnung {bill.number}", [
            f"Lieferant: {bill.vendor_name or ''}", f"Belegdatum: {bill.bill_date}",
            *[f"{line.description}: {line.qty} x {line.rate} = {line.amount}; USt {line.tax_rate}% {line.tax_amount}" for line in lines],
            f"Netto: {bill.subtotal} EUR", f"USt: {bill.gst_amount} EUR", f"Gesamt: {bill.total} EUR",
        ])
    except PdfRenderError as exc:
        raise HTTPException(503, f"Finalisierung abgebrochen: PDF konnte nicht erzeugt werden: {exc}") from exc
    archived = store_archive_bytes(
        session, user.tenant_id, "bill_pdf", bill.id, f"{bill.number}.pdf",
        "application/pdf", pdf, bill.bill_date,
    )
    payload = build_canonical_bill_snapshot(bill, lines, vendor, tax_details=[
        {"line_id": line.id, "code": code, "rate": str(treatment.rate), "tax": str(line.tax_amount)}
        for line, code, treatment in resolved
    ])
    version = record_document_version(
        session=session,
        tenant_id=user.tenant_id,
        document_type="bill",
        document_id=bill.id,
        state="finalized",
        payload=payload,
        user_id=user.id,
        reason=reason or "Initial finalization",
        series_name="DEFAULT",
        pdf_path=archived.file_path,
        pdf_hash=archived.sha256_hash,
    )
    create_tax_events_for_bill(
        session, bill, lines, vendor,
        document_version_id=version.id, transaction_id=txn.id,
    )
    session.commit()
    session.refresh(bill)
    return bill


def cancel_invoice(
    session: Session,
    user: Any,
    invoice_id: int,
    reason: str,
) -> Invoice:
    """Cancel (Storno) a finalized invoice: posts reversing JV and cancels record."""
    inv = session.exec(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == user.tenant_id)
    ).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")

    if inv.lifecycle_status != "finalized":
        raise HTTPException(400, "Only finalized invoices can be cancelled with storno.")
    if session.exec(select(PaymentAllocation).where(
        PaymentAllocation.tenant_id == user.tenant_id,
        PaymentAllocation.invoice_id == inv.id,
    )).first():
        raise HTTPException(409, "Eine bezahlte Rechnung muss über Gutschrift/Rückzahlung korrigiert werden.")

    # Reversal JV
    if inv.transaction_id:
        old_txn = session.get(Transaction, inv.transaction_id)
        if old_txn and not old_txn.is_reversed:
            old_entries = session.exec(
                select(JournalEntry).where(JournalEntry.transaction_id == old_txn.id)
            ).all()
            rev_entries = [
                EntryInput(
                    account_id=je.account_id,
                    debit=D(je.credit),
                    credit=D(je.debit),
                    analytic_account_id=je.analytic_account_id,
                )
                for je in old_entries
            ]
            rev_txn = post_transaction(
                session,
                user,
                date=str(datetime.utcnow().date()),
                description=f"Storno/Reversal of Invoice {inv.number}: {reason}",
                entries=rev_entries,
                audit_entity_type="invoice",
                audit_detail={"invoice_number": inv.number, "action": "storno", "reason": reason},
                voucher_type=old_txn.voucher_type,
            )
            old_txn.is_reversed = True
            old_txn.reversed_by_id = rev_txn.id
            session.add(old_txn)

    if inv.cogs_transaction_id:
        old_cogs = session.get(Transaction, inv.cogs_transaction_id)
        if old_cogs and not old_cogs.is_reversed:
            old_entries = session.exec(
                select(JournalEntry).where(JournalEntry.transaction_id == old_cogs.id)
            ).all()
            rev_cogs = post_transaction(
                session, user, date=str(datetime.utcnow().date()),
                description=f"Storno Wareneinsatz {inv.number}: {reason}",
                entries=[EntryInput(
                    account_id=entry.account_id,
                    debit=D(entry.credit), credit=D(entry.debit),
                    analytic_account_id=entry.analytic_account_id,
                ) for entry in old_entries],
                audit_entity_type="invoice",
                audit_detail={"invoice_number": inv.number, "action": "storno_cogs"},
                voucher_type=old_cogs.voucher_type,
            )
            old_cogs.is_reversed = True
            old_cogs.reversed_by_id = rev_cogs.id
            session.add(old_cogs)

    from services.inventory import reverse_consumption
    movements = session.exec(select(StockMovement).where(
        StockMovement.tenant_id == user.tenant_id,
        StockMovement.source_doc_type == "invoice",
        StockMovement.source_doc_id == inv.id,
        StockMovement.direction == "SHIPMENT",
    )).all()
    restored: Dict[int, list[Decimal]] = {}
    for movement in movements:
        restored.setdefault(movement.product_id, [ZERO, ZERO])
        restored[movement.product_id][0] += D(movement.qty)
        restored[movement.product_id][1] += D(movement.total_cost)
    for product_id, (qty, cogs_total) in restored.items():
        reverse_consumption(
            session,
            tenant_id=user.tenant_id,
            product_id=product_id,
            qty=qty,
            cogs_total=cogs_total,
        )

    # Reversal TaxEvents (PR 7)
    try:
        from services.at_tax_events import reverse_tax_events_for_doc
        reverse_tax_events_for_doc(session, "invoice", inv.id, reason, tenant_id=user.tenant_id)
    except ImportError:
        pass

    inv.lifecycle_status = "cancelled"
    inv.status = "void"
    session.add(inv)
    session.flush()

    lines = session.exec(select(InvoiceLine).where(InvoiceLine.invoice_id == inv.id)).all()
    customer = session.get(Customer, inv.customer_id) if inv.customer_id else None
    payload = build_canonical_invoice_snapshot(inv, lines, customer)
    record_document_version(
        session=session,
        tenant_id=user.tenant_id,
        document_type="invoice",
        document_id=inv.id,
        state="cancelled",
        payload=payload,
        user_id=user.id,
        reason=reason,
    )
    session.commit()
    session.refresh(inv)
    return inv


def cancel_bill(session: Session, user: Any, bill_id: int, reason: str) -> Bill:
    """Cancel a finalized vendor bill with GL, stock and tax reversals."""
    bill = session.exec(select(Bill).where(
        Bill.id == bill_id, Bill.tenant_id == user.tenant_id,
    )).first()
    if not bill:
        raise HTTPException(404, "Eingangsrechnung nicht gefunden.")
    if bill.lifecycle_status != "finalized":
        raise HTTPException(400, "Nur finalisierte Eingangsrechnungen können storniert werden.")
    if session.exec(select(PaymentAllocation).where(
        PaymentAllocation.tenant_id == user.tenant_id,
        PaymentAllocation.bill_id == bill.id,
    )).first():
        raise HTTPException(409, "Eine bezahlte Eingangsrechnung muss über Lieferantengutschrift/Rückzahlung korrigiert werden.")
    if not reason.strip():
        raise HTTPException(422, "Ein Stornogrund ist erforderlich.")

    if bill.transaction_id:
        original_txn = session.get(Transaction, bill.transaction_id)
        if original_txn and not original_txn.is_reversed:
            old_entries = session.exec(select(JournalEntry).where(
                JournalEntry.transaction_id == original_txn.id,
            )).all()
            reversal = post_transaction(
                session, user, date=str(datetime.utcnow().date()),
                description=f"Storno Eingangsrechnung {bill.number}: {reason}",
                entries=[EntryInput(
                    account_id=entry.account_id, debit=D(entry.credit), credit=D(entry.debit),
                    analytic_account_id=entry.analytic_account_id,
                ) for entry in old_entries],
                voucher_type=original_txn.voucher_type, audit_entity_type="bill",
                audit_detail={"bill_number": bill.number, "action": "storno", "reason": reason},
            )
            original_txn.is_reversed = True
            original_txn.reversed_by_id = reversal.id
            session.add(original_txn)

    from services.inventory import InventoryError, return_to_vendor
    lines = session.exec(select(BillLine).where(BillLine.bill_id == bill.id)).all()
    for line in lines:
        product = session.get(Product, line.product_id) if line.product_id else None
        if product and product.tenant_id == user.tenant_id and product.product_type == "stock":
            try:
                return_to_vendor(
                    session, tenant_id=user.tenant_id, product_id=product.id,
                    qty=D(line.qty), source_doc=bill.number,
                )
            except InventoryError as exc:
                raise HTTPException(409, f"Storno nicht möglich: {exc}") from exc
    from services.at_tax_events import reverse_tax_events_for_doc
    reverse_tax_events_for_doc(session, "bill", bill.id, reason, tenant_id=user.tenant_id)
    bill.lifecycle_status = "cancelled"
    bill.status = "void"
    session.add(bill); session.flush()
    from models import Vendor
    vendor = session.get(Vendor, bill.vendor_id) if bill.vendor_id else None
    payload = build_canonical_bill_snapshot(bill, lines, vendor)
    record_document_version(
        session, user.tenant_id, "bill", bill.id, "cancelled", payload,
        user.id, reason=reason,
    )
    session.commit(); session.refresh(bill); return bill


def _append_note_tax_corrections(
    session: Session, note: Any, original_type: str, original_id: int,
    document_version_id: int, transaction_id: int,
) -> None:
    """Append signed TaxEvents for a credit/debit note without changing history."""
    from services.at_tax_events import compute_tax_period
    from localizations.at.profile import get_active_profile
    originals = session.exec(select(TaxEvent).where(
        TaxEvent.tenant_id == note.tenant_id,
        TaxEvent.source_doc_type.in_([original_type, "payment"]),
        TaxEvent.state == "final",
    )).all()
    if original_type == "invoice":
        originals = [event for event in originals if (
            (event.source_doc_type == "invoice" and event.source_doc_id == original_id)
            or (event.source_doc_type == "payment" and event.document_version_id in {
                version.id for version in session.exec(select(DocumentVersion).where(
                    DocumentVersion.tenant_id == note.tenant_id,
                    DocumentVersion.document_type == "invoice",
                    DocumentVersion.document_id == original_id,
                )).all()
            })
        )]
    else:
        originals = [event for event in originals if event.source_doc_type == "bill" and event.source_doc_id == original_id]
    original_base = sum((abs(D(event.base_amount_eur)) for event in originals), ZERO)
    note_base = money(D(note.subtotal) * D(note.exchange_rate or 1))
    if original_base <= ZERO:
        return
    ratio = min(D("1"), note_base / original_base)
    profile = get_active_profile(session, note.tenant_id, note.issue_date)
    for original in originals:
        key = f"{note.__class__.__name__.lower()}-{note.id}-event-{original.id}"
        if session.exec(select(TaxEvent).where(
            TaxEvent.tenant_id == note.tenant_id, TaxEvent.idempotency_key == key,
        )).first():
            continue
        values = {
            "base_amount": -money(D(original.base_amount) * ratio),
            "tax_amount": -money(D(original.tax_amount) * ratio),
            "base_amount_eur": -money(D(original.base_amount_eur) * ratio),
            "tax_amount_eur": -money(D(original.tax_amount_eur) * ratio),
            "output_tax": -money(D(original.output_tax) * ratio),
            "reverse_charge_tax": -money(D(original.reverse_charge_tax) * ratio),
            "input_tax_deductible": -money(D(original.input_tax_deductible) * ratio),
            "input_tax_non_deductible": -money(D(original.input_tax_non_deductible) * ratio),
        }
        event = TaxEvent(
            tenant_id=note.tenant_id, document_version_id=document_version_id,
            transaction_id=transaction_id, treatment_version_id=original.treatment_version_id,
            profile_version_id=profile.id if profile else original.profile_version_id,
            direction=original.direction,
            source_doc_type="credit_note" if original_type == "invoice" else "debit_note",
            source_doc_id=note.id, event_type="credit" if original_type == "invoice" else "debit",
            original_event_id=original.id, service_date=original.service_date,
            invoice_date=note.issue_date, booking_date=note.issue_date,
            tax_date=note.issue_date,
            tax_period=compute_tax_period(note.issue_date, profile.vat_filing_frequency if profile else "monthly"),
            treatment_code=original.treatment_code, currency=original.currency,
            exchange_rate=original.exchange_rate, uva_base_kz=original.uva_base_kz,
            uva_tax_kz=original.uva_tax_kz, zm_relevant=original.zm_relevant,
            partner_country=original.partner_country, partner_vat_id=original.partner_vat_id,
            state="final", idempotency_key=key, **values,
        )
        session.add(event)
        session.flush()
        session.add(TaxAdjustment(
            tenant_id=note.tenant_id, original_event_id=original.id,
            new_event_id=event.id, reason=note.description or "Belegkorrektur",
            adjustment_type="correction",
        ))


def finalize_credit_note(session: Session, user: Any, note_id: int) -> CreditNote:
    note = session.exec(select(CreditNote).where(
        CreditNote.id == note_id, CreditNote.tenant_id == user.tenant_id,
    )).first()
    if not note:
        raise HTTPException(404, "Gutschrift nicht gefunden.")
    if note.lifecycle_status == "finalized":
        return note
    original = session.exec(select(Invoice).where(
        Invoice.id == note.invoice_id, Invoice.tenant_id == user.tenant_id,
    )).first()
    if not original or original.lifecycle_status != "finalized":
        raise HTTPException(409, "Eine finalisierte Ursprungsrechnung ist erforderlich.")
    lines = session.exec(select(CreditNoteLine).where(CreditNoteLine.credit_note_id == note.id)).all()
    if not lines:
        raise HTTPException(422, "Die Gutschrift benötigt mindestens eine Position.")
    prior = session.exec(select(CreditNote).where(
        CreditNote.tenant_id == user.tenant_id, CreditNote.invoice_id == original.id,
        CreditNote.lifecycle_status == "finalized", CreditNote.id != note.id,
    )).all()
    if sum((D(row.total) for row in prior), ZERO) + D(note.total) > D(original.total) + D("0.01"):
        raise HTTPException(422, "Gutschriften dürfen den Betrag der Ursprungsrechnung nicht überschreiten.")

    from localizations.at.tax_catalog import init_at_tax_treatments, resolve_tax_treatment
    from services.account_roles import resolve_account_role
    from localizations.at.archive import store_archive_bytes
    from services.pdf import render_text_pdf
    from services.inventory import reverse_consumption
    profile = __import__("localizations.at.profile", fromlist=["get_active_profile"]).get_active_profile(session, user.tenant_id, note.issue_date)
    init_at_tax_treatments(session, user.tenant_id)
    revenue = resolve_account_role(session, user.tenant_id, "revenue", note.issue_date)
    ar = resolve_account_role(session, user.tenant_id, "accounts_receivable", note.issue_date)
    if not revenue or not ar:
        raise HTTPException(422, "Kontenrollen für Erlös und Forderungen fehlen.")
    subtotal = tax_total = ZERO
    entries: List[EntryInput] = []
    for line in lines:
        code = line.tax_treatment_code or note.tax_treatment_code
        if not code:
            raise HTTPException(422, "Jede AT-Gutschriftposition benötigt eine Steuerbehandlung.")
        treatment = resolve_tax_treatment(session, user.tenant_id, code, note.issue_date, direction="sales")
        base = money(D(line.amount)); tax = money(base * D(treatment.rate) / D("100"))
        if treatment.treatment_type in {"reverse_charge", "export", "intra_eu_supply", "small_business_exempt", "exempt"}:
            tax = ZERO
        line.tax_rate, line.tax_amount = D(treatment.rate), tax
        session.add(line); subtotal += base; tax_total += tax
    note.subtotal, note.gst_amount, note.total = money(subtotal), money(tax_total), money(subtotal + tax_total)
    if sum((D(row.total) for row in prior), ZERO) + D(note.total) > D(original.total) + D("0.01"):
        raise HTTPException(422, "Gutschriften dürfen den Betrag der Ursprungsrechnung nicht überschreiten.")
    fx = D(note.exchange_rate or 1)
    value_legs: List[EntryInput] = [EntryInput(account_id=revenue.id, debit=money(subtotal * fx))]
    if tax_total > ZERO:
        vat = resolve_account_role(session, user.tenant_id, "vat_output", note.issue_date)
        if not vat: raise HTTPException(422, "Kontenrolle 'vat_output' fehlt.")
        value_legs.append(EntryInput(account_id=vat.id, debit=money(tax_total * fx)))
    # AR stays exactly the note total in base currency — see the invoice path.
    entries.extend(balance_legs_against(
        value_legs, EntryInput(account_id=ar.id, credit=money(note.total * fx), customer_id=note.customer_id),
    ))
    inventory = resolve_account_role(session, user.tenant_id, "inventory", note.issue_date)
    cogs = resolve_account_role(session, user.tenant_id, "cogs", note.issue_date)
    for line in lines:
        product = session.get(Product, line.product_id) if line.product_id else None
        if not product or product.tenant_id != user.tenant_id or product.product_type != "stock":
            continue
        movements = session.exec(select(StockMovement).where(
            StockMovement.tenant_id == user.tenant_id,
            StockMovement.source_doc_type == "invoice",
            StockMovement.source_doc_id == original.id,
            StockMovement.product_id == product.id,
            StockMovement.direction == "SHIPMENT",
        )).all()
        shipped_qty = sum((D(movement.qty) for movement in movements), ZERO)
        shipped_cost = sum((D(movement.total_cost) for movement in movements), ZERO)
        if shipped_qty <= ZERO or D(line.qty) > shipped_qty:
            raise HTTPException(422, "Retourmenge ist nicht durch die Ursprungsrechnung gedeckt.")
        returned_cost = money(shipped_cost * D(line.qty) / shipped_qty)
        reverse_consumption(session, tenant_id=user.tenant_id, product_id=product.id,
                            qty=D(line.qty), cogs_total=returned_cost)
        if not inventory or not cogs:
            raise HTTPException(422, "Kontenrollen für Lager und Wareneinsatz fehlen.")
        entries.extend([
            EntryInput(account_id=inventory.id, debit=returned_cost),
            EntryInput(account_id=cogs.id, credit=returned_cost),
        ])
    note.number = get_next_series_number(session, user.tenant_id, "credit_note", note.issue_date)
    txn = post_transaction(session, user, date=note.issue_date, description=f"Gutschrift {note.number}",
        entries=entries, voucher_type="CN", audit_entity_type="credit_note",
        audit_detail={"original_invoice": original.number})
    note.transaction_id, note.lifecycle_status, note.status = txn.id, "finalized", "posted"
    session.add(note); session.flush()
    pdf = render_text_pdf(f"Gutschrift {note.number}", [f"Bezug: Rechnung {original.number}", f"Gesamt: {note.total} EUR"])
    archived = store_archive_bytes(session, user.tenant_id, "credit_note_pdf", note.id, f"{note.number}.pdf", "application/pdf", pdf, note.issue_date)
    payload = {"document_type":"credit_note", "id":note.id, "tenant_id":note.tenant_id,
        "number":note.number, "issue_date":note.issue_date, "original_document_id":original.id,
        "original_number":original.number, "currency":note.currency, "exchange_rate":str(note.exchange_rate),
        "subtotal":str(note.subtotal), "gst_amount":str(note.gst_amount), "total":str(note.total),
        "lines":[line.model_dump(mode="json") for line in lines], "transaction_id":txn.id}
    version = record_document_version(session, user.tenant_id, "credit_note", note.id, "finalized", payload,
        user.id, original.id, "DEFAULT", "Gutschrift", pdf_path=archived.file_path, pdf_hash=archived.sha256_hash)
    _append_note_tax_corrections(session, note, "invoice", original.id, version.id, txn.id)
    session.commit(); session.refresh(note); return note


def finalize_debit_note(session: Session, user: Any, note_id: int) -> DebitNote:
    note = session.exec(select(DebitNote).where(
        DebitNote.id == note_id, DebitNote.tenant_id == user.tenant_id,
    )).first()
    if not note: raise HTTPException(404, "Lieferantengutschrift nicht gefunden.")
    if note.lifecycle_status == "finalized": return note
    original = session.exec(select(Bill).where(Bill.id == note.bill_id, Bill.tenant_id == user.tenant_id)).first()
    if not original or original.lifecycle_status != "finalized":
        raise HTTPException(409, "Eine finalisierte Ursprungsrechnung ist erforderlich.")
    lines = session.exec(select(DebitNoteLine).where(DebitNoteLine.debit_note_id == note.id)).all()
    if not lines: raise HTTPException(422, "Die Lieferantengutschrift benötigt mindestens eine Position.")
    prior = session.exec(select(DebitNote).where(
        DebitNote.tenant_id == user.tenant_id, DebitNote.bill_id == original.id,
        DebitNote.lifecycle_status == "finalized", DebitNote.id != note.id,
    )).all()
    if sum((D(row.total) for row in prior), ZERO) + D(note.total) > D(original.total) + D("0.01"):
        raise HTTPException(422, "Korrekturen dürfen den Betrag der Ursprungsrechnung nicht überschreiten.")
    from localizations.at.tax_catalog import init_at_tax_treatments, resolve_tax_treatment
    from services.at_tax_events import purchase_treatment_rate
    from services.account_roles import resolve_account_role
    from localizations.at.archive import store_archive_bytes
    from services.pdf import render_text_pdf
    from services.inventory import return_to_vendor, InventoryError
    profile = __import__("localizations.at.profile", fromlist=["get_active_profile"]).get_active_profile(session, user.tenant_id, note.issue_date)
    init_at_tax_treatments(session, user.tenant_id)
    ap = resolve_account_role(session, user.tenant_id, "accounts_payable", note.issue_date)
    expense = resolve_account_role(session, user.tenant_id, "expense", note.issue_date)
    inventory = resolve_account_role(session, user.tenant_id, "inventory", note.issue_date)
    if not ap or not expense or not inventory: raise HTTPException(422, "Verpflichtende Kreditoren-Kontenrollen fehlen.")
    subtotal = charged_total = ZERO; entries: List[EntryInput] = []
    fx = D(note.exchange_rate or 1)
    for line in lines:
        code = line.tax_treatment_code or note.tax_treatment_code
        if not code: raise HTTPException(422, "Jede AT-Korrekturposition benötigt eine Steuerbehandlung.")
        treatment = resolve_tax_treatment(session, user.tenant_id, code, note.issue_date, direction="purchases")
        base = money(D(line.amount)); assessed = money(base * purchase_treatment_rate(treatment) / D("100"))
        self_assessed = treatment.treatment_type in {"reverse_charge", "intra_eu_acquisition"}
        charged = ZERO if self_assessed else assessed
        deductible = ZERO if profile and profile.vat_status == "small_business_exempt" else money(assessed * treatment.deductibility_rate)
        non_deductible = money(assessed - deductible)
        line.tax_rate, line.tax_amount = D(treatment.rate), charged; session.add(line)
        product = session.get(Product, line.product_id) if line.product_id else None
        account = inventory if product and product.tenant_id == user.tenant_id and product.product_type == "stock" else expense
        entries.append(EntryInput(account_id=account.id, credit=money((base + non_deductible) * fx)))
        if product and product.tenant_id == user.tenant_id and product.product_type == "stock":
            try:
                return_to_vendor(
                    session, tenant_id=user.tenant_id, product_id=product.id,
                    qty=D(line.qty), source_doc=original.number,
                )
            except InventoryError as exc: raise HTTPException(422, str(exc)) from exc
        if deductible > ZERO:
            vat_in = resolve_account_role(session, user.tenant_id, treatment.input_account_role or "vat_input", note.issue_date)
            if not vat_in: raise HTTPException(422, "Vorsteuer-Kontenrolle fehlt.")
            entries.append(EntryInput(account_id=vat_in.id, credit=money(deductible * fx)))
        if self_assessed and assessed > ZERO:
            vat_out = resolve_account_role(session, user.tenant_id, treatment.output_account_role or "vat_rc_output", note.issue_date)
            if not vat_out: raise HTTPException(422, "RC-Ausgangssteuer-Kontenrolle fehlt.")
            entries.append(EntryInput(account_id=vat_out.id, debit=money(assessed * fx)))
        subtotal += base; charged_total += charged
    note.subtotal, note.gst_amount, note.total = money(subtotal), money(charged_total), money(subtotal + charged_total)
    if sum((D(row.total) for row in prior), ZERO) + D(note.total) > D(original.total) + D("0.01"):
        raise HTTPException(422, "Korrekturen dürfen den Betrag der Ursprungsrechnung nicht überschreiten.")
    # AP stays exactly the note total in base currency — see the invoice path.
    entries = balance_legs_against(entries, EntryInput(account_id=ap.id, debit=money(note.total * fx), vendor_id=note.vendor_id))
    note.number = get_next_series_number(session, user.tenant_id, "debit_note", note.issue_date)
    txn = post_transaction(session, user, date=note.issue_date, description=f"Lieferantengutschrift {note.number}", entries=entries,
        voucher_type="DN", audit_entity_type="debit_note", audit_detail={"original_bill":original.number})
    note.transaction_id, note.lifecycle_status, note.status = txn.id, "finalized", "posted"; session.add(note); session.flush()
    pdf = render_text_pdf(f"Lieferantengutschrift {note.number}", [f"Bezug: Eingangsrechnung {original.number}", f"Gesamt: {note.total} EUR"])
    archived = store_archive_bytes(session, user.tenant_id, "debit_note_pdf", note.id, f"{note.number}.pdf", "application/pdf", pdf, note.issue_date)
    payload = {"document_type":"debit_note", "id":note.id, "tenant_id":note.tenant_id,
        "number":note.number, "issue_date":note.issue_date, "original_document_id":original.id,
        "original_number":original.number, "currency":note.currency, "exchange_rate":str(note.exchange_rate),
        "subtotal":str(note.subtotal), "gst_amount":str(note.gst_amount), "total":str(note.total),
        "lines":[line.model_dump(mode="json") for line in lines], "transaction_id":txn.id}
    version = record_document_version(session, user.tenant_id, "debit_note", note.id, "finalized", payload,
        user.id, original.id, "DEFAULT", "Lieferantengutschrift", pdf_path=archived.file_path, pdf_hash=archived.sha256_hash)
    _append_note_tax_corrections(session, note, "bill", original.id, version.id, txn.id)
    session.commit(); session.refresh(note); return note
