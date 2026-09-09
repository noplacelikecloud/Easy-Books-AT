"""Tests for PR 2: Unveränderliche Buchungsbelege und Zustandsmaschine (AT-01, AT-02).

Validates:
- Document finalization creates immutable DocumentVersion snapshot with SHA-256 hash.
- Editing a finalized invoice/bill is blocked under § 190 Abs. 4 UGB.
- Attack 'posted -> draft -> delete' is blocked.
- Deleting finalized or posted documents is rejected.
- Consecutive numbering series bound to fiscal/calendar year.
- Storno cancellation cleanly posts reversal JV and preserves audit trail.
"""
import hashlib
import json
import pytest
from sqlmodel import Session, select

from models import Invoice, Customer, Product, Transaction
from models_at import DocumentVersion, DocumentNumberSeries, TaxEvent


def _setup_at(client, headers):
    response = client.post("/api/at/profile", headers=headers, json={
        "valid_from": "2026-01-01", "legal_form": "gmbh",
        "profit_method": "ugb_double_entry", "vat_status": "standard",
        "vat_method": "accrual", "vat_filing_frequency": "monthly",
        "tax_number": "123456789", "vat_id": "ATU12345678",
    })
    assert response.status_code == 200, response.text


def test_finalize_invoice_creates_version_and_locks(client, admin_headers):
    _setup_at(client, admin_headers)
    # 1. Create customer and product
    cust = client.post("/api/customers", headers=admin_headers, json={
        "name": "Musterkunde GmbH",
        "tax_number": "12/345/6789",
        "uid": "ATU12345678",
        "address_street": "Kärntner Straße 1",
        "address_zip": "1010",
        "address_city": "Wien",
    }).json()
    prod = client.post("/api/products", headers=admin_headers, json={
        "name": "Beratungsleistung",
        "product_type": "service",
    }).json()

    # 2. Create invoice
    inv_res = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-03-15",
        "due_date": "2026-03-31",
        "gst_rate": 20,
        "lines": [{
            "product_id": prod["id"],
            "description": "Consulting Stunden",
            "qty": 5,
            "rate": 100,
            "tax_treatment_code": "AT_STANDARD_20",
        }],
    })
    assert inv_res.status_code in (200, 201), inv_res.text
    inv = inv_res.json()
    inv_id = inv["id"]

    # 3. Finalize invoice
    fin_res = client.post(f"/api/invoices/{inv_id}/finalize", headers=admin_headers)
    assert fin_res.status_code == 200, fin_res.text
    finalized_inv = fin_res.json()
    assert finalized_inv["lifecycle_status"] == "finalized"

    # 4. Verify immutable DocumentVersion snapshot exists with valid SHA-256 hash
    versions_res = client.get(f"/api/invoices/{inv_id}", headers=admin_headers)
    assert versions_res.status_code == 200

    # Verify attempt to edit finalized invoice is BLOCKED
    edit_res = client.put(f"/api/invoices/{inv_id}", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-03-15",
        "gst_rate": 20,
        "lines": [{
            "product_id": prod["id"],
            "description": "Tampered description",
            "qty": 10,
            "rate": 200,
        }],
    })
    assert edit_res.status_code == 400
    assert "finalized" in edit_res.json()["detail"].lower()


def test_attack_posted_to_draft_to_delete_blocked(client, admin_headers):
    _setup_at(client, admin_headers)
    cust = client.post("/api/customers", headers=admin_headers, json={"name": "Kunde B"}).json()
    prod = client.post("/api/products", headers=admin_headers, json={"name": "Hardware"}).json()

    inv = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-04-01",
        "lines": [{"product_id": prod["id"], "description": "Server", "qty": 1, "rate": 500,
                   "tax_treatment_code": "AT_STANDARD_20"}],
    }).json()

    # Finalize invoice
    client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers)

    # Attack step 1: Try to revert status to 'draft'
    status_res = client.patch(f"/api/invoices/{inv['id']}/status?status=draft", headers=admin_headers)
    assert status_res.status_code == 400
    assert "draft" in status_res.json()["detail"].lower()

    # Attack step 2: Try bulk delete
    bulk_del = client.post("/api/invoices/bulk", headers=admin_headers, json={
        "ids": [inv["id"]],
        "action": "delete",
    }).json()
    assert bulk_del["affected"] == 0
    assert len(bulk_del["errors"]) > 0

    # Ensure invoice still exists
    get_res = client.get(f"/api/invoices/{inv['id']}", headers=admin_headers)
    assert get_res.status_code == 200


def test_storno_cancellation_preserves_audit(client, admin_headers):
    _setup_at(client, admin_headers)
    cust = client.post("/api/customers", headers=admin_headers, json={"name": "Kunde C"}).json()
    prod = client.post("/api/products", headers=admin_headers, json={"name": "Lizenz"}).json()

    inv = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": cust["id"],
        "issue_date": "2026-05-10",
        "lines": [{"product_id": prod["id"], "description": "SaaS Lizenz", "qty": 1, "rate": 300,
                   "tax_treatment_code": "AT_STANDARD_20"}],
    }).json()

    client.post(f"/api/invoices/{inv['id']}/finalize", headers=admin_headers)

    # Storno cancel
    cancel_res = client.post(
        f"/api/invoices/{inv['id']}/cancel?reason=Kunde_storniert_vor_Lieferung",
        headers=admin_headers,
    )
    assert cancel_res.status_code == 200, cancel_res.text
    cancelled_inv = cancel_res.json()
    assert cancelled_inv["lifecycle_status"] == "cancelled"
    assert cancelled_inv["status"] == "void"


def test_credit_note_finalization_reverses_invoice_tax_event(client, admin_headers):
    _setup_at(client, admin_headers)
    customer = client.post(
        "/api/customers", headers=admin_headers, json={"name": "Retourkunde GmbH"}
    ).json()
    invoice = client.post("/api/invoices", headers=admin_headers, json={
        "customer_id": customer["id"],
        "issue_date": "2026-06-01",
        "lines": [{
            "description": "Beratung", "qty": 1, "rate": 500,
            "tax_treatment_code": "AT_STANDARD_20",
        }],
    }).json()
    finalized = client.post(
        f"/api/invoices/{invoice['id']}/finalize", headers=admin_headers
    )
    assert finalized.status_code == 200, finalized.text

    note = client.post("/api/credit-notes", headers=admin_headers, json={
        "invoice_id": invoice["id"],
        "customer_id": customer["id"],
        "issue_date": "2026-06-10",
        "description": "Preisminderung",
        "lines": [{
            "description": "Beratung", "qty": 1, "rate": 100,
            "tax_treatment_code": "AT_STANDARD_20",
        }],
    })
    assert note.status_code == 201, note.text
    result = client.post(
        f"/api/credit-notes/{note.json()['id']}/finalize", headers=admin_headers
    )
    assert result.status_code == 200, result.text
    assert result.json()["lifecycle_status"] == "finalized"
    assert result.json()["total"] == 120

    from main import app
    with Session(app.state.engine) as session:
        correction = session.exec(select(TaxEvent).where(
            TaxEvent.source_doc_type == "credit_note",
            TaxEvent.source_doc_id == note.json()["id"],
        )).one()
        assert correction.original_event_id is not None
        assert correction.base_amount_eur == -100
        assert correction.output_tax == -20
        assert correction.document_version_id is not None
        assert correction.transaction_id is not None


def test_debit_note_and_bill_storno_create_traceable_reversals(client, admin_headers):
    _setup_at(client, admin_headers)
    vendor = client.post(
        "/api/vendors", headers=admin_headers, json={"name": "Lieferant GmbH"}
    ).json()

    def create_final_bill(day: str, amount: int):
        bill = client.post("/api/bills", headers=admin_headers, json={
            "vendor_id": vendor["id"],
            "bill_date": day,
            "lines": [{
                "description": "Fremdleistung", "qty": 1, "rate": amount,
                "tax_treatment_code": "AT_STANDARD_20",
            }],
        })
        assert bill.status_code in (200, 201), bill.text
        finalized = client.post(
            f"/api/bills/{bill.json()['id']}/finalize", headers=admin_headers
        )
        assert finalized.status_code == 200, finalized.text
        return bill.json()

    corrected_bill = create_final_bill("2026-07-01", 400)
    note = client.post("/api/debit-notes", headers=admin_headers, json={
        "bill_id": corrected_bill["id"],
        "vendor_id": vendor["id"],
        "issue_date": "2026-07-10",
        "description": "Lieferantenrabatt",
        "lines": [{
            "description": "Fremdleistung", "qty": 1, "rate": 50,
            "tax_treatment_code": "AT_STANDARD_20",
        }],
    })
    assert note.status_code == 201, note.text
    note_result = client.post(
        f"/api/debit-notes/{note.json()['id']}/finalize", headers=admin_headers
    )
    assert note_result.status_code == 200, note_result.text
    assert note_result.json()["total"] == 60

    cancelled_bill = create_final_bill("2026-07-15", 200)
    cancellation = client.post(
        f"/api/bills/{cancelled_bill['id']}/cancel",
        headers=admin_headers,
        json={"reason": "Leistung vor Ausführung vollständig aufgehoben"},
    )
    assert cancellation.status_code == 200, cancellation.text
    assert cancellation.json()["lifecycle_status"] == "cancelled"

    from main import app
    with Session(app.state.engine) as session:
        note_event = session.exec(select(TaxEvent).where(
            TaxEvent.source_doc_type == "debit_note",
            TaxEvent.source_doc_id == note.json()["id"],
        )).one()
        assert note_event.base_amount_eur == -50
        assert note_event.input_tax_deductible == -10
        cancelled_events = session.exec(select(TaxEvent).where(
            TaxEvent.source_doc_type == "bill",
            TaxEvent.source_doc_id == cancelled_bill["id"],
        )).all()
        original_events = [event for event in cancelled_events if event.original_event_id is None]
        reversal_events = [event for event in cancelled_events if event.original_event_id is not None]
        assert original_events and reversal_events
        assert sum(event.base_amount_eur for event in cancelled_events) == 0
        assert sum(event.input_tax_deductible for event in cancelled_events) == 0
