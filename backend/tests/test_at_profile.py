"""Tests for PR 4: Austrian Compliance Profile, Capabilities, and Currency Integrity."""
import pytest
from sqlmodel import Session, select

from models import User
from models_at import AccountingProfileVersion


def test_create_and_fetch_at_profile(client, admin_headers):
    # Check initial profile (none)
    init_res = client.get("/api/at/profile", headers=admin_headers)
    assert init_res.status_code == 200
    assert init_res.json()["active"] is False

    # Create GmbH UGB-VAT profile
    post_res = client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "standard",
        "vat_method": "accrual",
        "vat_filing_frequency": "monthly",
        "company_register_number": "FN 123456 a",
        "company_register_court": "Handelsgericht Wien",
        "tax_number": "12/345/6789",
        "vat_id": "ATU12345678",
        "registered_seat": "Wien",
        "valid_from": "2026-01-01",
    })
    assert post_res.status_code == 200, post_res.text
    assert post_res.json()["ok"] is True

    # Fetch active profile
    get_res = client.get("/api/at/profile", headers=admin_headers)
    assert get_res.status_code == 200
    assert get_res.json()["active"] is True
    prof = get_res.json()["profile"]
    assert prof["legal_form"] == "gmbh"
    assert prof["company_register_number"] == "FN 123456 a"
    assert prof["vat_id"] == "ATU12345678"


def test_effective_dated_profile_update(client, admin_headers):
    # Version 1 from 2025
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "sole_proprietor",
        "profit_method": "ear",
        "vat_status": "small_business_exempt",
        "valid_from": "2025-01-01",
    })

    # Version 2 from 2026 (status transition to standard VAT)
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "sole_proprietor",
        "profit_method": "ear",
        "vat_status": "standard",
        "valid_from": "2026-01-01",
        "change_reason": "Kleinunternehmergrenze überschritten",
    })

    # Profile as of 2025 should be small_business_exempt
    p2025 = client.get("/api/at/profile?on_date=2025-06-01", headers=admin_headers).json()
    assert p2025["profile"]["vat_status"] == "small_business_exempt"

    # Profile as of 2026 should be standard
    p2026 = client.get("/api/at/profile?on_date=2026-06-01", headers=admin_headers).json()
    assert p2026["profile"]["vat_status"] == "standard"


def test_same_day_profile_correction_keeps_superseded_audit_row(client, admin_headers):
    first = client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "standard",
        "valid_from": "2026-01-01",
    })
    assert first.status_code == 200
    second = client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "standard",
        "vat_id": "ATU12345678",
        "valid_from": "2026-01-01",
        "change_reason": "UID ergänzt",
    })
    assert second.status_code == 200

    from main import app
    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        versions = session.exec(select(AccountingProfileVersion).where(
            AccountingProfileVersion.tenant_id == user.tenant_id,
        ).order_by(AccountingProfileVersion.id)).all()
        assert len(versions) == 2
        assert versions[0].superseded_at is not None
        assert versions[0].superseded_by_id == versions[1].id
        assert versions[1].superseded_at is None

    active = client.get("/api/at/profile?on_date=2026-01-01", headers=admin_headers).json()["profile"]
    assert active["vat_id"] == "ATU12345678"


def test_capability_gate_blocks_conditional_modules(client, admin_headers):
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "valid_from": "2026-01-01",
    })

    # RKSV is initially blocked
    rksv_check = client.post("/api/at/check-capability?capability=at_rksv", headers=admin_headers)
    assert rksv_check.status_code == 403
    assert "gesperrt" in rksv_check.json()["detail"].lower()

    # Payroll is initially blocked
    pay_check = client.post("/api/at/check-capability?capability=at_payroll", headers=admin_headers)
    assert pay_check.status_code == 403

    # Peppol / Bundese-Rechnung is initially blocked
    erb_check = client.post("/api/at/check-capability?capability=at_erb", headers=admin_headers)
    assert erb_check.status_code == 403
