"""Austrian Recapitulative Statement (Zusammenfassende Meldung / ZM) gem. Art. 21 Abs. 3 UStG (PR 10: AT-10).

Reports cross-border B2B supplies to other EU member states:
- "L": Innergemeinschaftliche steuerfreie Warenlieferungen (Art. 7 UStG)
- "S": B2B-Dienstleistungen mit Übergang der Steuerschuld (Art. 196 MwSt-SystRL / § 3a Abs. 6 UStG)
- "D": Dreiecksgeschäfte
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

from fastapi import HTTPException
from sqlmodel import Session, select

from models import Tenant
from models_at import TaxEvent, TaxFiling, TaxFilingSubmissionLog, TaxFilingVersion
from localizations.at.profile import get_active_profile
from services.money import D, ZERO, money


def compute_zm(session: Session, tenant_id: int, period_key: str) -> Dict[str, Any]:
    """Compute Austrian ZM line items aggregated by partner UID and transaction type."""
    events = session.exec(
        select(TaxEvent).where(
            TaxEvent.tenant_id == tenant_id,
            TaxEvent.tax_period == period_key,
            TaxEvent.zm_relevant == True,  # noqa: E712
            TaxEvent.state == "final",
        )
    ).all()

    grouped: Dict[tuple, Dict[str, Any]] = {}
    total_amount = ZERO
    event_ids: List[int] = []

    for ev in events:
        if ev.id:
            event_ids.append(ev.id)

        # Determine art: "L" for supplies, "S" for services
        if ev.treatment_code == "AT_ZERO_IG_SUPPLY":
            art = "L"
        elif ev.treatment_code == "AT_RC_EU_SERVICE_OUT":
            art = "S"
        else:
            art = "L"

        # Correction events already carry signed amounts.
        amount = money(ev.base_amount_eur)
        country = (ev.partner_country or "AT").upper()
        uid = (ev.partner_vat_id or "").strip()

        key = (country, uid, art)
        if key not in grouped:
            grouped[key] = {
                "country": country,
                "partner_vat_id": uid,
                "art": art,
                "amount": ZERO,
            }

        grouped[key]["amount"] += amount
        total_amount += amount

    entries = []
    for k, v in grouped.items():
        entries.append({
            "country": v["country"],
            "partner_vat_id": v["partner_vat_id"],
            "art": v["art"],
            "amount": money(v["amount"]),
        })

    # Sort entries by country, then UID
    entries.sort(key=lambda x: (x["country"], x["partner_vat_id"], x["art"]))

    return {
        "period_key": period_key,
        "entry_count": len(entries),
        "entries": entries,
        "total_amount_eur": money(total_amount),
        "event_ids": event_ids,
    }


def generate_zm_xml(
    session: Session,
    tenant_id: int,
    period_key: str,
    zm_data: Dict[str, Any],
) -> str:
    """Generate FinanzOnline U13 XML according to the published BMF XSD."""
    prof = get_active_profile(session, tenant_id)
    if not prof:
        raise HTTPException(422, "Kein aktives AT-Profil vorhanden.")
    fastnr = re.sub(r"\D", "", prof.tax_number or "")
    if len(fastnr) != 9:
        raise HTTPException(422, "Für den ZM-Export ist eine neunstellige FASTNR erforderlich.")

    parts = period_key.split("-")
    year_str = parts[0]
    if len(parts) != 2:
        raise HTTPException(422, "Ungültiger ZM-Zeitraum.")
    if parts[1].startswith("Q"):
        quarter = int(parts[1][1:])
        start_month, end_month = (quarter - 1) * 3 + 1, quarter * 3
    else:
        start_month = end_month = int(parts[1])
    now = datetime.now()
    root = ET.Element("ERKLAERUNGS_UEBERMITTLUNG")
    info = ET.SubElement(root, "INFO_DATEN")
    ET.SubElement(info, "ART_IDENTIFIKATIONSBEGRIFF").text = "FASTNR"
    ET.SubElement(info, "IDENTIFIKATIONSBEGRIFF").text = fastnr
    ET.SubElement(info, "PAKET_NR").text = str(int(now.strftime("%j%H%M%S")))
    ET.SubElement(info, "DATUM_ERSTELLUNG", {"type": "datum"}).text = now.date().isoformat()
    ET.SubElement(info, "UHRZEIT_ERSTELLUNG", {"type": "uhrzeit"}).text = now.time().replace(microsecond=0).isoformat()
    ET.SubElement(info, "ANZAHL_ERKLAERUNGEN").text = "1"
    declaration = ET.SubElement(root, "ERKLAERUNG", {"art": "U13"})
    ET.SubElement(declaration, "SATZNR").text = "1"
    general = ET.SubElement(declaration, "ALLGEMEINE_DATEN")
    ET.SubElement(general, "ANBRINGEN").text = "U13"
    ET.SubElement(general, "ZRVON", {"type": "jahrmonat"}).text = f"{year_str}-{start_month:02d}"
    ET.SubElement(general, "ZRBIS", {"type": "jahrmonat"}).text = f"{year_str}-{end_month:02d}"
    ET.SubElement(general, "FASTNR").text = fastnr
    ET.SubElement(general, "KUNDENINFO").text = f"OpenBooksAT {period_key}"[:50]
    for entry in zm_data.get("entries", []):
        uid = (entry.get("partner_vat_id") or "").replace(" ", "").upper()
        if not uid:
            raise HTTPException(422, "Jeder ZM-Eintrag benötigt eine Partner-UID.")
        item = ET.SubElement(declaration, "ZM")
        ET.SubElement(item, "UID_MS").text = uid
        # FinanzOnline U13 accepts whole euros with a sign.
        rounded = D(entry["amount"]).quantize(Decimal("1"))
        ET.SubElement(item, "SUM_BGL", {"type": "kz"}).text = str(rounded)
        if entry["art"] == "S":
            ET.SubElement(item, "SOLEI").text = "J"
        elif entry["art"] == "D":
            ET.SubElement(item, "DREIECK").text = "J"
    return ET.tostring(root, encoding="iso-8859-1", xml_declaration=True).decode("iso-8859-1")


def finalize_zm_filing(
    session: Session,
    tenant_id: int,
    user_id: int,
    period_key: str,
) -> TaxFiling:
    """Finalize ZM filing, creating snapshot and audit trail."""
    zm_data = compute_zm(session, tenant_id, period_key)
    xml_str = generate_zm_xml(session, tenant_id, period_key, zm_data)
    xml_hash = hashlib.sha256(xml_str.encode("iso-8859-1")).hexdigest()

    parts = period_key.split("-")
    year = int(parts[0])

    filing = session.exec(
        select(TaxFiling).where(
            TaxFiling.tenant_id == tenant_id,
            TaxFiling.filing_type == "zm",
            TaxFiling.period_key == period_key,
        )
    ).first()

    if not filing:
        filing = TaxFiling(
            tenant_id=tenant_id,
            filing_type="zm",
            period_key=period_key,
            year=year,
            version=1,
            status="finalized",
            xml_payload=xml_str,
            xml_hash=xml_hash,
            total_payable=ZERO,
            created_at=datetime.utcnow(),
            finalized_at=datetime.utcnow(),
        )
        session.add(filing)
        session.flush()
    else:
        filing.version += 1
        filing.status = "finalized"
        filing.xml_payload = xml_str
        filing.xml_hash = xml_hash
        filing.finalized_at = datetime.utcnow()
        session.add(filing)
        session.flush()

    summary_serializable = {
        "entry_count": zm_data["entry_count"],
        "total_amount_eur": str(zm_data["total_amount_eur"]),
        "entries": [
            {k: str(v) if isinstance(v, Decimal) else v for k, v in e.items()}
            for e in zm_data["entries"]
        ],
    }

    ver = TaxFilingVersion(
        tenant_id=tenant_id,
        tax_filing_id=filing.id,
        version=filing.version,
        event_ids=json.dumps(zm_data["event_ids"]),
        summary_data=json.dumps(summary_serializable),
        xml_payload=xml_str,
        xml_hash=xml_hash,
        created_at=datetime.utcnow(),
    )
    session.add(ver)

    sub_log = TaxFilingSubmissionLog(
        tenant_id=tenant_id,
        tax_filing_id=filing.id,
        submitted_at=datetime.utcnow(),
        status="local_generated",
        request_hash=xml_hash,
        response_payload="Local ZM XML snapshot generated; not submitted to FinanzOnline",
    )
    session.add(sub_log)

    from localizations.at.archive import store_archive_bytes
    store_archive_bytes(
        session, tenant_id, "tax_filing_xml", filing.id,
        f"ZM_{period_key}_v{filing.version}.xml", "application/xml",
        xml_str.encode("iso-8859-1"), f"{year}-12-31",
    )

    session.flush()
    return filing
