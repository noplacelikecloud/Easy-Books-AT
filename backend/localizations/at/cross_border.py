"""Austrian Cross-Border and Reverse Charge VAT Determination (PR 8: AT-04).

Covers:
- Innergemeinschaftliche Lieferung (Art. 6 Abs. 1 UStG)
- Innergemeinschaftlicher Erwerb (Art. 1 UStG)
- Dienstleistungsexport B2B EU Reverse Charge (§ 3a Abs. 6 UStG)
- Dienstleistungsimport B2B EU Reverse Charge (§ 19 Abs. 1 UStG)
- Bauleistungen / Inländisches Reverse Charge (§ 19 Abs. 1a UStG)
- Ausfuhrlieferung Drittland (§ 6 Abs. 1 Z 1 UStG)
"""
from __future__ import annotations

from typing import Optional

EU_COUNTRY_CODES = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR",
    "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO",
    "SE", "SI", "SK",
}


def is_eu_country(country_code: Optional[str]) -> bool:
    if not country_code:
        return False
    return country_code.strip().upper() in EU_COUNTRY_CODES


def determine_cross_border_treatment(
    direction: str,  # sales | purchases
    partner_country: Optional[str],
    partner_vat_id: Optional[str],
    is_b2b: bool = True,
    is_service: bool = False,
    is_construction: bool = False,
    domestic_country: str = "AT",
) -> str:
    """Determine statutory Austrian tax treatment code for cross-border and RC scenarios."""
    partner_c = (partner_country or domestic_country).strip().upper()

    # 1. Domestic transactions
    if partner_c == domestic_country:
        if is_construction and is_b2b:
            return "AT_RC_DOMESTIC"
        return "AT_STANDARD_20"

    # 2. Sales (Outbound)
    if direction == "sales":
        if is_eu_country(partner_c):
            if is_b2b and partner_vat_id:
                if is_service:
                    return "AT_RC_EU_SERVICE_OUT"
                return "AT_ZERO_IG_SUPPLY"
            # B2C EU sales standard rate / OSS
            return "AT_STANDARD_20"
        else:
            # Third country export
            return "AT_ZERO_EXPORT"

    # 3. Purchases (Inbound)
    if direction == "purchases":
        if is_eu_country(partner_c):
            if is_service:
                return "AT_RC_EU_SERVICE_IN"
            return "AT_IG_ACQUISITION_20"
        else:
            # Third country import
            return "AT_STANDARD_20"

    return "AT_STANDARD_20"
