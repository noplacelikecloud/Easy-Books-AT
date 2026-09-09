"""Austrian Cash Accounting (Einnahmen-Ausgaben-Rechnung / EAR) & E1a Tax Form Mapping (PR 12: AT-11, § 4 Abs. 3 EStG 1988).

Implements:
- Zufluss- und Abflussprinzip gem. § 19 EStG
- Offizielle Kennzahlen der Beilage E1a zur Einkommensteuererklärung:
  - KZ 9040: Erlöse 20 %
  - KZ 9050: Erlöse 10 %
  - KZ 9060: Erlöse 13 %
  - KZ 9070: Erlöse 4,9 %
  - KZ 9090: Steuerfreie Erlöse (u. a. Kleinunternehmer)
  - KZ 9100: Summe Betriebseinnahmen
  - KZ 9120: Waren, Roh-, Hilfs- und Betriebsstoffe
  - KZ 9130: Bezogene Fremdleistungen
  - KZ 9140: Personalaufwand
  - KZ 9150: AfA (Absetzung für Abnutzung gem. § 7 EStG)
  - KZ 9160: Geringwertige Wirtschaftsgüter (GWG bis 1.000 €)
  - KZ 9170: Kfz-Kosten (betrieblicher Anteil)
  - KZ 9180: Miete und Pacht
  - KZ 9220: Zinsen und Geldbeschaffungskosten
  - KZ 9230: Übrige Betriebsausgaben
  - KZ 9240: Summe Betriebsausgaben
  - KZ 9250: Vorläufiges Ergebnis (Betriebseinnahmen ./. Betriebsausgaben)
  - KZ 9260: Steuerliche Zurechnungen (Privatanteile Telefon, Kfz, Bewirtung 50 %)
  - KZ 9290: Steuerlicher Gewinn / Verlust (Reingewinn)
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from models import (
    Account, Bill, BillLine, BillPayment, Invoice, InvoiceLine, JournalEntry,
    PaymentAllocation, PaymentReceived, Product, Transaction,
)
from models_at import AtAssetDepreciation, AtAssetValuation, TaxEvent
from services.money import D, ZERO, money


def compute_ear_report(
    session: Session,
    tenant_id: int,
    year: int,
    private_share_adjustments: Decimal = ZERO,
) -> Dict[str, Any]:
    """Compute statutory Austrian Einnahmen-Ausgaben-Rechnung and Form E1a figures."""
    year_str = str(year)
    start_date = f"{year_str}-01-01"
    end_date = f"{year_str}-12-31"

    payment_txn_ids = {
        txn_id for txn_id in session.exec(
            select(PaymentReceived.transaction_id).where(
                PaymentReceived.tenant_id == tenant_id,
                PaymentReceived.payment_date >= start_date,
                PaymentReceived.payment_date <= end_date,
            )
        ).all() if txn_id
    }
    payment_txn_ids.update({
        txn_id for txn_id in session.exec(
            select(BillPayment.transaction_id).where(
                BillPayment.tenant_id == tenant_id,
                BillPayment.payment_date >= start_date,
                BillPayment.payment_date <= end_date,
            )
        ).all() if txn_id
    })

    # Only direct cash/bank vouchers are read from GL. Sales and purchase
    # settlements are calculated from allocations below, avoiding accrual JVs.
    entries = session.exec(
        select(JournalEntry, Account, Transaction)
        .join(Account, JournalEntry.account_id == Account.id)
        .join(Transaction, JournalEntry.transaction_id == Transaction.id)
        .where(
            JournalEntry.tenant_id == tenant_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.voucher_type.in_(["CR", "BR", "CP", "BP"]),
        )
    ).all()

    # Aggregate by account codes
    net_sales_20 = ZERO
    net_sales_10 = ZERO
    net_sales_13 = ZERO
    net_sales_4_9 = ZERO
    net_sales_exempt = ZERO

    goods_expense = ZERO
    subcontracting = ZERO
    payroll_expense = ZERO
    gwg_expense = ZERO
    rent_expense = ZERO
    car_expense = ZERO
    interest_expense = ZERO
    other_operating_expense = ZERO

    # Allocated customer receipts: recognise net business income at inflow.
    receipt_rows = session.exec(
        select(PaymentAllocation, PaymentReceived, Invoice)
        .join(PaymentReceived, PaymentAllocation.payment_received_id == PaymentReceived.id)
        .join(Invoice, PaymentAllocation.invoice_id == Invoice.id)
        .where(
            PaymentAllocation.tenant_id == tenant_id,
            PaymentReceived.payment_date >= start_date,
            PaymentReceived.payment_date <= end_date,
        )
    ).all()
    for allocation, _payment, invoice in receipt_rows:
        if D(invoice.total) > ZERO:
            net_sales_20 += money(D(allocation.amount) * D(invoice.subtotal) / D(invoice.total))

    # Allocated vendor payments: recognise net outflow. Stock purchases are
    # shown under goods; service purchases under external services.
    expense_rows = session.exec(
        select(PaymentAllocation, BillPayment, Bill)
        .join(BillPayment, PaymentAllocation.bill_payment_id == BillPayment.id)
        .join(Bill, PaymentAllocation.bill_id == Bill.id)
        .where(
            PaymentAllocation.tenant_id == tenant_id,
            BillPayment.payment_date >= start_date,
            BillPayment.payment_date <= end_date,
        )
    ).all()
    for allocation, _payment, bill in expense_rows:
        if D(bill.total) <= ZERO:
            continue
        net_paid = money(D(allocation.amount) * D(bill.subtotal) / D(bill.total))
        bill_lines = session.exec(select(BillLine).where(BillLine.bill_id == bill.id)).all()
        stock_base = ZERO
        for line in bill_lines:
            if not line.product_id:
                continue
            product = session.exec(select(Product).where(
                Product.id == line.product_id, Product.tenant_id == tenant_id,
            )).first()
            if product and product.product_type == "stock":
                stock_base += D(line.amount)
        stock_share = money(net_paid * stock_base / D(bill.subtotal)) if D(bill.subtotal) > ZERO else ZERO
        goods_expense += stock_share
        subcontracting += money(net_paid - stock_share)

    for je, acc, txn in entries:
        if txn.id in payment_txn_ids:
            continue
        code = acc.code
        credit = D(je.credit)
        debit = D(je.debit)

        # Revenue accounts (Klasse 4)
        if code == "4000":
            net_sales_20 += (credit - debit)
        elif code == "4010":
            net_sales_10 += (credit - debit)
        elif code == "4020":
            net_sales_13 += (credit - debit)
        elif code == "4030":
            net_sales_4_9 += (credit - debit)
        elif code.startswith("40") or code.startswith("4"):
            net_sales_exempt += (credit - debit)

        # Expense accounts
        elif code in ("5000", "5010"):
            goods_expense += (debit - credit)
        elif code == "5100":
            subcontracting += (debit - credit)
        elif code.startswith("6") or code in ("7000", "7100"):
            payroll_expense += (debit - credit)
        elif code in ("0800", "8010"):
            gwg_expense += (debit - credit)
        elif code in ("7300", "7310"):
            car_expense += (debit - credit)
        elif code in ("7400", "7410"):
            rent_expense += (debit - credit)
        elif code in ("8200", "8210"):
            interest_expense += (debit - credit)
        elif code.startswith("7") or (code.startswith("8") and not code.startswith("80")):
            other_operating_expense += (debit - credit)

    # AfA from asset subsidiary ledger (§ 7 EStG)
    depreciation_rows = session.exec(
        select(AtAssetDepreciation).where(
            AtAssetDepreciation.tenant_id == tenant_id,
            AtAssetDepreciation.year == year,
        )
    ).all()
    afa_expense = sum((row.depreciation_amount for row in depreciation_rows), ZERO)

    # E1a 2025: 9040 contains ordinary goods/service revenue; it is not a VAT-rate field.
    kz_9040 = money(net_sales_20 + net_sales_10 + net_sales_13 + net_sales_4_9 + net_sales_exempt)
    kz_9050 = ZERO  # income reported under § 109a EStG requires explicit classification
    kz_9060 = ZERO  # asset disposal proceeds require explicit classification
    kz_9090 = ZERO  # other business income requires explicit classification
    total_revenue = money(kz_9040 + kz_9050 + kz_9060 + kz_9090)

    # Operating expenses
    kz_9100 = money(goods_expense)
    kz_9110 = money(subcontracting)
    kz_9120 = money(payroll_expense)
    kz_9130 = money(afa_expense + gwg_expense)
    kz_9160 = ZERO
    kz_9180 = money(rent_expense)
    kz_9220 = money(interest_expense)
    kz_9230 = money(other_operating_expense + car_expense)

    total_expenses = money(
        kz_9100 + kz_9110 + kz_9120 + kz_9130 + kz_9160 + kz_9180 + kz_9220 + kz_9230
    )

    # Preliminary result
    preliminary_profit = money(total_revenue - total_expenses)

    # Tax additions (e.g. non-deductible expenses, private shares)
    kz_9260 = money(private_share_adjustments)

    # Final taxable income / profit
    taxable_profit = money(preliminary_profit + kz_9260)

    e1a_positions = [
        {"kz": "9040", "title": "Waren-/Leistungserlöse (ohne § 109a)", "amount": kz_9040},
        {"kz": "9050", "title": "Betriebseinnahmen gemäß § 109a", "amount": kz_9050},
        {"kz": "9060", "title": "Anlagenerträge / Entnahmewerte", "amount": kz_9060},
        {"kz": "9090", "title": "Übrige Betriebseinnahmen", "amount": kz_9090},
        {"kz": None, "title": "Summe Betriebseinnahmen", "amount": total_revenue, "is_subtotal": True},
        {"kz": "9100", "title": "Waren, Roh-, Hilfs- und Betriebsstoffe", "amount": kz_9100},
        {"kz": "9110", "title": "Fremdpersonal und Fremdleistungen", "amount": kz_9110},
        {"kz": "9120", "title": "Ausgaben für eigenes Personal", "amount": kz_9120},
        {"kz": "9130", "title": "Abschreibungen auf das Anlagevermögen", "amount": kz_9130},
        {"kz": "9160", "title": "Reise- und Fahrtspesen", "amount": kz_9160},
        {"kz": "9180", "title": "Miete und Pacht", "amount": kz_9180},
        {"kz": "9220", "title": "Zinsen und Geldbeschaffungskosten", "amount": kz_9220},
        {"kz": "9230", "title": "Übrige Betriebsausgaben", "amount": kz_9230},
        {"kz": None, "title": "Summe Betriebsausgaben", "amount": total_expenses, "is_subtotal": True},
        {"kz": None, "title": "Vorläufiges Ergebnis", "amount": preliminary_profit, "is_subtotal": True},
        {"kz": "9260", "title": "Steuerliche Zurechnungen (Privatanteile)", "amount": kz_9260},
        {"kz": "9290", "title": "Steuerlicher Gewinn / Verlust (Reingewinn)", "amount": taxable_profit, "is_total": True},
    ]

    return {
        "year": year,
        "method": "einnahmen_ausgaben_rechnung",
        "legal_basis": "§ 4 Abs. 3 EStG",
        "positions": e1a_positions,
        "form_version": "E1a-2025",
        "operating_revenue": total_revenue,
        "operating_expenses": total_expenses,
        "preliminary_profit": preliminary_profit,
        "tax_additions": kz_9260,
        "taxable_profit": taxable_profit,
    }
