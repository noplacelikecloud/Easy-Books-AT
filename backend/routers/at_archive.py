"""Router for Austrian Document Archive, Retention, Legal Hold, and Tax Audit Export (PR 15: AT-07, AT-10)."""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from localizations.at.archive import (
    assert_archive_deletable,
    institute_legal_hold,
    release_legal_hold,
)
from localizations.at.income_tax_workpapers import compute_austrian_corporate_tax_workpaper
from localizations.at.audit_export import generate_tax_audit_export
from services.money import D
from .common import CurrentUserDep, SessionDep, WriteUserDep, log_audit


router = APIRouter(prefix="/api/at", tags=["at_archive"])


class LegalHoldCreateRequest(BaseModel):
    title: str
    reason: str
    object_ids: Optional[List[int]] = None


@router.post("/archive/legal-hold")
def create_legal_hold(
    session: SessionDep,
    user: WriteUserDep,
    body: LegalHoldCreateRequest,
):
    """Institute a legal hold locking documents against deletion (§ 132 BAO)."""
    hold = institute_legal_hold(
        session=session,
        tenant_id=user.tenant_id,
        user_id=user.id,
        title=body.title,
        reason=body.reason,
        object_ids=body.object_ids,
    )
    session.commit()
    return {"ok": True, "legal_hold_id": hold.id, "title": hold.title}


@router.post("/archive/legal-hold/{hold_id}/release")
def remove_legal_hold(
    session: SessionDep,
    user: WriteUserDep,
    hold_id: int,
):
    """Release an active legal hold."""
    release_legal_hold(session, user.tenant_id, hold_id)
    session.commit()
    return {"ok": True, "released": True}


@router.delete("/archive/{archive_id}")
def delete_archived_object(
    session: SessionDep,
    user: WriteUserDep,
    archive_id: int,
):
    """Attempt to delete an archived object, enforced against § 132 BAO 7-year retention & legal hold."""
    assert_archive_deletable(session, user.tenant_id, archive_id)
    # If allowed (past 7 years and no legal hold), delete
    from models_at import ArchiveObject
    obj = session.get(ArchiveObject, archive_id)
    session.delete(obj)
    session.commit()
    return {"ok": True, "deleted": True}


@router.get("/tax/corporate-workpaper")
def get_corporate_tax_workpaper(
    session: SessionDep,
    user: CurrentUserDep,
    year: int,
    non_deductible_expenses: Optional[float] = 0.0,
    luxury_car_addback: Optional[float] = 0.0,
    tax_exempt_dividends: Optional[float] = 0.0,
    loss_carryforward: Optional[float] = 0.0,
    is_new_incorporation: Optional[bool] = True,
):
    """Compute statutory Austrian Corporate Income Tax workpaper (23% KSt & MWR)."""
    return compute_austrian_corporate_tax_workpaper(
        session=session,
        tenant_id=user.tenant_id,
        year=year,
        non_deductible_expenses=D(non_deductible_expenses),
        luxury_car_addback=D(luxury_car_addback),
        tax_exempt_dividends=D(tax_exempt_dividends),
        loss_carryforward=D(loss_carryforward),
        is_new_incorporation=is_new_incorporation,
    )


@router.get("/audit/export")
def get_audit_export(
    session: SessionDep,
    user: CurrentUserDep,
    year: int,
):
    """Generate comprehensive Austrian tax audit export package with SHA-256 manifest."""
    return generate_tax_audit_export(session, user.tenant_id, year)
