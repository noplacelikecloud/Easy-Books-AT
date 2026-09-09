"""Regression tests for two GL posting defects found in the 2026-09 audit.

1. Currency conversion rounded each voucher leg on its own, so Σdebit could
   miss Σcredit by a cent and the whole document refused to post (HTTP 400
   "Journal not balanced"). At a typical rate that hit roughly a quarter of
   all amounts.
2. Editing a posted invoice/bill dated the reversal "today" while re-posting
   the replacement on the document date, so the original amount stayed in the
   document's own period and was pulled out of the current one. Every
   statement between the two dates was wrong while the year-to-date total
   still looked right — which is why no existing test caught it.
"""
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from models import Account, JournalEntry, Transaction


# A rate and net amount where money(net*rate) + money(vat*rate) != money(gross*rate).
NASTY_RATE = 1.0854
NASTY_NET = 100.06


def _legs(engine, jv_number: str):
    with Session(engine) as s:
        txn = s.exec(select(Transaction).where(Transaction.jv_number == jv_number)).one()
        rows = s.exec(select(JournalEntry).where(JournalEntry.transaction_id == txn.id)).all()
        return txn, [(s.get(Account, r.account_id).code, r.debit, r.credit) for r in rows]


def test_fx_invoice_posts_and_ar_carries_the_document_total(client, admin_headers):
    from main import app

    res = client.post("/api/invoices", headers=admin_headers, json={
        "customer_name": "Kunde", "issue_date": "2026-03-02", "gst_rate": 20,
        "currency": "EUR", "exchange_rate": NASTY_RATE,
        "lines": [{"description": "Beratung", "qty": 1, "rate": NASTY_NET}],
    })
    assert res.status_code in (200, 201), res.text

    with Session(app.state.engine) as s:
        txn = s.get(Transaction, res.json()["transaction_id"]) if res.json().get("transaction_id") else \
            s.exec(select(Transaction).where(Transaction.voucher_type == "SL")).first()
        rows = s.exec(select(JournalEntry).where(JournalEntry.transaction_id == txn.id)).all()
        debits = sum((r.debit for r in rows), Decimal("0"))
        credits = sum((r.credit for r in rows), Decimal("0"))
        assert debits == credits, f"{debits} != {credits}"
        # AR keeps the exact document total in base currency, so a later
        # payment clears it without leaving a stray cent behind.
        ar = [r for r in rows if r.debit > 0]
        assert len(ar) == 1
        assert ar[0].debit == Decimal("130.32")


def test_fx_bill_posts_balanced(client, admin_headers):
    from main import app

    res = client.post("/api/bills", headers=admin_headers, json={
        "vendor_name": "Lieferant", "bill_date": "2026-03-02", "gst_rate": 20,
        "currency": "EUR", "exchange_rate": NASTY_RATE,
        "lines": [{"description": "Material", "qty": 1, "rate": NASTY_NET}],
    })
    assert res.status_code in (200, 201), res.text

    with Session(app.state.engine) as s:
        txn = s.exec(select(Transaction).where(Transaction.voucher_type == "PR")).first()
        rows = s.exec(select(JournalEntry).where(JournalEntry.transaction_id == txn.id)).all()
        assert sum((r.debit for r in rows), Decimal("0")) == sum((r.credit for r in rows), Decimal("0"))
        ap = [r for r in rows if r.credit > 0]
        assert len(ap) == 1 and ap[0].credit == Decimal("130.32")


@pytest.mark.parametrize("rate", [1.0854, 0.9137, 1.35, 3.75])
def test_fx_invoice_posts_across_many_amounts(client, admin_headers, rate):
    """Sweep the cent range that used to fail — none of it may 400."""
    for cents in range(0, 40):
        res = client.post("/api/invoices", headers=admin_headers, json={
            "customer_name": "Kunde", "issue_date": "2026-03-02", "gst_rate": 20,
            "currency": "EUR", "exchange_rate": rate,
            "lines": [{"description": "L", "qty": 1, "rate": 100 + cents / 100}],
        })
        assert res.status_code in (200, 201), f"rate={rate} rate_amt={100 + cents / 100}: {res.text}"


def test_editing_a_posted_invoice_keeps_both_legs_in_its_own_period(client, admin_headers):
    """Reversal and replacement must share the invoice date, so the period the
    invoice belongs to shows the edited amount and nothing else."""
    from main import app

    body = {"customer_name": "K", "issue_date": "2026-01-15", "gst_rate": 0,
            "lines": [{"description": "Leistung", "qty": 1, "rate": 1000}]}
    inv = client.post("/api/invoices", headers=admin_headers, json=body)
    assert inv.status_code in (200, 201), inv.text
    inv_id = inv.json()["id"]

    body["lines"][0]["rate"] = 1200
    upd = client.put(f"/api/invoices/{inv_id}", headers=admin_headers, json=body)
    assert upd.status_code == 200, upd.text

    with Session(app.state.engine) as s:
        dates = {t.jv_number: t.date for t in s.exec(select(Transaction)).all()}
    assert set(dates.values()) == {"2026-01-15"}, dates

    pl = client.get(
        "/api/reports/income-statement?start=2026-01-01&end=2026-01-31", headers=admin_headers
    ).json()
    assert Decimal(str(pl["totals"]["revenue"])) == Decimal("1200")


def test_editing_a_posted_bill_keeps_both_legs_in_its_own_period(client, admin_headers):
    from main import app

    body = {"vendor_name": "L", "bill_date": "2026-01-15", "gst_rate": 0,
            "lines": [{"description": "Material", "qty": 1, "rate": 500}]}
    bill = client.post("/api/bills", headers=admin_headers, json=body)
    assert bill.status_code in (200, 201), bill.text

    body["lines"][0]["rate"] = 700
    upd = client.put(f"/api/bills/{bill.json()['id']}", headers=admin_headers, json=body)
    assert upd.status_code == 200, upd.text

    with Session(app.state.engine) as s:
        dates = [t.date for t in s.exec(select(Transaction)).all()]
    assert set(dates) == {"2026-01-15"}, dates
