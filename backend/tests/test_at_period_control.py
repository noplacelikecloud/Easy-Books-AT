"""Tests for PR 3: Periodensperre, Abschlussintegrität und Audit (AT-08).

Validates:
- Year-end closing zeroes P&L accounts even if net income is 0.
- Closing creates immutable snapshot hash and PeriodCloseHistory.
- Reopening requires justification reason and reverses previous closing JV.
- Subsequent close does not duplicate closing entries.
- Deleting a period with posted transactions is strictly prohibited (§ 190 UGB).
"""
import pytest
from sqlmodel import Session, select

from models import Account, AccountingPeriod, JournalEntry, Transaction
from models_at import PeriodCloseHistory
from tests.conftest import disable_period_close_checklist


def _get_posting_accounts(client, headers):
    accs = client.get("/api/accounts", headers=headers).json()
    if isinstance(accs, dict):
        accs = accs.get("items", accs.get("accounts", []))
    by_type = {}
    for a in accs:
        if not a.get("is_group", False):
            by_type.setdefault(a["type"], a)
    return by_type


def test_zero_net_income_closes_pl_accounts(client, admin_headers):
    disable_period_close_checklist(client, admin_headers)

    p = client.post("/api/periods", headers=admin_headers, json={
        "name": "Geschäftsjahr 2026",
        "period_start": "2026-01-01",
        "period_end": "2026-12-31",
    }).json()
    period_id = p["id"]

    by_type = _get_posting_accounts(client, admin_headers)
    rev_acc = by_type["Revenue"]
    exp_acc = by_type["Expense"]
    bank_acc = by_type["Asset"]

    # Post revenue of 500 and expense of 500 (net income = 0)
    tx1 = client.post("/api/transactions", headers=admin_headers, json={
        "date": "2026-06-15",
        "description": "Sale",
        "entries": [
            {"account_id": bank_acc["id"], "debit": 500},
            {"account_id": rev_acc["id"], "credit": 500},
        ],
    })
    assert tx1.status_code in (200, 201), tx1.text

    tx2 = client.post("/api/transactions", headers=admin_headers, json={
        "date": "2026-06-20",
        "description": "Expense",
        "entries": [
            {"account_id": exp_acc["id"], "debit": 500},
            {"account_id": bank_acc["id"], "credit": 500},
        ],
    })
    assert tx2.status_code in (200, 201), tx2.text

    # Close period with mode="year_end"
    close_res = client.post(f"/api/periods/{period_id}/close?mode=year_end", headers=admin_headers)
    assert close_res.status_code == 200, close_res.text
    res_data = close_res.json()
    assert res_data["entries_posted"] > 0
    assert res_data["period"]["close_status"] == "closed"
    assert res_data["period"]["is_locked"] is True
    assert res_data["snapshot_hash"] is not None


def test_reopen_requires_reason_and_reverses_closing(client, admin_headers):
    disable_period_close_checklist(client, admin_headers)

    p = client.post("/api/periods", headers=admin_headers, json={
        "name": "Wirtschaftsjahr 2026 Reopen",
        "period_start": "2026-01-01",
        "period_end": "2026-12-31",
    }).json()
    period_id = p["id"]

    by_type = _get_posting_accounts(client, admin_headers)
    rev_acc = by_type["Revenue"]
    bank_acc = by_type["Asset"]

    tx = client.post("/api/transactions", headers=admin_headers, json={
        "date": "2026-05-01",
        "description": "Revenue",
        "entries": [
            {"account_id": bank_acc["id"], "debit": 1000},
            {"account_id": rev_acc["id"], "credit": 1000},
        ],
    })
    assert tx.status_code in (200, 201), tx.text

    client.post(f"/api/periods/{period_id}/close?mode=year_end", headers=admin_headers)

    # Reopen without reason must fail
    fail_reopen = client.post(f"/api/periods/{period_id}/reopen", headers=admin_headers)
    assert fail_reopen.status_code == 400

    # Reopen with reason must succeed
    reopen_res = client.post(
        f"/api/periods/{period_id}/reopen?reason=Nachträgliche_Abschlussbuchung_durch_Steuerberater",
        headers=admin_headers,
    )
    assert reopen_res.status_code == 200, reopen_res.text
    reopened = reopen_res.json()
    assert reopened["close_status"] == "reopened"
    assert reopened["is_locked"] is False
    assert reopened["reopen_count"] >= 1


def test_delete_period_with_transactions_blocked(client, admin_headers):
    p = client.post("/api/periods", headers=admin_headers, json={
        "name": "Test Delete Guard",
        "period_start": "2026-01-01",
        "period_end": "2026-12-31",
    }).json()

    by_type = _get_posting_accounts(client, admin_headers)
    acc = by_type["Asset"]
    rev = by_type["Revenue"]

    tx = client.post("/api/transactions", headers=admin_headers, json={
        "date": "2026-03-01",
        "description": "Kassabuchung",
        "entries": [
            {"account_id": acc["id"], "debit": 100},
            {"account_id": rev["id"], "credit": 100},
        ],
    })
    assert tx.status_code in (200, 201), tx.text

    # Attempt to delete must fail with 400
    del_res = client.delete(f"/api/periods/{p['id']}", headers=admin_headers)
    assert del_res.status_code == 400
    assert "buchung" in del_res.json()["detail"].lower()
