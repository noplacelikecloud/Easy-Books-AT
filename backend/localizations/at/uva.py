"""Austrian VAT Advance Return (UVA / U30) Calculation and XML Generator (PR 10: AT-10).

Calculates statutory Kennzahlen (KZ) per § 21 UStG 1994 from finalized TaxEvents:
- KZ 000: Gesamtbetrag der Bemessungsgrundlagen der steuerbaren Lieferungen und sonstigen Leistungen
- KZ 022: Lieferungen/Leistungen 20 %
- KZ 029: Lieferungen/Leistungen 10 %
- KZ 006: Lieferungen/Leistungen 13 %
- KZ 124: Lieferungen/Leistungen 4,9 % (ab 01.07.2026 bzw. Q3/2026)
- KZ 125: Steuer auf 4,9 %
- KZ 011: Steuerfreie Ausfuhren (§ 6 Abs. 1 Z 1 UStG)
- KZ 017: Steuerfreie innergemeinschaftliche Lieferungen (Art. 6 UStG)
- KZ 016: Steuerfreie Umsätze ohne Vorsteuerabzug (Kleinunternehmer § 6 Abs. 1 Z 27)
- KZ 021: Übergang der Steuerschuld Ausgang (Reverse Charge Bau/B2B EU Dienstleistungen)
- KZ 070: Innergemeinschaftliche Erwerbe (Art. 1 UStG) Bemessungsgrundlage
- KZ 072: Erwerbsteuer 20 %
- KZ 073: Erwerbsteuer 10 %
- KZ 088: Erwerbsteuer 13 %
- KZ 057: Steuerschuld gemäß § 19 (Reverse Charge Eingang)
- KZ 060: Vorsteuerbeträge aus Rechnungen anderer Unternehmer
- KZ 065: Vorsteuer aus dem innergemeinschaftlichen Erwerb
- KZ 066: Vorsteuer bei Übergang der Steuerschuld
- KZ 095: Vorauszahlung / Restguthaben (Gesamte Zahllast / Gutschrift)
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


def compute_uva(session: Session, tenant_id: int, period_key: str) -> Dict[str, Any]:
    """Compute official Austrian UVA U30 Kennzahlen from finalized TaxEvents."""
    events = session.exec(
        select(TaxEvent).where(
            TaxEvent.tenant_id == tenant_id,
            TaxEvent.tax_period == period_key,
            TaxEvent.state == "final",
        )
    ).all()

    # Base Kennzahlen
    kz_022_base = ZERO
    kz_022_tax = ZERO
    kz_029_base = ZERO
    kz_029_tax = ZERO
    kz_006_base = ZERO
    kz_006_tax = ZERO
    kz_124_base = ZERO
    kz_124_tax = ZERO
    kz_011_base = ZERO
    kz_017_base = ZERO
    kz_016_base = ZERO
    kz_021_base = ZERO

    # Intra-EU acquisitions
    kz_070_base = ZERO
    kz_125_acquisition_base = ZERO
    kz_072_tax = ZERO
    kz_073_tax = ZERO
    kz_088_tax = ZERO

    # Reverse Charge liability
    kz_057_tax = ZERO

    # Input tax deductions
    kz_060_input = ZERO
    kz_065_input = ZERO
    kz_066_input = ZERO

    event_ids: List[int] = []

    for ev in events:
        if ev.id:
            event_ids.append(ev.id)

        # Sales / Output tax
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
                kz_124_tax += tax
            elif ev.uva_base_kz == "011":
                kz_011_base += base
            elif ev.uva_base_kz == "017":
                kz_017_base += base
            elif ev.uva_base_kz == "016":
                kz_016_base += base
            elif ev.uva_base_kz == "021":
                kz_021_base += base

        # Purchases / Input tax & Reverse Charge
        elif getattr(ev, "direction", "sales") == "purchases":
            base = money(ev.base_amount_eur)

            if ev.treatment_code.startswith("AT_IG_ACQUISITION"):
                kz_070_base += base
                if "4_9" in ev.treatment_code:
                    kz_125_acquisition_base += base
                elif "10" in ev.treatment_code:
                    kz_073_tax += money(ev.output_tax)
                elif "13" in ev.treatment_code:
                    kz_088_tax += money(ev.output_tax)
                else:
                    kz_072_tax += money(ev.output_tax)
                kz_065_input += money(ev.input_tax_deductible)
            elif ev.treatment_code.startswith("AT_RC_"):
                kz_057_tax += money(ev.reverse_charge_tax)
                kz_066_input += money(ev.input_tax_deductible)
            else:
                # Regular domestic input tax
                kz_060_input += money(ev.input_tax_deductible)

    # KZ 000: Gesamtbetrag der Bemessungsgrundlagen der Lieferungen/Leistungen
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
        + kz_124_tax
        + kz_072_tax
        + kz_073_tax
        + kz_088_tax
        + kz_057_tax
    )

    total_input_tax = kz_060_input + kz_065_input + kz_066_input

    # KZ 095: Vorauszahlung / Restguthaben
    kz_095 = money(total_output_tax - total_input_tax)

    return {
        "period_key": period_key,
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
        "kz_124_tax": money(kz_124_tax),
        "kz_125": money(kz_125_acquisition_base),
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
        "kz_095": kz_095,
    }


def generate_uva_xml(
    session: Session,
    tenant_id: int,
    period_key: str,
    uva_data: Dict[str, Any],
) -> str:
    """Generate the BMF ``ERKLAERUNGS_UEBERMITTLUNG`` U30 XML (07/2026)."""
    prof = get_active_profile(session, tenant_id)
    if not prof:
        raise HTTPException(422, "Kein aktives AT-Profil vorhanden.")
    fastnr = re.sub(r"\D", "", prof.tax_number or "")
    if len(fastnr) != 9 or not (10_000_010 <= int(fastnr) <= 989_999_999):
        raise HTTPException(422, "Für den FinanzOnline-Export ist eine gültige neunstellige FASTNR erforderlich.")

    # Parse period
    parts = period_key.split("-")
    year_str = parts[0]
    if len(parts) != 2:
        raise HTTPException(422, "Ungültiger UVA-Zeitraum.")
    if parts[1].startswith("Q"):
        quarter = int(parts[1][1:])
        if quarter not in (1, 2, 3, 4):
            raise HTTPException(422, "Ungültiges Quartal.")
        start_month, end_month = (quarter - 1) * 3 + 1, quarter * 3
    else:
        start_month = end_month = int(parts[1])
        if start_month not in range(1, 13):
            raise HTTPException(422, "Ungültiger Monat.")
    zr_von = f"{year_str}-{start_month:02d}"
    zr_bis = f"{year_str}-{end_month:02d}"
    now = datetime.now()

    def amount(parent: ET.Element, kz: str, value: Any, *, allow_zero: bool = False) -> None:
        val = money(D(value or ZERO))
        if val < ZERO:
            raise HTTPException(422, f"KZ {kz} darf im amtlichen U30-Schema nicht negativ sein.")
        if val == ZERO and not allow_zero:
            return
        ET.SubElement(parent, f"KZ{kz}", {"type": "kz"}).text = f"{val:.2f}"

    root = ET.Element("ERKLAERUNGS_UEBERMITTLUNG")
    info = ET.SubElement(root, "INFO_DATEN")
    ET.SubElement(info, "ART_IDENTIFIKATIONSBEGRIFF").text = "FASTNR"
    ET.SubElement(info, "IDENTIFIKATIONSBEGRIFF").text = fastnr
    ET.SubElement(info, "PAKET_NR").text = str(int(now.strftime("%j%H%M%S")))
    ET.SubElement(info, "DATUM_ERSTELLUNG", {"type": "datum"}).text = now.date().isoformat()
    ET.SubElement(info, "UHRZEIT_ERSTELLUNG", {"type": "uhrzeit"}).text = now.time().replace(microsecond=0).isoformat()
    ET.SubElement(info, "ANZAHL_ERKLAERUNGEN").text = "1"
    declaration = ET.SubElement(root, "ERKLAERUNG", {"art": "U30"})
    ET.SubElement(declaration, "SATZNR").text = "1"
    general = ET.SubElement(declaration, "ALLGEMEINE_DATEN")
    ET.SubElement(general, "ANBRINGEN").text = "U30"
    ET.SubElement(general, "ZRVON", {"type": "jahrmonat"}).text = zr_von
    ET.SubElement(general, "ZRBIS", {"type": "jahrmonat"}).text = zr_bis
    ET.SubElement(general, "FASTNR").text = fastnr
    ET.SubElement(general, "KUNDENINFO").text = f"OpenBooksAT {period_key}"[:50]

    supplies = ET.SubElement(declaration, "LIEFERUNGEN_LEISTUNGEN_EIGENVERBRAUCH")
    amount(supplies, "000", uva_data.get("kz_000"), allow_zero=True)
    amount(supplies, "021", uva_data.get("kz_021"))
    exempt_values = [("011", "kz_011"), ("017", "kz_017"), ("016", "kz_016")]
    if any(D(uva_data.get(key, ZERO)) != ZERO for _, key in exempt_values):
        exempt = ET.SubElement(supplies, "STEUERFREI")
        for kz, key in exempt_values:
            amount(exempt, kz, uva_data.get(key))
    taxed_values = [("022", "kz_022"), ("124", "kz_124"), ("029", "kz_029"), ("006", "kz_006"), ("057", "kz_057")]
    if any(D(uva_data.get(key, ZERO)) != ZERO for _, key in taxed_values):
        taxed = ET.SubElement(supplies, "VERSTEUERT")
        for kz, key in taxed_values:
            amount(taxed, kz, uva_data.get(key))

    acquisition_values = [("072", "kz_072"), ("125", "kz_125"), ("073", "kz_073"), ("088", "kz_088")]
    if D(uva_data.get("kz_070", ZERO)) != ZERO or any(D(uva_data.get(key, ZERO)) != ZERO for _, key in acquisition_values):
        acquisitions = ET.SubElement(declaration, "INNERGEMEINSCHAFTLICHE_ERWERBE")
        amount(acquisitions, "070", uva_data.get("kz_070"), allow_zero=True)
        if any(D(uva_data.get(key, ZERO)) != ZERO for _, key in acquisition_values):
            taxed_acquisitions = ET.SubElement(acquisitions, "VERSTEUERT_IGE")
            for kz, key in acquisition_values:
                amount(taxed_acquisitions, kz, uva_data.get(key))

    input_values = [("060", "kz_060"), ("065", "kz_065"), ("066", "kz_066")]
    if any(D(uva_data.get(key, ZERO)) != ZERO for _, key in input_values):
        input_tax = ET.SubElement(declaration, "VORSTEUER")
        for kz, key in input_values:
            amount(input_tax, kz, uva_data.get(key))

    return ET.tostring(root, encoding="iso-8859-1", xml_declaration=True).decode("iso-8859-1")


def finalize_uva_filing(
    session: Session,
    tenant_id: int,
    user_id: int,
    period_key: str,
) -> TaxFiling:
    """Finalize UVA filing, snapshotting events, XML payload and hash immutably (§ 21 UStG)."""
    from localizations.at.reconciliation import reconcile_vat_period
    reconciliation = reconcile_vat_period(session, tenant_id, period_key)
    if not reconciliation["is_reconciled"]:
        raise HTTPException(
            409,
            "UVA kann erst nach vollständiger Abstimmung von Hauptbuch und Steuerereignissen finalisiert werden: "
            + "; ".join(reconciliation["discrepancies"]),
        )
    uva_data = compute_uva(session, tenant_id, period_key)
    xml_str = generate_uva_xml(session, tenant_id, period_key, uva_data)
    xml_bytes = xml_str.encode("iso-8859-1")
    xml_hash = hashlib.sha256(xml_bytes).hexdigest()

    parts = period_key.split("-")
    year = int(parts[0])

    # Find existing filing
    filing = session.exec(
        select(TaxFiling).where(
            TaxFiling.tenant_id == tenant_id,
            TaxFiling.filing_type == "uva",
            TaxFiling.period_key == period_key,
        )
    ).first()

    if not filing:
        filing = TaxFiling(
            tenant_id=tenant_id,
            filing_type="uva",
            period_key=period_key,
            year=year,
            version=1,
            status="finalized",
            xml_payload=xml_str,
            xml_hash=xml_hash,
            total_payable=uva_data["kz_095"],
            created_at=datetime.utcnow(),
            finalized_at=datetime.utcnow(),
        )
        session.add(filing)
        session.flush()
    else:
        # Increment version for correction (Berichtigung)
        filing.version += 1
        filing.status = "finalized"
        filing.xml_payload = xml_str
        filing.xml_hash = xml_hash
        filing.total_payable = uva_data["kz_095"]
        filing.finalized_at = datetime.utcnow()
        session.add(filing)
        session.flush()

    # Create immutable version record
    summary_serializable = {k: str(v) for k, v in uva_data.items() if k != "event_ids"}
    ver = TaxFilingVersion(
        tenant_id=tenant_id,
        tax_filing_id=filing.id,
        version=filing.version,
        event_ids=json.dumps(uva_data["event_ids"]),
        summary_data=json.dumps(summary_serializable),
        xml_payload=xml_str,
        xml_hash=xml_hash,
        created_at=datetime.utcnow(),
    )
    session.add(ver)

    # This is a local, immutable generation record; it is not a submission receipt.
    sub_log = TaxFilingSubmissionLog(
        tenant_id=tenant_id,
        tax_filing_id=filing.id,
        submitted_at=datetime.utcnow(),
        status="local_generated",
        request_hash=xml_hash,
        response_payload="Local XML snapshot generated; not submitted to FinanzOnline",
    )
    session.add(sub_log)

    from localizations.at.archive import store_archive_bytes
    store_archive_bytes(
        session, tenant_id, "tax_filing_xml", filing.id,
        f"UVA_{period_key}_v{filing.version}.xml", "application/xml",
        xml_bytes, f"{year}-12-31",
    )

    session.flush()
    return filing
