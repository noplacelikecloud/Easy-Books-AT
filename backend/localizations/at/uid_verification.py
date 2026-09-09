"""EU VIES UID validation with auditable party status snapshots."""
from __future__ import annotations

from datetime import datetime
import re
import xml.etree.ElementTree as ET

import httpx
from fastapi import HTTPException
from sqlmodel import Session, select

from models import Customer, Vendor

VIES_URL = "https://ec.europa.eu/taxation_customs/vies/services/checkVatService"


def verify_party_uid(
    session: Session, tenant_id: int, party_type: str, party_id: int
) -> dict:
    model = Customer if party_type == "customer" else Vendor if party_type == "vendor" else None
    if model is None:
        raise HTTPException(422, "party_type muss 'customer' oder 'vendor' sein.")
    party = session.exec(select(model).where(model.id == party_id, model.tenant_id == tenant_id)).first()
    if not party:
        raise HTTPException(404, "Geschäftspartner nicht gefunden.")
    normalized = re.sub(r"[^A-Za-z0-9]", "", party.uid or "").upper()
    if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{2,12}", normalized):
        raise HTTPException(422, "UID hat kein gültiges EU-Format.")
    country, number = normalized[:2], normalized[2:]
    envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body><checkVat xmlns="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
    <countryCode>{country}</countryCode><vatNumber>{number}</vatNumber>
  </checkVat></soap:Body>
</soap:Envelope>"""
    try:
        response = httpx.post(
            VIES_URL, content=envelope,
            headers={"Content-Type": "text/xml; charset=utf-8"}, timeout=12,
        )
        response.raise_for_status()
        root = ET.fromstring(response.content)
        valid_node = next((node for node in root.iter() if node.tag.endswith("valid")), None)
        name_node = next((node for node in root.iter() if node.tag.endswith("name")), None)
        address_node = next((node for node in root.iter() if node.tag.endswith("address")), None)
        valid = valid_node is not None and (valid_node.text or "").lower() == "true"
    except (httpx.HTTPError, ET.ParseError) as exc:
        raise HTTPException(503, "VIES ist derzeit nicht erreichbar; UID-Prüfung wurde nicht gespeichert.") from exc
    party.uid = normalized
    party.uid_verification_status = "valid" if valid else "invalid"
    party.uid_verified_at = datetime.utcnow()
    party.uid_verification_method = "EU VIES checkVatService"
    session.add(party)
    session.flush()
    return {
        "party_type": party_type, "party_id": party.id, "uid": normalized,
        "valid": valid, "name": name_node.text if name_node is not None else None,
        "address": address_node.text if address_node is not None else None,
        "verified_at": party.uid_verified_at,
        "method": party.uid_verification_method,
    }
