"""Tests for PR 4: Austrian KMU Chart of Accounts and Semantic Account Roles."""
import pytest


def test_install_at_coa_and_roles(client, admin_headers):
    # Install Austrian KMU CoA
    res = client.post("/api/at/install-coa", headers=admin_headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["installed"] is True
    assert data["accounts_count"] >= 30
    assert data["roles_bound"] >= 10

    # Fetch role bindings
    roles_res = client.get("/api/at/roles", headers=admin_headers)
    assert roles_res.status_code == 200
    roles = {r["role_key"]: r for r in roles_res.json()["roles"]}

    assert "accounts_receivable" in roles
    assert roles["accounts_receivable"]["account_code"] == "2000"

    assert "accounts_payable" in roles
    assert roles["accounts_payable"]["account_code"] == "3300"

    assert "vat_output" in roles
    assert roles["vat_output"]["account_code"] == "3500"

    assert "vat_input" in roles
    assert roles["vat_input"]["account_code"] == "2500"

    assert "retained_earnings" in roles
    assert roles["retained_earnings"]["account_code"] == "9300"


def test_custom_role_rebinding(client, admin_headers):
    client.post("/api/at/install-coa", headers=admin_headers)

    # Create a custom bank account
    custom_bank = client.post("/api/accounts", headers=admin_headers, json={
        "code": "2810",
        "name": "Erste Bank Hauptkonto",
        "type": "Asset",
    }).json()

    # Rebind 'bank' role to custom account
    rebind_res = client.post("/api/at/roles", headers=admin_headers, json={
        "role_key": "bank",
        "account_id": custom_bank["id"],
    })
    assert rebind_res.status_code == 200

    roles_res = client.get("/api/at/roles", headers=admin_headers).json()["roles"]
    bank_role = next(r for r in roles_res if r["role_key"] == "bank")
    assert bank_role["account_code"] == "2810"
