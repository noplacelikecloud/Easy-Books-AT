"""Tests for Austrian Cash Accounting (Einnahmen-Ausgaben-Rechnung) & Form E1a (PR 12: AT-11)."""
from decimal import Decimal
import pytest
from sqlmodel import Session, select

from models import Account, User
from services.posting import EntryInput, post_transaction


@pytest.fixture
def at_ear_env(client, admin_headers):
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "sole_proprietor",
        "profit_method": "ear",
        "vat_status": "standard",
        "vat_method": "cash",
        "vat_filing_frequency": "quarterly",
        "valid_from": "2026-01-01",
    })
    client.post("/api/at/install-coa", headers=admin_headers)


def test_ear_calculation_and_e1a_positions(client, admin_headers, at_ear_env):
    """Test EAR and Form E1a lines computation for sole proprietor with private shares."""
    from main import app

    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        acc_bank = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "2800")).first()
        acc_rev20 = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "4000")).first()
        acc_rev10 = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "4010")).first()
        # EKR: 5100 Verbrauch Rohstoffe (Material, KZ 9100),
        #      5700 Bezogene Leistungen (Fremdleistungen, KZ 9110)
        acc_mat = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "5100")).first()
        acc_fremd = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "5700")).first()

        # 1. Cash Revenue 20%: 6,000 EUR
        post_transaction(
            session=session,
            user=user,
            date="2026-02-10",
            description="Bar-/Bankerlös 20%",
            entries=[
                EntryInput(account_id=acc_bank.id, debit=Decimal("6000.00")),
                EntryInput(account_id=acc_rev20.id, credit=Decimal("6000.00")),
            ],
            voucher_type="CR",
        )

        # 2. Cash Revenue 10%: 2,000 EUR
        post_transaction(
            session=session,
            user=user,
            date="2026-03-12",
            description="Bar-/Bankerlös 10%",
            entries=[
                EntryInput(account_id=acc_bank.id, debit=Decimal("2000.00")),
                EntryInput(account_id=acc_rev10.id, credit=Decimal("2000.00")),
            ],
            voucher_type="CR",
        )

        # 3. Cash Expenses: 2,500 Material + 1,500 Fremdleistung = 4,000
        post_transaction(
            session=session,
            user=user,
            date="2026-04-05",
            description="Ausgaben Einkauf & Subunternehmer",
            entries=[
                EntryInput(account_id=acc_mat.id, debit=Decimal("2500.00")),
                EntryInput(account_id=acc_fremd.id, debit=Decimal("1500.00")),
                EntryInput(account_id=acc_bank.id, credit=Decimal("4000.00")),
            ],
            voucher_type="CP",
        )
        session.commit()

    # Query EAR with 500 EUR private share additions (e.g. Kfz-Privatanteil)
    res = client.get("/api/at/ear?year=2026&private_share_adjustments=500.00", headers=admin_headers)
    assert res.status_code == 200, res.text
    ear = res.json()

    pos = {p["kz"]: Decimal(str(p["amount"])) for p in ear["positions"] if p["kz"]}

    assert pos["9040"] == Decimal("8000.00")
    assert pos["9050"] == Decimal("0.00")

    assert pos["9100"] == Decimal("2500.00")  # Material
    assert pos["9110"] == Decimal("1500.00")  # Fremdleistungen

    assert Decimal(str(ear["preliminary_profit"])) == Decimal("4000.00")
    assert pos["9260"] == Decimal("500.00")   # Private share adjustment
    assert pos["9290"] == Decimal("4500.00")  # 4000 + 500 = 4500 taxable income
