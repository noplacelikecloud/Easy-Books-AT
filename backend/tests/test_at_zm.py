"""Tests for Austrian Zusammenfassende Meldung (ZM) (PR 10: AT-10)."""
from decimal import Decimal
import xml.etree.ElementTree as ET
import pytest


@pytest.fixture
def at_zm_env(client, admin_headers):
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


def test_zm_aggregation_and_xml(client, admin_headers, at_zm_env):
    """Test ZM correctly aggregates EU cross-border goods ('L') and services ('S') with valid XML."""
    de_cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Kunde Deutschland GmbH",
        "is_business": True,
        "uid": "DE123456789",
        "address_country": "DE",
    }).json()

    fr_cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Client France SAS",
        "is_business": True,
        "uid": "FR987654321",
        "address_country": "FR",
    }).json()

    prod_goods = client.post("/api/products", headers=admin_headers, json={
        "name": "Maschinenteile",
        "default_rate": 5000.00,
        "product_type": "goods",
    }).json()

    prod_serv = client.post("/api/products", headers=admin_headers, json={
        "name": "IT Beratung",
        "default_rate": 3000.00,
        "product_type": "service",
    }).json()

    # 1. Intra-EU supply of goods to Germany (Art "L")
    inv1 = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": de_cust["id"],
        "issue_date": "2026-04-10",
        "due_date": "2026-04-25",
        "currency": "EUR",
        "gst_rate": 0,
        "notes": "Steuerfreie innergemeinschaftliche Lieferung gem. Art. 6 UStG",
        "lines": [{
            "product_id": prod_goods["id"],
            "description": "Maschinen",
            "qty": 2,
            "rate": 5000.00,  # 10000 EUR
            "tax_treatment_code": "AT_ZERO_IG_SUPPLY",
        }],
    }).json()
    assert client.post(f"/api/invoices/{inv1['id']}/finalize", headers=admin_headers).status_code == 200

    # 2. B2B service to France (Art "S")
    inv2 = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": fr_cust["id"],
        "issue_date": "2026-04-15",
        "due_date": "2026-04-30",
        "currency": "EUR",
        "gst_rate": 0,
        "notes": "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge gem. Art. 196 MwSt-SystRL)",
        "lines": [{
            "product_id": prod_serv["id"],
            "description": "Softwarearchitektur",
            "qty": 1,
            "rate": 3000.00,
            "tax_treatment_code": "AT_RC_EU_SERVICE_OUT",
        }],
    }).json()
    assert client.post(f"/api/invoices/{inv2['id']}/finalize", headers=admin_headers).status_code == 200

    # Query ZM for 2026-04
    res = client.get("/api/at/tax/zm?period=2026-04", headers=admin_headers)
    assert res.status_code == 200, res.text
    zm_data = res.json()

    assert zm_data["entry_count"] == 2
    assert Decimal(str(zm_data["total_amount_eur"])) == Decimal("13000.00")

    entries = {e["partner_vat_id"]: e for e in zm_data["entries"]}
    assert "DE123456789" in entries
    assert entries["DE123456789"]["country"] == "DE"
    assert entries["DE123456789"]["art"] == "L"
    assert Decimal(str(entries["DE123456789"]["amount"])) == Decimal("10000.00")

    assert "FR987654321" in entries
    assert entries["FR987654321"]["country"] == "FR"
    assert entries["FR987654321"]["art"] == "S"
    assert Decimal(str(entries["FR987654321"]["amount"])) == Decimal("3000.00")

    # Finalize ZM
    fin_res = client.post("/api/at/tax/zm/finalize?period=2026-04", headers=admin_headers)
    assert fin_res.status_code == 200
    assert fin_res.json()["ok"] is True

    # Check ZM XML
    xml_res = client.get("/api/at/tax/zm/xml?period=2026-04", headers=admin_headers)
    assert xml_res.status_code == 200
    assert "application/xml" in xml_res.headers["content-type"]

    root = ET.fromstring(xml_res.content)
    assert root.tag == "ERKLAERUNGS_UEBERMITTLUNG"
    amounts = [Decimal(node.text) for node in root.findall(".//SUM_BGL")]
    assert sum(amounts) == Decimal("13000")
    assert root.findtext(".//SOLEI") == "J"
