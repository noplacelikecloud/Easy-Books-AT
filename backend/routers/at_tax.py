"""Router for Austrian Tax Filings (UVA / U30, ZM, U1) and Tax Reconciliation (PR 10: AT-10)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from sqlmodel import select, desc

from models_at import TaxFiling, TaxFilingVersion
from localizations.at.uva import compute_uva, finalize_uva_filing
from localizations.at.zm import compute_zm, finalize_zm_filing
from localizations.at.u1 import compute_u1, finalize_u1_filing
from localizations.at.reconciliation import reconcile_vat_period
from .common import CurrentUserDep, SessionDep, WriteUserDep, log_audit


router = APIRouter(prefix="/api/at/tax", tags=["at_tax"])


@router.get("/uva")
def get_uva(session: SessionDep, user: CurrentUserDep, period: str):
    """Compute official Austrian UVA U30 Kennzahlen for a period (month/quarter)."""
    return compute_uva(session, user.tenant_id, period)


@router.post("/uva/finalize")
def finalize_uva(session: SessionDep, user: WriteUserDep, period: str):
    """Finalize UVA filing, generate XML, compute SHA-256 hash and persist immutable snapshot."""
    filing = finalize_uva_filing(session, user.tenant_id, user.id, period)
    session.commit()
    return {
        "ok": True,
        "filing_id": filing.id,
        "period_key": filing.period_key,
        "version": filing.version,
        "status": filing.status,
        "xml_hash": filing.xml_hash,
        "total_payable": float(filing.total_payable),
    }


def _filing_xml(session, tenant_id: int, filing_type: str, period_key: str, version: Optional[int]):
    filing = session.exec(select(TaxFiling).where(
        TaxFiling.tenant_id == tenant_id,
        TaxFiling.filing_type == filing_type,
        TaxFiling.period_key == period_key,
        TaxFiling.status == "finalized",
    )).first()
    if not filing:
        raise HTTPException(404, "Für diesen Zeitraum wurde noch keine Meldung finalisiert.")
    selected_version = version or filing.version
    snapshot = session.exec(select(TaxFilingVersion).where(
        TaxFilingVersion.tenant_id == tenant_id,
        TaxFilingVersion.tax_filing_id == filing.id,
        TaxFilingVersion.version == selected_version,
    )).first()
    if not snapshot or not snapshot.xml_payload:
        raise HTTPException(404, "Die gewählte Meldungsversion wurde nicht gefunden.")
    return snapshot.xml_payload


@router.get("/uva/xml")
def get_uva_xml(session: SessionDep, user: CurrentUserDep, period: str, version: Optional[int] = None):
    """Download an immutable finalized FinanzOnline U30 XML version."""
    xml_content = _filing_xml(session, user.tenant_id, "uva", period, version)
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="UVA_{period}.xml"'},
    )


@router.get("/zm")
def get_zm(session: SessionDep, user: CurrentUserDep, period: str):
    """Compute Austrian Recapitulative Statement (Zusammenfassende Meldung / ZM)."""
    return compute_zm(session, user.tenant_id, period)


@router.post("/zm/finalize")
def finalize_zm(session: SessionDep, user: WriteUserDep, period: str):
    """Finalize ZM filing, archive XML and create immutable snapshot."""
    filing = finalize_zm_filing(session, user.tenant_id, user.id, period)
    session.commit()
    return {
        "ok": True,
        "filing_id": filing.id,
        "period_key": filing.period_key,
        "version": filing.version,
        "xml_hash": filing.xml_hash,
    }


@router.get("/zm/xml")
def get_zm_xml(session: SessionDep, user: CurrentUserDep, period: str, version: Optional[int] = None):
    """Download an immutable finalized FinanzOnline ZM XML version."""
    xml_content = _filing_xml(session, user.tenant_id, "zm", period, version)
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="ZM_{period}.xml"'},
    )


@router.get("/u1")
def get_u1(session: SessionDep, user: CurrentUserDep, year: int):
    """Compute Austrian Annual VAT Return (U1) figures."""
    return compute_u1(session, user.tenant_id, year)


@router.post("/u1/finalize")
def finalize_u1(session: SessionDep, user: WriteUserDep, year: int):
    """Finalize annual U1 filing and persist snapshot."""
    filing = finalize_u1_filing(session, user.tenant_id, user.id, year)
    session.commit()
    return {
        "ok": True,
        "filing_id": filing.id,
        "year": filing.year,
        "version": filing.version,
        "xml_hash": filing.xml_hash,
        "annual_tax_liability": float(filing.total_payable),
    }


@router.get("/u1/xml")
def get_u1_xml(session: SessionDep, user: CurrentUserDep, year: int, version: Optional[int] = None):
    """Download an immutable finalized FinanzOnline U1 XML version."""
    xml_content = _filing_xml(session, user.tenant_id, "u1", str(year), version)
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="U1_{year}.xml"'},
    )


@router.get("/reconciliation")
def get_reconciliation(session: SessionDep, user: CurrentUserDep, period: str):
    """Perform three-way reconciliation between General Ledger, TaxEvents, and UVA Form."""
    return reconcile_vat_period(session, user.tenant_id, period)


@router.get("/filings")
def list_filings(
    session: SessionDep,
    user: CurrentUserDep,
    filing_type: Optional[str] = None,
):
    """List historical tax filings and versions for the tenant."""
    query = select(TaxFiling).where(TaxFiling.tenant_id == user.tenant_id)
    if filing_type:
        query = query.where(TaxFiling.filing_type == filing_type)
    query = query.order_by(desc(TaxFiling.created_at))
    return session.exec(query).all()
