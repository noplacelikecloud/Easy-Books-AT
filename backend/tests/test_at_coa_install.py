"""Installing the Austrian EKR chart must replace the generic chart, not layer on it.

Every tenant is seeded with the generic English chart, whose codes collide with
the EKR at completely different meanings (2000 is Accounts Payable there and
Forderungen aus Lieferungen und Leistungen here). The old installer only created
codes that did not exist yet, so those English accounts survived and the semantic
roles were bound to them — `accounts_receivable` ended up on a liability account
called "Accounts Payable", and finalized Austrian invoices debited it.
"""
from decimal import Decimal

from sqlmodel import Session, select

from models import Account, JournalEntry, Transaction, User
from services.posting import EntryInput, post_transaction


def _accounts(client, headers):
    return {a["code"]: a for a in client.get("/api/accounts?limit=500", headers=headers).json()["items"]}


def test_install_realigns_colliding_english_accounts(client, admin_headers):
    before = _accounts(client, admin_headers)
    assert before["2000"]["name"] == "Accounts Payable"   # generic seed
    assert before["2000"]["type"] == "Liability"

    res = client.post("/api/at/install-coa", headers=admin_headers)
    assert res.status_code == 200, res.text
    assert res.json()["accounts_realigned"] > 0

    after = _accounts(client, admin_headers)
    assert after["2000"]["name"] == "Forderungen aus Lieferungen und Leistungen Inland"
    assert after["2000"]["type"] == "Asset"
    assert after["2000"]["party_type"] == "customer"
    # 2510 was "Lease Liability" in the generic chart; the EKR keeps VAT rate
    # splits off that number entirely, so it must not have been reused.
    assert after["2510"]["name"] == "Lease Liability"
    assert after["2501"]["name"].startswith("Vorsteuer 10%")


def test_install_deactivates_unposted_leftovers_but_keeps_history(client, admin_headers):
    from main import app

    # Post to one generic account so it counts as real bookkeeping history.
    with Session(app.state.engine) as s:
        user = s.exec(select(User)).first()
        # 1010 "Bank" and 3100 "Retained Earnings" have no EKR counterpart in
        # the template (EKR keeps bank on 2800 and Bilanzgewinn on 9390), so
        # posting to them collides with nothing.
        cash = s.exec(select(Account).where(
            Account.tenant_id == user.tenant_id, Account.code == "1010")).first()
        other = s.exec(select(Account).where(
            Account.tenant_id == user.tenant_id, Account.code == "3100")).first()
        post_transaction(
            session=s, user=user, date="2026-02-01", description="Einlage",
            entries=[EntryInput(account_id=cash.id, debit=Decimal("100")),
                     EntryInput(account_id=other.id, credit=Decimal("100"))],
            voucher_type="JV",
        )
        s.commit()

    res = client.post("/api/at/install-coa", headers=admin_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert "1010" in body["legacy_kept_with_history"]  # posted → kept
    assert "3100" in body["legacy_kept_with_history"]
    assert "2200" in body["legacy_deactivated"]        # unposted → retired

    accounts = _accounts(client, admin_headers)
    assert accounts["1010"]["is_active"] is True
    assert accounts["2200"]["is_active"] is False


def test_install_refuses_when_a_colliding_account_is_already_posted(client, admin_headers):
    """Renaming 2000 from Accounts Payable to Forderungen under existing journal
    entries would silently reinterpret them, so the install must refuse."""
    from main import app

    with Session(app.state.engine) as s:
        user = s.exec(select(User)).first()
        ap = s.exec(select(Account).where(
            Account.tenant_id == user.tenant_id, Account.code == "2000")).first()
        exp = s.exec(select(Account).where(
            Account.tenant_id == user.tenant_id, Account.code == "5000")).first()
        post_transaction(
            session=s, user=user, date="2026-02-01", description="Eingangsrechnung",
            entries=[EntryInput(account_id=exp.id, debit=Decimal("250")),
                     EntryInput(account_id=ap.id, credit=Decimal("250"))],
            voucher_type="JV",
        )
        s.commit()

    res = client.post("/api/at/install-coa", headers=admin_headers)
    assert res.status_code == 409, res.text
    assert "2000" in res.json()["detail"]

    # And nothing was changed on the way out.
    assert _accounts(client, admin_headers)["2000"]["name"] == "Accounts Payable"


def test_finalized_at_invoice_debits_the_receivable_account(client, admin_headers):
    """End-to-end: the defect this whole module guards against."""
    from main import app

    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh", "profit_method": "ugb_double_entry",
        "vat_status": "regular", "vat_method": "accrual",
        "vat_filing_frequency": "monthly", "valid_from": "2026-01-01",
    })
    cust = client.post("/api/customers", headers=admin_headers,
                       json={"name": "Kunde GmbH", "is_business": False}).json()
    inv = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"], "issue_date": "2026-03-01", "due_date": "2026-03-15",
        "currency": "EUR", "exchange_rate": 1.0, "gst_rate": 0,
        "lines": [{"description": "Beratung", "qty": 1, "rate": 300.00}],
    }).json()
    fin = client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers)
    assert fin.status_code == 200, fin.text

    with Session(app.state.engine) as s:
        txn = s.exec(select(Transaction).where(Transaction.voucher_type == "SL")).one()
        rows = s.exec(select(JournalEntry).where(JournalEntry.transaction_id == txn.id)).all()
        booked = {s.get(Account, r.account_id).code: (r.debit, r.credit) for r in rows}

    assert booked["2000"][0] == Decimal("300")   # Soll Forderungen L&L
    assert booked["4000"][1] == Decimal("300")   # Haben Umsatzerlöse 20%
