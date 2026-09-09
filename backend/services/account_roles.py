"""Semantic Account Role Binding Service for Austrian Compliance (PR 4, AT-05, AT-11).

Maps semantic roles (e.g. accounts_receivable, accounts_payable, vat_output,
retained_earnings) to concrete tenant accounts without hardcoded numbers (§ 190 UGB).
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from sqlmodel import Session, select

from models import Account
from models_at import AccountRoleBinding


# Standard role fallback heuristcs for legacy / non-AT fallback
DEFAULT_ROLE_FALLBACKS: Dict[str, tuple[str, str, str]] = {
    "accounts_receivable": ("1100", "Accounts Receivable", "Asset"),
    "accounts_payable": ("2100", "Accounts Payable", "Liability"),
    "cash": ("1000", "Cash in Hand", "Asset"),
    "bank": ("1010", "Main Bank Account", "Asset"),
    "inventory": ("1200", "Inventory (Raw Material)", "Asset"),
    "revenue": ("4000", "Sales Revenue", "Revenue"),
    "expense": ("5000", "General Operating Expense", "Expense"),
    "retained_earnings": ("3100", "Retained Earnings", "Equity"),
    "vat_output": ("2200", "GST / VAT Payable (Output)", "Liability"),
    "vat_input": ("1250", "GST / VAT Receivable (Input)", "Asset"),
    "vat_rc_output": ("2210", "Reverse Charge Tax Liability", "Liability"),
    "vat_rc_input": ("1260", "Reverse Charge Input Tax", "Asset"),
    "customer_advances": ("2150", "Customer Advances", "Liability"),
    "vendor_advances": ("1150", "Vendor Advances", "Asset"),
    "rounding_difference": ("5990", "Rounding Differences", "Expense"),
    "cogs": ("5010", "Cost of Goods Sold", "Expense"),
}


def resolve_account_role(
    session: Session,
    tenant_id: int,
    role_key: str,
    on_date: Optional[str] = None,
) -> Optional[Account]:
    """Resolve an account bound to a semantic role for the tenant."""
    query = select(AccountRoleBinding).where(
        AccountRoleBinding.tenant_id == tenant_id,
        AccountRoleBinding.role_key == role_key,
    )
    if on_date:
        query = query.where(AccountRoleBinding.valid_from <= on_date)
        query = query.where(
            (AccountRoleBinding.valid_to == None)  # noqa: E711
            | (AccountRoleBinding.valid_to >= on_date)
        )
    binding = session.exec(query.order_by(AccountRoleBinding.valid_from.desc())).first()
    if binding:
        return session.get(Account, binding.account_id)

    # Fallback to standard code lookup if role not explicitly mapped
    if role_key in DEFAULT_ROLE_FALLBACKS:
        code, name, acc_type = DEFAULT_ROLE_FALLBACKS[role_key]
        acc = session.exec(
            select(Account).where(
                Account.tenant_id == tenant_id,
                Account.code == code,
            )
        ).first()
        if acc:
            return acc

    return None


def bind_account_role(
    session: Session,
    tenant_id: int,
    role_key: str,
    account_id: int,
    valid_from: str = "1900-01-01",
) -> AccountRoleBinding:
    """Bind an account to a semantic role, updating or creating the binding."""
    existing = session.exec(
        select(AccountRoleBinding).where(
            AccountRoleBinding.tenant_id == tenant_id,
            AccountRoleBinding.role_key == role_key,
            AccountRoleBinding.valid_from == valid_from,
        )
    ).first()
    if existing:
        existing.account_id = account_id
        session.add(existing)
        session.flush()
        return existing

    binding = AccountRoleBinding(
        tenant_id=tenant_id,
        role_key=role_key,
        account_id=account_id,
        valid_from=valid_from,
    )
    session.add(binding)
    session.flush()
    return binding
