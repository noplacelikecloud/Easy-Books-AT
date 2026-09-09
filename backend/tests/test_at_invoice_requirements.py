"""Tests for Austrian Invoice & Document Requirements (PR 5, AT-06, § 11 UStG, § 14 UGB)."""
import pytest


def test_kleinbetrag_and_standard_invoice_validation(client, admin_headers):
    """Invoice <= 400 EUR passes without supplier UID, but > 400 EUR requires supplier UID under AT profile."""
    # 1. Enable Austrian profile without VAT ID initially
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "regular",
        "vat_method": "accrual",
        "vat_filing_frequency": "monthly",
        "company_register_number": "FN 123456 a",
        "company_register_court": "HG Wien",
        "registered_seat": "Wien",
        "valid_from": "2026-01-01",
    })

    cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Endverbraucher Max",
        "is_business": False,
    }).json()

    prod_small = client.post("/api/products", headers=admin_headers, json={
        "name": "Kleinleistung",
        "default_rate": 350.00,
        "product_type": "service",
    }).json()

    # Small invoice <= 400 EUR (gst_rate=0, exchange_rate=1.0)
    inv_small_res = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-03-01",
        "due_date": "2026-03-15",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "gst_rate": 0,
        "lines": [{"product_id": prod_small["id"], "description": "Kleinleistung", "qty": 1, "rate": 350.00}],
    })
    assert inv_small_res.status_code in (200, 201), inv_small_res.text
    inv_small = inv_small_res.json()

    # Finalize should succeed for <= 400 EUR
    fin_res_small = client.post(f"/api/invoices/{inv_small['id']}/finalize", headers=admin_headers)
    assert fin_res_small.status_code == 200, f"Error: {fin_res_small.text}"

    # Invoice > 400 EUR without supplier UID should fail
    prod_large = client.post("/api/products", headers=admin_headers, json={
        "name": "Großleistung",
        "default_rate": 500.00,
        "product_type": "service",
    }).json()

    inv_large_res = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-03-02",
        "due_date": "2026-03-16",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "gst_rate": 0,
        "lines": [{"product_id": prod_large["id"], "description": "Großleistung", "qty": 1, "rate": 500.00}],
    })
    assert inv_large_res.status_code in (200, 201), inv_large_res.text
    inv_large = inv_large_res.json()

    fin_res_large = client.post(f"/api/invoices/{inv_large['id']}/finalize", headers=admin_headers)
    assert fin_res_large.status_code == 422
    assert "UID des leistenden Unternehmers" in fin_res_large.json()["detail"]

    # Now update profile with supplier UID and verify finalize succeeds
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "regular",
        "vat_method": "accrual",
        "vat_filing_frequency": "monthly",
        "vat_id": "ATU12345678",
        "company_register_number": "FN 123456 a",
        "company_register_court": "HG Wien",
        "registered_seat": "Wien",
        "valid_from": "2026-01-01",
    })
    fin_res_large2 = client.post(f"/api/invoices/{inv_large['id']}/finalize", headers=admin_headers)
    assert fin_res_large2.status_code == 200


def test_large_b2b_invoice_requires_customer_uid(client, admin_headers):
    """B2B invoice > 10,000 EUR requires customer UID (§ 11 Abs. 1 Z 3 lit. b UStG)."""
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "regular",
        "vat_method": "accrual",
        "vat_filing_frequency": "monthly",
        "vat_id": "ATU12345678",
        "valid_from": "2026-01-01",
    })

    cust_no_uid = client.post("/api/customers", headers=admin_headers, json={
        "name": "Kunde Ohne UID GmbH",
        "is_business": True,
    }).json()

    prod = client.post("/api/products", headers=admin_headers, json={
        "name": "Server Cluster",
        "default_rate": 12000.00,
        "product_type": "service",
    }).json()

    inv_res = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust_no_uid["id"],
        "issue_date": "2026-03-03",
        "due_date": "2026-03-17",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "gst_rate": 0,
        "lines": [{"product_id": prod["id"], "description": "Server Cluster", "qty": 1, "rate": 12000.00}],
    })
    assert inv_res.status_code in (200, 201), inv_res.text
    inv = inv_res.json()

    res = client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers)
    assert res.status_code == 422
    assert "UID des Kunden verpflichtend" in res.json()["detail"]

    # Update customer with UID and re-try
    client.put(f"/api/customers/{cust_no_uid['id']}", headers=admin_headers, json={
        "name": "Kunde Mit UID GmbH",
        "is_business": True,
        "uid": "ATU99988877",
    })

    res2 = client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers)
    assert res2.status_code == 200


def test_statutory_reverse_charge_notice_enforced(client, admin_headers):
    """Reverse charge invoices require statutory notice (§ 11 Abs. 1a UStG)."""
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "regular",
        "vat_method": "accrual",
        "vat_filing_frequency": "monthly",
        "vat_id": "ATU12345678",
        "valid_from": "2026-01-01",
    })

    cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Baupartner AG",
        "is_business": True,
        "uid": "ATU55544433",
    }).json()

    prod = client.post("/api/products", headers=admin_headers, json={
        "name": "Subunternehmer Bauleistung",
        "default_rate": 2000.00,
        "product_type": "service",
    }).json()

    # Invoice with tax_treatment_code = AT_RC_DOMESTIC but no notice
    inv_res = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-03-04",
        "due_date": "2026-03-18",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "gst_rate": 0,
        "notes": "",
        "lines": [{
            "product_id": prod["id"],
            "description": "Bauleistung",
            "qty": 1,
            "rate": 2000.00,
            "tax_treatment_code": "AT_RC_DOMESTIC",
        }],
    })
    assert inv_res.status_code in (200, 201), inv_res.text
    inv = inv_res.json()

    res = client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers)
    assert res.status_code == 422
    assert "Steuerschuldnerschaft des Leistungsempfängers" in res.json()["detail"]

    # Add mandatory notice and finalize
    client.put(f"/api/invoices/{inv['id']}", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-03-04",
        "due_date": "2026-03-18",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "gst_rate": 0,
        "notes": "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge)",
        "lines": [{
            "product_id": prod["id"],
            "description": "Bauleistung",
            "qty": 1,
            "rate": 2000.00,
            "tax_treatment_code": "AT_RC_DOMESTIC",
        }],
    })

    res2 = client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers)
    assert res2.status_code == 200
