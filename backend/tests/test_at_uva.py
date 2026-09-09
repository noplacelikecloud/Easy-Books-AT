"""Tests for Austrian Umsatzsteuervoranmeldung (UVA / U30) and XML export (PR 10: AT-10)."""
from decimal import Decimal
import xml.etree.ElementTree as ET
import pytest
from sqlmodel import Session, select

from models import User
from models_at import TaxFiling, TaxFilingVersion


@pytest.fixture
def at_uva_env(client, admin_headers):
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


def test_uva_computation_and_kennzahlen(client, admin_headers, at_uva_env):
    """Verify statutory UVA Kennzahlen calculation across 20%, 10%, 4.9%, and input tax."""
    cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Kunde Wien GmbH",
        "is_business": True,
        "uid": "ATU12345678",
        "address_country": "AT",
    }).json()

    vendor = client.post("/api/vendors", headers=admin_headers, json={
        "name": "Lieferant Graz KG",
        "is_business": True,
        "uid": "ATU87654321",
        "address_country": "AT",
    }).json()

    prod_20 = client.post("/api/products", headers=admin_headers, json={
        "name": "Standard Service 20%",
        "default_rate": 1000.00,
        "product_type": "service",
    }).json()

    prod_4_9 = client.post("/api/products", headers=admin_headers, json={
        "name": "Bio Brot 4.9%",
        "default_rate": 100.00,
        "product_type": "goods",
        "pct_code": "staple_food",
    }).json()

    # 1. Invoice in 2026-07 (after July 2026 4.9% rate active)
    inv = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-07-15",
        "due_date": "2026-07-30",
        "currency": "EUR",
        "lines": [
            {
                "product_id": prod_20["id"],
                "description": "Beratung",
                "qty": 5,
                "rate": 1000.00,  # 5000 base, 1000 tax
                "tax_treatment_code": "AT_STANDARD_20",
            },
            {
                "product_id": prod_4_9["id"],
                "description": "Brotlieferung",
                "qty": 10,
                "rate": 100.00,  # 1000 base, 49 tax
                "tax_treatment_code": "AT_REDUCED_4_9",
            },
        ],
    }).json()
    assert client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers).status_code == 200

    # 2. Purchase bill in 2026-07 (Input tax)
    bill = client.post("/api/bills", headers=admin_headers, json={
        "vendor_id": vendor["id"],
        "bill_date": "2026-07-18",
        "due_date": "2026-08-01",
        "currency": "EUR",
        "lines": [
            {
                "product_id": prod_20["id"],
                "description": "Büromaterial",
                "qty": 2,
                "rate": 500.00,  # 1000 base, 200 input tax
                "tax_treatment_code": "AT_STANDARD_20",
            }
        ],
    }).json()
    assert client.post(f"/api/bills/{bill['id']}/finalize", headers=admin_headers).status_code == 200

    # Fetch UVA for 2026-07
    res = client.get("/api/at/tax/uva?period=2026-07", headers=admin_headers)
    assert res.status_code == 200, res.text
    data = res.json()

    # KZ 000 = 5000 + 1000 = 6000
    assert Decimal(str(data["kz_000"])) == Decimal("6000.00")
    # KZ 022 = 5000
    assert Decimal(str(data["kz_022"])) == Decimal("5000.00")
    assert Decimal(str(data["kz_022_tax"])) == Decimal("1000.00")
    # KZ 124 = 4.9%-Umsatzbasis; KZ 125 is reserved for 4.9%-IGE basis.
    assert Decimal(str(data["kz_124"])) == Decimal("1000.00")
    assert Decimal(str(data["kz_124_tax"])) == Decimal("49.00")
    assert Decimal(str(data["kz_125"])) == Decimal("0.00")
    # KZ 060 (input tax) = 200
    assert Decimal(str(data["kz_060"])) == Decimal("200.00")
    # Total output tax = 1000 + 49 = 1049
    assert Decimal(str(data["total_output_tax"])) == Decimal("1049.00")
    # Total input tax = 200
    assert Decimal(str(data["total_input_tax"])) == Decimal("200.00")
    # KZ 095 = 1049 - 200 = 849 Zahllast
    assert Decimal(str(data["kz_095"])) == Decimal("849.00")


def test_uva_finalization_xml_and_versioning(client, admin_headers, at_uva_env):
    """Test UVA finalization produces immutable TaxFilingVersion, XML payload, and hash."""
    from main import app

    cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Kunde Linz AG",
        "is_business": True,
        "uid": "ATU33445566",
        "address_country": "AT",
    }).json()

    prod = client.post("/api/products", headers=admin_headers, json={
        "name": "Ingenieurleistung",
        "default_rate": 2000.00,
        "product_type": "service",
    }).json()

    inv = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-08-10",
        "due_date": "2026-08-25",
        "currency": "EUR",
        "lines": [{
            "product_id": prod["id"],
            "description": "Planungsleistung",
            "qty": 1,
            "rate": 2000.00,
            "tax_treatment_code": "AT_STANDARD_20",
        }],
    }).json()
    client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers)

    # 1. Finalize UVA for 2026-08
    fin_res = client.post("/api/at/tax/uva/finalize?period=2026-08", headers=admin_headers)
    assert fin_res.status_code == 200, fin_res.text
    fin_data = fin_res.json()
    assert fin_data["ok"] is True
    assert fin_data["version"] == 1
    assert fin_data["total_payable"] == 400.00
    assert fin_data["xml_hash"] is not None

    # 2. Download XML and check XML schema / tags
    xml_res = client.get("/api/at/tax/uva/xml?period=2026-08", headers=admin_headers)
    assert xml_res.status_code == 200
    assert "application/xml" in xml_res.headers["content-type"]

    root = ET.fromstring(xml_res.content)
    assert root.tag == "ERKLAERUNGS_UEBERMITTLUNG"
    # Find KZ 022
    assert root.findtext(".//KZ022") == "2000.00"
    # KZ 095 is calculated for the UI but is not an element in the U30 XSD.
    assert root.find(".//KZ095") is None

    # 3. Second finalization creates version 2 (Berichtigung)
    fin_res2 = client.post("/api/at/tax/uva/finalize?period=2026-08", headers=admin_headers)
    assert fin_res2.status_code == 200
    assert fin_res2.json()["version"] == 2

    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        versions = session.exec(
            select(TaxFilingVersion).where(TaxFilingVersion.tenant_id == user.tenant_id)
        ).all()
        assert len(versions) == 2

    # 4. List filings endpoint check (verifies session.exec(query).all() execution)
    list_res = client.get("/api/at/tax/filings", headers=admin_headers)
    assert list_res.status_code == 200, list_res.text
    filings = list_res.json()
    assert len(filings) >= 1
    assert any(f["period_key"] == "2026-08" for f in filings)
