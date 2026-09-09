"""Austrian Tax Audit & Accountant Export (BMF / Kanzleiexport) (PR 15: AT-07, AT-10, BAO).

Exports complete audit trail, General Ledger journals, Chart of Accounts, TaxEvents,
filings, and an integrity manifest with SHA-256 checksums.
"""
from __future__ import annotations

import hashlib
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from sqlmodel import Session, select

from models import Account, AuditLog, JournalEntry, Tenant, Transaction
from models_at import ArchiveObject, DocumentVersion, TaxEvent, TaxFiling, TaxFilingVersion
from localizations.at.profile import get_active_profile


def generate_tax_audit_export(
    session: Session,
    tenant_id: int,
    year: int,
) -> Dict[str, Any]:
    """Compile comprehensive Austrian tax audit export package with integrity hashes."""
    year_str = str(year)
    start_date = f"{year_str}-01-01"
    end_date = f"{year_str}-12-31"

    tenant = session.get(Tenant, tenant_id)
    profile = get_active_profile(session, tenant_id)

    # 1. Chart of Accounts
    accounts = session.exec(
        select(Account).where(Account.tenant_id == tenant_id).order_by(Account.code)
    ).all()
    accounts_data = [
        {"id": a.id, "code": a.code, "name": a.name, "type": a.type, "is_group": a.is_group, "is_memo": a.is_memo}
        for a in accounts
    ]
    accounts_json = json.dumps(accounts_data, sort_keys=True)
    accounts_hash = hashlib.sha256(accounts_json.encode("utf-8")).hexdigest()

    # 2. General Ledger Bookings
    transactions = session.exec(
        select(Transaction)
        .where(
            Transaction.tenant_id == tenant_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
        )
        .order_by(Transaction.date, Transaction.id)
    ).all()

    bookings_data = []
    account_by_id = {account.id: account for account in accounts}
    for txn in transactions:
        lines = session.exec(
            select(JournalEntry).where(JournalEntry.transaction_id == txn.id)
        ).all()
        for ln in lines:
            counterparts = sorted({
                account_by_id[other.account_id].code
                for other in lines
                if other.id != ln.id and other.account_id in account_by_id
            })
            bookings_data.append({
                "transaction_id": txn.id,
                "journal_number": txn.jv_number,
                "voucher_type": txn.voucher_type,
                "date": txn.date,
                "description": txn.description,
                "account_id": ln.account_id,
                "account_code": account_by_id[ln.account_id].code if ln.account_id in account_by_id else None,
                "counterpart_account_codes": counterparts,
                "debit": float(ln.debit),
                "credit": float(ln.credit),
                "customer_id": ln.customer_id,
                "vendor_id": ln.vendor_id,
            })
    bookings_json = json.dumps(bookings_data, sort_keys=True)
    bookings_hash = hashlib.sha256(bookings_json.encode("utf-8")).hexdigest()

    # 3. Tax Events
    events = session.exec(
        select(TaxEvent)
        .where(
            TaxEvent.tenant_id == tenant_id,
            TaxEvent.tax_date.startswith(f"{year_str}-"),
        )
        .order_by(TaxEvent.tax_date, TaxEvent.id)
    ).all()
    events_data = [
        {
            "id": e.id,
            "transaction_id": e.transaction_id,
            "document_version_id": e.document_version_id,
            "source_doc_type": e.source_doc_type,
            "source_doc_id": e.source_doc_id,
            "direction": e.direction,
            "tax_date": e.tax_date,
            "tax_period": e.tax_period,
            "treatment_code": e.treatment_code,
            "base_amount_eur": float(e.base_amount_eur),
            "tax_amount_eur": float(e.tax_amount_eur),
            "output_tax": float(e.output_tax),
            "reverse_charge_tax": float(e.reverse_charge_tax),
            "input_tax_deductible": float(e.input_tax_deductible),
            "uva_base_kz": e.uva_base_kz,
            "uva_tax_kz": e.uva_tax_kz,
            "partner_country": e.partner_country,
            "partner_vat_id": e.partner_vat_id,
            "state": e.state,
        }
        for e in events
    ]
    events_json = json.dumps(events_data, sort_keys=True)
    events_hash = hashlib.sha256(events_json.encode("utf-8")).hexdigest()

    # 4. Tax Filings
    filings = session.exec(
        select(TaxFiling).where(
            TaxFiling.tenant_id == tenant_id,
            TaxFiling.year == year,
        )
    ).all()
    filings_data = [
        {
            "id": f.id,
            "filing_type": f.filing_type,
            "period_key": f.period_key,
            "version": f.version,
            "status": f.status,
            "total_payable": float(f.total_payable),
            "xml_hash": f.xml_hash,
        }
        for f in filings
    ]
    filings_json = json.dumps(filings_data, sort_keys=True)
    filings_hash = hashlib.sha256(filings_json.encode("utf-8")).hexdigest()

    document_versions = session.exec(select(DocumentVersion).where(
        DocumentVersion.tenant_id == tenant_id,
        DocumentVersion.effective_date >= start_date,
        DocumentVersion.effective_date <= end_date,
    ).order_by(DocumentVersion.document_type, DocumentVersion.document_id, DocumentVersion.version)).all()
    document_versions_data = [version.model_dump() for version in document_versions]

    filing_versions = session.exec(
        select(TaxFilingVersion).join(TaxFiling).where(
            TaxFilingVersion.tenant_id == tenant_id,
            TaxFiling.year == year,
        )
    ).all()
    filing_versions_data = [version.model_dump() for version in filing_versions]

    archives = session.exec(select(ArchiveObject).where(
        ArchiveObject.tenant_id == tenant_id,
        ArchiveObject.recorded_at >= datetime(year, 1, 1),
        ArchiveObject.recorded_at < datetime(year + 1, 1, 1),
    )).all()
    archives_data = []
    for archive in archives:
        item = archive.model_dump()
        path = Path(archive.file_path)
        if path.is_file():
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != archive.sha256_hash:
                raise ValueError(f"Archivintegrität verletzt: {archive.file_name}")
            item["content_base64"] = base64.b64encode(raw).decode("ascii")
        else:
            item["content_base64"] = None
            item["restore_warning"] = "Physische Datei am Archivpfad fehlt"
        archives_data.append(item)

    audit_rows = session.exec(select(AuditLog).where(
        AuditLog.tenant_id == tenant_id,
        AuditLog.timestamp >= datetime(year, 1, 1),
        AuditLog.timestamp < datetime(year + 1, 1, 1),
    ).order_by(AuditLog.timestamp, AuditLog.id)).all()
    audit_data = [row.model_dump() for row in audit_rows]

    supplemental = {
        "document_versions": document_versions_data,
        "filing_versions": filing_versions_data,
        "archive_objects": archives_data,
        "audit_log": audit_data,
    }
    supplemental_json = json.dumps(supplemental, sort_keys=True, default=str)
    supplemental_hash = hashlib.sha256(supplemental_json.encode("utf-8")).hexdigest()

    # Overall Manifest
    manifest = {
        "export_format": "Easy-Books-Austrian-Audit-v1",
        "jurisdiction": "AT",
        "fiscal_year": year,
        "exported_at": datetime.utcnow().isoformat(),
        "tenant_id": tenant_id,
        "company_name": tenant.name if tenant else None,
        "tax_number": profile.tax_number if profile else None,
        "vat_id": profile.vat_id if profile else None,
        "hashes": {
            "chart_of_accounts": accounts_hash,
            "bookings": bookings_hash,
            "tax_events": events_hash,
            "tax_filings": filings_hash,
            "documents_archive_audit": supplemental_hash,
        },
    }

    manifest_hash = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()
    manifest["package_signature"] = manifest_hash

    return {
        "manifest": manifest,
        "chart_of_accounts": accounts_data,
        "bookings": bookings_data,
        "tax_events": events_data,
        "tax_filings": filings_data,
        **supplemental,
    }
