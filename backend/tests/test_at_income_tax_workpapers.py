"""Tests for Austrian Corporate Income Tax (KSt) Workpaper & Mehr-/Weniger-Rechnung (PR 15: AT-10)."""
from decimal import Decimal
import pytest
from sqlmodel import Session, select

from models import Account, User
from services.posting import EntryInput, post_transaction


@pytest.fixture
def at_corp_tax_env(client, admin_headers):
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "standard",
        "valid_from": "2026-01-01",
    })
    client.post("/api/at/install-coa", headers=admin_headers)


def test_corporate_tax_calculation_and_mwr(client, admin_headers, at_corp_tax_env):
    """Test 23% statutory KSt computation, Mehr-/Weniger-Rechnung additions and Mindest-KSt."""
    from main import app

    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        acc_bank = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "2800")).first()
        acc_rev = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "4000")).first()
        acc_exp = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "5000")).first()

        # Revenue: 50,000 EUR
        post_transaction(
            session=session,
            user=user,
            date="2026-05-01",
            description="Erlöse 2026",
            entries=[
                EntryInput(account_id=acc_bank.id, debit=Decimal("50000.00")),
                EntryInput(account_id=acc_rev.id, credit=Decimal("50000.00")),
            ],
            voucher_type="CR",
        )

        # Operating Expenses: 20,000 EUR -> Commercial UGB Profit = 30,000 EUR
        post_transaction(
            session=session,
            user=user,
            date="2026-06-01",
            description="Betriebsaufwand",
            entries=[
                EntryInput(account_id=acc_exp.id, debit=Decimal("20000.00")),
                EntryInput(account_id=acc_bank.id, credit=Decimal("20000.00")),
            ],
            voucher_type="CP",
        )
        session.commit()

    # Query KSt workpaper with MWR additions:
    # + 2,000 EUR non-deductible expenses (50% meals / fines)
    # + 3,000 EUR luxury car addback
    # Taxable income = 30,000 + 2,000 + 3,000 = 35,000 EUR
    # 23% KSt = 35,000 * 0.23 = 8,050 EUR
    res = client.get(
        "/api/at/tax/corporate-workpaper?year=2026&non_deductible_expenses=2000.00&luxury_car_addback=3000.00",
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["statutory_rate_pct"] == 23.0
    assert Decimal(str(data["ugb_profit"])) == Decimal("30000.00")
    assert Decimal(str(data["taxable_income"])) == Decimal("35000.00")
    assert Decimal(str(data["calculated_kst"])) == Decimal("8050.00")
    assert Decimal(str(data["final_tax_liability"])) == Decimal("8050.00")


def test_corporate_tax_minimum_kst_on_loss(client, admin_headers, at_corp_tax_env):
    """A loss-making GmbH must pay Mindest-KSt of 500 EUR (§ 24 Abs. 4 KStG)."""
    res = client.get("/api/at/tax/corporate-workpaper?year=2026", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert Decimal(str(data["calculated_kst"])) == Decimal("0.00")
    assert Decimal(str(data["mindest_kst"])) == Decimal("500.00")
    assert Decimal(str(data["final_tax_liability"])) == Decimal("500.00")
