"""
Locale-aware number, currency, and date parsing for imports and forms.

Provides deterministic parsing of monetary amounts across Austrian/European (1.234,56),
Anglo-American (1,234.56), and space-separated formats, with strict validation against
silent misinterpretation or data corruption.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal, Optional

from services.money import CENTS, ROUND_HALF_EVEN, ZERO, D


class NumberParseError(ValueError):
    """Raised when a numeric string cannot be parsed."""
    pass


class AmbiguousNumberFormatError(NumberParseError):
    """Raised when a number format cannot be unambiguously resolved or contradicts the profile."""
    pass


class DateParseError(ValueError):
    """Raised when a date string cannot be parsed into YYYY-MM-DD."""
    pass


SignConvention = Literal["standard", "parentheses", "trailing_minus", "trailing_cr_dr", "auto"]
DecimalSeparator = Literal[".", ","]
ThousandsSeparator = Literal[",", ".", " ", "'", ""]


@dataclass(frozen=True)
class NumberParseConfig:
    decimal_separator: Optional[DecimalSeparator] = None
    thousands_separator: Optional[ThousandsSeparator] = None
    sign_convention: SignConvention = "auto"
    allow_empty: bool = True
    default_empty: Decimal = ZERO


@dataclass(frozen=True)
class ImportProfile:
    delimiter: str = ","
    decimal_separator: DecimalSeparator = "."
    thousands_separator: Optional[ThousandsSeparator] = None
    date_format: Optional[str] = None
    sign_convention: SignConvention = "auto"
    date_col: str = "date"
    description_col: str = "description"
    debit_col: Optional[str] = "debit"
    credit_col: Optional[str] = "credit"
    amount_col: Optional[str] = None
    balance_col: Optional[str] = "balance"


# Pre-compiled currency and whitespace regexes
_CURRENCY_SYMBOLS_RE = re.compile(r"[$€£¥₹₽CHF\sA-Z]{1,4}", re.IGNORECASE)


def parse_money(
    value: str | int | float | Decimal | None,
    config: Optional[NumberParseConfig] = None,
) -> Decimal:
    """
    Parse any monetary string or number into a Decimal quantized to 2 decimal places.

    Raises NumberParseError or AmbiguousNumberFormatError on invalid / contradictory formats.
    """
    cfg = config or NumberParseConfig()

    if value is None:
        if cfg.allow_empty:
            return cfg.default_empty
        raise NumberParseError("Empty value not allowed")

    if isinstance(value, (int, Decimal)):
        return D(value).quantize(CENTS, rounding=ROUND_HALF_EVEN)

    if isinstance(value, float):
        # str() avoids binary float drift
        return D(str(value)).quantize(CENTS, rounding=ROUND_HALF_EVEN)

    s = str(value).strip()
    if not s:
        if cfg.allow_empty:
            return cfg.default_empty
        raise NumberParseError("Empty string not allowed")

    # Detect sign and strip sign wrappers
    is_negative = False
    is_positive = False

    # 1. Parentheses: (123.45) or (123,45)
    if s.startswith("(") and s.endswith(")"):
        if cfg.sign_convention in ("parentheses", "auto"):
            is_negative = True
            s = s[1:-1].strip()
        else:
            raise NumberParseError(f"Parentheses negative not allowed by sign convention '{cfg.sign_convention}'")

    # 2. Trailing CR / DR
    s_upper = s.upper()
    if s_upper.endswith(" CR"):
        if cfg.sign_convention in ("trailing_cr_dr", "auto"):
            # In banking statements, CR is credit (usually positive inflow), DR is debit (negative outflow)
            # Unless configured differently, CR is positive, DR is negative
            is_positive = True
            s = s[:-3].strip()
        else:
            raise NumberParseError(f"CR suffix not allowed by sign convention '{cfg.sign_convention}'")
    elif s_upper.endswith(" DR"):
        if cfg.sign_convention in ("trailing_cr_dr", "auto"):
            is_negative = True
            s = s[:-3].strip()
        else:
            raise NumberParseError(f"DR suffix not allowed by sign convention '{cfg.sign_convention}'")

    # 3. Trailing minus: 123.45-
    if s.endswith("-"):
        if cfg.sign_convention in ("trailing_minus", "auto"):
            if is_negative:
                raise NumberParseError(f"Double negative sign in '{value}'")
            is_negative = True
            s = s[:-1].strip()
        else:
            raise NumberParseError(f"Trailing minus not allowed by sign convention '{cfg.sign_convention}'")
    elif s.endswith("+"):
        s = s[:-1].strip()

    # 4. Leading sign: -123.45 or +123.45
    if s.startswith("-"):
        if is_negative:
            raise NumberParseError(f"Double negative sign in '{value}'")
        is_negative = True
        s = s[1:].strip()
    elif s.startswith("+"):
        s = s[1:].strip()

    # Strip currency code/symbols at edges (e.g. "EUR 123,45" or "123,45 €" or "$123.45")
    # Clean leading
    s = re.sub(r"^[\s$€£¥₹₽A-Za-z]+", "", s).strip()
    # Clean trailing
    s = re.sub(r"[\s$€£¥₹₽A-Za-z]+$", "", s).strip()

    if not s:
        if cfg.allow_empty:
            return cfg.default_empty
        raise NumberParseError(f"No numeric characters found in '{value}'")

    # Remove non-breaking spaces and regular spaces if used as thousands separator
    s = s.replace("\u00a0", " ")
    has_spaces = " " in s
    if has_spaces:
        # Check if space is thousands separator
        parts = s.split(" ")
        # Every part except the first should be 3 digits if it's grouping, or space before decimal
        # Remove spaces
        s = s.replace(" ", "")

    # Count dots and commas
    dot_count = s.count(".")
    comma_count = s.count(",")
    quote_count = s.count("'")

    if quote_count > 0:
        # Swiss thousands separator: e.g. 1'234.56 or 1'234,56
        s = s.replace("'", "")

    # Determine decimal separator
    dec_sep = cfg.decimal_separator
    th_sep = cfg.thousands_separator

    if dec_sep == ",":
        # Explicit European format: comma is decimal, dot can be thousands
        if comma_count > 1:
            raise AmbiguousNumberFormatError(f"Multiple decimal commas in '{value}'")
        if th_sep == "." or th_sep is None:
            if dot_count > 0:
                # Dots must be thousands separator
                # If dot appears after comma, it's contradictory!
                if comma_count == 1 and s.find(".") > s.find(","):
                    raise AmbiguousNumberFormatError(
                        f"Dot appears after comma in '{value}', which contradicts decimal_separator=','"
                    )
                # Verify grouping if dot present
                dot_parts = s.split(",")
                integer_part = dot_parts[0]
                # Each dot group except first should be 3 digits
                sub_parts = integer_part.split(".")
                for p in sub_parts[1:]:
                    if len(p) != 3:
                        raise AmbiguousNumberFormatError(
                            f"Invalid thousands grouping in '{value}' for thousands_separator='.'"
                        )
                s = integer_part.replace(".", "") + ("," + dot_parts[1] if len(dot_parts) > 1 else "")
        elif th_sep == "" and dot_count > 0:
            raise AmbiguousNumberFormatError(f"Unexpected dot in '{value}' with thousands_separator=''")

        # Now replace decimal comma with dot
        s = s.replace(",", ".")

    elif dec_sep == ".":
        # Explicit Anglo format: dot is decimal, comma can be thousands
        if dot_count > 1:
            raise AmbiguousNumberFormatError(f"Multiple decimal dots in '{value}'")
        if th_sep == "," or th_sep is None:
            if comma_count > 0:
                # Comma must be thousands separator
                if dot_count == 1 and s.find(",") > s.find("."):
                    raise AmbiguousNumberFormatError(
                        f"Comma appears after dot in '{value}', which contradicts decimal_separator='.'"
                    )
                comma_parts = s.split(".")
                integer_part = comma_parts[0]
                sub_parts = integer_part.split(",")
                for p in sub_parts[1:]:
                    if len(p) != 3:
                        raise AmbiguousNumberFormatError(
                            f"Invalid thousands grouping in '{value}' for thousands_separator=','"
                        )
                s = integer_part.replace(",", "") + ("." + comma_parts[1] if len(comma_parts) > 1 else "")
        elif th_sep == "" and comma_count > 0:
            raise AmbiguousNumberFormatError(f"Unexpected comma in '{value}' with thousands_separator=''")

    else:
        # Auto-detect when decimal_separator is not specified
        if dot_count > 0 and comma_count > 0:
            # Both present: order reveals the role
            last_dot = s.rfind(".")
            last_comma = s.rfind(",")
            if last_comma > last_dot:
                # European: 1.234,56
                if comma_count > 1:
                    raise AmbiguousNumberFormatError(f"Multiple commas in '{value}'")
                s = s.replace(".", "").replace(",", ".")
            else:
                # US: 1,234.56
                if dot_count > 1:
                    raise AmbiguousNumberFormatError(f"Multiple dots in '{value}'")
                s = s.replace(",", "")
        elif comma_count == 1 and dot_count == 0:
            # e.g. "123,45" or "1,234"
            parts = s.split(",")
            if len(parts[1]) == 2:
                # Two decimal places -> unambiguously decimal comma: 123,45 -> 123.45
                s = s.replace(",", ".")
            elif len(parts[1]) == 3 and len(parts[0]) <= 3:
                # Ambiguous: could be 1,000 (thousands) or 1,234 (3 decimals)
                # In banking statements without config, reject to avoid 1000x corruption
                raise AmbiguousNumberFormatError(
                    f"Ambiguous number '{value}': ambiguous comma separator. Specify decimal_separator in profile."
                )
            else:
                s = s.replace(",", ".")
        elif dot_count == 1 and comma_count == 0:
            # e.g. "123.45" or "1.234"
            parts = s.split(".")
            if len(parts[1]) == 2:
                # Two decimal places -> decimal dot: 123.45
                pass
            elif len(parts[1]) == 3 and len(parts[0]) <= 3:
                # Ambiguous: could be 1.000 (thousands) or 1.234 (3 decimals)
                raise AmbiguousNumberFormatError(
                    f"Ambiguous number '{value}': ambiguous dot separator. Specify decimal_separator in profile."
                )
            else:
                pass
        elif dot_count > 1 and comma_count == 0:
            # e.g. 1.234.567 -> thousands separators without decimals
            sub_parts = s.split(".")
            for p in sub_parts[1:]:
                if len(p) != 3:
                    raise AmbiguousNumberFormatError(f"Invalid grouping in '{value}'")
            s = s.replace(".", "")
        elif comma_count > 1 and dot_count == 0:
            # e.g. 1,234,567 -> thousands separators without decimals
            sub_parts = s.split(",")
            for p in sub_parts[1:]:
                if len(p) != 3:
                    raise AmbiguousNumberFormatError(f"Invalid grouping in '{value}'")
            s = s.replace(",", "")

    # Final conversion to Decimal
    try:
        dec = Decimal(s)
    except InvalidOperation as exc:
        raise NumberParseError(f"Cannot parse '{value}' as number: {exc}") from exc

    if is_negative:
        dec = -dec

    return dec.quantize(CENTS, rounding=ROUND_HALF_EVEN)


def parse_date_flexible(val: str, format_hint: Optional[str] = None) -> str:
    """
    Parse a date string into ISO YYYY-MM-DD format.

    Supports ISO (YYYY-MM-DD), Austrian/German (DD.MM.YYYY), European (DD/MM/YYYY, DD-MM-YYYY),
    and US (MM/DD/YYYY if format_hint is specified).
    """
    s = (val or "").strip()
    if not s:
        raise DateParseError("Date value cannot be empty")

    # If format_hint is explicitly given, try it first
    if format_hint:
        from datetime import datetime
        try:
            return datetime.strptime(s, format_hint).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Regex matches
    # 1. ISO format: YYYY-MM-DD or YYYY/MM/DD
    m_iso = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    if m_iso:
        y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        _validate_date_parts(y, m, d, s)
        return f"{y:04d}-{m:02d}-{d:02d}"

    # 2. Dot-delimited Austrian/German: DD.MM.YYYY
    m_dot = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})", s)
    if m_dot:
        d, m, y = int(m_dot.group(1)), int(m_dot.group(2)), int(m_dot.group(3))
        _validate_date_parts(y, m, d, s)
        return f"{y:04d}-{m:02d}-{d:02d}"

    # 3. Dash-delimited: DD-MM-YYYY
    m_dash = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})", s)
    if m_dash:
        d, m, y = int(m_dash.group(1)), int(m_dash.group(2)), int(m_dash.group(3))
        _validate_date_parts(y, m, d, s)
        return f"{y:04d}-{m:02d}-{d:02d}"

    # 4. Slash-delimited: DD/MM/YYYY vs MM/DD/YYYY
    m_slash = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m_slash:
        p1, p2, y = int(m_slash.group(1)), int(m_slash.group(2)), int(m_slash.group(3))
        if format_hint and "%m/%d" in format_hint:
            m, d = p1, p2
        elif p1 > 12 >= p2:
            # p1 cannot be month, so p1=day, p2=month
            d, m = p1, p2
        elif p2 > 12 >= p1:
            # p2 cannot be month, so p2=day, p1=month
            m, d = p1, p2
        else:
            # Default to European convention DD/MM/YYYY unless hint says US
            d, m = p1, p2
        _validate_date_parts(y, m, d, s)
        return f"{y:04d}-{m:02d}-{d:02d}"

    raise DateParseError(f"Unrecognized date format in '{val}'")


def _validate_date_parts(year: int, month: int, day: int, raw: str) -> None:
    if not (1 <= month <= 12):
        raise DateParseError(f"Invalid month {month} in date '{raw}'")
    if not (1 <= day <= 31):
        raise DateParseError(f"Invalid day {day} in date '{raw}'")
    if not (1900 <= year <= 2100):
        raise DateParseError(f"Year {year} out of reasonable range in date '{raw}'")
