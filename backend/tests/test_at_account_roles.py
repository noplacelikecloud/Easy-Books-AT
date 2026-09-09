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
    assert roles["retained_earnings"]["account_code"] == "9390"  # EKR Bilanzgewinn


def test_roles_bind_to_accounts_with_the_right_meaning(client, admin_headers):
    """A role must point at an account that is actually that thing.

    The earlier version of this test only compared account *codes*, which is
    exactly how the chart could end up with `accounts_receivable` bound to a
    liability account named "Accounts Payable": the generic English chart is
    seeded first and its 2000 is AP, so installing the Austrian chart on top
    reused that row and the code assertion still passed.
    """
    res = client.post("/api/at/install-coa", headers=admin_headers)
    assert res.status_code == 200, res.text

    acc_res = client.get("/api/accounts?limit=500", headers=admin_headers).json()
    accounts = {a["code"]: a for a in acc_res["items"]}
    roles = {r["role_key"]: r for r in client.get("/api/at/roles", headers=admin_headers).json()["roles"]}

    expected = {
        "accounts_receivable": ("2000", "Forderungen aus Lieferungen und Leistungen Inland", "Asset"),
        "accounts_payable":    ("3300", "Verbindlichkeiten aus Lieferungen und Leistungen Inland", "Liability"),
        "inventory":           ("1600", "Handelswarenvorrat", "Asset"),
        "cogs":                ("5010", "Handelswaren-Verbrauch", "Expense"),
        "revenue":             ("4000", "Umsatzerlöse Inland 20% USt", "Revenue"),
        "vat_output":          ("3500", "Umsatzsteuer 20%", "Liability"),
        "vat_input":           ("2500", "Vorsteuer 20%", "Asset"),
        "retained_earnings":   ("9390", "Bilanzgewinn / Bilanzverlust", "Equity"),
    }
    for role_key, (code, name, acc_type) in expected.items():
        assert roles[role_key]["account_code"] == code, role_key
        acc = accounts[code]
        assert acc["name"] == name, f"{role_key} → {code} heißt '{acc['name']}'"
        assert acc["type"] == acc_type, f"{role_key} → {code} ist '{acc['type']}'"


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
