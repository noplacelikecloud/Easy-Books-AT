"""Bank statement CSV / OFX import + confidence-scored auto-match (#268).

CSV:
    Default columns: date, description, debit, credit, balance
    Optional Form mapping: date_col, description_col, debit_col, credit_col,
    amount_col, balance_col — when a bank uses different headers. amount_col
    alone is signed (negative = debit / money out).

OFX/QFX:
    Detected by filename / content; FITID stored as external_id for de-dupe.

Workflow:
    1. POST /api/bank-imports        upload → StatementLines + apply rules
    2. POST /api/bank-imports/{id}/auto-match
                                     score candidates; auto-accept ≥90 unique
    3. POST /api/statement-lines/{id}/accept|reject
                                     one-click decision (audited)
"""
from __future__ import annotations

import csv
import base64
import hashlib
import hmac
import io
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import select

from models import (
    BankAccount, BankStatementImport, StatementLine, Transaction,
)
from services.bank_match import (
    accept_match, apply_match_suggestions, find_candidates, reject_match,
)
from services.bank_rules import apply_rules_to_lines
from services.money import D, ZERO, money
from services.ofx_parse import parse_ofx
from services.permissions import perm_dep

from .common import CurrentUserDep, SessionDep, WriteUserDep, log_audit

router = APIRouter(tags=["bank-imports"], dependencies=[perm_dep("bank_imports")])


def _preview_token(tenant_id: int, bank_account_id: int, file_hash: str, options: dict) -> str:
    from auth import SECRET_KEY
    payload = json.dumps({
        "tenant_id": tenant_id,
        "bank_account_id": bank_account_id,
        "file_hash": file_hash,
        "options": options,
    }, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(SECRET_KEY.encode(), payload, hashlib.sha256).hexdigest().encode()
    return base64.urlsafe_b64encode(payload + b"." + signature).decode()


def _assert_preview_token(token: str, tenant_id: int, bank_account_id: int, file_hash: str, options: dict) -> None:
    expected = _preview_token(tenant_id, bank_account_id, file_hash, options)
    if not hmac.compare_digest(token, expected):
        raise HTTPException(409, "Datei oder Parsing-Einstellungen weichen von der bestätigten Vorschau ab.")


def _looks_like_ofx(filename: str | None, content: str) -> bool:
    name = (filename or "").lower()
    if name.endswith(".ofx") or name.endswith(".qfx"):
        return True
    head = content.lstrip()[:200].upper()
    return "OFXHEADER" in head or "<OFX>" in head or "<STMTTRN>" in head


from services.number_parse import (
    AmbiguousNumberFormatError,
    DateParseError,
    NumberParseConfig,
    NumberParseError,
    parse_date_flexible,
    parse_money,
)


def _detect_delimiter(content: str, default: str = ",") -> str:
    """Detect whether CSV uses comma, semicolon or tab."""
    first_lines = [line for line in content.splitlines()[:5] if line.strip()]
    if not first_lines:
        return default
    sample = "\n".join(first_lines)
    counts = {
        ";": sample.count(";"),
        ",": sample.count(","),
        "\t": sample.count("\t"),
    }
    if counts[";"] > counts[","] and counts[";"] >= len(first_lines):
        return ";"
    if counts["\t"] > counts[","] and counts["\t"] >= len(first_lines):
        return "\t"
    return default


def _parse_csv(
    content: str,
    *,
    date_col: str = "date",
    description_col: str = "description",
    debit_col: str = "debit",
    credit_col: str = "credit",
    amount_col: str | None = None,
    balance_col: str = "balance",
    delimiter: str | None = None,
    decimal_separator: str | None = None,
    thousands_separator: str | None = None,
    date_format: str | None = None,
    sign_convention: str = "auto",
    collect_errors: bool = False,
):
    eff_delim = delimiter if delimiter else _detect_delimiter(content)
    reader = csv.DictReader(io.StringIO(content), delimiter=eff_delim)
    if not reader.fieldnames:
        return ([], []) if collect_errors else []
    # Normalise header → original for lookup
    headers = { (h or "").strip().lower(): (h or "").strip() for h in reader.fieldnames }

    def col(name: str) -> str | None:
        key = name.strip().lower()
        return headers.get(key)

    d_key = col(date_col)
    desc_key = col(description_col)
    if not d_key or not desc_key:
        raise HTTPException(
            400,
            f"CSV missing required columns '{date_col}' / '{description_col}' "
            f"(found: {list(headers.keys())})",
        )
    debit_key = col(debit_col)
    credit_key = col(credit_col)
    amount_key = col(amount_col) if amount_col else None
    balance_key = col(balance_col)

    num_cfg = NumberParseConfig(
        decimal_separator=decimal_separator,  # type: ignore[arg-type]
        thousands_separator=thousands_separator,  # type: ignore[arg-type]
        sign_convention=sign_convention,  # type: ignore[arg-type]
        allow_empty=True,
    )

    rows: list[dict] = []
    errors: list[dict] = []

    for idx, raw in enumerate(reader):
        row_num = idx + 2  # 1-indexed header is row 1
        date_raw = (raw.get(d_key) or "").strip()
        desc_v = (raw.get(desc_key) or "").strip()
        if not date_raw and not desc_v:
            continue
        if not date_raw or not desc_v:
            err = f"Row {row_num}: Missing required date or description"
            if collect_errors:
                errors.append({"row": row_num, "error": err, "raw": raw})
                continue
            raise HTTPException(400, err)

        try:
            date_v = parse_date_flexible(date_raw, format_hint=date_format)
        except DateParseError as exc:
            err = f"Row {row_num}: Invalid date '{date_raw}' ({exc})"
            if collect_errors:
                errors.append({"row": row_num, "error": err, "raw": raw})
                continue
            raise HTTPException(400, err) from exc

        debit = ZERO
        credit = ZERO
        bal = ZERO

        try:
            if amount_key:
                raw_amt = raw.get(amount_key)
                amt = parse_money(raw_amt, num_cfg)
                if amt < ZERO:
                    debit = abs(amt)
                else:
                    credit = amt
            else:
                raw_deb = raw.get(debit_key) if debit_key else None
                raw_crd = raw.get(credit_key) if credit_key else None
                debit = parse_money(raw_deb, num_cfg) if raw_deb else ZERO
                credit = parse_money(raw_crd, num_cfg) if raw_crd else ZERO

            if balance_key:
                raw_bal = raw.get(balance_key)
                bal = parse_money(raw_bal, num_cfg) if raw_bal else ZERO

        except (NumberParseError, AmbiguousNumberFormatError) as exc:
            err = f"Row {row_num}: Number parse error ({exc})"
            if collect_errors:
                errors.append({"row": row_num, "error": err, "raw": raw})
                continue
            raise HTTPException(400, err) from exc

        rows.append({
            "date": date_v,
            "description": desc_v[:500],
            "debit": debit,
            "credit": credit,
            "balance": bal,
            "external_id": None,
        })

    if collect_errors:
        return rows, errors
    return rows


def _add_lines(session, user, imp: BankStatementImport, rows: list[dict]) -> int:
    """Insert rows; skip by external_id when already present. Returns inserted count."""
    inserted = 0
    for r in rows:
        ext = r.get("external_id")
        if ext:
            exists = session.exec(
                select(StatementLine).where(
                    StatementLine.tenant_id == user.tenant_id,
                    StatementLine.external_id == str(ext),
                )
            ).first()
            if exists:
                continue
        session.add(StatementLine(
            tenant_id=user.tenant_id,
            import_id=imp.id,
            date=r["date"],
            description=r["description"],
            debit=money(r["debit"]),
            credit=money(r["credit"]),
            balance=money(r.get("balance") or 0),
            external_id=str(ext) if ext else None,
        ))
        inserted += 1
    return inserted


@router.post("/api/bank-imports/preview")
async def preview_bank_statement(
    session: SessionDep, user: WriteUserDep,
    bank_account_id: int = Form(...),
    file: UploadFile = File(...),
    date_col: str = Form("date"),
    description_col: str = Form("description"),
    debit_col: str = Form("debit"),
    credit_col: str = Form("credit"),
    amount_col: Optional[str] = Form(None),
    balance_col: str = Form("balance"),
    delimiter: Optional[str] = Form(None),
    decimal_separator: Optional[str] = Form(None),
    thousands_separator: Optional[str] = Form(None),
    date_format: Optional[str] = Form(None),
    sign_convention: str = Form("auto"),
):
    acct = session.exec(
        select(BankAccount).where(
            BankAccount.id == bank_account_id,
            BankAccount.tenant_id == user.tenant_id,
        )
    ).first()
    if not acct:
        raise HTTPException(404, "Bank account not found")

    raw_bytes = await file.read()
    file_hash = hashlib.sha256(raw_bytes).hexdigest()

    existing = session.exec(
        select(BankStatementImport).where(
            BankStatementImport.tenant_id == user.tenant_id,
            BankStatementImport.bank_account_id == bank_account_id,
            BankStatementImport.file_hash == file_hash,
        )
    ).first()
    if existing:
        raise HTTPException(409, f"This file was already imported as #{existing.id}")

    try:
        content = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "Upload must be UTF-8 text (CSV or OFX/QFX)")

    filename = file.filename or "statement.csv"
    is_ofx = _looks_like_ofx(filename, content)

    if is_ofx:
        try:
            rows = parse_ofx(content)
            errors = []
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
    else:
        try:
            rows, errors = _parse_csv(
                content,
                date_col=date_col,
                description_col=description_col,
                debit_col=debit_col,
                credit_col=credit_col,
                amount_col=amount_col or None,
                balance_col=balance_col,
                delimiter=delimiter,
                decimal_separator=decimal_separator,
                thousands_separator=thousands_separator,
                date_format=date_format,
                sign_convention=sign_convention,
                collect_errors=True,
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(400, f"CSV parse error: {exc}") from exc

    total_debit = sum((D(r["debit"]) for r in rows), ZERO)
    total_credit = sum((D(r["credit"]) for r in rows), ZERO)
    parse_options = {
        "date_col": date_col, "description_col": description_col,
        "debit_col": debit_col, "credit_col": credit_col,
        "amount_col": amount_col, "balance_col": balance_col,
        "delimiter": delimiter, "decimal_separator": decimal_separator,
        "thousands_separator": thousands_separator, "date_format": date_format,
        "sign_convention": sign_convention,
    }

    return {
        "file_name": filename,
        "file_hash": file_hash,
        "format": "ofx" if is_ofx else "csv",
        "total_rows": len(rows) + len(errors),
        "valid_rows": len(rows),
        "error_count": len(errors),
        "error_rows": errors[:50],
        "total_debit": money(total_debit),
        "total_credit": money(total_credit),
        "preview_token": _preview_token(
            user.tenant_id, bank_account_id, file_hash, parse_options,
        ),
        "preview_lines": [
            {
                "date": r["date"],
                "description": r["description"],
                "debit": float(r["debit"]),
                "credit": float(r["credit"]),
                "balance": float(r["balance"]),
            }
            for r in rows[:10]
        ],
    }


@router.post("/api/bank-imports", status_code=201)
async def upload_bank_statement(
    session: SessionDep, user: WriteUserDep,
    bank_account_id: int = Form(...),
    file: UploadFile = File(...),
    date_col: str = Form("date"),
    description_col: str = Form("description"),
    debit_col: str = Form("debit"),
    credit_col: str = Form("credit"),
    amount_col: Optional[str] = Form(None),
    balance_col: str = Form("balance"),
    delimiter: Optional[str] = Form(None),
    decimal_separator: Optional[str] = Form(None),
    thousands_separator: Optional[str] = Form(None),
    date_format: Optional[str] = Form(None),
    sign_convention: str = Form("auto"),
    expected_hash: Optional[str] = Form(None),
    preview_token: Optional[str] = Form(None),
):
    acct = session.exec(
        select(BankAccount).where(
            BankAccount.id == bank_account_id,
            BankAccount.tenant_id == user.tenant_id,
        )
    ).first()
    if not acct:
        raise HTTPException(404, "Bank account not found")

    raw_bytes = await file.read()
    file_hash = hashlib.sha256(raw_bytes).hexdigest()

    parse_options = {
        "date_col": date_col, "description_col": description_col,
        "debit_col": debit_col, "credit_col": credit_col,
        "amount_col": amount_col, "balance_col": balance_col,
        "delimiter": delimiter, "decimal_separator": decimal_separator,
        "thousands_separator": thousands_separator, "date_format": date_format,
        "sign_convention": sign_convention,
    }
    from localizations.at.profile import is_at_compliance_active
    if is_at_compliance_active(session, user.tenant_id):
        if not preview_token:
            raise HTTPException(409, "AT-Bankimporte müssen aus einer bestätigten Vorschau übernommen werden.")
        _assert_preview_token(
            preview_token, user.tenant_id, bank_account_id, file_hash, parse_options,
        )

    if expected_hash and file_hash != expected_hash:
        raise HTTPException(
            400,
            f"File hash mismatch: expected {expected_hash}, got {file_hash}. "
            "The file changed since preview.",
        )

    existing = session.exec(
        select(BankStatementImport).where(
            BankStatementImport.tenant_id == user.tenant_id,
            BankStatementImport.bank_account_id == bank_account_id,
            BankStatementImport.file_hash == file_hash,
        )
    ).first()
    if existing:
        raise HTTPException(409, f"This file was already imported as #{existing.id}")

    try:
        content = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "Upload must be UTF-8 text (CSV or OFX/QFX)")

    filename = file.filename or "statement.csv"
    if _looks_like_ofx(filename, content):
        try:
            rows = parse_ofx(content)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        if not rows:
            raise HTTPException(400, "OFX/QFX contained no STMTTRN transactions")
    else:
        try:
            rows = _parse_csv(
                content,
                date_col=date_col,
                description_col=description_col,
                debit_col=debit_col,
                credit_col=credit_col,
                amount_col=amount_col or None,
                balance_col=balance_col,
                delimiter=delimiter,
                decimal_separator=decimal_separator,
                thousands_separator=thousands_separator,
                date_format=date_format,
                sign_convention=sign_convention,
                collect_errors=False,
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(400, f"CSV parse error: {exc}") from exc
        if not rows:
            raise HTTPException(
                400,
                "CSV is empty or missing required columns (date, description)",
            )

    imp = BankStatementImport(
        tenant_id=user.tenant_id,
        bank_account_id=bank_account_id,
        file_name=filename,
        file_hash=file_hash,
        line_count=0,
    )
    session.add(imp)
    session.flush()

    inserted = _add_lines(session, user, imp, rows)
    imp.line_count = inserted
    session.add(imp)
    session.flush()

    lines = list(session.exec(
        select(StatementLine).where(StatementLine.import_id == imp.id)
    ).all())
    apply_rules_to_lines(session, tenant_id=user.tenant_id, lines=lines)

    log_audit(
        session, user, "CREATE", "bank_import", imp.id,
        {"file_name": imp.file_name, "lines": imp.line_count, "format": "ofx" if _looks_like_ofx(filename, content) else "csv"},
    )
    session.commit()
    session.refresh(imp)
    return imp


@router.get("/api/bank-imports")
def list_imports(session: SessionDep, user: CurrentUserDep):
    return session.exec(
        select(BankStatementImport)
        .where(BankStatementImport.tenant_id == user.tenant_id)
        .order_by(BankStatementImport.created_at.desc())
    ).all()


@router.get("/api/bank-imports/{import_id}/lines")
def list_lines(session: SessionDep, user: CurrentUserDep, import_id: int):
    imp = session.exec(
        select(BankStatementImport).where(
            BankStatementImport.id == import_id,
            BankStatementImport.tenant_id == user.tenant_id,
        )
    ).first()
    if not imp:
        raise HTTPException(404, "Import not found")
    lines = session.exec(
        select(StatementLine)
        .where(StatementLine.import_id == imp.id)
        .order_by(StatementLine.date)
    ).all()
    out = []
    for line in lines:
        data = line.model_dump()
        if not line.is_matched:
            data["suggestions"] = find_candidates(
                session, tenant_id=user.tenant_id, line=line
            )[:5]
        else:
            data["suggestions"] = []
        out.append(data)
    return out


@router.post("/api/bank-imports/{import_id}/auto-match")
def auto_match(session: SessionDep, user: WriteUserDep, import_id: int):
    """Score unmatched lines; auto-accept unique matches with confidence ≥ 90."""
    imp = session.exec(
        select(BankStatementImport).where(
            BankStatementImport.id == import_id,
            BankStatementImport.tenant_id == user.tenant_id,
        )
    ).first()
    if not imp:
        raise HTTPException(404, "Import not found")

    counts = apply_match_suggestions(
        session, tenant_id=user.tenant_id, import_id=imp.id, auto_accept=True
    )
    newly_matched = counts["newly_matched"]
    imp.matched_count = (imp.matched_count or 0) + newly_matched
    if imp.line_count and imp.matched_count >= imp.line_count:
        imp.status = "matched"
    session.add(imp)
    log_audit(
        session, user, "UPDATE", "bank_import", imp.id,
        {"action": "auto_match", **counts},
    )
    session.commit()
    session.refresh(imp)
    return {
        "newly_matched": newly_matched,
        "suggested": counts["suggested"],
        "total_matched": imp.matched_count,
        "import": imp,
    }


@router.post("/api/bank-imports/{import_id}/apply-rules")
def apply_rules(session: SessionDep, user: WriteUserDep, import_id: int):
    imp = session.exec(
        select(BankStatementImport).where(
            BankStatementImport.id == import_id,
            BankStatementImport.tenant_id == user.tenant_id,
        )
    ).first()
    if not imp:
        raise HTTPException(404, "Import not found")
    lines = list(session.exec(
        select(StatementLine).where(StatementLine.import_id == imp.id)
    ).all())
    # Allow re-run: clear prior categorization on unmatched lines
    for ln in lines:
        if not ln.is_matched:
            ln.categorized_account_id = None
            ln.expense_draft_suggested = False
            session.add(ln)
    session.flush()
    n = apply_rules_to_lines(session, tenant_id=user.tenant_id, lines=lines)
    session.commit()
    return {"categorized": n}


class StatementLinePatch(BaseModel):
    matched_transaction_id: Optional[int] = None
    clear_match: bool = False


@router.patch("/api/statement-lines/{line_id}")
def patch_line(
    session: SessionDep, user: WriteUserDep,
    line_id: int, body: StatementLinePatch,
):
    line = session.exec(
        select(StatementLine).where(
            StatementLine.id == line_id, StatementLine.tenant_id == user.tenant_id
        )
    ).first()
    if not line:
        raise HTTPException(404, "Line not found")

    if body.clear_match or (
        "matched_transaction_id" in body.model_dump(exclude_unset=True)
        and body.matched_transaction_id is None
    ):
        was_matched = line.is_matched
        line.matched_transaction_id = None
        line.is_matched = False
        line.match_status = None
        line.suggested_transaction_id = None
        line.match_confidence = None
        session.add(line)
        if was_matched:
            imp = session.get(BankStatementImport, line.import_id)
            if imp and imp.tenant_id == user.tenant_id:
                imp.matched_count = max(0, (imp.matched_count or 0) - 1)
                session.add(imp)
        session.commit()
        session.refresh(line)
        return line

    if body.matched_transaction_id is not None:
        txn = session.get(Transaction, body.matched_transaction_id)
        if not txn or txn.tenant_id != user.tenant_id:
            raise HTTPException(400, "Transaction not found")
        was_matched = line.is_matched
        line.matched_transaction_id = txn.id
        line.is_matched = True
        line.suggested_transaction_id = txn.id
        line.match_status = "accepted"
        line.match_decided_by_id = user.id
        line.match_decided_at = datetime.utcnow()
        line.match_confidence = line.match_confidence or 100.0
        session.add(line)
        if not was_matched:
            imp = session.get(BankStatementImport, line.import_id)
            if imp and imp.tenant_id == user.tenant_id:
                imp.matched_count = (imp.matched_count or 0) + 1
                session.add(imp)
        log_audit(
            session, user, "UPDATE", "statement_line", line.id,
            {"action": "accept", "transaction_id": txn.id},
        )
    session.commit()
    session.refresh(line)
    return line


class AcceptBody(BaseModel):
    transaction_id: Optional[int] = None


@router.post("/api/statement-lines/{line_id}/accept")
def accept_line_match(
    session: SessionDep, user: WriteUserDep, line_id: int, body: AcceptBody = AcceptBody(),
):
    line = session.exec(
        select(StatementLine).where(
            StatementLine.id == line_id, StatementLine.tenant_id == user.tenant_id
        )
    ).first()
    if not line:
        raise HTTPException(404, "Line not found")
    txn_id = body.transaction_id or line.suggested_transaction_id
    if not txn_id:
        raise HTTPException(400, "No suggested transaction to accept")
    txn = session.get(Transaction, txn_id)
    if not txn or txn.tenant_id != user.tenant_id:
        raise HTTPException(400, "Transaction not found")
    was_matched = line.is_matched
    try:
        accept_match(session, line=line, user_id=user.id, transaction_id=txn_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not was_matched:
        imp = session.get(BankStatementImport, line.import_id)
        if imp and imp.tenant_id == user.tenant_id:
            imp.matched_count = (imp.matched_count or 0) + 1
            session.add(imp)
    log_audit(
        session, user, "UPDATE", "statement_line", line.id,
        {"action": "accept", "transaction_id": txn_id, "confidence": line.match_confidence},
    )
    session.commit()
    session.refresh(line)
    return line


@router.post("/api/statement-lines/{line_id}/reject")
def reject_line_match(session: SessionDep, user: WriteUserDep, line_id: int):
    line = session.exec(
        select(StatementLine).where(
            StatementLine.id == line_id, StatementLine.tenant_id == user.tenant_id
        )
    ).first()
    if not line:
        raise HTTPException(404, "Line not found")
    was_matched = line.is_matched
    reject_match(session, line=line, user_id=user.id)
    if was_matched:
        imp = session.get(BankStatementImport, line.import_id)
        if imp and imp.tenant_id == user.tenant_id:
            imp.matched_count = max(0, (imp.matched_count or 0) - 1)
            session.add(imp)
    log_audit(
        session, user, "UPDATE", "statement_line", line.id,
        {"action": "reject"},
    )
    session.commit()
    session.refresh(line)
    return line
