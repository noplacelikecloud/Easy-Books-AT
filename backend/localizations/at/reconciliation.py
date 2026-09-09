"""Austrian VAT Reconciliation Engine (PR 10: AT-10).

Reconciles General Ledger VAT accounts vs TaxEvents vs UVA Kennzahlen (§ 21 UStG).
Detects posting discrepancies before tax filings are finalized.
"""
from __future__ import annotations

import calendar
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from models import Account, JournalEntry, Transaction
from models_at import AccountRoleBinding, TaxEvent
from localizations.at.uva import compute_uva
from services.account_roles import resolve_account_role
from services.money import D, ZERO, money


def reconcile_vat_period(
    session: Session,
    tenant_id: int,
    period_key: str,
) -> Dict[str, Any]:
    """Perform three-way reconciliation: GL Balances ↔ TaxEvents ↔ UVA Form Kennzahlen."""
    # 1. TaxEvent figures
    uva = compute_uva(session, tenant_id, period_key)
    events_output_tax = uva["total_output_tax"]
    events_input_tax = uva["total_input_tax"]
    events_net_payable = uva["kz_095"]

    # 2. General Ledger balances for the tax period
    # Resolve role bindings for tax accounts
    output_roles = [
        "vat_output",
        "vat_output_20", "vat_output_10", "vat_output_13", "vat_output_4_9",
        "vat_rc_output", "vat_rc_eu_payable", "vat_ig_acquisition_tax", "vat_rc_domestic_payable",
    ]
    input_roles = [
        "vat_input",
        "vat_input_20", "vat_input_10", "vat_input_13", "vat_input_4_9",
        "vat_rc_input", "vat_ig_acquisition_input", "vat_rc_eu_input", "vat_rc_domestic_input",
    ]

    output_acc_ids: List[int] = []
    for r in output_roles:
        acc = resolve_account_role(session, tenant_id, r)
        if acc:
            output_acc_ids.append(acc.id)

    input_acc_ids: List[int] = []
    for r in input_roles:
        acc = resolve_account_role(session, tenant_id, r)
        if acc:
            input_acc_ids.append(acc.id)

    # Determine date range for period_key
    parts = period_key.split("-")
    year = int(parts[0])
    if parts[1].startswith("Q"):
        q = int(parts[1][1:])
        start_month = (q - 1) * 3 + 1
        end_month = q * 3
        last_day = calendar.monthrange(year, end_month)[1]
        start_date = f"{year:04d}-{start_month:02d}-01"
        end_date = f"{year:04d}-{end_month:02d}-{last_day:02d}"
    else:
        month = int(parts[1])
        last_day = calendar.monthrange(year, month)[1]
        start_date = f"{year:04d}-{month:02d}-01"
        end_date = f"{year:04d}-{month:02d}-{last_day:02d}"

    # Query GL lines
    gl_output_tax = ZERO
    if output_acc_ids:
        out_lines = session.exec(
            select(JournalEntry)
            .join(Transaction)
            .where(
                JournalEntry.tenant_id == tenant_id,
                JournalEntry.account_id.in_(output_acc_ids),
                Transaction.date >= start_date,
                Transaction.date <= end_date,
            )
        ).all()
        # VAT output is credited on sale (Credit increases liability)
        for ln in out_lines:
            gl_output_tax += (D(ln.credit) - D(ln.debit))

    gl_input_tax = ZERO
    if input_acc_ids:
        in_lines = session.exec(
            select(JournalEntry)
            .join(Transaction)
            .where(
                JournalEntry.tenant_id == tenant_id,
                JournalEntry.account_id.in_(input_acc_ids),
                Transaction.date >= start_date,
                Transaction.date <= end_date,
            )
        ).all()
        # VAT input is debited on purchase (Debit increases asset/receivable)
        for ln in in_lines:
            gl_input_tax += (D(ln.debit) - D(ln.credit))

    gl_output_tax = money(gl_output_tax)
    gl_input_tax = money(gl_input_tax)
    gl_net_payable = money(gl_output_tax - gl_input_tax)

    diff_output = money(gl_output_tax - events_output_tax)
    diff_input = money(gl_input_tax - events_input_tax)
    diff_net = money(gl_net_payable - events_net_payable)

    # Reconciled if diff within 0.05 EUR tolerance
    is_reconciled = all(
        abs(diff) <= Decimal("0.05")
        for diff in (diff_output, diff_input, diff_net)
    )

    discrepancies: List[str] = []
    if abs(diff_output) > Decimal("0.05"):
        discrepancies.append(f"Ausgangssteuer-Differenz GL vs Events: {diff_output} EUR")
    if abs(diff_input) > Decimal("0.05"):
        discrepancies.append(f"Vorsteuer-Differenz GL vs Events: {diff_input} EUR")

    return {
        "period_key": period_key,
        "is_reconciled": is_reconciled,
        "gl_output_tax": gl_output_tax,
        "events_output_tax": events_output_tax,
        "diff_output": diff_output,
        "gl_input_tax": gl_input_tax,
        "events_input_tax": events_input_tax,
        "diff_input": diff_input,
        "gl_net_payable": gl_net_payable,
        "events_net_payable": events_net_payable,
        "diff_net": diff_net,
        "discrepancies": discrepancies,
    }
