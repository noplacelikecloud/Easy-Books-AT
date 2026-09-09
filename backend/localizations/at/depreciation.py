"""Austrian Fixed Asset Accounting & Tax Valuation (§§ 7, 8, 13 EStG 1988, § 203 UGB) (PR 13: AT-12).

Rules implemented:
- Halbjahres-AfA (§ 7 Abs. 2 EStG): Inbetriebnahmedatum nach dem 30. Juni bewirkt halbe Jahres-AfA
- Geringwertige Wirtschaftsgüter (GWG gem. § 13 EStG): Bis 1.000 € Netto-AK sofortige Vollabschreibung
- Degressive AfA (§ 7 Abs. 1a EStG): Max. 30 % auf den steuerlichen Restbuchwert;
  ausdrücklich ausgeschlossen für Gebäude, Pkw/Kombi, Firmenwert
- Vorsteuerabzugsquote in Anschaffungskosten: Netto-AK bei Vorsteuerabzug, Brutto-AK ohne Abzug (z. B. normaler PKW)
- Anlagenverzeichnis & Abschreibungslauf mit automatischer Buchung im Hauptbuch (Dr 8000 / Cr kumulierte AfA)
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from models import Account, FixedAsset, Transaction
from models_at import AtAssetDepreciation, AtAssetValuation
from services.money import D, ZERO, money
from services.posting import EntryInput, post_transaction


def register_asset_valuation(
    session: Session,
    tenant_id: int,
    asset_id: int,
    commissioning_date: str,
    initial_cost_gross: Decimal,
    input_vat_deducted: Decimal = ZERO,
    useful_life_years: Decimal = Decimal("5.0"),
    depreciation_method: str = "linear",
    asset_category: str = "other",
    is_gwg: Optional[bool] = None,
) -> AtAssetValuation:
    """Register Austrian statutory asset valuation with tax rules (§ 7, 8, 13 EStG)."""
    asset = session.exec(
        select(FixedAsset).where(FixedAsset.id == asset_id, FixedAsset.tenant_id == tenant_id)
    ).first()
    if not asset:
        raise HTTPException(404, "Anlage nicht gefunden.")
    # 1. Tax acquisition cost (Net if VAT deducted, gross if no VAT deduction)
    initial_tax = money(initial_cost_gross - input_vat_deducted)
    if initial_tax < ZERO:
        raise HTTPException(400, "Tax acquisition cost cannot be negative.")

    # 2. GWG validation (§ 13 EStG: limit 1,000.00 EUR)
    if is_gwg is None:
        is_gwg = (initial_tax <= Decimal("1000.00")) and (depreciation_method == "gwg")

    if is_gwg:
        if initial_tax > Decimal("1000.00"):
            raise HTTPException(
                400,
                f"GWG-Sofortabschreibung unzulässig: Anschaffungskosten {initial_tax} EUR "
                f"übersteigen den Grenzwert von 1.000,00 EUR gem. § 13 EStG.",
            )
        depreciation_method = "gwg"
        useful_life_years = Decimal("1.0")

    # 3. Degressive AfA exclusion check (§ 7 Abs. 1a EStG)
    if depreciation_method == "degressiv":
        if asset_category in ("pkw", "gebaeude", "goodwill"):
            raise HTTPException(
                400,
                f"Degressive AfA ist für die Kategorie '{asset_category}' gesetzlich ausgeschlossen "
                f"(§ 7 Abs. 1a EStG für Gebäude, Pkw und unkörperliche Wirtschaftsgüter).",
            )

    # 4. Halbjahres-AfA determination (§ 7 Abs. 2 EStG)
    parts = commissioning_date.split("-")
    month = int(parts[1])
    is_half_year = (month >= 7)

    # 5. First year depreciation calculation
    if depreciation_method == "gwg":
        current_depr = initial_tax
        book_val = ZERO
    elif depreciation_method == "linear":
        annual_afa = money(initial_tax / useful_life_years)
        current_depr = money(annual_afa * Decimal("0.5")) if is_half_year else annual_afa
        book_val = money(initial_tax - current_depr)
    elif depreciation_method == "degressiv":
        # Standard degressive rate is up to 2.5x linear rate, max 30%
        deg_rate = min(Decimal("30.00"), money(Decimal("100.00") / useful_life_years * Decimal("2.0")))
        annual_afa = money(initial_tax * deg_rate / Decimal("100.00"))
        current_depr = money(annual_afa * Decimal("0.5")) if is_half_year else annual_afa
        book_val = money(initial_tax - current_depr)
    else:
        raise HTTPException(400, f"Unknown depreciation method: {depreciation_method}")

    # Check for existing
    existing = session.exec(
        select(AtAssetValuation).where(
            AtAssetValuation.tenant_id == tenant_id,
            AtAssetValuation.asset_id == asset_id,
        )
    ).first()

    if existing:
        if session.exec(select(AtAssetDepreciation).where(
            AtAssetDepreciation.tenant_id == tenant_id,
            AtAssetDepreciation.valuation_id == existing.id,
        )).first():
            raise HTTPException(409, "Eine Anlage mit gebuchten AfA-Jahren kann nicht überschrieben werden.")
        existing.commissioning_date = commissioning_date
        existing.initial_cost_gross = initial_cost_gross
        existing.input_vat_deducted = input_vat_deducted
        existing.initial_cost_tax = initial_tax
        existing.depreciation_method = depreciation_method
        existing.half_year_rule_applied = is_half_year
        existing.useful_life_years = useful_life_years
        existing.tax_book_value = book_val
        existing.current_year_tax_depreciation = current_depr
        existing.is_gwg = is_gwg
        existing.asset_category = asset_category
        session.add(existing)
        session.flush()
        return existing

    val = AtAssetValuation(
        tenant_id=tenant_id,
        asset_id=asset_id,
        commissioning_date=commissioning_date,
        initial_cost_gross=initial_cost_gross,
        input_vat_deducted=input_vat_deducted,
        initial_cost_tax=initial_tax,
        depreciation_method=depreciation_method,
        half_year_rule_applied=is_half_year,
        useful_life_years=useful_life_years,
        tax_book_value=book_val,
        current_year_tax_depreciation=current_depr,
        is_gwg=is_gwg,
        asset_category=asset_category,
    )
    session.add(val)
    session.flush()
    return val


def get_asset_schedule(session: Session, tenant_id: int) -> List[Dict[str, Any]]:
    """Retrieve full statutory Austrian Anlagenverzeichnis (§ 7 EStG)."""
    valuations = session.exec(
        select(AtAssetValuation, FixedAsset)
        .join(FixedAsset, AtAssetValuation.asset_id == FixedAsset.id)
        .where(
            AtAssetValuation.tenant_id == tenant_id,
            FixedAsset.tenant_id == tenant_id,
        )
    ).all()

    schedule = []
    for val, fa in valuations:
        movements = session.exec(select(AtAssetDepreciation).where(
            AtAssetDepreciation.tenant_id == tenant_id,
            AtAssetDepreciation.valuation_id == val.id,
        ).order_by(AtAssetDepreciation.year)).all()
        schedule.append({
            "asset_id": fa.id,
            "name": fa.name,
            "commissioning_date": val.commissioning_date,
            "initial_cost_gross": float(val.initial_cost_gross),
            "input_vat_deducted": float(val.input_vat_deducted),
            "initial_cost_tax": float(val.initial_cost_tax),
            "depreciation_method": val.depreciation_method,
            "half_year_rule_applied": val.half_year_rule_applied,
            "useful_life_years": float(val.useful_life_years),
            "current_year_tax_depreciation": float(val.current_year_tax_depreciation),
            "tax_book_value": float(val.tax_book_value),
            "is_gwg": val.is_gwg,
            "asset_category": val.asset_category,
            "depreciation_movements": [movement.model_dump() for movement in movements],
        })
    return schedule


def post_annual_depreciation_run(
    session: Session,
    user: Any,
    year: int,
) -> Transaction:
    desc = f"Jahres-AfA {year} gem. § 7 EStG"
    existing_txn = session.exec(
        select(Transaction).where(
            Transaction.tenant_id == user.tenant_id,
            Transaction.description == desc,
            Transaction.is_reversed == False,  # noqa: E712
        )
    ).first()
    if existing_txn:
        raise HTTPException(
            400,
            f"AfA-Buchungslauf für das Wirtschaftsjahr {year} wurde bereits durchgeführt (Buchung #{existing_txn.id}).",
        )

    valuations = session.exec(
        select(AtAssetValuation, FixedAsset)
        .join(FixedAsset, AtAssetValuation.asset_id == FixedAsset.id)
        .where(
            AtAssetValuation.tenant_id == user.tenant_id,
            FixedAsset.tenant_id == user.tenant_id,
        )
    ).all()

    total_depr = ZERO
    entries: List[EntryInput] = []
    movements: list[AtAssetDepreciation] = []

    # EKR 7020 — planmäßige Abschreibung von Sachanlagen. (This used to post to
    # 8000, which the EKR assigns to Erträge aus Beteiligungen: the AfA debit
    # landed on an income account and skewed the Finanzergebnis.)
    depr_exp_acc = session.exec(
        select(Account).where(Account.tenant_id == user.tenant_id, Account.code == "7020")
    ).first()
    if not depr_exp_acc:
        depr_exp_acc = Account(
            tenant_id=user.tenant_id,
            code="7020",
            name="Planmäßige Abschreibung von Sachanlagen (AfA)",
            type="Expense",
        )
        session.add(depr_exp_acc)
        session.flush()

    for val, fa in valuations:
        commissioning_year = int(val.commissioning_date[:4])
        if year < commissioning_year:
            continue
        is_first_year = year == commissioning_year
        opening = money(D(val.initial_cost_tax) if is_first_year else D(val.tax_book_value))
        if opening <= ZERO:
            continue
        if is_first_year:
            depr_amt = min(opening, money(D(val.current_year_tax_depreciation)))
        elif val.depreciation_method == "gwg":
            depr_amt = ZERO
        elif val.depreciation_method == "linear":
            annual = money(D(val.initial_cost_tax) / D(val.useful_life_years))
            depr_amt = annual
            depr_amt = min(opening, depr_amt)
        elif val.depreciation_method == "degressiv":
            rate = min(D("30"), D("100") / D(val.useful_life_years) * D("2"))
            depr_amt = money(opening * rate / D("100"))
            depr_amt = min(opening, depr_amt)
        else:
            raise HTTPException(422, f"Unbekannte AfA-Methode: {val.depreciation_method}")
        if depr_amt > ZERO:
            total_depr += depr_amt
            # Credit accumulated depr or direct asset account
            credit_acc_id = fa.accum_depr_account_id or fa.asset_account_id
            entries.append(EntryInput(account_id=credit_acc_id, credit=depr_amt))
            closing = money(opening - depr_amt)
            movements.append(AtAssetDepreciation(
                tenant_id=user.tenant_id,
                valuation_id=val.id,
                year=year,
                opening_tax_book_value=opening,
                depreciation_amount=depr_amt,
                closing_tax_book_value=closing,
            ))
            val.current_year_tax_depreciation = depr_amt
            val.tax_book_value = closing
            session.add(val)

    if total_depr == ZERO:
        raise HTTPException(400, "Keine Abschreibungen für dieses Wirtschaftsjahr zu buchen.")

    # Debit total depreciation to 8000
    entries.insert(0, EntryInput(account_id=depr_exp_acc.id, debit=total_depr))

    txn = post_transaction(
        session=session,
        user=user,
        date=f"{year}-12-31",
        description=f"Jahres-AfA {year} gem. § 7 EStG",
        entries=entries,
        voucher_type="JV",
    )
    for movement in movements:
        movement.transaction_id = txn.id
        session.add(movement)
    session.flush()
    return txn
