"""Tests for Austrian Tax Audit and Accountant Export (PR 15: AT-07, AT-10)."""
import hashlib
import json
import pytest


@pytest.fixture
def at_export_env(client, admin_headers):
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "standard",
        "tax_number": "12-345/6789",
        "vat_id": "ATU12345678",
        "valid_from": "2026-01-01",
    })
    client.post("/api/at/install-coa", headers=admin_headers)


def test_audit_export_package_structure_and_hashes(client, admin_headers, at_export_env):
    """The audit export generates complete datasets with verifiable SHA-256 package manifest."""
    res = client.get("/api/at/audit/export?year=2026", headers=admin_headers)
    assert res.status_code == 200, res.text
    data = res.json()

    # Verify root keys
    assert "manifest" in data
    assert "chart_of_accounts" in data
    assert "bookings" in data
    assert "tax_events" in data
    assert "tax_filings" in data

    manifest = data["manifest"]
    assert manifest["export_format"] == "Easy-Books-Austrian-Audit-v1"
    assert manifest["jurisdiction"] == "AT"
    assert manifest["fiscal_year"] == 2026
    assert manifest["tax_number"] == "12-345/6789"
    assert manifest["vat_id"] == "ATU12345678"

    hashes = manifest["hashes"]
    assert "chart_of_accounts" in hashes
    assert "bookings" in hashes
    assert "tax_events" in hashes
    assert "tax_filings" in hashes

    # Verify SHA-256 integrity of chart_of_accounts
    coa_json = json.dumps(data["chart_of_accounts"], sort_keys=True)
    expected_coa_hash = hashlib.sha256(coa_json.encode("utf-8")).hexdigest()
    assert hashes["chart_of_accounts"] == expected_coa_hash

    # Verify package signature exists
    assert "package_signature" in manifest
    assert len(manifest["package_signature"]) == 64
