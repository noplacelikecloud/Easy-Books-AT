"""Austrian Compliance Profile and Capability Management (PR 4, PR 16-18).

Provides versioned, effective-dated compliance profiles and enforces feature gates
for conditional Austrian modules (§ 189 ff. UGB, § 21 UStG).
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlmodel import Session, desc, select

from models import Settings, Tenant, Transaction
from models_at import AccountingProfileVersion


# Conditional / restricted modules for Austria that are initially blocked until certified
BLOCKED_AT_CAPABILITIES = {
    "at_rksv": "Registrierkassensicherheitsverordnung (RKSV / POS)",
    "at_erb": "e-Rechnung an den Bund (ebInterface / Peppol BIS)",
    "at_payroll": "Österreichische Personalverrechnung (Lohnkonto / ELDA)",
}


def get_active_profile(
    session: Session,
    tenant_id: int,
    on_date: Optional[str] = None,
) -> Optional[AccountingProfileVersion]:
    """Get the active effective-dated Austrian accounting profile for a tenant."""
    effective_date = on_date or date.today().isoformat()
    query = select(AccountingProfileVersion).where(
        AccountingProfileVersion.tenant_id == tenant_id,
        AccountingProfileVersion.jurisdiction == "AT",
        AccountingProfileVersion.superseded_at == None,  # noqa: E711
        AccountingProfileVersion.valid_from <= effective_date,
        (AccountingProfileVersion.valid_to == None)  # noqa: E711
        | (AccountingProfileVersion.valid_to >= effective_date),
    )
    query = query.order_by(
        desc(AccountingProfileVersion.valid_from),
        desc(AccountingProfileVersion.created_at),
        desc(AccountingProfileVersion.id),
    )
    return session.exec(query).first()


def is_at_compliance_active(
    session: Session,
    tenant_id: int,
    on_date: Optional[str] = None,
) -> bool:
    """Check whether Austrian compliance rules apply to this tenant on the given date."""
    return get_active_profile(session, tenant_id, on_date) is not None


def create_profile_version(
    session: Session,
    tenant_id: int,
    user_id: Optional[int],
    data: Dict[str, Any],
) -> AccountingProfileVersion:
    """Create a new effective-dated profile version without overwriting history."""
    valid_from = data.get("valid_from") or date.today().isoformat()
    try:
        valid_from_date = date.fromisoformat(valid_from)
    except ValueError as exc:
        raise HTTPException(422, "valid_from muss ein ISO-Datum (YYYY-MM-DD) sein.") from exc

    legal_form = data.get("legal_form", "gmbh")
    profit_method = data.get("profit_method", "ugb_double_entry")
    vat_status = data.get("vat_status", "standard")
    if vat_status == "regular":  # backwards-compatible API alias
        vat_status = "standard"
    vat_method = data.get("vat_method", "accrual")
    filing_frequency = data.get("vat_filing_frequency", "monthly")
    if legal_form not in {"sole_proprietor", "gmbh", "flexco", "og", "kg"}:
        raise HTTPException(422, "Nicht unterstützte österreichische Rechtsform.")
    if profit_method not in {"ugb_double_entry", "ear"}:
        raise HTTPException(422, "profit_method muss 'ugb_double_entry' oder 'ear' sein.")
    if legal_form in {"gmbh", "flexco"} and profit_method != "ugb_double_entry":
        raise HTTPException(422, "Kapitalgesellschaften müssen UGB-Doppik verwenden.")
    if vat_status not in {"standard", "small_business_exempt", "opted_in"}:
        raise HTTPException(422, "Ungültiger Umsatzsteuerstatus.")
    if vat_method not in {"accrual", "cash"}:
        raise HTTPException(422, "vat_method muss 'accrual' oder 'cash' sein.")
    if filing_frequency not in {"monthly", "quarterly", "annual_only"}:
        raise HTTPException(422, "Ungültiger UVA-Zeitraum.")
    if data.get("vat_id") and not str(data["vat_id"]).upper().startswith("ATU"):
        raise HTTPException(422, "Eine österreichische UID muss mit ATU beginnen.")
    if vat_status == "small_business_exempt" and float(data.get("prior_year_turnover") or 0) > 55_000:
        raise HTTPException(
            422,
            "Die Kleinunternehmerbefreiung ist bei einem Vorjahresumsatz über 55.000 EUR nicht anwendbar.",
        )
    if vat_status == "small_business_exempt":
        binding_option = session.exec(
            select(AccountingProfileVersion).where(
                AccountingProfileVersion.tenant_id == tenant_id,
                AccountingProfileVersion.jurisdiction == "AT",
                AccountingProfileVersion.vat_status == "opted_in",
                AccountingProfileVersion.valid_from >= f"{valid_from_date.year - 4}-01-01",
                AccountingProfileVersion.valid_from <= valid_from,
            ).order_by(desc(AccountingProfileVersion.valid_from))
        ).first()
        if binding_option:
            raise HTTPException(
                409,
                "Die Option zur Steuerpflicht bindet fünf Kalenderjahre; ein Wechsel zur Kleinunternehmerbefreiung ist noch gesperrt.",
            )

    overlaps = session.exec(
        select(AccountingProfileVersion).where(
            AccountingProfileVersion.tenant_id == tenant_id,
            AccountingProfileVersion.jurisdiction == "AT",
            AccountingProfileVersion.superseded_at == None,  # noqa: E711
            AccountingProfileVersion.valid_from <= (data.get("valid_to") or "9999-12-31"),
            (AccountingProfileVersion.valid_to == None)  # noqa: E711
            | (AccountingProfileVersion.valid_to >= valid_from),
        )
    ).all()
    
    # Close previous active versions. A same-day correction supersedes the
    # previous immutable payload explicitly, avoiding two active overlapping
    # profiles while retaining the replaced row as audit history.
    superseded_same_day: list[AccountingProfileVersion] = []
    superseded_at = datetime.utcnow()
    for prev in overlaps:
        if prev.valid_from > valid_from:
            raise HTTPException(409, "Das neue AT-Profil überlappt eine bereits erfasste spätere Version.")
        if prev.valid_from == valid_from:
            prev.superseded_at = superseded_at
            superseded_same_day.append(prev)
        else:
            prev.valid_to = (valid_from_date - timedelta(days=1)).isoformat()
        session.add(prev)

    cap_json = data.get("capabilities")
    if isinstance(cap_json, (dict, list)):
        cap_json = json.dumps(cap_json)

    profile = AccountingProfileVersion(
        tenant_id=tenant_id,
        jurisdiction="AT",
        valid_from=valid_from,
        valid_to=data.get("valid_to"),
        legal_form=legal_form,
        profit_method=profit_method,
        vat_status=vat_status,
        vat_method=vat_method,
        vat_filing_frequency=filing_frequency,
        fiscal_year_start=data.get("fiscal_year_start", "01-01"),
        tax_number=data.get("tax_number"),
        vat_id=data.get("vat_id"),
        company_register_number=data.get("company_register_number"),
        company_register_court=data.get("company_register_court"),
        registered_seat=data.get("registered_seat"),
        prior_year_turnover=data.get("prior_year_turnover"),
        capabilities=cap_json,
        created_at=datetime.utcnow(),
        created_by_id=user_id,
        change_reason=data.get("change_reason", "Profile onboarding / update"),
    )
    session.add(profile)
    session.flush()
    for previous in superseded_same_day:
        previous.superseded_by_id = profile.id
        session.add(previous)

    # AT ledgers must start in EUR. Never rewrite an already posted ledger.
    tenant = session.get(Tenant, tenant_id)
    if tenant and tenant.base_currency != "EUR":
        if session.exec(select(Transaction).where(Transaction.tenant_id == tenant_id)).first():
            raise HTTPException(
                409,
                "AT kann nicht nachträglich auf einem bereits in Fremdwährung gebuchten Mandanten aktiviert werden.",
            )
        tenant.base_currency = "EUR"
        session.add(tenant)

    from localizations.at.coa import install_at_kmu_coa
    install_at_kmu_coa(session, tenant_id)
    for key, value in {
        "country": "AT",
        "currency": "EUR",
        "app_language": "de",
        "timezone": "Europe/Vienna",
    }.items():
        setting = session.exec(select(Settings).where(
            Settings.tenant_id == tenant_id, Settings.key == key,
        )).first()
        if setting:
            setting.value = value
        else:
            setting = Settings(tenant_id=tenant_id, key=key, value=value)
        session.add(setting)

    session.flush()
    session.refresh(profile)
    return profile


def assert_capability(
    session: Session,
    tenant_id: int,
    capability: str,
    on_date: Optional[str] = None,
) -> None:
    """Enforce capability gate. Blocks uncertified/unapproved Austrian modules.

    PR 16 (AT-RKSV), PR 17 (AT-ERB), PR 18 (AT-PAYROLL).
    """
    prof = get_active_profile(session, tenant_id, on_date)
    if not prof:
        return  # Non-AT tenant; capability gate not active

    # Product capabilities are enabled only by the operator after technical and
    # legal acceptance. Tenant-provided profile JSON can never lift this gate.
    if capability in BLOCKED_AT_CAPABILITIES:
        approved = {
            item.strip()
            for item in os.getenv("AT_APPROVED_CAPABILITIES", "").split(",")
            if item.strip()
        }
        allowed = capability in approved
        if not allowed:
            label = BLOCKED_AT_CAPABILITIES[capability]
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Modul '{label}' ({capability}) ist für AT-Mandanten zurzeit gesperrt "
                    f"und bedarf einer gesonderten Zertifizierung/Freigabe."
                ),
            )


def assert_base_currency_mutable(session: Session, tenant_id: int, new_currency: str) -> None:
    """Guard against changing base currency after first posted transaction in AT mode."""
    if not is_at_compliance_active(session, tenant_id):
        return
    tenant = session.get(Tenant, tenant_id)
    if not tenant or tenant.base_currency == new_currency:
        return
    first_txn = session.exec(
        select(Transaction).where(Transaction.tenant_id == tenant_id)
    ).first()
    if first_txn:
        raise HTTPException(
            status_code=400,
            detail="Basiswährungsänderung ist nach erster Buchung für AT-Mandanten gesperrt (§ 190 UGB).",
        )
