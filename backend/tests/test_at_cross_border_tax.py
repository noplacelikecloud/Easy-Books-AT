"""Tests for Austrian Cross-Border & Reverse Charge Tax Determination (PR 8: AT-04)."""
from decimal import Decimal
import pytest
from sqlmodel import Session, select

from localizations.at.cross_border import determine_cross_border_treatment, is_eu_country
from models_at import TaxEvent
from models import Invoice, User


@pytest.fixture
def at_cross_border_env(client, admin_headers):
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "regular",
        "vat_method": "accrual",
        "vat_filing_frequency": "monthly",
        "vat_id": "ATU12345678",
        "valid_from": "2026-01-01",
    })


def test_cross_border_treatment_determination():
    """Validates pure function mapping of cross-border statutory rules."""
    assert is_eu_country("DE") is True
    assert is_eu_country("US") is False
    assert is_eu_country("AT") is True

    # 1. Outbound EU B2B with UID (Goods) -> ig. Lieferung
    t1 = determine_cross_border_treatment(
        direction="sales", partner_country="DE", partner_vat_id="DE123456789", is_b2b=True, is_service=False
    )
    assert t1 == "AT_ZERO_IG_SUPPLY"

    # 2. Outbound EU B2B with UID (Service) -> RC EU Service Out
    t2 = determine_cross_border_treatment(
        direction="sales", partner_country="DE", partner_vat_id="DE123456789", is_b2b=True, is_service=True
    )
    assert t2 == "AT_RC_EU_SERVICE_OUT"

    # 3. Outbound Third Country (Export) -> Export
    t3 = determine_cross_border_treatment(
        direction="sales", partner_country="US", partner_vat_id=None, is_b2b=True
    )
    assert t3 == "AT_ZERO_EXPORT"

    # 4. Inbound EU goods -> Innergemeinschaftlicher Erwerb
    t4 = determine_cross_border_treatment(
        direction="purchases", partner_country="IT", partner_vat_id="IT12345678901", is_b2b=True, is_service=False
    )
    assert t4 == "AT_IG_ACQUISITION_20"

    # 5. Inbound EU service -> RC EU Service In
    t5 = determine_cross_border_treatment(
        direction="purchases", partner_country="IT", partner_vat_id="IT12345678901", is_b2b=True, is_service=True
    )
    assert t5 == "AT_RC_EU_SERVICE_IN"

    # 6. Domestic Bauleistung -> RC Domestic
    t6 = determine_cross_border_treatment(
        direction="purchases", partner_country="AT", partner_vat_id="ATU99999999", is_b2b=True, is_construction=True
    )
    assert t6 == "AT_RC_DOMESTIC"


def test_intra_eu_supply_invoice_lifecycle(client, admin_headers, at_cross_border_env):
    """An intra-EU supply generates ZM-relevant TaxEvent with KZ 017."""
    from main import app

    cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Deutscher B2B Kunde GmbH",
        "is_business": True,
        "uid": "DE987654321",
        "address_country": "DE",
    }).json()

    prod = client.post("/api/products", headers=admin_headers, json={
        "name": "Export Ware",
        "default_rate": 3000.00,
        "product_type": "service",
    }).json()

    treatment = determine_cross_border_treatment(
        direction="sales",
        partner_country=cust.get("address_country"),
        partner_vat_id=cust.get("uid"),
        is_b2b=True,
        is_service=False,
    )
    assert treatment == "AT_ZERO_IG_SUPPLY"

    inv = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-03-20",
        "due_date": "2026-04-05",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "gst_rate": 0,
        "notes": "Steuerfreie innergemeinschaftliche Lieferung gem. Art. 6 UStG",
        "lines": [{
            "product_id": prod["id"],
            "description": "Export Ware nach Deutschland",
            "qty": 1,
            "rate": 3000.00,
            "tax_treatment_code": treatment,
        }],
    }).json()

    fin_res = client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers)
    assert fin_res.status_code == 200, fin_res.text

    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        events = session.exec(
            select(TaxEvent).where(
                TaxEvent.tenant_id == user.tenant_id,
                TaxEvent.source_doc_type == "invoice",
                TaxEvent.source_doc_id == inv["id"],
            )
        ).all()

        assert len(events) == 1
        ev = events[0]
        assert ev.treatment_code == "AT_ZERO_IG_SUPPLY"
        assert ev.base_amount == Decimal("3000.00")
        assert ev.output_tax == Decimal("0.00")
        assert ev.uva_base_kz == "017"
        assert ev.zm_relevant is True
        assert ev.partner_country == "DE"
        assert ev.partner_vat_id == "DE987654321"
