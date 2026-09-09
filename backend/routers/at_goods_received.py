"""Router for Austrian Wareneingangsbuch gem. § 127 BAO (PR 14)."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Response
from pydantic import BaseModel

from localizations.at.goods_received import (
    export_goods_received_csv,
    get_goods_received_book,
    record_goods_receipt,
)
from services.money import D
from .common import CurrentUserDep, SessionDep, WriteUserDep


router = APIRouter(prefix="/api/at/goods-received", tags=["at_goods_received"])


class GoodsReceiptCreateRequest(BaseModel):
    received_date: str
    vendor_name: str
    description: str
    net_amount: float
    vat_amount: float
    vendor_address: Optional[str] = None
    bill_id: Optional[int] = None
    document_number: Optional[str] = None


@router.post("")
def create_receipt(
    session: SessionDep,
    user: WriteUserDep,
    body: GoodsReceiptCreateRequest,
):
    """Record a goods received entry with automatic sequential numbering (§ 127 BAO)."""
    rec = record_goods_receipt(
        session=session,
        tenant_id=user.tenant_id,
        received_date=body.received_date,
        vendor_name=body.vendor_name,
        description=body.description,
        net_amount=D(body.net_amount),
        vat_amount=D(body.vat_amount),
        vendor_address=body.vendor_address,
        bill_id=body.bill_id,
        document_number=body.document_number,
    )
    session.commit()
    session.refresh(rec)
    return {"ok": True, "record": rec.model_dump()}


@router.get("")
def get_book(
    session: SessionDep,
    user: CurrentUserDep,
    year: int,
    month: Optional[int] = None,
):
    """Retrieve Wareneingangsbuch for year / month with subtotals."""
    return get_goods_received_book(session, user.tenant_id, year, month)


@router.get("/export")
def export_csv(
    session: SessionDep,
    user: CurrentUserDep,
    year: int,
):
    """Download official CSV export of Wareneingangsbuch for tax audit."""
    csv_content = export_goods_received_csv(session, user.tenant_id, year)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="Wareneingangsbuch_{year}.csv"'},
    )
