"""Tests for Austrian Commercial Code (UGB) Financial Statements (§§ 224, 231 UGB) (PR 11: AT-11)."""
from decimal import Decimal
import pytest
from sqlmodel import Session, select

from models import Account, Transaction, User
from services.posting import EntryInput, post_transaction


@pytest.fixture
def at_ugb_env(client, admin_headers):
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "standard",
        "vat_method": "accrual",
        "vat_filing_frequency": "monthly",
        "company_register_number": "FN 654321 b",
        "company_register_court": "HG Wien",
        "registered_seat": "Wien",
        "valid_from": "2026-01-01",
    })
    client.post("/api/at/install-coa", headers=admin_headers)


def test_ugb_balance_sheet_and_income_statement_profit(client, admin_headers, at_ugb_env):
    """Clean commercial year with profit produces aligned § 224 Balance Sheet and § 231 P&L."""
    from main import app

    # 1. Post initial share capital: 10,000 EUR (Dr 2800 Bank / Cr 9000 Stammkapital)
    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        acc_bank = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "2800")).first()
        acc_equity = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "9000")).first()
        acc_ar = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "2000")).first()
        acc_rev = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "4000")).first()
        acc_vat = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "3500")).first()
        acc_exp = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "5000")).first()
        acc_ap = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "3000")).first()

        # Opening capital
        post_transaction(
            session=session,
            user=user,
            date="2026-01-02",
            description="Stammkapitaleinzahlung",
            entries=[
                EntryInput(account_id=acc_bank.id, debit=Decimal("10000.00")),
                EntryInput(account_id=acc_equity.id, credit=Decimal("10000.00")),
            ],
            voucher_type="JV",
        )

        # Revenue: 8,000 net + 1,600 VAT = 9,600 AR
        post_transaction(
            session=session,
            user=user,
            date="2026-03-15",
            description="Ausgangsrechnung AR-101",
            entries=[
                EntryInput(account_id=acc_ar.id, debit=Decimal("9600.00")),
                EntryInput(account_id=acc_rev.id, credit=Decimal("8000.00")),
                EntryInput(account_id=acc_vat.id, credit=Decimal("1600.00")),
            ],
            voucher_type="SL",
        )

        # Expense: 3,000 Material (Dr 5000 / Cr 3000)
        post_transaction(
            session=session,
            user=user,
            date="2026-04-10",
            description="Eingangsrechnung ER-201",
            entries=[
                EntryInput(account_id=acc_exp.id, debit=Decimal("3000.00")),
                EntryInput(account_id=acc_ap.id, credit=Decimal("3000.00")),
            ],
            voucher_type="PI",
        )
        session.commit()

    # 2. Query GuV for 2026
    guv_res = client.get("/api/at/reports/income-statement?start_date=2026-01-01&end_date=2026-12-31", headers=admin_headers)
    assert guv_res.status_code == 200, guv_res.text
    guv = guv_res.json()

    assert Decimal(str(guv["net_income_current"])) == Decimal("5000.00")
    assert Decimal(str(guv["annual_profit"])) == Decimal("5000.00")

    # 3. Query Bilanz as of 2026-12-31
    bs_res = client.get("/api/at/reports/balance-sheet?as_of_date=2026-12-31", headers=admin_headers)
    assert bs_res.status_code == 200, bs_res.text
    bs = bs_res.json()

    # Total Aktiva: Bank (10,000) + AR (9,600) = 19,600
    assert Decimal(str(bs["total_aktiva"])) == Decimal("19600.00")
    # Total Passiva: Stammkapital (10,000) + Bilanzgewinn (5,000) + AP (3,000) + USt (1,600) = 19,600
    assert Decimal(str(bs["total_passiva"])) == Decimal("19600.00")
    assert bs["is_balanced"] is True
    assert bs["has_negative_equity"] is False


def test_ugb_balance_sheet_negative_equity(client, admin_headers, at_ugb_env):
    """When losses exceed equity, § 225 Abs. 1 UGB activates offset on the asset side."""
    from main import app

    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        acc_bank = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "2800")).first()
        acc_equity = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "9000")).first()
        acc_exp = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "5000")).first()
        acc_ap = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "3000")).first()

        # Stammkapital: 10,000 EUR
        post_transaction(
            session=session,
            user=user,
            date="2026-01-02",
            description="Stammkapital",
            entries=[
                EntryInput(account_id=acc_bank.id, debit=Decimal("10000.00")),
                EntryInput(account_id=acc_equity.id, credit=Decimal("10000.00")),
            ],
            voucher_type="JV",
        )

        # Huge expense: 30,000 EUR loss
        post_transaction(
            session=session,
            user=user,
            date="2026-06-01",
            description="Hoher Projektaufwand",
            entries=[
                EntryInput(account_id=acc_exp.id, debit=Decimal("30000.00")),
                EntryInput(account_id=acc_ap.id, credit=Decimal("30000.00")),
            ],
            voucher_type="PI",
        )
        session.commit()

    bs_res = client.get("/api/at/reports/balance-sheet?as_of_date=2026-12-31", headers=admin_headers)
    assert bs_res.status_code == 200
    bs = bs_res.json()

    # Net equity is 10,000 - 30,000 = -20,000 EUR
    assert Decimal(str(bs["eigenkapital_computed"])) == Decimal("-20000.00")
    assert bs["has_negative_equity"] is True

    # Under § 225 UGB:
    # Aktiva has asset offset "Nicht durch Eigenkapital gedeckter Fehlbetrag" = 20,000 EUR
    # Passiva equity is presented as 0.00 EUR
    # Aktiva = Bank (10,000) + Fehlbetrag (20,000) = 30,000
    # Passiva = AP (30,000) = 30,000
    assert Decimal(str(bs["total_aktiva"])) == Decimal("10000.00")
    assert Decimal(str(bs["total_passiva"])) == Decimal("10000.00")
    assert bs["is_balanced"] is True


def test_at_closing_checklist(client, admin_headers, at_ugb_env):
    """Closing checklist validates UGB readiness and reports item statuses."""
    res = client.get("/api/at/reports/closing-checklist?year=2026", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["fiscal_year"] == 2026
    assert "items" in data
    assert len(data["items"]) >= 4
    item_ids = [i["id"] for i in data["items"]]
    assert "balance_sheet_balanced" in item_ids
    assert "equity_status" in item_ids


def test_ugb_reports_with_alphanumeric_account_codes(client, admin_headers, at_ugb_env):
    """Accounts with alphanumeric codes like '4A00' or '4-REV' do not crash GuV with ValueError."""
    from main import app
    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        acc_bank = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "2800")).first()
        custom_rev = Account(
            tenant_id=user.tenant_id,
            code="4A-REV",
            name="Custom Alphanumeric Revenue",
            type="Revenue",
        )
        session.add(custom_rev)
        session.flush()

        post_transaction(
            session=session,
            user=user,
            date="2026-07-01",
            description="Alpha Revenue Sale",
            entries=[
                EntryInput(account_id=acc_bank.id, debit=Decimal("500.00")),
                EntryInput(account_id=custom_rev.id, credit=Decimal("500.00")),
            ],
            voucher_type="JV",
        )
        session.commit()

    res = client.get("/api/at/reports/income-statement?start_date=2026-01-01&end_date=2026-12-31", headers=admin_headers)
    assert res.status_code == 200, res.text
    guv = res.json()
    assert Decimal(str(guv["net_income_current"])) >= Decimal("500.00")
