"""Austrian Corporate Income Tax (KSt) Workpapers & Mehr-/Weniger-Rechnung (PR 15: AT-10, KStG 1988).

Rules implemented:
- 23 % Körperschaftsteuersatz (§ 22 Abs. 1 KStG ab 2024/2026)
- Mehr-/Weniger-Rechnung (MWR) zur Überleitung vom UGB-Ergebnis zum steuerlichen Einkommen:
  + Nicht abzugsfähige Aufwendungen (§ 12 KStG: z. B. 50 % Geschäftsessen, Strafen)
  + Kfz-Luxustangente (> 40.000 € Anschaffungskosten)
  - Steuerfreie Beteiligungserträge (§ 10 KStG)
- Mindest-Körperschaftsteuer (§ 24 Abs. 4 KStG):
  Mindestens 500 € / Jahr für Neugründungen (GmbH / FlexCo in den ersten 5 Jahren)
- Strikt frei von ausländischen / pakistanischen Steuertarifen
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlmodel import Session

from localizations.at.profile import get_active_profile
from localizations.at.ugb_reports import compute_ugb_income_statement
from services.money import D, ZERO, money


MINDEST_KST_GMBH = Decimal("500.00")


def corporate_tax_rate(year: int) -> Decimal:
    if year <= 2022:
        return Decimal("25.00")
    if year == 2023:
        return Decimal("24.00")
    return Decimal("23.00")


def compute_austrian_corporate_tax_workpaper(
    session: Session,
    tenant_id: int,
    year: int,
    non_deductible_expenses: Decimal = ZERO,
    luxury_car_addback: Decimal = ZERO,
    tax_exempt_dividends: Decimal = ZERO,
    loss_carryforward: Decimal = ZERO,
    is_new_incorporation: bool = True,
) -> Dict[str, Any]:
    """Compute statutory Austrian Corporate Income Tax workpaper and Mehr-/Weniger-Rechnung."""
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    profile = get_active_profile(session, tenant_id, end_date)
    if not profile or profile.legal_form not in {"gmbh", "flexco"}:
        raise HTTPException(422, "Das KSt-Arbeitsblatt ist nur für österreichische Kapitalgesellschaften verfügbar.")

    # 1. Commercial profit before income taxes under § 231 UGB.
    guv = compute_ugb_income_statement(session, tenant_id, start_date, end_date)
    pre_tax_line = next((row for row in guv["lines"] if row["position"] == "16"), None)
    ugb_profit = D(pre_tax_line["current"] if pre_tax_line else guv["net_income_current"])

    # 2. Mehr-/Weniger-Rechnung (MWR) adjustments
    additions = money(non_deductible_expenses + luxury_car_addback)
    deductions = money(tax_exempt_dividends)

    # Steuerlicher Gesamtbetrag der Einkünfte vor Verlustvortrag
    taxable_before_losses = money(ugb_profit + additions - deductions)

    # 3. Loss carryforward utilization (75% cap per § 8 Abs. 4 KStG)
    allowed_loss_deduction = ZERO
    if taxable_before_losses > ZERO and loss_carryforward > ZERO:
        max_deduction = money(taxable_before_losses * Decimal("0.75"))
        allowed_loss_deduction = min(loss_carryforward, max_deduction)

    taxable_income = money(max(ZERO, taxable_before_losses - allowed_loss_deduction))

    # 4. 23% KSt computation
    rate = corporate_tax_rate(year)
    calculated_kst = money(taxable_income * rate / Decimal("100.00"))

    # 5. Minimum Corporate Tax (§ 24 Abs. 4 KStG)
    mindest_kst = MINDEST_KST_GMBH
    final_kst = max(calculated_kst, mindest_kst)

    steps = [
        {"step": "1", "label": "UGB Jahresergebnis vor Ertragsteuern", "amount": float(ugb_profit)},
        {"step": "2", "label": "+ Nicht abzugsfähige Aufwendungen (§ 12 KStG)", "amount": float(non_deductible_expenses)},
        {"step": "3", "label": "+ Kfz-Luxustangente (> 40.000 €)", "amount": float(luxury_car_addback)},
        {"step": "4", "label": "- Steuerfreie Beteiligungserträge (§ 10 KStG)", "amount": -float(deductions)},
        {"step": "5", "label": "Steuerlicher Gewinn vor Verlustabzug", "amount": float(taxable_before_losses), "is_subtotal": True},
        {"step": "6", "label": "- Verrechneter Verlustvortrag (max. 75 % gem. § 8 Abs. 4 KStG)", "amount": -float(allowed_loss_deduction)},
        {"step": "7", "label": "Steuerliche Bemessungsgrundlage (Einkommen)", "amount": float(taxable_income), "is_subtotal": True},
        {"step": "8", "label": f"Körperschaftsteuer ({rate} % KStG)", "amount": float(calculated_kst)},
        {"step": "9", "label": "Gesetzliche Mindest-KSt (§ 24 Abs. 4 KStG)", "amount": float(mindest_kst)},
        {"step": "10", "label": "Festzusetzende Körperschaftsteuer (KSt)", "amount": float(final_kst), "is_total": True},
    ]

    return {
        "fiscal_year": year,
        "tax_type": "Körperschaftsteuer (KSt)",
        "statutory_rate_pct": float(rate),
        "steps": steps,
        "ugb_profit": float(ugb_profit),
        "taxable_income": float(taxable_income),
        "calculated_kst": float(calculated_kst),
        "mindest_kst": float(mindest_kst),
        "final_tax_liability": float(final_kst),
    }
