"""Austrian Document Archive, 7-Year Retention & Legal Hold (§ 132 BAO) (PR 15: AT-07).

Rules implemented:
- 7-jährige gesetzliche Aufbewahrungsfrist (§ 132 Abs. 1 BAO):
  Frist beginnt mit dem Schluss des Kalenderjahres, in dem die Verbuchung/Belegung erfolgte.
  (z. B. Beleg aus 2026 -> Aufbewahrung bis mindestens 31.12.2033)
- 22-jährige Aufbewahrungsfrist für Grundstücke/Gebäude (§ 18 Abs. 2 UStG)
- Verfrühter Löschschutz: Physische und logische Löschung vor Fristablauf wird serverseitig abgewiesen
- Legal Hold (§ 132 BAO): Bei anhängigen behördlichen/gerichtlichen Verfahren oder Betriebsprüfungen
  wird die Löschung auch nach Ablauf der 7 Jahre blockiert
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from models_at import ArchiveLegalHold, ArchiveObject, LegalHold
from local_config import uploads_dir


def calculate_retention_until(booking_date: str, is_real_estate: bool = False) -> str:
    """Calculate statutory § 132 BAO retention date (end of calendar year + 7 or 22 years)."""
    year = int(booking_date.split("-")[0])
    retention_years = 22 if is_real_estate else 7
    expiry_year = year + retention_years
    return f"{expiry_year}-12-31"


def archive_object(
    session: Session,
    tenant_id: int,
    object_type: str,
    reference_id: int,
    file_name: str,
    file_path: str,
    mime_type: str,
    content_bytes: bytes,
    booking_date: str,
    is_real_estate: bool = False,
) -> ArchiveObject:
    """Create immutable archive record with computed retention deadline and SHA-256 checksum."""
    sha256 = hashlib.sha256(content_bytes).hexdigest()
    retain_until = calculate_retention_until(booking_date, is_real_estate)

    obj = ArchiveObject(
        tenant_id=tenant_id,
        object_type=object_type,
        reference_id=reference_id,
        file_name=file_name,
        file_path=file_path,
        mime_type=mime_type,
        file_size=len(content_bytes),
        sha256_hash=sha256,
        recorded_at=datetime.utcnow(),
        retain_until=retain_until,
        legal_hold=False,
    )
    session.add(obj)
    session.flush()
    session.refresh(obj)
    return obj


def store_archive_bytes(
    session: Session,
    tenant_id: int,
    object_type: str,
    reference_id: int,
    file_name: str,
    mime_type: str,
    content_bytes: bytes,
    booking_date: str,
    is_real_estate: bool = False,
) -> ArchiveObject:
    """Persist bytes atomically in the managed tenant archive and record their hash."""
    safe_name = Path(file_name).name
    target_dir = uploads_dir() / str(tenant_id) / "at_archive" / str(booking_date)[:4]
    target_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(content_bytes).hexdigest()
    target = target_dir / f"{reference_id}-{digest[:16]}-{safe_name}"
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(content_bytes)
    os.replace(temporary, target)
    return archive_object(
        session=session,
        tenant_id=tenant_id,
        object_type=object_type,
        reference_id=reference_id,
        file_name=safe_name,
        file_path=str(target),
        mime_type=mime_type,
        content_bytes=content_bytes,
        booking_date=booking_date,
        is_real_estate=is_real_estate,
    )


def assert_archive_deletable(session: Session, tenant_id: int, archive_id: int) -> None:
    """Ensure document cannot be deleted before statutory retention expires or while under legal hold."""
    obj = session.exec(
        select(ArchiveObject).where(
            ArchiveObject.id == archive_id,
            ArchiveObject.tenant_id == tenant_id,
        )
    ).first()
    if not obj:
        raise HTTPException(404, "Archivobjekt nicht gefunden.")

    # 1. Legal Hold check
    if obj.legal_hold:
        raise HTTPException(
            403,
            f"Löschung verboten: Dokument '{obj.file_name}' unterliegt einem aktiven Legal Hold "
            f"(Grund: {obj.legal_hold_reason or 'Laufendes Verfahren / Betriebsprüfung'}).",
        )

    # 2. Statutory 7-year retention check (§ 132 BAO)
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    if today_str < obj.retain_until:
        raise HTTPException(
            403,
            f"Löschung vor Ablauf der gesetzlichen Aufbewahrungsfrist unzulässig. "
            f"Gemäß § 132 BAO muss das Dokument bis mindestens {obj.retain_until} aufbewahrt werden.",
        )


def institute_legal_hold(
    session: Session,
    tenant_id: int,
    user_id: int,
    title: str,
    reason: str,
    object_ids: Optional[List[int]] = None,
) -> LegalHold:
    """Institute a legal hold locking specified or all archive records (§ 132 BAO)."""
    hold = LegalHold(
        tenant_id=tenant_id,
        title=title,
        reason=reason,
        instituted_at=datetime.utcnow(),
        instituted_by_id=user_id,
        is_active=True,
    )
    session.add(hold)
    session.flush()

    query = select(ArchiveObject).where(ArchiveObject.tenant_id == tenant_id)
    if object_ids:
        query = query.where(ArchiveObject.id.in_(object_ids))

    objects = session.exec(query).all()
    for obj in objects:
        session.add(ArchiveLegalHold(
            tenant_id=tenant_id, archive_object_id=obj.id, legal_hold_id=hold.id,
        ))
        obj.legal_hold = True
        obj.legal_hold_reason = f"[{hold.id}] {title}: {reason}"
        session.add(obj)

    session.flush()
    return hold


def release_legal_hold(
    session: Session,
    tenant_id: int,
    hold_id: int,
) -> None:
    """Release a legal hold instruction."""
    hold = session.exec(
        select(LegalHold).where(
            LegalHold.id == hold_id,
            LegalHold.tenant_id == tenant_id,
        )
    ).first()
    if not hold:
        raise HTTPException(404, "Legal Hold nicht gefunden.")

    hold.is_active = False
    session.add(hold)

    links = session.exec(select(ArchiveLegalHold).where(
        ArchiveLegalHold.tenant_id == tenant_id,
        ArchiveLegalHold.legal_hold_id == hold.id,
    )).all()
    for link in links:
        obj = session.get(ArchiveObject, link.archive_object_id)
        session.delete(link)
        if not obj:
            continue
        other_active = session.exec(
            select(ArchiveLegalHold)
            .join(LegalHold, ArchiveLegalHold.legal_hold_id == LegalHold.id)
            .where(
                ArchiveLegalHold.tenant_id == tenant_id,
                ArchiveLegalHold.archive_object_id == obj.id,
                ArchiveLegalHold.legal_hold_id != hold.id,
                LegalHold.is_active == True,  # noqa: E712
            )
        ).first()
        if not other_active:
            obj.legal_hold = False
            obj.legal_hold_reason = None
        session.add(obj)

    session.flush()
