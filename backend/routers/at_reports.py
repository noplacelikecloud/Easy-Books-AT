"""Router for Austrian Statutory Reports (UGB Bilanz/GuV §§ 224, 231 UGB) (PR 11: AT-11)."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter

from localizations.at.ugb_reports import (
    compute_ugb_balance_sheet,
    compute_ugb_income_statement,
    get_at_closing_checklist,
)
from .common import CurrentUserDep, SessionDep


router = APIRouter(prefix="/api/at/reports", tags=["at_reports"])


@router.get("/balance-sheet")
def get_balance_sheet(
    session: SessionDep,
    user: CurrentUserDep,
    as_of_date: str,
    prior_date: Optional[str] = None,
):
    """Generate statutory Austrian balance sheet per § 224 UGB."""
    return compute_ugb_balance_sheet(
        session=session,
        tenant_id=user.tenant_id,
        as_of_date=as_of_date,
        prior_date=prior_date,
    )


@router.get("/income-statement")
def get_income_statement(
    session: SessionDep,
    user: CurrentUserDep,
    start_date: str,
    end_date: str,
    prior_start_date: Optional[str] = None,
    prior_end_date: Optional[str] = None,
):
    """Generate statutory Austrian income statement (GuV) per § 231 UGB (Gesamtkostenverfahren)."""
    return compute_ugb_income_statement(
        session=session,
        tenant_id=user.tenant_id,
        start_date=start_date,
        end_date=end_date,
        prior_start_date=prior_start_date,
        prior_end_date=prior_end_date,
    )


@router.get("/closing-checklist")
def get_closing_checklist(
    session: SessionDep,
    user: CurrentUserDep,
    year: int,
):
    """Retrieve Austrian year-end closing and compliance checklist."""
    return get_at_closing_checklist(
        session=session,
        tenant_id=user.tenant_id,
        fiscal_year=year,
    )
