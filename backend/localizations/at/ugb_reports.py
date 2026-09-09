"""Austrian Commercial Code (UGB) Statutory Financial Statements (§§ 224, 231 UGB) (PR 11: AT-11).

Implements:
- Bilanz nach § 224 UGB (Balance sheet: Aktiva / Passiva, Negatives Eigenkapital gem. § 225 Abs. 1 UGB)
- Gewinn- und Verlustrechnung nach § 231 Abs. 2 UGB (Gesamtkostenverfahren)
- Vorjahresvergleich (Comparative periods)
- Jahresabschluss-Checkliste (Year-end closing audit checklist)
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from models import Account, JournalEntry, Transaction
from localizations.at.profile import get_active_profile
from services.money import D, ZERO, money


def _get_account_balances(
    session: Session,
    tenant_id: int,
    up_to_date: str,
    from_date: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """Compute debit/credit net balances for all accounts up to a date."""
    query = (
        select(JournalEntry, Account)
        .join(Account, JournalEntry.account_id == Account.id)
        .join(Transaction, JournalEntry.transaction_id == Transaction.id)
        .where(
            JournalEntry.tenant_id == tenant_id,
            Transaction.date <= up_to_date,
            Account.is_memo == False,  # noqa: E712
        )
    )
    if from_date:
        query = query.where(Transaction.date >= from_date)

    results = session.exec(query).all()
    balances: Dict[str, Dict[str, Any]] = {}

    for je, acc in results:
        code = acc.code
        if code not in balances:
            balances[code] = {
                "account_id": acc.id,
                "code": acc.code,
                "name": acc.name,
                "type": acc.type,
                "debit": ZERO,
                "credit": ZERO,
            }
        balances[code]["debit"] += D(je.debit)
        balances[code]["credit"] += D(je.credit)

    for code, b in balances.items():
        b["net_debit"] = money(b["debit"] - b["credit"])
        b["net_credit"] = money(b["credit"] - b["debit"])

    return balances


def compute_ugb_income_statement(
    session: Session,
    tenant_id: int,
    start_date: str,
    end_date: str,
    prior_start_date: Optional[str] = None,
    prior_end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute GuV nach dem Gesamtkostenverfahren gem. § 231 Abs. 2 UGB."""
    cur_b = _get_account_balances(session, tenant_id, end_date, start_date)
    pri_b = _get_account_balances(session, tenant_id, prior_end_date, prior_start_date) if prior_end_date and prior_start_date else {}

    def get_sums(codes: List[str], use_credit: bool = True):
        cur_sum = ZERO
        pri_sum = ZERO
        for c in codes:
            if c in cur_b:
                cur_sum += cur_b[c]["net_credit"] if use_credit else cur_b[c]["net_debit"]
            if c in pri_b:
                pri_sum += pri_b[c]["net_credit"] if use_credit else pri_b[c]["net_debit"]
        return money(cur_sum), money(pri_sum)

    # 1. Umsatzerlöse (Klasse 4000-4799)
    rev_codes = [c for c in cur_b.keys() | pri_b.keys() if c.startswith("4") and (not c[:2].isdigit() or int(c[:2]) < 48)]
    if not rev_codes:
        rev_codes = ["4000", "4010", "4020", "4030", "4040", "4050", "4060"]
    z1_cur, z1_pri = get_sums(rev_codes, use_credit=True)

    # 2. Bestandsveränderungen (Klasse 4800-4899)
    inv_change_codes = [c for c in cur_b.keys() | pri_b.keys() if c.startswith("48")]
    z2_cur, z2_pri = get_sums(inv_change_codes, use_credit=True)

    # 3. Andere aktivierte Eigenleistungen
    z3_cur, z3_pri = ZERO, ZERO

    # 4. Sonstige betriebliche Erträge (Klasse 4900-4999)
    other_inc_codes = [c for c in cur_b.keys() | pri_b.keys() if c.startswith("49")]
    z4_cur, z4_pri = get_sums(other_inc_codes, use_credit=True)

    # 5. Materialaufwand und bezogene Herstellungsleistungen (Klasse 5)
    mat_codes = [c for c in cur_b.keys() | pri_b.keys() if c.startswith("5")]
    if not mat_codes:
        mat_codes = ["5000", "5010", "5100"]
    z5_cur, z5_pri = get_sums(mat_codes, use_credit=False)

    # 6. Personalaufwand (Klasse 6 oder 7000-7199)
    pers_codes = [c for c in cur_b.keys() | pri_b.keys() if c.startswith("6") or c.startswith("70") or c.startswith("71")]
    if not pers_codes:
        pers_codes = ["7000", "7100"]
    z6_cur, z6_pri = get_sums(pers_codes, use_credit=False)

    # 7. Abschreibungen (AfA auf Sachanlagen/immaterielle Vermögenswerte) (Klasse 8000-8099 oder 70xx)
    depr_codes = [c for c in cur_b.keys() | pri_b.keys() if c.startswith("80")]
    if not depr_codes:
        depr_codes = ["8000", "8010"]
    z7_cur, z7_pri = get_sums(depr_codes, use_credit=False)

    # 8. Sonstige betriebliche Aufwendungen (Klasse 7200-7999)
    other_exp_codes = [c for c in cur_b.keys() | pri_b.keys() if c.startswith("7") and not (c.startswith("70") or c.startswith("71"))]
    z8_cur, z8_pri = get_sums(other_exp_codes, use_credit=False)

    # 9. Betriebsergebnis (Zwischensumme Z 1 bis 8)
    z9_cur = money(z1_cur + z2_cur + z3_cur + z4_cur - z5_cur - z6_cur - z7_cur - z8_cur)
    z9_pri = money(z1_pri + z2_pri + z3_pri + z4_pri - z5_pri - z6_pri - z7_pri - z8_pri)

    # 10-12. Finanzerträge (Zinserträge, Beteiligungserträge: 8100-8199)
    fin_inc_codes = [c for c in cur_b.keys() | pri_b.keys() if c.startswith("81")]
    fin_inc_cur, fin_inc_pri = get_sums(fin_inc_codes, use_credit=True)

    # 13-14. Finanzaufwendungen (Zinsaufwand: 8200-8399)
    fin_exp_codes = [c for c in cur_b.keys() | pri_b.keys() if c.startswith("82") or c.startswith("83")]
    if not fin_exp_codes:
        fin_exp_codes = ["8200"]
    fin_exp_cur, fin_exp_pri = get_sums(fin_exp_codes, use_credit=False)

    # 15. Finanzergebnis (Zwischensumme Z 10 bis 14)
    z15_cur = money(fin_inc_cur - fin_exp_cur)
    z15_pri = money(fin_inc_pri - fin_exp_pri)

    # 16. Ergebnis vor Steuern (EGT = Z 9 + Z 15)
    z16_cur = money(z9_cur + z15_cur)
    z16_pri = money(z9_pri + z15_pri)

    # 17. Steuern vom Einkommen und vom Ertrag (KSt: 8500-8599)
    tax_codes = [c for c in cur_b.keys() | pri_b.keys() if c.startswith("85")]
    if not tax_codes:
        tax_codes = ["8500"]
    z17_cur, z17_pri = get_sums(tax_codes, use_credit=False)

    # 18. Ergebnis nach Steuern (Jahresüberschuss / Jahresfehlbetrag)
    z18_cur = money(z16_cur - z17_cur)
    z18_pri = money(z16_pri - z17_pri)

    # 19. Zuweisung / Auflösung von Rücklagen
    z19_cur, z19_pri = ZERO, ZERO

    # 20. Bilanzgewinn / Bilanzverlust
    z20_cur = money(z18_cur + z19_cur)
    z20_pri = money(z18_pri + z19_pri)

    lines = [
        {"position": "1", "name": "Umsatzerlöse", "current": z1_cur, "prior": z1_pri},
        {"position": "2", "name": "Veränderung des Bestands an fertigen und unfertigen Erzeugnissen", "current": z2_cur, "prior": z2_pri},
        {"position": "3", "name": "Andere aktivierte Eigenleistungen", "current": z3_cur, "prior": z3_pri},
        {"position": "4", "name": "Sonstige betriebliche Erträge", "current": z4_cur, "prior": z4_pri},
        {"position": "5", "name": "Materialaufwand und bezogene Leistungen", "current": -z5_cur, "prior": -z5_pri},
        {"position": "6", "name": "Personalaufwand", "current": -z6_cur, "prior": -z6_pri},
        {"position": "7", "name": "Abschreibungen auf Sachanlagen und immaterielle Gegenstände", "current": -z7_cur, "prior": -z7_pri},
        {"position": "8", "name": "Sonstige betriebliche Aufwendungen", "current": -z8_cur, "prior": -z8_pri},
        {"position": "9", "name": "Betriebsergebnis (Zwischensumme Z 1 bis 8)", "current": z9_cur, "prior": z9_pri, "is_subtotal": True},
        {"position": "10-12", "name": "Finanzerträge", "current": fin_inc_cur, "prior": fin_inc_pri},
        {"position": "13-14", "name": "Finanzaufwendungen", "current": -fin_exp_cur, "prior": -fin_exp_pri},
        {"position": "15", "name": "Finanzergebnis (Zwischensumme Z 10 bis 14)", "current": z15_cur, "prior": z15_pri, "is_subtotal": True},
        {"position": "16", "name": "Ergebnis vor Steuern (EGT)", "current": z16_cur, "prior": z16_pri, "is_subtotal": True},
        {"position": "17", "name": "Steuern vom Einkommen und vom Ertrag", "current": -z17_cur, "prior": -z17_pri},
        {"position": "18", "name": "Ergebnis nach Steuern (Jahresüberschuss / Jahresfehlbetrag)", "current": z18_cur, "prior": z18_pri, "is_subtotal": True},
        {"position": "19", "name": "Auflösung / Zuweisung von Rücklagen", "current": z19_cur, "prior": z19_pri},
        {"position": "20", "name": "Bilanzgewinn / Bilanzverlust", "current": z20_cur, "prior": z20_pri, "is_total": True},
    ]

    return {
        "report_type": "ugb_guv",
        "method": "gesamtkostenverfahren",
        "start_date": start_date,
        "end_date": end_date,
        "prior_start_date": prior_start_date,
        "prior_end_date": prior_end_date,
        "lines": lines,
        "net_income_current": z18_cur,
        "net_income_prior": z18_pri,
        "annual_profit": z20_cur,
    }


def compute_ugb_balance_sheet(
    session: Session,
    tenant_id: int,
    as_of_date: str,
    prior_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute Bilanz gem. § 224 UGB including negative equity logic (§ 225 UGB)."""
    cur_b = _get_account_balances(session, tenant_id, as_of_date)
    pri_b = _get_account_balances(session, tenant_id, prior_date) if prior_date else {}

    # Calculate current year net income from P&L accounts (Classes 4-8) up to as_of_date
    pl_current = ZERO
    pl_prior = ZERO
    for code, data in cur_b.items():
        if code and code[0] in ("4", "5", "6", "7", "8"):
            # Revenue is credit, expense is debit -> Net profit = credit - debit
            pl_current += (data["credit"] - data["debit"])
    if pri_b:
        for code, data in pri_b.items():
            if code and code[0] in ("4", "5", "6", "7", "8"):
                pl_prior += (data["credit"] - data["debit"])

    def sum_class(first_digit: str, sub_digits: Optional[List[str]] = None, is_asset: bool = True):
        c_sum = ZERO
        p_sum = ZERO
        for code, b in cur_b.items():
            if code.startswith(first_digit):
                if sub_digits is None or any(code.startswith(first_digit + s) for s in sub_digits):
                    c_sum += b["net_debit"] if is_asset else b["net_credit"]
        for code, b in pri_b.items():
            if code.startswith(first_digit):
                if sub_digits is None or any(code.startswith(first_digit + s) for s in sub_digits):
                    p_sum += b["net_debit"] if is_asset else b["net_credit"]
        return money(c_sum), money(p_sum)

    # ── AKTIVA ──
    # A. Anlagevermögen (Klasse 0)
    # I. Immaterielle Vermögensgegenstände (0100-0199)
    a_i_c, a_i_p = sum_class("0", ["1"], is_asset=True)
    # II. Sachanlagen (0200-0699, 0800)
    a_ii_c, a_ii_p = sum_class("0", ["2", "3", "4", "5", "6", "8"], is_asset=True)
    # III. Finanzanlagen (0700-0799)
    a_iii_c, a_iii_p = sum_class("0", ["7"], is_asset=True)
    anlagevermoegen_c = money(a_i_c + a_ii_c + a_iii_c)
    anlagevermoegen_p = money(a_i_p + a_ii_p + a_iii_p)

    # B. Umlaufvermögen
    # I. Vorräte (Klasse 1)
    b_i_c, b_i_p = sum_class("1", is_asset=True)
    # II. Forderungen und sonstige Vermögensgegenstände (2000-2599)
    b_ii_c, b_ii_p = sum_class("2", ["0", "1", "2", "3", "4", "5"], is_asset=True)
    # III. Wertpapiere des Umlaufvermögens (2600-2699)
    b_iii_c, b_iii_p = sum_class("2", ["6"], is_asset=True)
    # IV. Kassenbestand, Guthaben bei Kreditinstituten (2700-2899)
    b_iv_c, b_iv_p = sum_class("2", ["7", "8"], is_asset=True)
    umlaufvermoegen_c = money(b_i_c + b_ii_c + b_iii_c + b_iv_c)
    umlaufvermoegen_p = money(b_i_p + b_ii_p + b_iii_p + b_iv_p)

    # C. Rechnungsabgrenzungsposten Aktiva (2900-2999)
    ara_c, ara_p = sum_class("2", ["9"], is_asset=True)

    # D. Aktive latente Steuern
    aktive_latente_c, aktive_latente_p = ZERO, ZERO

    subtotal_aktiva_c = money(anlagevermoegen_c + umlaufvermoegen_c + ara_c + aktive_latente_c)
    subtotal_aktiva_p = money(anlagevermoegen_p + umlaufvermoegen_p + ara_p + aktive_latente_p)

    # ── PASSIVA ──
    # A. Eigenkapital (Klasse 9)
    # I. Nennkapital / Stammkapital (9000-9099)
    stammkapital_c, stammkapital_p = sum_class("9", ["0"], is_asset=False)
    # II. Kapitalrücklagen (9100-9199)
    kapitalruecklagen_c, kapitalruecklagen_p = sum_class("9", ["1"], is_asset=False)
    # III. Gewinnrücklagen (9200-9299)
    gewinnruecklagen_c, gewinnruecklagen_p = sum_class("9", ["2"], is_asset=False)
    # IV. Bilanzgewinn / Bilanzverlust (inkl. Jahresergebnis pl_current)
    carried_profit_c, carried_profit_p = sum_class("9", ["3"], is_asset=False)
    bilanzgewinn_c = money(carried_profit_c + pl_current)
    bilanzgewinn_p = money(carried_profit_p + pl_prior)

    # Privateinlagen / Privatentnahmen bei Einzelunternehmen (9600-9799)
    privat_c = ZERO
    privat_p = ZERO
    for code, b in cur_b.items():
        if code.startswith("96") or code.startswith("97"):
            privat_c += b["net_credit"]
    for code, b in pri_b.items():
        if code.startswith("96") or code.startswith("97"):
            privat_p += b["net_credit"]

    eigenkapital_computed_c = money(stammkapital_c + kapitalruecklagen_c + gewinnruecklagen_c + bilanzgewinn_c + privat_c)
    eigenkapital_computed_p = money(stammkapital_p + kapitalruecklagen_p + gewinnruecklagen_p + bilanzgewinn_p + privat_p)

    # B. Rückstellungen (3000-3099)
    rueckstellungen_c, rueckstellungen_p = sum_class("3", ["0"], is_asset=False)

    # C. Verbindlichkeiten (3100-3899)
    # 1. Verbindlichkeiten Kreditinstitute (3100-3199)
    verb_bank_c, verb_bank_p = sum_class("3", ["1"], is_asset=False)
    # 2. Erhaltene Anzahlungen (3200-3299)
    verb_anz_c, verb_anz_p = sum_class("3", ["2"], is_asset=False)
    # 3. Verbindlichkeiten LuL (3300-3399)
    verb_lul_c, verb_lul_p = sum_class("3", ["3"], is_asset=False)
    # 4. Sonstige Verbindlichkeiten (3400-3899: USt, SV, etc.)
    verb_sonst_c, verb_sonst_p = sum_class("3", ["4", "5", "6", "7", "8"], is_asset=False)
    verbindlichkeiten_c = money(verb_bank_c + verb_anz_c + verb_lul_c + verb_sonst_c)
    verbindlichkeiten_p = money(verb_bank_p + verb_anz_p + verb_lul_p + verb_sonst_p)

    # D. Rechnungsabgrenzungsposten Passiva (3900-3999)
    pra_c, pra_p = sum_class("3", ["9"], is_asset=False)

    # § 225 Abs. 1 UGB: exhausted equity remains a negative equity item on
    # the liabilities side and is explicitly labelled "negatives Eigenkapital".
    eigenkapital_ausweis_c = eigenkapital_computed_c
    eigenkapital_ausweis_p = eigenkapital_computed_p
    total_aktiva_c = subtotal_aktiva_c
    total_aktiva_p = subtotal_aktiva_p

    total_passiva_c = money(eigenkapital_ausweis_c + rueckstellungen_c + verbindlichkeiten_c + pra_c)
    total_passiva_p = money(eigenkapital_ausweis_p + rueckstellungen_p + verbindlichkeiten_p + pra_p)

    # Balancing check
    is_balanced = total_aktiva_c == total_passiva_c

    aktiva_structure = [
        {
            "code": "A",
            "name": "Anlagevermögen",
            "current": anlagevermoegen_c,
            "prior": anlagevermoegen_p,
            "subitems": [
                {"code": "A.I", "name": "Immaterielle Vermögensgegenstände", "current": a_i_c, "prior": a_i_p},
                {"code": "A.II", "name": "Sachanlagen", "current": a_ii_c, "prior": a_ii_p},
                {"code": "A.III", "name": "Finanzanlagen", "current": a_iii_c, "prior": a_iii_p},
            ],
        },
        {
            "code": "B",
            "name": "Umlaufvermögen",
            "current": umlaufvermoegen_c,
            "prior": umlaufvermoegen_p,
            "subitems": [
                {"code": "B.I", "name": "Vorräte", "current": b_i_c, "prior": b_i_p},
                {"code": "B.II", "name": "Forderungen und sonstige Vermögensgegenstände", "current": b_ii_c, "prior": b_ii_p},
                {"code": "B.III", "name": "Wertpapiere und Anteile", "current": b_iii_c, "prior": b_iii_p},
                {"code": "B.IV", "name": "Kassenbestand, Guthaben bei Kreditinstituten", "current": b_iv_c, "prior": b_iv_p},
            ],
        },
        {"code": "C", "name": "Rechnungsabgrenzungsposten", "current": ara_c, "prior": ara_p},
        {"code": "D", "name": "Aktive latente Steuern", "current": aktive_latente_c, "prior": aktive_latente_p},
    ]

    passiva_structure = [
        {
            "code": "A",
            "name": "Negatives Eigenkapital (§ 225 Abs. 1 UGB)" if eigenkapital_computed_c < ZERO else "Eigenkapital",
            "current": eigenkapital_ausweis_c,
            "prior": eigenkapital_ausweis_p,
            "subitems": [
                {"code": "A.I", "name": "Nennkapital / Stammkapital", "current": stammkapital_c, "prior": stammkapital_p},
                {"code": "A.II", "name": "Kapitalrücklagen", "current": kapitalruecklagen_c, "prior": kapitalruecklagen_p},
                {"code": "A.III", "name": "Gewinnrücklagen", "current": gewinnruecklagen_c, "prior": gewinnruecklagen_p},
                {"code": "A.IV", "name": "Bilanzgewinn / Bilanzverlust (Jahresergebnis)", "current": bilanzgewinn_c, "prior": bilanzgewinn_p},
            ],
            "requires_insolvency_note": eigenkapital_computed_c < ZERO,
        },
        {"code": "B", "name": "Rückstellungen", "current": rueckstellungen_c, "prior": rueckstellungen_p},
        {
            "code": "C",
            "name": "Verbindlichkeiten",
            "current": verbindlichkeiten_c,
            "prior": verbindlichkeiten_p,
            "subitems": [
                {"code": "C.1", "name": "Verbindlichkeiten gegenüber Kreditinstituten", "current": verb_bank_c, "prior": verb_bank_p},
                {"code": "C.2", "name": "Erhaltene Anzahlungen auf Bestellungen", "current": verb_anz_c, "prior": verb_anz_p},
                {"code": "C.3", "name": "Verbindlichkeiten aus Lieferungen und Leistungen", "current": verb_lul_c, "prior": verb_lul_p},
                {"code": "C.4", "name": "Sonstige Verbindlichkeiten (davon Steuern/SV)", "current": verb_sonst_c, "prior": verb_sonst_p},
            ],
        },
        {"code": "D", "name": "Rechnungsabgrenzungsposten", "current": pra_c, "prior": pra_p},
    ]

    return {
        "report_type": "ugb_balance_sheet",
        "as_of_date": as_of_date,
        "prior_date": prior_date,
        "aktiva": aktiva_structure,
        "passiva": passiva_structure,
        "total_aktiva": total_aktiva_c,
        "total_passiva": total_passiva_c,
        "total_aktiva_prior": total_aktiva_p,
        "total_passiva_prior": total_passiva_p,
        "is_balanced": is_balanced,
        "eigenkapital_computed": eigenkapital_computed_c,
        "has_negative_equity": eigenkapital_computed_c < ZERO,
        "negative_equity_note_required": eigenkapital_computed_c < ZERO,
    }


def get_at_closing_checklist(
    session: Session,
    tenant_id: int,
    fiscal_year: int,
) -> Dict[str, Any]:
    """Provide statutory year-end audit and closing checklist (§ 193 ff. UGB)."""
    end_date = f"{fiscal_year}-12-31"
    bs = compute_ugb_balance_sheet(session, tenant_id, end_date)

    from models import Bill, Invoice, JournalEntry, PaymentAllocation, Transaction
    from models_at import TaxEvent
    from services.account_roles import resolve_account_role
    from localizations.at.reconciliation import reconcile_vat_period

    def role_balance(role: str) -> Optional[Decimal]:
        account = resolve_account_role(session, tenant_id, role, end_date)
        if not account:
            return None
        rows = session.exec(
            select(JournalEntry, Transaction)
            .join(Transaction, JournalEntry.transaction_id == Transaction.id)
            .where(
                JournalEntry.tenant_id == tenant_id,
                JournalEntry.account_id == account.id,
                Transaction.date <= end_date,
            )
        ).all()
        return money(sum((D(je.debit) - D(je.credit) for je, _txn in rows), ZERO))

    cash_balance = role_balance("cash")
    ar_balance = role_balance("accounts_receivable")
    ap_debit_balance = role_balance("accounts_payable")
    ap_balance = -ap_debit_balance if ap_debit_balance is not None else None

    allocations = session.exec(select(PaymentAllocation).where(
        PaymentAllocation.tenant_id == tenant_id,
    )).all()
    inv_alloc = {}
    bill_alloc = {}
    for allocation in allocations:
        if allocation.invoice_id:
            inv_alloc[allocation.invoice_id] = inv_alloc.get(allocation.invoice_id, ZERO) + D(allocation.amount)
        if allocation.bill_id:
            bill_alloc[allocation.bill_id] = bill_alloc.get(allocation.bill_id, ZERO) + D(allocation.amount)
    open_ar = money(sum((
        max(ZERO, D(inv.total) - inv_alloc.get(inv.id, ZERO))
        for inv in session.exec(select(Invoice).where(
            Invoice.tenant_id == tenant_id,
            Invoice.issue_date <= end_date,
            Invoice.lifecycle_status == "finalized",
            Invoice.status.not_in(["void", "cancelled", "reversed"]),
        )).all()
    ), ZERO))
    open_ap = money(sum((
        max(ZERO, D(bill.total) - bill_alloc.get(bill.id, ZERO))
        for bill in session.exec(select(Bill).where(
            Bill.tenant_id == tenant_id,
            Bill.bill_date <= end_date,
            Bill.lifecycle_status == "finalized",
            Bill.status.not_in(["void", "cancelled", "reversed"]),
        )).all()
    ), ZERO))
    subledger_ok = (
        ar_balance is not None and ap_balance is not None
        and abs(ar_balance - open_ar) <= D("0.01")
        and abs(ap_balance - open_ap) <= D("0.01")
    )

    periods = sorted(set(session.exec(select(TaxEvent.tax_period).where(
        TaxEvent.tenant_id == tenant_id,
        TaxEvent.tax_date >= f"{fiscal_year}-01-01",
        TaxEvent.tax_date <= end_date,
        TaxEvent.state == "final",
    )).all()))
    vat_results = [reconcile_vat_period(session, tenant_id, period) for period in periods]
    vat_ok = all(result["is_reconciled"] for result in vat_results)

    items = [
        {
            "id": "balance_sheet_balanced",
            "title": "Bilanzgleichung (Aktiva = Passiva)",
            "legal_basis": "§ 224 UGB",
            "status": "passed" if bs["is_balanced"] else "failed",
            "detail": f"Aktiva: {bs['total_aktiva']} EUR, Passiva: {bs['total_passiva']} EUR",
        },
        {
            "id": "equity_status",
            "title": "Eigenkapitalprüfung",
            "legal_basis": "§ 225 UGB / URG",
            "status": "warning" if bs["has_negative_equity"] else "passed",
            "detail": "Negatives Eigenkapital vorhanden" if bs["has_negative_equity"] else "Eigenkapital positiv",
        },
        {
            "id": "cash_non_negative",
            "title": "Kassenprüfung (Kein negativer Kassenstand)",
            "legal_basis": "§ 131 BAO",
            "status": "passed" if cash_balance is not None and cash_balance >= ZERO else "failed",
            "detail": (
                f"Kassenbestand: {cash_balance} EUR" if cash_balance is not None
                else "Kontenrolle 'cash' ist nicht zugeordnet"
            ),
        },
        {
            "id": "subledger_reconciliation",
            "title": "Abstimmung Debitoren/Kreditoren-Personenkonten",
            "legal_basis": "§ 190 UGB",
            "status": "passed" if subledger_ok else "failed",
            "detail": f"AR Hauptbuch/OP: {ar_balance}/{open_ar} EUR; AP Hauptbuch/OP: {ap_balance}/{open_ap} EUR",
        },
        {
            "id": "vat_reconciliation",
            "title": "Umsatzsteuer-Jahresabstimmung",
            "legal_basis": "§ 21 UStG",
            "status": "passed" if vat_ok else "failed",
            "detail": (
                f"{len(periods)} Steuerperioden mit dem Hauptbuch abgestimmt"
                if vat_ok else "; ".join(
                    discrepancy
                    for result in vat_results for discrepancy in result["discrepancies"]
                )
            ),
        },
    ]

    required_ids = {"balance_sheet_balanced", "cash_non_negative", "subledger_reconciliation", "vat_reconciliation"}
    all_passed = all(i["status"] == "passed" for i in items if i["id"] in required_ids)

    return {
        "fiscal_year": fiscal_year,
        "is_ready_for_closing": all_passed,
        "items": items,
    }
