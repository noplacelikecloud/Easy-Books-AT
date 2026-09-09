"""Tests for Austrian Document Archive, 7-Year Retention & Legal Hold (§ 132 BAO) (PR 15: AT-07)."""
import pytest
from sqlmodel import Session, select

from localizations.at.archive import archive_object, calculate_retention_until
from models import User
from models_at import ArchiveObject


@pytest.fixture
def at_archive_env(client, admin_headers):
    client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "valid_from": "2026-01-01",
    })


def test_retention_calculation_and_premature_deletion_protection(client, admin_headers, at_archive_env):
    """Document from 2026 must be retained until 2033-12-31; premature deletion is rejected (§ 132 BAO)."""
    from main import app

    # Verify calculation: 2026 -> 2033-12-31 (7 years from end of calendar year)
    assert calculate_retention_until("2026-04-15") == "2033-12-31"
    # Real estate (22 years): 2026 -> 2048-12-31
    assert calculate_retention_until("2026-04-15", is_real_estate=True) == "2048-12-31"

    # Archive dummy invoice PDF
    content = b"%PDF-1.4 test invoice content"
    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        obj = archive_object(
            session=session,
            tenant_id=user.tenant_id,
            object_type="invoice_pdf",
            reference_id=101,
            file_name="Rechnung_2026_001.pdf",
            file_path="/var/data/archive/Rechnung_2026_001.pdf",
            mime_type="application/pdf",
            content_bytes=content,
            booking_date="2026-04-15",
        )
        session.commit()
        obj_id = obj.id

    # Attempt premature deletion via API -> must fail with HTTP 403
    del_res = client.delete(f"/api/at/archive/{obj_id}", headers=admin_headers)
    assert del_res.status_code == 403
    assert "2033-12-31" in del_res.text
    assert "§ 132 BAO" in del_res.text


def test_legal_hold_blocks_deletion_override(client, admin_headers, at_archive_env):
    """An active Legal Hold blocks deletion with explicit reason and audit trail."""
    from main import app

    content = b"%PDF-1.4 tax audit document"
    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.email == "owner@acme.test")).first()
        obj = archive_object(
            session=session,
            tenant_id=user.tenant_id,
            object_type="tax_export",
            reference_id=999,
            file_name="Pruefbericht_2026.pdf",
            file_path="/var/data/archive/Pruefbericht_2026.pdf",
            mime_type="application/pdf",
            content_bytes=content,
            booking_date="2026-01-01",
        )
        # Artificially set retain_until to yesterday to test that legal hold independently blocks
        obj.retain_until = "2020-01-01"
        session.add(obj)
        session.commit()
        obj_id = obj.id

    # 1. Institute Legal Hold
    hold_res = client.post("/api/at/archive/legal-hold", headers=admin_headers, json={
        "title": "Finanzamt Betriebsprüfung 2026",
        "reason": "Anordnung der Großbetriebsprüfung Wien",
        "object_ids": [obj_id],
    })
    assert hold_res.status_code == 200
    hold_id = hold_res.json()["legal_hold_id"]

    # 2. Deletion must be blocked due to active legal hold
    del_res = client.delete(f"/api/at/archive/{obj_id}", headers=admin_headers)
    assert del_res.status_code == 403
    assert "Legal Hold" in del_res.text

    # 3. Release Legal Hold
    rel_res = client.post(f"/api/at/archive/legal-hold/{hold_id}/release", headers=admin_headers)
    assert rel_res.status_code == 200

    # 4. Now that legal hold is released and retain_until is past, deletion succeeds
    del_res_ok = client.delete(f"/api/at/archive/{obj_id}", headers=admin_headers)
    assert del_res_ok.status_code == 200
    assert del_res_ok.json()["deleted"] is True
