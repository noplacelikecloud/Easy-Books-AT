"""Tests for Austrian Wareneingangsbuch gem. § 127 BAO (PR 14)."""
from decimal import Decimal
import pytest


@pytest.fixture
def at_gr_env(client, admin_headers):
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "sole_proprietor",
        "profit_method": "ear",
        "valid_from": "2026-01-01",
    })


def test_goods_received_sequential_numbering_and_totals(client, admin_headers, at_gr_env):
    """Test sequential numbering per calendar year and subtotal calculations (§ 127 BAO)."""
    # 1. First record in 2026
    r1 = client.post("/api/at/goods-received", headers=admin_headers, json={
        "received_date": "2026-03-10",
        "vendor_name": "Holzgroßhandel Salzburg GmbH",
        "vendor_address": "Salzburg, Holzwinkl 1",
        "description": "Fichtenholz Schnittholz",
        "net_amount": 2000.00,
        "vat_amount": 400.00,
        "document_number": "ER-2026-001",
    }).json()["record"]
    assert r1["entry_number"] == 1
    assert Decimal(str(r1["gross_amount"])) == Decimal("2400.00")

    # 2. Second record in 2026
    r2 = client.post("/api/at/goods-received", headers=admin_headers, json={
        "received_date": "2026-04-15",
        "vendor_name": "Metallwaren Graz KG",
        "description": "Schrauben und Beschläge",
        "net_amount": 500.00,
        "vat_amount": 100.00,
        "document_number": "ER-2026-002",
    }).json()["record"]
    assert r2["entry_number"] == 2
    assert Decimal(str(r2["gross_amount"])) == Decimal("600.00")

    # 3. First record in next year (2027) resets to 1
    r3 = client.post("/api/at/goods-received", headers=admin_headers, json={
        "received_date": "2027-01-08",
        "vendor_name": "Holzgroßhandel Salzburg GmbH",
        "description": "Eichenbretter",
        "net_amount": 1500.00,
        "vat_amount": 300.00,
    }).json()["record"]
    assert r3["entry_number"] == 1

    # 4. Check 2026 totals
    book_2026 = client.get("/api/at/goods-received?year=2026", headers=admin_headers).json()
    assert book_2026["record_count"] == 2
    assert Decimal(str(book_2026["total_net"])) == Decimal("2500.00")
    assert Decimal(str(book_2026["total_vat"])) == Decimal("500.00")
    assert Decimal(str(book_2026["total_gross"])) == Decimal("3000.00")

    # 5. Check month filter (April 2026)
    book_april = client.get("/api/at/goods-received?year=2026&month=4", headers=admin_headers).json()
    assert book_april["record_count"] == 1
    assert book_april["records"][0]["entry_number"] == 2


def test_goods_received_csv_export(client, admin_headers, at_gr_env):
    """CSV export format conforms to Austrian tax audit specifications (§ 127 BAO)."""
    client.post("/api/at/goods-received", headers=admin_headers, json={
        "received_date": "2026-05-20",
        "vendor_name": "Werkzeug Handel Linz",
        "description": "Fräswerkzeuge",
        "net_amount": 800.00,
        "vat_amount": 160.00,
        "document_number": "ER-2026-088",
    })

    csv_res = client.get("/api/at/goods-received/export?year=2026", headers=admin_headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    lines = csv_res.text.strip().split("\r\n") if "\r\n" in csv_res.text else csv_res.text.strip().split("\n")

    header = lines[0].split(";")
    assert "Laufende Nr" in header
    assert "Eingangsdatum" in header
    assert "Nettobetrag EUR" in header
    assert "Bruttobetrag EUR" in header

    assert len(lines) >= 2
    assert "Werkzeug Handel Linz" in lines[1]
    assert "800.00" in lines[1]
    assert "960.00" in lines[1]
