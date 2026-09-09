"""Austrian Goods Received Book (Wareneingangsbuch gem. § 127 BAO) (PR 14).

Mandatory recording of all trade merchandise and raw materials for E/A-Rechner:
- Consecutive entry numbers per calendar year (fortlaufende Nummerierung)
- Date of receipt (Eingangstag / Rechnungsdatum)
- Supplier name and address (Name und Anschrift des Lieferanten)
- Exact goods description (Genaue Bezeichnung der Ware)
- Net, VAT, and gross amounts (Preise und Abgaben)
- Reference to original document / receipt (Belegbezug)
- Monthly and annual totals
- Tax-compliant CSV export
"""
from __future__ import annotations

import csv
import io
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlmodel import Session, func, select

from models_at import DocumentNumberSeries, GoodsReceivedRecord
from services.money import D, ZERO, money


def record_goods_receipt(
    session: Session,
    tenant_id: int,
    received_date: str,
    vendor_name: str,
    description: str,
    net_amount: Decimal,
    vat_amount: Decimal,
    vendor_address: Optional[str] = None,
    bill_id: Optional[int] = None,
    document_number: Optional[str] = None,
) -> GoodsReceivedRecord:
    """Record a new goods receipt entry with sequential numbering per year (§ 127 BAO)."""
    year = int(received_date.split("-")[0])
    series = session.exec(select(DocumentNumberSeries).where(
        DocumentNumberSeries.tenant_id == tenant_id,
        DocumentNumberSeries.document_type == "goods_received",
        DocumentNumberSeries.series_code == "DEFAULT",
        DocumentNumberSeries.year == year,
    ).with_for_update()).first()
    if not series:
        series = DocumentNumberSeries(
            tenant_id=tenant_id, document_type="goods_received", series_code="DEFAULT",
            year=year, current_number=0, prefix="WEB",
        )
        session.add(series)
        session.flush()
    series.current_number += 1
    next_number = series.current_number
    session.add(series)
    gross_amount = money(net_amount + vat_amount)

    rec = GoodsReceivedRecord(
        tenant_id=tenant_id,
        calendar_year=year,
        entry_number=next_number,
        received_date=received_date,
        vendor_name=vendor_name,
        vendor_address=vendor_address,
        description=description,
        net_amount=money(net_amount),
        vat_amount=money(vat_amount),
        gross_amount=gross_amount,
        bill_id=bill_id,
        document_number=document_number,
    )
    session.add(rec)
    session.flush()
    session.refresh(rec)
    return rec


def get_goods_received_book(
    session: Session,
    tenant_id: int,
    year: int,
    month: Optional[int] = None,
) -> Dict[str, Any]:
    """Retrieve goods received book records and compute period totals (§ 127 BAO)."""
    if month is not None:
        prefix = f"{year:04d}-{month:02d}-"
    else:
        prefix = f"{year:04d}-"

    records = session.exec(
        select(GoodsReceivedRecord)
        .where(
            GoodsReceivedRecord.tenant_id == tenant_id,
            GoodsReceivedRecord.received_date.startswith(prefix),
        )
        .order_by(GoodsReceivedRecord.entry_number)
    ).all()

    total_net = sum((r.net_amount for r in records), ZERO)
    total_vat = sum((r.vat_amount for r in records), ZERO)
    total_gross = sum((r.gross_amount for r in records), ZERO)

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "entry_number": r.entry_number,
            "received_date": r.received_date,
            "vendor_name": r.vendor_name,
            "vendor_address": r.vendor_address,
            "description": r.description,
            "net_amount": float(r.net_amount),
            "vat_amount": float(r.vat_amount),
            "gross_amount": float(r.gross_amount),
            "bill_id": r.bill_id,
            "document_number": r.document_number,
        })

    return {
        "year": year,
        "month": month,
        "record_count": len(records),
        "total_net": float(money(total_net)),
        "total_vat": float(money(total_vat)),
        "total_gross": float(money(total_gross)),
        "records": items,
    }


def export_goods_received_csv(
    session: Session,
    tenant_id: int,
    year: int,
) -> str:
    """Generate official semicolon-delimited CSV export for tax audit (§ 127 BAO)."""
    data = get_goods_received_book(session, tenant_id, year)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "Laufende Nr",
        "Eingangsdatum",
        "Lieferant",
        "Anschrift",
        "Bezeichnung der Ware",
        "Nettobetrag EUR",
        "USt-Betrag EUR",
        "Bruttobetrag EUR",
        "Belegnummer",
    ])

    for r in data["records"]:
        writer.writerow([
            r["entry_number"],
            r["received_date"],
            r["vendor_name"],
            r["vendor_address"] or "",
            r["description"],
            f"{r['net_amount']:.2f}",
            f"{r['vat_amount']:.2f}",
            f"{r['gross_amount']:.2f}",
            r["document_number"] or "",
        ])

    return output.getvalue()
