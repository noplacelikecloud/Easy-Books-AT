"""P6 tests: CSV upload de-dupe, auto-match by amount+date, manual match."""
import io
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


def _auth(client: TestClient) -> dict:
    client.post(
        "/api/auth/signup",
        json={
            "email": "bk@bk.test",
            "password": "password123",
            "full_name": "U",
            "company_name": "Bank Co",
        },
    )
    r = client.post(
        "/api/auth/login", data={"username": "bk@bk.test", "password": "password123"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _bank_account(client: TestClient, auth: dict) -> int:
    r = client.post(
        "/api/bank-accounts",
        headers=auth,
        json={"name": "Main Checking", "account_number": "12345"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


SAMPLE_CSV = """date,description,debit,credit,balance
2026-05-02,Customer payment Alice,0,500,1500
2026-05-03,Stripe payout,0,1000,2500
2026-05-04,Office rent,200,0,2300
"""


def test_upload_creates_statement_lines(client: TestClient):
    auth = _auth(client)
    acct_id = _bank_account(client, auth)

    files = {"file": ("statement.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")}
    r = client.post(
        "/api/bank-imports",
        headers=auth,
        data={"bank_account_id": str(acct_id)},
        files=files,
    )
    assert r.status_code == 201, r.text
    imp = r.json()
    assert imp["line_count"] == 3

    lines = client.get(f"/api/bank-imports/{imp['id']}/lines", headers=auth).json()
    assert len(lines) == 3
    assert lines[0]["description"] == "Customer payment Alice"
    assert Decimal(str(lines[0]["credit"])) == Decimal("500")


def test_duplicate_upload_409s(client: TestClient):
    auth = _auth(client)
    acct_id = _bank_account(client, auth)
    files = {"file": ("statement.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")}
    r1 = client.post(
        "/api/bank-imports",
        headers=auth,
        data={"bank_account_id": str(acct_id)},
        files=files,
    )
    assert r1.status_code == 201

    files2 = {"file": ("statement.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")}
    r2 = client.post(
        "/api/bank-imports",
        headers=auth,
        data={"bank_account_id": str(acct_id)},
        files=files2,
    )
    assert r2.status_code == 409


def test_auto_match_links_lines_to_existing_jvs_by_amount(client: TestClient):
    auth = _auth(client)
    acct_id = _bank_account(client, auth)

    # Post a JV that should be matchable: Dr Cash 500 / Cr Sales 500 on 2026-05-02
    accounts = client.get("/api/accounts", headers=auth).json()["items"]
    cash = next(a for a in accounts if a["code"] == "1000")
    sales = next(a for a in accounts if a["code"] == "4000")
    tenant_id = cash["tenant_id"]
    r = client.post(
        "/api/transactions",
        headers=auth,
        json={
            "tenant_id": tenant_id,
            "date": "2026-05-02",
            "description": "Test sale",
            "entries": [
                {"tenant_id": tenant_id, "account_id": cash["id"], "debit": 500, "credit": 0},
                {"tenant_id": tenant_id, "account_id": sales["id"], "debit": 0, "credit": 500},
            ],
        },
    )
    assert r.status_code == 200

    # Upload the CSV
    files = {"file": ("statement.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")}
    imp = client.post(
        "/api/bank-imports",
        headers=auth,
        data={"bank_account_id": str(acct_id)},
        files=files,
    ).json()

    # Auto-match
    r = client.post(f"/api/bank-imports/{imp['id']}/auto-match", headers=auth)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["newly_matched"] == 1  # the 500 credit line matches the JV

    lines = client.get(f"/api/bank-imports/{imp['id']}/lines", headers=auth).json()
    matched = [l for l in lines if l["is_matched"]]
    assert len(matched) == 1
    assert Decimal(str(matched[0]["credit"])) == Decimal("500")


AUSTRIAN_CSV_SEMICOLON = """Datum;Text;Soll;Haben;Saldo
02.05.2026;Kunde Müller Rechnung 1001;;1.234,56;1.234,56
03.05.2026;Bürobedarf Libro;123,45;;1.111,11
04.05.2026;Miete Büro;500,00;;611,11
"""


def test_upload_austrian_semicolon_format(client: TestClient):
    auth = _auth(client)
    acct_id = _bank_account(client, auth)

    files = {"file": ("statement_at.csv", io.BytesIO(AUSTRIAN_CSV_SEMICOLON.encode("utf-8")), "text/csv")}
    r = client.post(
        "/api/bank-imports",
        headers=auth,
        data={
            "bank_account_id": str(acct_id),
            "date_col": "Datum",
            "description_col": "Text",
            "debit_col": "Soll",
            "credit_col": "Haben",
            "balance_col": "Saldo",
            "decimal_separator": ",",
            "thousands_separator": ".",
        },
        files=files,
    )
    assert r.status_code == 201, r.text
    imp = r.json()
    assert imp["line_count"] == 3

    lines = client.get(f"/api/bank-imports/{imp['id']}/lines", headers=auth).json()
    assert len(lines) == 3
    # 1.234,56 must parse as 1234.56, NOT 123456 or 1.23456!
    assert lines[0]["date"] == "2026-05-02"
    assert lines[0]["description"] == "Kunde Müller Rechnung 1001"
    assert Decimal(str(lines[0]["credit"])) == Decimal("1234.56")
    # 123,45 must parse as 123.45, NOT 12345!
    assert lines[1]["date"] == "2026-05-03"
    assert Decimal(str(lines[1]["debit"])) == Decimal("123.45")
    assert Decimal(str(lines[2]["debit"])) == Decimal("500.00")


def test_preview_bank_statement(client: TestClient):
    auth = _auth(client)
    acct_id = _bank_account(client, auth)

    files = {"file": ("statement_at.csv", io.BytesIO(AUSTRIAN_CSV_SEMICOLON.encode("utf-8")), "text/csv")}
    r = client.post(
        "/api/bank-imports/preview",
        headers=auth,
        data={
            "bank_account_id": str(acct_id),
            "date_col": "Datum",
            "description_col": "Text",
            "debit_col": "Soll",
            "credit_col": "Haben",
            "balance_col": "Saldo",
            "decimal_separator": ",",
            "thousands_separator": ".",
        },
        files=files,
    )
    assert r.status_code == 200, r.text
    preview = r.json()
    assert preview["total_rows"] == 3
    assert preview["valid_rows"] == 3
    assert preview["error_count"] == 0
    assert Decimal(str(preview["total_debit"])) == Decimal("623.45")   # 123.45 + 500.00
    assert Decimal(str(preview["total_credit"])) == Decimal("1234.56")
    assert "file_hash" in preview
    assert len(preview["preview_lines"]) == 3
    assert preview["preview_lines"][0]["credit"] == 1234.56


def test_upload_with_expected_hash(client: TestClient):
    auth = _auth(client)
    acct_id = _bank_account(client, auth)

    # 1. Preview
    files1 = {"file": ("statement_at.csv", io.BytesIO(AUSTRIAN_CSV_SEMICOLON.encode("utf-8")), "text/csv")}
    r_prev = client.post(
        "/api/bank-imports/preview",
        headers=auth,
        data={"bank_account_id": str(acct_id), "date_col": "Datum", "description_col": "Text", "debit_col": "Soll", "credit_col": "Haben"},
        files=files1,
    )
    assert r_prev.status_code == 200
    file_hash = r_prev.json()["file_hash"]

    # 2. Upload with mismatched hash should fail 400
    files2 = {"file": ("statement_at.csv", io.BytesIO(AUSTRIAN_CSV_SEMICOLON.encode("utf-8")), "text/csv")}
    r_mismatch = client.post(
        "/api/bank-imports",
        headers=auth,
        data={
            "bank_account_id": str(acct_id),
            "date_col": "Datum",
            "description_col": "Text",
            "debit_col": "Soll",
            "credit_col": "Haben",
            "expected_hash": "wrong_hash_value",
        },
        files=files2,
    )
    assert r_mismatch.status_code == 400
    assert "hash mismatch" in r_mismatch.text.lower()

    # 3. Upload with correct expected_hash should succeed
    files3 = {"file": ("statement_at.csv", io.BytesIO(AUSTRIAN_CSV_SEMICOLON.encode("utf-8")), "text/csv")}
    r_ok = client.post(
        "/api/bank-imports",
        headers=auth,
        data={
            "bank_account_id": str(acct_id),
            "date_col": "Datum",
            "description_col": "Text",
            "debit_col": "Soll",
            "credit_col": "Haben",
            "expected_hash": file_hash,
            "decimal_separator": ",",
        },
        files=files3,
    )
    assert r_ok.status_code == 201


def test_upload_rejects_contradictory_format(client: TestClient):
    auth = _auth(client)
    acct_id = _bank_account(client, auth)

    # US-style CSV with quoted "1,234.56" but uploaded with decimal_separator=","
    bad_csv = '''date,description,amount
2026-05-02,Test,"1,234.56"
'''
    files = {"file": ("bad.csv", io.BytesIO(bad_csv.encode("utf-8")), "text/csv")}
    r = client.post(
        "/api/bank-imports",
        headers=auth,
        data={
            "bank_account_id": str(acct_id),
            "amount_col": "amount",
            "decimal_separator": ",",
            "thousands_separator": ".",
        },
        files=files,
    )
    assert r.status_code == 400
    assert "error" in r.text.lower()