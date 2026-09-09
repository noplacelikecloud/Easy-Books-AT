"""Tests for Austrian Asset Depreciation & Valuation (PR 13: AT-12, §§ 7, 8, 13 EStG)."""
from decimal import Decimal
import pytest
from sqlmodel import Session, select

from models import Account, FixedAsset, JournalEntry, User
from services.money import D


@pytest.fixture
def at_asset_env(client, admin_headers):
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "standard",
        "valid_from": "2026-01-01",
    })
    client.post("/api/at/install-coa", headers=admin_headers)


def _create_test_fixed_asset(session: Session, user: User, name: str, cost: Decimal) -> int:
    acc_asset = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "0400")).first()
    acc_depr = session.exec(select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "8000")).first()

    fa = FixedAsset(
        tenant_id=user.tenant_id,
        name=name,
        asset_account_id=acc_asset.id,
        accum_depr_account_id=acc_asset.id,
        depr_expense_account_id=acc_depr.id,
        acquisition_date="2026-01-15",
        acquisition_cost=cost,
        salvage_value=Decimal("0"),
        useful_life_months=60,
    )
    session.add(fa)
    session.commit()
    session.refresh(fa)
    return fa.id


def test_first_half_vs_second_half_depreciation(client, admin_headers, at_asset_env):
    """Assets commissioned in H1 receive full-year AfA; H2 receive half-year AfA (§ 7 Abs. 2 EStG)."""
    from main import app

    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        fa1_id = _create_test_fixed_asset(session, user, "Maschine H1", Decimal("10000.00"))
        fa2_id = _create_test_fixed_asset(session, user, "Maschine H2", Decimal("10000.00"))

    # Asset 1: Commissioned 2026-03-10 (First half -> Full year AfA = 2000 EUR)
    res1 = client.post("/api/at/assets/register", headers=admin_headers, json={
        "asset_id": fa1_id,
        "commissioning_date": "2026-03-10",
        "initial_cost_gross": 12000.00,
        "input_vat_deducted": 2000.00,  # 10,000 net
        "useful_life_years": 5.0,
        "depreciation_method": "linear",
    })
    assert res1.status_code == 200, res1.text
    val1 = res1.json()["valuation"]
    assert val1["half_year_rule_applied"] is False
    assert Decimal(str(val1["current_year_tax_depreciation"])) == Decimal("2000.00")
    assert Decimal(str(val1["tax_book_value"])) == Decimal("8000.00")

    # Asset 2: Commissioned 2026-08-20 (Second half -> Half year AfA = 1000 EUR)
    res2 = client.post("/api/at/assets/register", headers=admin_headers, json={
        "asset_id": fa2_id,
        "commissioning_date": "2026-08-20",
        "initial_cost_gross": 12000.00,
        "input_vat_deducted": 2000.00,  # 10,000 net
        "useful_life_years": 5.0,
        "depreciation_method": "linear",
    })
    assert res2.status_code == 200, res2.text
    val2 = res2.json()["valuation"]
    assert val2["half_year_rule_applied"] is True
    assert Decimal(str(val2["current_year_tax_depreciation"])) == Decimal("1000.00")
    assert Decimal(str(val2["tax_book_value"])) == Decimal("9000.00")


def test_gwg_immediate_writeoff_and_limit(client, admin_headers, at_asset_env):
    """Assets <= 1,000 EUR net qualify as GWG; assets > 1,000 EUR are rejected (§ 13 EStG)."""
    from main import app

    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        fa_gwg_id = _create_test_fixed_asset(session, user, "Bürosessel", Decimal("600.00"))
        fa_large_id = _create_test_fixed_asset(session, user, "High-End Server", Decimal("2500.00"))

    # Valid GWG (600 EUR net)
    res_gwg = client.post("/api/at/assets/register", headers=admin_headers, json={
        "asset_id": fa_gwg_id,
        "commissioning_date": "2026-04-01",
        "initial_cost_gross": 720.00,
        "input_vat_deducted": 120.00,
        "is_gwg": True,
    })
    assert res_gwg.status_code == 200
    val_gwg = res_gwg.json()["valuation"]
    assert val_gwg["is_gwg"] is True
    assert Decimal(str(val_gwg["current_year_tax_depreciation"])) == Decimal("600.00")
    assert Decimal(str(val_gwg["tax_book_value"])) == Decimal("0.00")

    # Invalid GWG (> 1,000 EUR)
    res_large = client.post("/api/at/assets/register", headers=admin_headers, json={
        "asset_id": fa_large_id,
        "commissioning_date": "2026-04-01",
        "initial_cost_gross": 2500.00,
        "input_vat_deducted": 0.00,
        "is_gwg": True,
    })
    assert res_large.status_code == 400
    assert "1.000,00 EUR" in res_large.text


def test_pkw_and_building_degressive_afa_blocked(client, admin_headers, at_asset_env):
    """Degressive AfA is prohibited for passenger cars (PKW) and buildings (§ 7 Abs. 1a EStG)."""
    from main import app

    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        fa_car_id = _create_test_fixed_asset(session, user, "Geschäfts-PKW", Decimal("35000.00"))

    res = client.post("/api/at/assets/register", headers=admin_headers, json={
        "asset_id": fa_car_id,
        "commissioning_date": "2026-05-15",
        "initial_cost_gross": 35000.00,
        "input_vat_deducted": 0.00,  # PKW no VAT deduction
        "useful_life_years": 8.0,
        "depreciation_method": "degressiv",
        "asset_category": "pkw",
    })
    assert res.status_code == 400
    assert "ausgeschlossen" in res.text


def test_post_annual_depreciation_run(client, admin_headers, at_asset_env):
    """Annual depreciation run posts Dr 8000 (AfA) / Cr Asset Accounts to the General Ledger."""
    from main import app

    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        fa_id = _create_test_fixed_asset(session, user, "Produktionsanlage", Decimal("50000.00"))

    client.post("/api/at/assets/register", headers=admin_headers, json={
        "asset_id": fa_id,
        "commissioning_date": "2026-02-01",
        "initial_cost_gross": 50000.00,
        "input_vat_deducted": 0.00,
        "useful_life_years": 10.0,
        "depreciation_method": "linear",
    })

    # Execute annual depreciation run for 2026
    run_res = client.post("/api/at/assets/depreciate-year?year=2026", headers=admin_headers)
    assert run_res.status_code == 200, run_res.text
    txn_id = run_res.json()["transaction_id"]

    with Session(app.state.engine) as session:
        lines = session.exec(
            select(JournalEntry).where(JournalEntry.transaction_id == txn_id)
        ).all()
        assert len(lines) == 2
        debit_line = next(l for l in lines if D(l.debit) > 0)
        credit_line = next(l for l in lines if D(l.credit) > 0)
        assert D(debit_line.debit) == Decimal("5000.00")
        assert D(credit_line.credit) == Decimal("5000.00")

    # Duplicate run must be rejected with 400
    dup_res = client.post("/api/at/assets/depreciate-year?year=2026", headers=admin_headers)
    assert dup_res.status_code == 400
    assert "bereits durchgeführt" in dup_res.text
