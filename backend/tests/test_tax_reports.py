"""
Tests for /api/reports/tax-summary and tax reporting correctness (PR 1 / AT-03).
Verifies:
1. Account 1200 (Inventory) is NEVER counted as input tax.
2. Output tax and input tax properly net debits and credits (reversals, credit notes).
3. Tax accounts are resolved via TaxCode.
4. Pakistan ITO tax slabs are isolated to Pakistan tenants only.
5. CIT worksheet defaults to 23% for Austrian tenants.
"""
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from db import get_session
from main import app


@pytest.fixture(name="client")
def client_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def _override():
        with Session(engine) as session:
            yield session

    app.state.engine = engine
    app.dependency_overrides[get_session] = _override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
    if hasattr(app.state, "engine"):
        delattr(app.state, "engine")
    engine.dispose()


def _auth(client: TestClient, email: str = "tax@test.local", business_model: str = "trader") -> dict:
    client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Tax Tester",
            "company_name": "Tax Test GmbH",
            "business_model": business_model,
        },
    )
    r = client.post(
        "/api/auth/login", data={"username": email, "password": "password123"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_inventory_account_1200_never_treated_as_input_tax(client: TestClient):
    """Befund AT-03: Account 1200 (Finished Goods / Raw Materials) must NOT appear as input tax."""
    auth = _auth(client, "inv1200@test.local", business_model="trader")
    accounts = client.get("/api/accounts", headers=auth).json()["items"]
    tenant_id = accounts[0]["tenant_id"]

    # Post a debit of 5000 to account 1200 (e.g. Finished Goods Inventory purchase / stock receipt)
    # and a debit of 1000 to account 1250 (actual input VAT)
    acct_1200 = next(a for a in accounts if a["code"] == "1200")
    acct_1250 = next(a for a in accounts if a["code"] == "1250")
    acct_bank = next(a for a in accounts if a["code"] == "1010")

    r = client.post(
        "/api/transactions",
        headers=auth,
        json={
            "tenant_id": tenant_id,
            "date": "2026-05-10",
            "description": "Stock purchase with input tax",
            "entries": [
                {"tenant_id": tenant_id, "account_id": acct_1200["id"], "debit": 5000, "credit": 0},
                {"tenant_id": tenant_id, "account_id": acct_1250["id"], "debit": 1000, "credit": 0},
                {"tenant_id": tenant_id, "account_id": acct_bank["id"], "debit": 0, "credit": 6000},
            ],
        },
    )
    assert r.status_code == 200, r.text

    tax_rep = client.get(
        "/api/reports/tax-summary?start=2026-05-01&end=2026-05-31",
        headers=auth,
    ).json()

    # Input tax must ONLY be 1000 from account 1250, NOT 6000!
    assert Decimal(str(tax_rep["gst"]["input_gst"])) == Decimal("1000.00")


def test_output_tax_and_input_tax_netting_with_reversals(client: TestClient):
    """Befund AT-03: Tax accounts must net credit and debit (e.g. credit notes, cancellations)."""
    auth = _auth(client, "netting@test.local", business_model="trader")
    accounts = client.get("/api/accounts", headers=auth).json()["items"]
    tenant_id = accounts[0]["tenant_id"]

    acct_2200 = next(a for a in accounts if a["code"] == "2200")  # Output tax (liability)
    acct_1250 = next(a for a in accounts if a["code"] == "1250")  # Input tax (asset)
    acct_1100 = next(a for a in accounts if a["code"] == "1100")  # AR
    acct_2000 = next(a for a in accounts if a["code"] == "2000")  # AP
    acct_rev = next(a for a in accounts if a["code"] == "4000")   # Sales
    acct_exp = next(a for a in accounts if a["code"] == "5000")   # Expense

    # 1. Invoice: Sale 1000 + 200 output tax
    r1 = client.post(
        "/api/transactions",
        headers=auth,
        json={
            "tenant_id": tenant_id,
            "date": "2026-06-05",
            "description": "Invoice sale",
            "entries": [
                {"tenant_id": tenant_id, "account_id": acct_1100["id"], "debit": 1200, "credit": 0},
                {"tenant_id": tenant_id, "account_id": acct_rev["id"], "debit": 0, "credit": 1000},
                {"tenant_id": tenant_id, "account_id": acct_2200["id"], "debit": 0, "credit": 200},
            ],
        },
    )
    assert r1.status_code == 200
    tx1_id = r1.json()["id"]

    # Check tax summary before credit note: output = 200
    rep1 = client.get("/api/reports/tax-summary?start=2026-06-01&end=2026-06-30", headers=auth).json()
    assert Decimal(str(rep1["gst"]["output_gst"])) == Decimal("200.00")

    # 2. Customer credit note in the same period (debits 2200 by 200)
    r_cn = client.post(
        "/api/transactions",
        headers=auth,
        json={
            "tenant_id": tenant_id,
            "date": "2026-06-20",
            "description": "Credit note reversal",
            "entries": [
                {"tenant_id": tenant_id, "account_id": acct_rev["id"], "debit": 1000, "credit": 0},
                {"tenant_id": tenant_id, "account_id": acct_2200["id"], "debit": 200, "credit": 0},
                {"tenant_id": tenant_id, "account_id": acct_1100["id"], "debit": 0, "credit": 1200},
            ],
        },
    )
    assert r_cn.status_code == 200

    # Tax summary after credit note must net to 0 (200 credit - 200 debit = 0), NOT stay at 200!
    rep2 = client.get("/api/reports/tax-summary?start=2026-06-01&end=2026-06-30", headers=auth).json()
    assert Decimal(str(rep2["gst"]["output_gst"])) == Decimal("0.00")

    # 3. Input tax netting: Purchase with 100 input tax, then vendor return with 30 credit
    client.post(
        "/api/transactions",
        headers=auth,
        json={
            "tenant_id": tenant_id,
            "date": "2026-06-10",
            "description": "Bill purchase",
            "entries": [
                {"tenant_id": tenant_id, "account_id": acct_exp["id"], "debit": 500, "credit": 0},
                {"tenant_id": tenant_id, "account_id": acct_1250["id"], "debit": 100, "credit": 0},
                {"tenant_id": tenant_id, "account_id": acct_2000["id"], "debit": 0, "credit": 600},
            ],
        },
    )
    client.post(
        "/api/transactions",
        headers=auth,
        json={
            "tenant_id": tenant_id,
            "date": "2026-06-12",
            "description": "Vendor credit note",
            "entries": [
                {"tenant_id": tenant_id, "account_id": acct_2000["id"], "debit": 180, "credit": 0},
                {"tenant_id": tenant_id, "account_id": acct_exp["id"], "debit": 0, "credit": 150},
                {"tenant_id": tenant_id, "account_id": acct_1250["id"], "debit": 0, "credit": 30},
            ],
        },
    )

    rep3 = client.get("/api/reports/tax-summary?start=2026-06-01&end=2026-06-30", headers=auth).json()
    # Net input tax = 100 - 30 = 70.00
    assert Decimal(str(rep3["gst"]["input_gst"])) == Decimal("70.00")
    # Net payable = 0 - 70 = -70.00 (credit/receivable)
    assert Decimal(str(rep3["gst"]["net_gst_payable"])) == Decimal("-70.00")


def test_tax_accounts_resolved_via_tax_code(client: TestClient):
    """Tax accounts are dynamically resolved via TaxCode gl_account_id."""
    auth = _auth(client, "taxcode_res@test.local", business_model="trader")
    accounts = client.get("/api/accounts", headers=auth).json()["items"]
    tenant_id = accounts[0]["tenant_id"]

    # Create custom tax account
    r_acct = client.post(
        "/api/accounts",
        headers=auth,
        json={"name": "Custom Austrian VAT 20%", "type": "Liability", "code": "3800"},
    )
    assert r_acct.status_code in (200, 201)
    custom_acct_id = r_acct.json()["id"]

    # Create TaxCode pointing to custom account
    r_tc = client.post(
        "/api/tax-codes",
        headers=auth,
        json={"code": "AT20", "name": "Austrian VAT 20%", "rate": 20, "type": "output", "gl_account_id": custom_acct_id},
    )
    assert r_tc.status_code == 201

    # Post JV with custom account
    acct_1100 = next(a for a in accounts if a["code"] == "1100")
    acct_rev = next(a for a in accounts if a["code"] == "4000")
    client.post(
        "/api/transactions",
        headers=auth,
        json={
            "tenant_id": tenant_id,
            "date": "2026-07-01",
            "description": "Sale with AT20",
            "entries": [
                {"tenant_id": tenant_id, "account_id": acct_1100["id"], "debit": 120, "credit": 0},
                {"tenant_id": tenant_id, "account_id": acct_rev["id"], "debit": 0, "credit": 100},
                {"tenant_id": tenant_id, "account_id": custom_acct_id, "debit": 0, "credit": 20},
            ],
        },
    )

    tax_rep = client.get(
        "/api/reports/tax-summary?start=2026-07-01&end=2026-07-31",
        headers=auth,
    ).json()

    assert Decimal(str(tax_rep["gst"]["output_gst"])) == Decimal("20.00")


def test_pakistan_ito_tax_isolated_by_country(client: TestClient):
    """Pakistan ITO 2001 slabs must not be applied to Austrian / international tenants."""
    auth = _auth(client, "country_iso@test.local", business_model="trader")
    accounts = client.get("/api/accounts", headers=auth).json()["items"]
    tenant_id = accounts[0]["tenant_id"]

    acct_1100 = next(a for a in accounts if a["code"] == "1100")
    acct_rev = next(a for a in accounts if a["code"] == "4000")

    # Post income of 1,000,000
    client.post(
        "/api/transactions",
        headers=auth,
        json={
            "tenant_id": tenant_id,
            "date": "2026-08-01",
            "description": "High revenue",
            "entries": [
                {"tenant_id": tenant_id, "account_id": acct_1100["id"], "debit": 1000000, "credit": 0},
                {"tenant_id": tenant_id, "account_id": acct_rev["id"], "debit": 0, "credit": 1000000},
            ],
        },
    )

    # By default, country is not PK
    tax_rep = client.get(
        "/api/reports/tax-summary?start=2026-08-01&end=2026-08-31",
        headers=auth,
    ).json()
    assert Decimal(str(tax_rep["income_tax"]["taxable_income"])) == Decimal("1000000.00")
    assert Decimal(str(tax_rep["income_tax"]["estimated_tax"])) == Decimal("0.00")
    assert "not configured" in tax_rep["income_tax"]["tax_basis"].lower()

    # Now set country to PK using PATCH
    r_patch = client.patch("/api/settings", headers=auth, json={"country": "PK"})
    assert r_patch.status_code == 200

    tax_rep_pk = client.get(
        "/api/reports/tax-summary?start=2026-08-01&end=2026-08-31",
        headers=auth,
    ).json()
    # In Pakistan ITO, (1000000 - 600000) * 0.05 = 20,000
    assert Decimal(str(tax_rep_pk["income_tax"]["estimated_tax"])) == Decimal("20000.00")
    assert "ITO 2001" in tax_rep_pk["income_tax"]["tax_basis"]


def test_cit_worksheet_austrian_kst_rate(client: TestClient):
    """CIT worksheet defaults to 23% for Austrian tenants."""
    auth = _auth(client, "cit_at@test.local", business_model="trader")
    r_patch = client.patch("/api/settings", headers=auth, json={"country": "AT"})
    assert r_patch.status_code == 200

    r = client.get("/api/reports/cit-worksheet?start=2026-01-01&end=2026-12-31", headers=auth)
    assert r.status_code == 200
    data = r.json()
    assert Decimal(str(data["tax_rate"])) == Decimal("23")
