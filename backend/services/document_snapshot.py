"""Document Snapshot Service for Austrian Compliance (AT-01, AT-02).

Produces canonical, deterministic JSON snapshots and SHA-256 cryptographic hashes
for finalized invoices, bills, and credit/debit notes (§ 190 Abs. 4 UGB, § 131 BAO).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from models_at import DocumentVersion


def _decimal_default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return f"{obj:.4f}"
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hex digest of canonical JSON payload."""
    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=_decimal_default,
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def build_canonical_invoice_snapshot(
    invoice: Any,
    lines: List[Any],
    customer: Optional[Any] = None,
    tax_details: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build canonical representation for an invoice."""
    return {
        "document_type": "invoice",
        "id": invoice.id,
        "tenant_id": invoice.tenant_id,
        "number": invoice.number,
        "issue_date": str(invoice.issue_date),
        "due_date": str(invoice.due_date),
        "service_date_start": getattr(invoice, "service_date_start", None),
        "service_date_end": getattr(invoice, "service_date_end", None),
        "currency": invoice.currency,
        "exchange_rate": str(invoice.exchange_rate),
        "subtotal": str(invoice.subtotal),
        "gst_rate": str(invoice.gst_rate),
        "gst_amount": str(invoice.gst_amount),
        "total": str(invoice.total),
        "customer": {
            "id": getattr(invoice, "customer_id", None),
            "name": invoice.customer_name or (customer.name if customer else None),
            "tax_number": getattr(customer, "tax_number", None) if customer else None,
            "uid": getattr(customer, "uid", None) if customer else None,
            "address_street": getattr(customer, "address_street", None) if customer else None,
            "address_zip": getattr(customer, "address_zip", None) if customer else None,
            "address_city": getattr(customer, "address_city", None) if customer else None,
            "address_country": getattr(customer, "address_country", "AT") if customer else "AT",
            "is_business": getattr(customer, "is_business", True) if customer else True,
        },
        "lines": [
            {
                "id": getattr(ln, "id", None),
                "description": ln.description,
                "qty": str(ln.qty),
                "rate": str(ln.rate),
                "amount": str(ln.amount),
                "discount_pct": str(getattr(ln, "discount_pct", Decimal("0"))),
                "tax_code_id": getattr(ln, "tax_code_id", None),
                "tax_rate": str(getattr(ln, "tax_rate", Decimal("0")) or Decimal("0")),
                "tax_amount": str(getattr(ln, "tax_amount", Decimal("0")) or Decimal("0")),
                "service_date": getattr(ln, "service_date", None),
                "tax_treatment_code": getattr(ln, "tax_treatment_code", None),
            }
            for ln in lines
        ],
        "tax_details": tax_details or [],
        "transaction_id": getattr(invoice, "transaction_id", None),
    }


def build_canonical_bill_snapshot(
    bill: Any,
    lines: List[Any],
    vendor: Optional[Any] = None,
    tax_details: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build canonical representation for a vendor bill."""
    return {
        "document_type": "bill",
        "id": bill.id,
        "tenant_id": bill.tenant_id,
        "number": bill.number,
        "bill_date": str(bill.bill_date),
        "due_date": str(bill.due_date),
        "service_date_start": getattr(bill, "service_date_start", None),
        "service_date_end": getattr(bill, "service_date_end", None),
        "currency": bill.currency,
        "exchange_rate": str(bill.exchange_rate),
        "subtotal": str(bill.subtotal),
        "gst_rate": str(bill.gst_rate),
        "gst_amount": str(bill.gst_amount),
        "total": str(bill.total),
        "vendor": {
            "id": getattr(bill, "vendor_id", None),
            "name": bill.vendor_name or (vendor.name if vendor else None),
            "tax_number": getattr(vendor, "tax_number", None) if vendor else None,
            "uid": getattr(vendor, "uid", None) if vendor else None,
            "address_street": getattr(vendor, "address_street", None) if vendor else None,
            "address_zip": getattr(vendor, "address_zip", None) if vendor else None,
            "address_city": getattr(vendor, "address_city", None) if vendor else None,
            "address_country": getattr(vendor, "address_country", "AT") if vendor else "AT",
            "is_business": getattr(vendor, "is_business", True) if vendor else True,
        },
        "lines": [
            {
                "id": getattr(ln, "id", None),
                "description": ln.description,
                "qty": str(ln.qty),
                "rate": str(ln.rate),
                "amount": str(ln.amount),
                "tax_code_id": getattr(ln, "tax_code_id", None),
                "tax_rate": str(getattr(ln, "tax_rate", Decimal("0")) or Decimal("0")),
                "tax_amount": str(getattr(ln, "tax_amount", Decimal("0")) or Decimal("0")),
                "service_date": getattr(ln, "service_date", None),
                "tax_treatment_code": getattr(ln, "tax_treatment_code", None),
            }
            for ln in lines
        ],
        "tax_details": tax_details or [],
        "transaction_id": getattr(bill, "transaction_id", None),
    }


def record_document_version(
    session: Session,
    tenant_id: int,
    document_type: str,
    document_id: int,
    state: str,
    payload: Dict[str, Any],
    user_id: Optional[int] = None,
    original_document_id: Optional[int] = None,
    series_name: Optional[str] = None,
    reason: Optional[str] = None,
    is_legacy: bool = False,
    pdf_path: Optional[str] = None,
    pdf_hash: Optional[str] = None,
) -> DocumentVersion:
    """Save immutable version snapshot with SHA-256 payload hash."""
    payload_hash = compute_payload_hash(payload)
    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=_decimal_default,
        ensure_ascii=False,
    )

    # Determine next version number for this document
    existing_versions = session.exec(
        select(DocumentVersion).where(
            DocumentVersion.tenant_id == tenant_id,
            DocumentVersion.document_type == document_type,
            DocumentVersion.document_id == document_id,
        )
    ).all()
    next_ver = len(existing_versions) + 1

    doc_version = DocumentVersion(
        tenant_id=tenant_id,
        document_type=document_type,
        document_id=document_id,
        version=next_ver,
        state=state,
        original_document_id=original_document_id,
        canonical_payload=canonical_json,
        payload_hash=payload_hash,
        pdf_path=pdf_path,
        pdf_hash=pdf_hash,
        series_name=series_name,
        recorded_at=datetime.utcnow(),
        recorded_by_id=user_id,
        effective_date=payload.get("issue_date") or payload.get("bill_date"),
        reason=reason,
        is_legacy=is_legacy,
    )
    session.add(doc_version)
    session.flush()
    return doc_version
