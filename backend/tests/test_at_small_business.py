"""Tests for Austrian Kleinunternehmer Exemption & Threshold Monitoring (PR 9: AT-EAR-KU)."""
from decimal import Decimal
import pytest


@pytest.fixture
def at_ku_env(client, admin_headers):
    # Setup AT-EAR-KU profile (E/A-Rechnung + Kleinunternehmer)
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "sole_proprietor",
        "profit_method": "ear",
        "vat_status": "small_business_exempt",
        "vat_method": "cash",
        "vat_filing_frequency": "annual_only",
        "tax_number": "98/765/4321",
        "valid_from": "2026-01-01",
    })


def test_small_business_threshold_and_tolerance_lifecycle(client, admin_headers, at_ku_env):
    """Monitors 55,000 EUR limit and 60,500 EUR tolerance window."""
    cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Kunde Max",
        "is_business": False,
    }).json()

    prod = client.post("/api/products", headers=admin_headers, json={
        "name": "Dienstleistung",
        "default_rate": 1000.00,
        "product_type": "service",
    }).json()

    # 1. Invoice 1: 50,000 EUR (below 55k threshold)
    inv1 = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-04-10",
        "due_date": "2026-04-25",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "gst_rate": 0,
        "notes": "Umsatzsteuerbefreit aufgrund der Kleinunternehmerregelung gem. § 6 Abs. 1 Z 27 UStG",
        "lines": [{
            "product_id": prod["id"],
            "description": "Leistung Paket 1",
            "qty": 50,
            "rate": 1000.00,
            "tax_treatment_code": "AT_EXEMPT_KU",
        }],
    }).json()
    client.post(f"/api/invoices/{inv1['id']}/finalize", headers=admin_headers)

    status1 = client.get("/api/at/small-business?year=2026", headers=admin_headers).json()
    assert status1["qualifying_turnover"] == 50000.0
    assert status1["status"] in ("ok", "warning_approaching")
    assert status1["is_exceeded"] is False

    # 2. Invoice 2: 7,000 EUR -> Total 57,000 EUR (Inside 10% tolerance: 55,000 < 57,000 <= 60,500)
    inv2 = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-06-15",
        "due_date": "2026-06-30",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "gst_rate": 0,
        "notes": "Umsatzsteuerbefreit aufgrund der Kleinunternehmerregelung gem. § 6 Abs. 1 Z 27 UStG",
        "lines": [{
            "product_id": prod["id"],
            "description": "Leistung Paket 2",
            "qty": 7,
            "rate": 1000.00,
            "tax_treatment_code": "AT_EXEMPT_KU",
        }],
    }).json()
    client.post(f"/api/invoices/{inv2['id']}/finalize", headers=admin_headers)

    status2 = client.get("/api/at/small-business?year=2026", headers=admin_headers).json()
    assert status2["qualifying_turnover"] == 57000.0
    assert status2["status"] == "tolerance_window"
    assert status2["is_exceeded"] is False

    # Profile is still small business exempt
    prof2_res = client.get("/api/at/profile?on_date=2026-06-15", headers=admin_headers).json()
    assert prof2_res["profile"]["vat_status"] == "small_business_exempt"

    # 3. Invoice 3: 5,000 EUR -> Total 62,000 EUR (Exceeds 60,500 tolerance limit!)
    inv3 = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-08-01",
        "due_date": "2026-08-15",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "gst_rate": 0,
        "notes": "Umsatzsteuerbefreit aufgrund der Kleinunternehmerregelung gem. § 6 Abs. 1 Z 27 UStG",
        "lines": [{
            "product_id": prod["id"],
            "description": "Leistung Paket 3",
            "qty": 5,
            "rate": 1000.00,
            "tax_treatment_code": "AT_EXEMPT_KU",
        }],
    }).json()
    # The crossing transaction itself must use standard VAT. An exempt draft
    # is rejected atomically and does not advance the ledger/profile.
    rejected = client.post(f"/api/invoices/{inv3['id']}/finalize", headers=admin_headers)
    assert rejected.status_code == 422

    inv3["lines"][0]["tax_treatment_code"] = "AT_STANDARD_20"
    inv3["gst_rate"] = 20
    inv3["notes"] = ""
    assert client.put(f"/api/invoices/{inv3['id']}", headers=admin_headers, json={
        "customer_id": cust["id"], "issue_date": "2026-08-01", "due_date": "2026-08-15",
        "currency": "EUR", "exchange_rate": 1, "gst_rate": 20,
        "lines": [{"product_id": prod["id"], "description": "Leistung Paket 3", "qty": 5,
                   "rate": 1000, "tax_treatment_code": "AT_STANDARD_20"}],
    }).status_code == 200
    assert client.post(f"/api/invoices/{inv3['id']}/finalize", headers=admin_headers).status_code == 200

    status3 = client.get("/api/at/small-business?year=2026", headers=admin_headers).json()
    assert status3["qualifying_turnover"] == 62000.0
    assert status3["status"] == "exceeded"
    assert status3["is_exceeded"] is True
    assert status3["exceeded_on_date"] == "2026-08-01"
    assert status3["exceeded_by_invoice_id"] == inv3["id"]

    # Profile automatically transitioned to standard VAT from 2026-08-01!
    prof3_res = client.get("/api/at/profile?on_date=2026-08-02", headers=admin_headers).json()
    assert prof3_res["profile"]["vat_status"] == "standard"


def test_voluntary_waiver_of_small_business_exemption(client, admin_headers, at_ku_env):
    """Regelbesteuerungsantrag gem. § 6 Abs. 3 UStG switches profile to regular VAT."""
    res = client.post("/api/at/small-business/opt-in", headers=admin_headers, json={
        "valid_from": "2026-02-01",
        "reason": "Freiwilliger Regelbesteuerungsantrag wegen hoher Vorsteuern",
    })
    assert res.status_code == 200, res.text

    status = client.get("/api/at/small-business?year=2026", headers=admin_headers).json()
    assert status["opted_into_standard_vat"] is True
    assert status["option_valid_from"] == "2026-02-01"

    prof = client.get("/api/at/profile?on_date=2026-01-02", headers=admin_headers).json()
    prof = client.get("/api/at/profile?on_date=2026-02-02", headers=admin_headers).json()
    assert prof["profile"]["vat_status"] == "opted_in"
