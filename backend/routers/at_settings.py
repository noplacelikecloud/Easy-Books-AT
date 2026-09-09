"""Router for Austrian Compliance Settings, Profile Onboarding, and Account Roles (PR 4)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from models import Account
from models_at import AccountRoleBinding, AccountingProfileVersion
from localizations.at.profile import (
    assert_capability,
    create_profile_version,
    get_active_profile,
    is_at_compliance_active,
)
from localizations.at.coa import install_at_kmu_coa
from services.account_roles import bind_account_role, resolve_account_role
from .common import CurrentUserDep, SessionDep, WriteUserDep, log_audit
from services.permissions import perm_dep


router = APIRouter(prefix="/api/at", tags=["at_compliance"])


class ProfileCreateRequest(BaseModel):
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    legal_form: str = "gmbh"  # sole_proprietor | gmbh | flexco | og | kg | other
    profit_method: str = "ugb_double_entry"  # ugb_double_entry | ear
    vat_status: str = "standard"  # standard | small_business_exempt | opted_in
    vat_method: str = "accrual"  # accrual | cash
    vat_filing_frequency: str = "monthly"  # monthly | quarterly | annual_only
    fiscal_year_start: str = "01-01"
    tax_number: Optional[str] = None
    vat_id: Optional[str] = None
    company_register_number: Optional[str] = None
    company_register_court: Optional[str] = None
    registered_seat: Optional[str] = None
    prior_year_turnover: Optional[float] = None
    capabilities: Optional[dict] = None
    change_reason: Optional[str] = None


class RoleBindingRequest(BaseModel):
    role_key: str
    account_id: int
    valid_from: str = "1900-01-01"


class UidVerificationRequest(BaseModel):
    party_type: str
    party_id: int


@router.get("/profile")
def get_profile(session: SessionDep, user: CurrentUserDep, on_date: Optional[str] = None):
    """Retrieve the active Austrian compliance profile for the current tenant."""
    prof = get_active_profile(session, user.tenant_id, on_date)
    if not prof:
        return {"active": False, "profile": None}
    return {"active": True, "profile": prof.model_dump()}


@router.post("/profile")
def save_profile(session: SessionDep, user: WriteUserDep, body: ProfileCreateRequest):
    """Create or update effective-dated Austrian compliance profile."""
    prof = create_profile_version(session, user.tenant_id, user.id, body.model_dump())
    log_audit(session, user, "UPDATE", "at_profile", prof.id, {"legal_form": prof.legal_form})
    session.commit()
    return {"ok": True, "profile": prof}


@router.get("/roles")
def get_roles(session: SessionDep, user: CurrentUserDep):
    """List all semantic account role bindings."""
    bindings = session.exec(
        select(AccountRoleBinding).where(AccountRoleBinding.tenant_id == user.tenant_id)
    ).all()
    results = []
    for b in bindings:
        acc = session.get(Account, b.account_id)
        results.append({
            "id": b.id,
            "role_key": b.role_key,
            "account_id": b.account_id,
            "account_code": acc.code if acc else None,
            "account_name": acc.name if acc else None,
            "valid_from": b.valid_from,
            "valid_to": b.valid_to,
        })
    return {"roles": results}


@router.post("/roles")
def set_role(session: SessionDep, user: WriteUserDep, body: RoleBindingRequest):
    """Bind a semantic role to a specific account."""
    acc = session.exec(
        select(Account).where(Account.id == body.account_id, Account.tenant_id == user.tenant_id)
    ).first()
    if not acc:
        raise HTTPException(404, "Account not found")
    binding = bind_account_role(
        session=session,
        tenant_id=user.tenant_id,
        role_key=body.role_key,
        account_id=body.account_id,
        valid_from=body.valid_from,
    )
    session.commit()
    return {"ok": True, "binding": binding}


@router.post("/install-coa")
def install_coa(session: SessionDep, user: WriteUserDep):
    """Install standard Austrian KMU Chart of Accounts template and role mappings."""
    result = install_at_kmu_coa(session, user.tenant_id)
    session.commit()
    return result


@router.post("/check-capability")
def check_capability(session: SessionDep, user: CurrentUserDep, capability: str):
    """Check if a conditional capability is permitted for the tenant's AT profile."""
    assert_capability(session, user.tenant_id, capability)
    return {"ok": True, "capability": capability, "allowed": True}


@router.post("/uid/verify")
def verify_uid(session: SessionDep, user: WriteUserDep, body: UidVerificationRequest):
    """Validate a customer/vendor UID with the official EU VIES service."""
    from localizations.at.uid_verification import verify_party_uid
    result = verify_party_uid(session, user.tenant_id, body.party_type, body.party_id)
    session.commit()
    return result


class OptInRequest(BaseModel):
    valid_from: str = "2026-01-01"
    reason: Optional[str] = None


@router.get("/small-business")
def get_small_business(session: SessionDep, user: CurrentUserDep, year: Optional[int] = None):
    """Retrieve Austrian small business threshold status and buffer."""
    from localizations.at.small_business import get_small_business_status
    current_year = year or datetime.utcnow().year
    return get_small_business_status(session, user.tenant_id, current_year)


@router.post("/small-business/opt-in")
def opt_in_small_business(session: SessionDep, user: WriteUserDep, body: OptInRequest):
    """Voluntarily waive small business exemption and opt into standard VAT (§ 6 Abs. 3 UStG)."""
    from localizations.at.small_business import opt_into_standard_vat
    ledger = opt_into_standard_vat(
        session=session,
        tenant_id=user.tenant_id,
        valid_from=body.valid_from,
        user_id=user.id,
        reason=body.reason,
    )
    session.commit()
    return {"ok": True, "opted_in": True, "valid_from": body.valid_from}
