"""Router for Austrian Cash Accounting (Einnahmen-Ausgaben-Rechnung / E1a) (PR 12: AT-11)."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional
from fastapi import APIRouter

from localizations.at.ear import compute_ear_report
from services.money import D
from .common import CurrentUserDep, SessionDep


router = APIRouter(prefix="/api/at/ear", tags=["at_ear"])


@router.get("")
def get_ear(
    session: SessionDep,
    user: CurrentUserDep,
    year: int,
    private_share_adjustments: Optional[float] = 0.0,
):
    """Compute statutory Austrian E/A-Rechnung and Form E1a figures per § 4 Abs. 3 EStG."""
    priv_d = D(private_share_adjustments)
    return compute_ear_report(
        session=session,
        tenant_id=user.tenant_id,
        year=year,
        private_share_adjustments=priv_d,
    )
