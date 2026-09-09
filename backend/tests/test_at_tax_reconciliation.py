"""Tests for Austrian VAT Reconciliation GL vs TaxEvents vs UVA (PR 10: AT-10)."""
from decimal import Decimal
import pytest


@pytest.fixture
def at_recon_env(client, admin_headers):
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "standard",
        "vat_method": "accrual",
        "vat_filing_frequency": "monthly",
        "tax_number": "12-345/6789",
        "vat_id": "ATU99887766",
        "valid_from": "2026-01-01",
    })
    client.post("/api/at/install-coa", headers=admin_headers)


def test_vat_reconciliation_balanced(client, admin_headers, at_recon_env):
    """Clean posted invoices and bills show full reconciliation between GL and TaxEvents."""
    cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Kunde Graz GmbH",
        "is_business": True,
        "uid": "ATU55443322",
        "address_country": "AT",
    }).json()

    vendor = client.post("/api/vendors", headers=admin_headers, json={
        "name": "Lieferant Linz AG",
        "is_business": True,
        "uid": "ATU22334455",
        "address_country": "AT",
    }).json()

    prod = client.post("/api/products", headers=admin_headers, json={
        "name": "Standardprodukt",
        "default_rate": 1000.00,
        "product_type": "goods",
    }).json()

    # 1. Invoice: 2000 EUR base + 400 EUR VAT
    inv = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-05-10",
        "due_date": "2026-05-25",
        "currency": "EUR",
        "gst_rate": 20,
        "lines": [{
            "product_id": prod["id"],
            "description": "Lieferung",
            "qty": 2,
            "rate": 1000.00,
            "tax_treatment_code": "AT_STANDARD_20",
        }],
    }).json()
    assert client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers).status_code == 200

    # 2. Bill: 500 EUR base + 100 EUR input VAT
    bill = client.post("/api/bills", headers=admin_headers, json={
        "vendor_id": vendor["id"],
        "bill_date": "2026-05-15",
        "due_date": "2026-05-30",
        "currency": "EUR",
        "gst_rate": 20,
        "lines": [{
            "product_id": prod["id"],
            "description": "Wareneinkauf",
            "qty": 1,
            "rate": 500.00,
            "tax_treatment_code": "AT_STANDARD_20",
        }],
    }).json()
    assert client.post(f"/api/bills/{bill['id']}/finalize", headers=admin_headers).status_code == 200

    # 3. Reconcile period 2026-05
    recon = client.get("/api/at/tax/reconciliation?period=2026-05", headers=admin_headers).json()
    assert recon["is_reconciled"] is True
    assert Decimal(str(recon["events_output_tax"])) == Decimal("400.00")
    assert Decimal(str(recon["events_input_tax"])) == Decimal("100.00")
    assert Decimal(str(recon["events_net_payable"])) == Decimal("300.00")
    assert len(recon["discrepancies"]) == 0


def test_vat_reconciliation_february_leap_year(client, admin_headers, at_recon_env):
    """Transactions booked on February 29th in a leap year (e.g. 2028) are included in reconciliation."""
    cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Leap Year Kunde",
        "is_business": True,
        "uid": "ATU11112222",
        "address_country": "AT",
    }).json()

    prod = client.post("/api/products", headers=admin_headers, json={
        "name": "Schaltjahr Service",
        "default_rate": 500.00,
        "product_type": "service",
    }).json()

    inv = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2028-02-29",
        "due_date": "2028-03-15",
        "currency": "EUR",
        "gst_rate": 20,
        "lines": [{
            "product_id": prod["id"],
            "description": "Leap day service",
            "qty": 2,
            "rate": 500.00,
            "tax_treatment_code": "AT_STANDARD_20",
        }],
    }).json()
    assert client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers).status_code == 200

    recon = client.get("/api/at/tax/reconciliation?period=2028-02", headers=admin_headers).json()
    assert recon["is_reconciled"] is True
    assert Decimal(str(recon["events_output_tax"])) == Decimal("200.00")
    assert Decimal(str(recon["gl_output_tax"])) == Decimal("200.00")
