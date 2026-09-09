"""Austrian Annual VAT Return (Umsatzsteuer-Jahreserklärung U1) (PR 10: AT-10).

Aggregates all TaxEvents across the calendar year to prepare Form U1 per § 21 Abs. 4 UStG 1994.
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


def compute_u1(session: Session, tenant_id: int, year: int) -> Dict[str, Any]:
    """Aggregate annual VAT figures from all finalized TaxEvents of the calendar year."""
    prefix = f"{year}-"
    events = session.exec(
        select(TaxEvent).where(
            TaxEvent.tenant_id == tenant_id,
            TaxEvent.tax_date.startswith(prefix),
            TaxEvent.state == "final",
        )
    ).all()

    kz_022_base = ZERO
    kz_022_tax = ZERO
    kz_029_base = ZERO
    kz_029_tax = ZERO
    kz_006_base = ZERO
    kz_006_tax = ZERO
    kz_124_base = ZERO
    kz_125_tax = ZERO
    kz_011_base = ZERO
    kz_017_base = ZERO
    kz_016_base = ZERO
    kz_021_base = ZERO

    kz_070_base = ZERO
    kz_072_tax = ZERO
    kz_073_tax = ZERO
    kz_088_tax = ZERO
    kz_057_tax = ZERO

    kz_060_input = ZERO
    kz_065_input = ZERO
    kz_066_input = ZERO

    event_ids: List[int] = []

    for ev in events:
        if ev.id:
            event_ids.append(ev.id)

        if getattr(ev, "direction", "sales") == "sales":
            base = money(ev.base_amount_eur)
            tax = money(ev.tax_amount_eur)

            if ev.uva_base_kz == "022":
                kz_022_base += base
                kz_022_tax += tax
            elif ev.uva_base_kz == "029":
                kz_029_base += base
                kz_029_tax += tax
            elif ev.uva_base_kz == "006":
                kz_006_base += base
                kz_006_tax += tax
            elif ev.uva_base_kz == "124":
                kz_124_base += base
                kz_125_tax += tax
            elif ev.uva_base_kz == "011":
                kz_011_base += base
            elif ev.uva_base_kz == "017":
                kz_017_base += base
            elif ev.uva_base_kz == "016":
                kz_016_base += base
            elif ev.uva_base_kz == "021":
                kz_021_base += base

        elif getattr(ev, "direction", "sales") == "purchases":
            base = money(ev.base_amount_eur)

            if ev.treatment_code == "AT_IG_ACQUISITION_20":
                kz_070_base += base
                kz_072_tax += money(ev.output_tax)
                kz_065_input += money(ev.input_tax_deductible)
            elif ev.treatment_code.startswith("AT_RC_"):
                kz_057_tax += money(ev.reverse_charge_tax)
                kz_066_input += money(ev.input_tax_deductible)
            else:
                kz_060_input += money(ev.input_tax_deductible)

    kz_000 = (
        kz_022_base
        + kz_029_base
        + kz_006_base
        + kz_124_base
        + kz_011_base
        + kz_017_base
        + kz_016_base
        + kz_021_base
    )

    total_output_tax = (
        kz_022_tax
        + kz_029_tax
        + kz_006_tax
        + kz_125_tax
        + kz_072_tax
        + kz_073_tax
        + kz_088_tax
        + kz_057_tax
    )

    total_input_tax = kz_060_input + kz_065_input + kz_066_input
    annual_tax_liability = money(total_output_tax - total_input_tax)

    # Sum UVA prepayments filed during the year
    uvas = session.exec(
        select(TaxFiling).where(
            TaxFiling.tenant_id == tenant_id,
            TaxFiling.filing_type == "uva",
            TaxFiling.year == year,
            TaxFiling.status == "finalized",
        )
    ).all()
    prepaid_uva_sum = sum((u.total_payable for u in uvas), ZERO)
    remaining_balance = money(annual_tax_liability - prepaid_uva_sum)

    return {
        "year": year,
        "event_count": len(events),
        "event_ids": event_ids,
        "kz_000": money(kz_000),
        "kz_022": money(kz_022_base),
        "kz_022_tax": money(kz_022_tax),
        "kz_029": money(kz_029_base),
        "kz_029_tax": money(kz_029_tax),
        "kz_006": money(kz_006_base),
        "kz_006_tax": money(kz_006_tax),
        "kz_124": money(kz_124_base),
        "kz_125": money(kz_125_tax),
        "kz_011": money(kz_011_base),
        "kz_017": money(kz_017_base),
        "kz_016": money(kz_016_base),
        "kz_021": money(kz_021_base),
        "kz_070": money(kz_070_base),
        "kz_072": money(kz_072_tax),
        "kz_073": money(kz_073_tax),
        "kz_088": money(kz_088_tax),
        "kz_057": money(kz_057_tax),
        "kz_060": money(kz_060_input),
        "kz_065": money(kz_065_input),
        "kz_066": money(kz_066_input),
        "total_output_tax": money(total_output_tax),
        "total_input_tax": money(total_input_tax),
        "annual_tax_liability": annual_tax_liability,
        "prepaid_uva_sum": money(prepaid_uva_sum),
        "remaining_balance": remaining_balance,
    }


def generate_u1_xml(
    session: Session,
    tenant_id: int,
    year: int,
    u1_data: Dict[str, Any],
) -> str:
    """Generate U1 XML for the latest published annual schema (2025)."""
    if year != 2025:
        raise HTTPException(501, "Ein amtliches U1-Datenstromschema ist in dieser Version nur für 2025 hinterlegt.")
    prof = get_active_profile(session, tenant_id, f"{year}-12-31")
    fastnr = re.sub(r"\D", "", prof.tax_number or "") if prof else ""
    if len(fastnr) != 9:
        raise HTTPException(422, "Für den U1-Export ist eine neunstellige FASTNR erforderlich.")
    now = datetime.now()
    root = ET.Element("ERKLAERUNGS_UEBERMITTLUNG")
    info = ET.SubElement(root, "INFO_DATEN")
    ET.SubElement(info, "ART_IDENTIFIKATIONSBEGRIFF").text = "FASTNR"
    ET.SubElement(info, "IDENTIFIKATIONSBEGRIFF").text = fastnr
    ET.SubElement(info, "PAKET_NR").text = str(int(now.strftime("%j%H%M%S")))
    ET.SubElement(info, "DATUM_ERSTELLUNG", {"type": "datum"}).text = now.date().isoformat()
    ET.SubElement(info, "UHRZEIT_ERSTELLUNG", {"type": "uhrzeit"}).text = now.time().replace(microsecond=0).isoformat()
    ET.SubElement(info, "ANZAHL_ERKLAERUNGEN").text = "1"
    annual = ET.SubElement(root, "JAHRESERKLAERUNG", {"art": "JAHR_ERKL"})
    declaration = ET.SubElement(annual, "ERKLAERUNG", {"art": "U1"})
    ET.SubElement(declaration, "SATZNR").text = "1"
    general = ET.SubElement(declaration, "ALLGEMEINE_DATEN")
    ET.SubElement(general, "ANBRINGEN").text = "U1"
    ET.SubElement(general, "ZR").text = str(year)
    ET.SubElement(general, "FASTNR").text = fastnr
    ET.SubElement(general, "KUNDENINFO").text = f"OpenBooksAT U1 {year}"

    def add(parent: ET.Element, kz: str, key: str, required: bool = False) -> None:
        value = money(D(u1_data.get(key, ZERO)))
        if value != ZERO or required:
            ET.SubElement(parent, f"KZ{kz}", {"type": "kz"}).text = f"{value:.2f}"

    supplies = ET.SubElement(declaration, "LIEFERUNGEN_LEISTUNGEN_EIGENVERBRAUCH")
    add(supplies, "000", "kz_000", True)
    add(supplies, "021", "kz_021")
    if any(D(u1_data.get(k, ZERO)) != ZERO for k in ("kz_011", "kz_017", "kz_016")):
        exempt = ET.SubElement(supplies, "STEUERFREI")
        for kz, key in (("011", "kz_011"), ("017", "kz_017"), ("016", "kz_016")):
            add(exempt, kz, key)
    if any(D(u1_data.get(k, ZERO)) != ZERO for k in ("kz_022", "kz_029", "kz_006", "kz_057")):
        taxed = ET.SubElement(supplies, "VERSTEUERT")
        for kz, key in (("022", "kz_022"), ("029", "kz_029"), ("006", "kz_006"), ("057", "kz_057")):
            add(taxed, kz, key)
    if any(D(u1_data.get(k, ZERO)) != ZERO for k in ("kz_070", "kz_072", "kz_073", "kz_088")):
        acquisitions = ET.SubElement(declaration, "INNERGEMEINSCHAFTLICHE_ERWERBE")
        add(acquisitions, "070", "kz_070", True)
        if any(D(u1_data.get(k, ZERO)) != ZERO for k in ("kz_072", "kz_073", "kz_088")):
            taxed_acq = ET.SubElement(acquisitions, "VERSTEUERT_IGE")
            for kz, key in (("072", "kz_072"), ("073", "kz_073"), ("088", "kz_088")):
                add(taxed_acq, kz, key)
    if any(D(u1_data.get(k, ZERO)) != ZERO for k in ("kz_060", "kz_065", "kz_066")):
        input_tax = ET.SubElement(declaration, "VORSTEUER")
        for kz, key in (("060", "kz_060"), ("065", "kz_065"), ("066", "kz_066")):
            add(input_tax, kz, key)
    return ET.tostring(root, encoding="iso-8859-1", xml_declaration=True).decode("iso-8859-1")


def finalize_u1_filing(
    session: Session,
    tenant_id: int,
    user_id: int,
    year: int,
) -> TaxFiling:
    """Finalize annual U1 filing and persist snapshot."""
    u1_data = compute_u1(session, tenant_id, year)
    xml_str = generate_u1_xml(session, tenant_id, year, u1_data)
    xml_hash = hashlib.sha256(xml_str.encode("iso-8859-1")).hexdigest()

    filing = session.exec(
        select(TaxFiling).where(
            TaxFiling.tenant_id == tenant_id,
            TaxFiling.filing_type == "u1",
            TaxFiling.year == year,
        )
    ).first()

    if not filing:
        filing = TaxFiling(
            tenant_id=tenant_id,
            filing_type="u1",
            period_key=str(year),
            year=year,
            version=1,
            status="finalized",
            xml_payload=xml_str,
            xml_hash=xml_hash,
            total_payable=u1_data["annual_tax_liability"],
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
        filing.total_payable = u1_data["annual_tax_liability"]
        filing.finalized_at = datetime.utcnow()
        session.add(filing)
        session.flush()

    summary_serializable = {k: str(v) for k, v in u1_data.items() if k != "event_ids"}
    ver = TaxFilingVersion(
        tenant_id=tenant_id,
        tax_filing_id=filing.id,
        version=filing.version,
        event_ids=json.dumps(u1_data["event_ids"]),
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
        response_payload="Local U1 XML snapshot generated; not submitted to FinanzOnline",
    )
    session.add(sub_log)

    from localizations.at.archive import store_archive_bytes
    store_archive_bytes(
        session, tenant_id, "tax_filing_xml", filing.id,
        f"U1_{year}_v{filing.version}.xml", "application/xml",
        xml_str.encode("iso-8859-1"), f"{year}-12-31",
    )

    session.flush()
    return filing
