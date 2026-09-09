"""Router for Austrian Fixed Asset Valuation and Statutory Depreciation (PR 13: AT-12)."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from localizations.at.depreciation import (
    get_asset_schedule,
    post_annual_depreciation_run,
    register_asset_valuation,
)
from services.money import D
from .common import CurrentUserDep, SessionDep, WriteUserDep


router = APIRouter(prefix="/api/at/assets", tags=["at_assets"])


class AssetValuationCreateRequest(BaseModel):
    asset_id: int
    commissioning_date: str
    initial_cost_gross: float
    input_vat_deducted: Optional[float] = 0.0
    useful_life_years: Optional[float] = 5.0
    depreciation_method: Optional[str] = "linear"  # linear | degressiv | gwg
    asset_category: Optional[str] = "other"  # pkw | gebaeude | gwg | software | maschinen | other
    is_gwg: Optional[bool] = None


@router.post("/register")
def register_asset(
    session: SessionDep,
    user: WriteUserDep,
    body: AssetValuationCreateRequest,
):
    """Register Austrian statutory asset valuation with tax rules (§ 7, 8, 13 EStG)."""
    val = register_asset_valuation(
        session=session,
        tenant_id=user.tenant_id,
        asset_id=body.asset_id,
        commissioning_date=body.commissioning_date,
        initial_cost_gross=D(body.initial_cost_gross),
        input_vat_deducted=D(body.input_vat_deducted),
        useful_life_years=D(body.useful_life_years),
        depreciation_method=body.depreciation_method,
        asset_category=body.asset_category,
        is_gwg=body.is_gwg,
    )
    session.commit()
    session.refresh(val)
    return {"ok": True, "valuation": val.model_dump()}


@router.get("/schedule")
def get_schedule(
    session: SessionDep,
    user: CurrentUserDep,
):
    """Retrieve statutory Austrian asset register (Anlagenverzeichnis)."""
    return get_asset_schedule(session, user.tenant_id)


@router.post("/depreciate-year")
def depreciate_year(
    session: SessionDep,
    user: WriteUserDep,
    year: int,
):
    """Execute annual depreciation run and post voucher to GL (§ 7 EStG)."""
    txn = post_annual_depreciation_run(session, user, year)
    session.commit()
    return {"ok": True, "transaction_id": txn.id, "year": year}
