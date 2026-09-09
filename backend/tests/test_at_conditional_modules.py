"""Tests for PR 16-18: Conditional Module Gates for AT Tenants (RKSV, Peppol/e-Rechnung.gv.at, Payroll)."""
import pytest


def test_pos_module_blocked_without_at_rksv_capability(client, admin_headers, monkeypatch):
    # Activate Austrian profile without at_rksv
    res = client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "valid_from": "2026-01-01",
        "capabilities": {},
    })
    assert res.status_code == 200

    # POS register list should be blocked by AT gate (HTTP 403)
    pos_res = client.get("/api/pos/registers", headers=admin_headers)
    assert pos_res.status_code == 403
    assert "at_rksv" in pos_res.json()["detail"].lower() or "gesperrt" in pos_res.json()["detail"].lower()

    # Enable at_rksv capability
    res2 = client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "valid_from": "2026-01-01",
        "capabilities": {"at_rksv": True},
    })
    assert res2.status_code == 200

    # A tenant cannot self-approve a certification-dependent capability.
    pos_res2 = client.get("/api/pos/registers", headers=admin_headers)
    assert pos_res2.status_code == 403
    assert "at_rksv" in pos_res2.json()["detail"].lower()

    # Only an operator-controlled deployment approval lifts the gate.
    monkeypatch.setenv("AT_APPROVED_CAPABILITIES", "at_rksv")
    pos_res2 = client.get("/api/pos/registers", headers=admin_headers)
    if pos_res2.status_code == 403:
        assert "at_rksv" not in pos_res2.json()["detail"].lower()


def test_peppol_module_blocked_without_at_erb_capability(client, admin_headers, monkeypatch):
    # Activate Austrian profile without at_erb
    res = client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "valid_from": "2026-01-01",
        "capabilities": {},
    })
    assert res.status_code == 200

    # Peppol test endpoint should be blocked by AT gate (HTTP 403)
    peppol_res = client.post("/api/peppol/test", headers=admin_headers)
    assert peppol_res.status_code == 403
    assert "at_erb" in peppol_res.json()["detail"].lower() or "gesperrt" in peppol_res.json()["detail"].lower()

    # Enable at_erb capability
    res2 = client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "valid_from": "2026-01-01",
        "capabilities": {"at_erb": True},
    })
    assert res2.status_code == 200

    # Profile JSON alone must not lift the operator approval gate.
    peppol_res2 = client.post("/api/peppol/test", headers=admin_headers)
    assert peppol_res2.status_code == 403
    assert "at_erb" in peppol_res2.json()["detail"].lower()

    monkeypatch.setenv("AT_APPROVED_CAPABILITIES", "at_erb")
    peppol_res2 = client.post("/api/peppol/test", headers=admin_headers)
    if peppol_res2.status_code == 403:
        assert "at_erb" not in peppol_res2.json()["detail"].lower()


def test_payroll_module_blocked_without_at_payroll_capability(client, admin_headers, monkeypatch):
    # Activate Austrian profile without at_payroll
    res = client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "valid_from": "2026-01-01",
        "capabilities": {},
    })
    assert res.status_code == 200

    # Payroll runs should be blocked by AT gate (HTTP 403)
    payroll_res = client.get("/api/payroll/runs", headers=admin_headers)
    assert payroll_res.status_code == 403
    assert "at_payroll" in payroll_res.json()["detail"].lower() or "gesperrt" in payroll_res.json()["detail"].lower()

    # Enable at_payroll capability
    res2 = client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "valid_from": "2026-01-01",
        "capabilities": {"at_payroll": True},
    })
    assert res2.status_code == 200

    payroll_res2 = client.get("/api/payroll/runs", headers=admin_headers)
    assert payroll_res2.status_code == 403
    assert "at_payroll" in payroll_res2.json()["detail"].lower()

    monkeypatch.setenv("AT_APPROVED_CAPABILITIES", "at_payroll")
    payroll_res2 = client.get("/api/payroll/runs", headers=admin_headers)
    assert payroll_res2.status_code == 200
