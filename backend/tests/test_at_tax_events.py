"""Tests for Austrian Tax Event Engine and Storno adjustments (PR 7, PR 8: AT-04, AT-10)."""
from decimal import Decimal
import pytest
from sqlmodel import Session, select

from models_at import TaxEvent, TaxAdjustment
from models import Invoice, Bill, User


@pytest.fixture
def at_tax_event_env(client, admin_headers):
    # Setup profile with VAT ID
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "regular",
        "vat_method": "accrual",
        "vat_filing_frequency": "monthly",
        "vat_id": "ATU12345678",
        "valid_from": "2026-01-01",
    })


def test_invoice_finalization_generates_tax_events(client, admin_headers, at_tax_event_env):
    """Finalizing an invoice generates immutable TaxEvent rows with UVA mapping."""
    from main import app

    cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Kunde A GmbH",
        "is_business": True,
        "uid": "ATU11122233",
        "address_country": "AT",
    }).json()

    prod = client.post("/api/products", headers=admin_headers, json={
        "name": "Software Lizenz",
        "default_rate": 1000.00,
        "product_type": "service",
    }).json()

    inv = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-03-10",
        "due_date": "2026-03-25",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "gst_rate": 20,
        "lines": [{
            "product_id": prod["id"],
            "description": "Software Lizenz",
            "qty": 2,
            "rate": 1000.00,
            "tax_treatment_code": "AT_STANDARD_20",
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
        assert ev.base_amount == Decimal("2000.00")
        assert ev.uva_base_kz == "022"
        assert ev.uva_tax_kz == "022"
        assert ev.tax_period == "2026-03"
        assert ev.state == "final"


def test_bill_reverse_charge_tax_event(client, admin_headers, at_tax_event_env):
    """Vendor bill with domestic reverse charge (Bauleistung) generates RC tax and input tax."""
    from main import app

    vendor = client.post("/api/vendors", headers=admin_headers, json={
        "name": "Subunternehmer Bau GmbH",
        "is_business": True,
        "uid": "ATU44433322",
        "address_country": "AT",
    }).json()

    prod = client.post("/api/products", headers=admin_headers, json={
        "name": "Bauleistung",
        "default_rate": 5000.00,
        "product_type": "service",
    }).json()

    bill = client.post("/api/bills", headers=admin_headers, json={
        "vendor_id": vendor["id"],
        "bill_date": "2026-03-12",
        "due_date": "2026-03-27",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "gst_rate": 20,
        "lines": [{
            "product_id": prod["id"],
            "description": "Bauleistung",
            "qty": 1,
            "rate": 5000.00,
            "tax_treatment_code": "AT_RC_DOMESTIC",
        }],
    }).json()

    fin_res = client.post(f"/api/bills/{bill['id']}/finalize", headers=admin_headers)
    assert fin_res.status_code == 200, fin_res.text

    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        all_evs = session.exec(select(TaxEvent)).all()
        print("ALL TAX EVENTS IN DB:", all_evs)
        print("BILL ID:", bill.get("id"), "BILL DATA:", bill)
        events = session.exec(
            select(TaxEvent).where(
                TaxEvent.tenant_id == user.tenant_id,
                TaxEvent.source_doc_type == "bill",
                TaxEvent.source_doc_id == bill["id"],
            )
        ).all()

        assert len(events) == 1
        ev = events[0]
        assert ev.base_amount == Decimal("5000.00")
        assert ev.reverse_charge_tax == Decimal("1000.00")
        assert ev.input_tax_deductible == Decimal("1000.00")


def test_invoice_storno_reverses_tax_events_with_audit_link(client, admin_headers, at_tax_event_env):
    """Cancelling a finalized invoice stornos tax events and records TaxAdjustment."""
    from main import app

    cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Storno Kunde GmbH",
        "is_business": True,
        "uid": "ATU77788899",
    }).json()

    prod = client.post("/api/products", headers=admin_headers, json={
        "name": "Falschlieferung",
        "default_rate": 500.00,
        "product_type": "service",
    }).json()

    inv = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-03-14",
        "due_date": "2026-03-28",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "gst_rate": 20,
        "lines": [{
            "product_id": prod["id"],
            "description": "Falschlieferung",
            "qty": 1,
            "rate": 500.00,
            "tax_treatment_code": "AT_STANDARD_20",
        }],
    }).json()

    client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers)

    # Cancel invoice
    cancel_res = client.post(
        f"/api/invoices/{inv['id']}/cancel",
        headers=admin_headers,
        json={"reason": "Kunde hat Auftrag storniert"},
    )
    assert cancel_res.status_code == 200, cancel_res.text

    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        adjustments = session.exec(
            select(TaxAdjustment).where(TaxAdjustment.tenant_id == user.tenant_id)
        ).all()
        assert len(adjustments) >= 1
        adj = adjustments[0]
        assert adj.reason == "Kunde hat Auftrag storniert"

        # Check reversing event
        rev_ev = session.get(TaxEvent, adj.new_event_id)
        assert rev_ev is not None
        assert rev_ev.base_amount == Decimal("-500.00")
        assert rev_ev.output_tax == Decimal("-100.00")
