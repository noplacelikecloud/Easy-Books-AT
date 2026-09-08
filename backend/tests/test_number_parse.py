"""
Tests for services/number_parse.py — locale-aware number and date parsing.
"""
from decimal import Decimal
import pytest

from services.number_parse import (
    AmbiguousNumberFormatError,
    DateParseError,
    NumberParseConfig,
    NumberParseError,
    parse_date_flexible,
    parse_money,
)


def test_parse_money_austrian_european_comma():
    cfg = NumberParseConfig(decimal_separator=",", thousands_separator=".")
    assert parse_money("123,45", cfg) == Decimal("123.45")
    assert parse_money("1.234,56", cfg) == Decimal("1234.56")
    assert parse_money("12.345.678,90", cfg) == Decimal("12345678.90")
    assert parse_money("0,05", cfg) == Decimal("0.05")
    assert parse_money("500", cfg) == Decimal("500.00")
    assert parse_money("EUR 1.234,56", cfg) == Decimal("1234.56")
    assert parse_money("1.234,56 €", cfg) == Decimal("1234.56")


def test_parse_money_us_anglo_dot():
    cfg = NumberParseConfig(decimal_separator=".", thousands_separator=",")
    assert parse_money("123.45", cfg) == Decimal("123.45")
    assert parse_money("1,234.56", cfg) == Decimal("1234.56")
    assert parse_money("12,345,678.90", cfg) == Decimal("12345678.90")
    assert parse_money("$1,234.56", cfg) == Decimal("1234.56")


def test_parse_money_negative_conventions():
    # Preceding minus
    assert parse_money("-123,45", NumberParseConfig(decimal_separator=",")) == Decimal("-123.45")
    assert parse_money("-1,234.56", NumberParseConfig(decimal_separator=".")) == Decimal("-1234.56")

    # Trailing minus (common in Austrian / German bank exports like Raiffeisen, Erste Bank)
    assert parse_money("123,45-", NumberParseConfig(decimal_separator=",")) == Decimal("-123.45")
    assert parse_money("1.234,56-", NumberParseConfig(decimal_separator=",")) == Decimal("-1234.56")

    # Parentheses
    assert parse_money("(123,45)", NumberParseConfig(decimal_separator=",")) == Decimal("-123.45")
    assert parse_money("(1,234.56)", NumberParseConfig(decimal_separator=".")) == Decimal("-1234.56")

    # Trailing CR / DR
    assert parse_money("500,00 CR", NumberParseConfig(decimal_separator=",")) == Decimal("500.00")
    assert parse_money("500,00 DR", NumberParseConfig(decimal_separator=",")) == Decimal("-500.00")


def test_parse_money_spaces_and_empty():
    cfg = NumberParseConfig(decimal_separator=",")
    assert parse_money("1 234,56", cfg) == Decimal("1234.56")
    assert parse_money("", cfg) == Decimal("0.00")
    assert parse_money("   ", cfg) == Decimal("0.00")
    assert parse_money(None, cfg) == Decimal("0.00")

    no_empty_cfg = NumberParseConfig(allow_empty=False)
    with pytest.raises(NumberParseError):
        parse_money("", no_empty_cfg)
    with pytest.raises(NumberParseError):
        parse_money(None, no_empty_cfg)


def test_parse_money_rejects_contradictory_formats():
    # Profile says decimal is comma, but input has US format with comma as thousands and dot as decimal
    cfg_at = NumberParseConfig(decimal_separator=",", thousands_separator=".")
    with pytest.raises(AmbiguousNumberFormatError):
        parse_money("1,234.56", cfg_at)

    # Profile says decimal is dot, but input has dot as thousands and comma as decimal
    cfg_us = NumberParseConfig(decimal_separator=".", thousands_separator=",")
    with pytest.raises(AmbiguousNumberFormatError):
        parse_money("1.234,56", cfg_us)

    # Invalid grouping
    with pytest.raises(AmbiguousNumberFormatError):
        parse_money("1.23.456,78", cfg_at)


def test_parse_money_auto_detect():
    # Unambiguous formats with auto config
    assert parse_money("1.234,56") == Decimal("1234.56")
    assert parse_money("1,234.56") == Decimal("1234.56")
    assert parse_money("123,45") == Decimal("123.45")
    assert parse_money("123.45") == Decimal("123.45")
    assert parse_money("-500,25") == Decimal("-500.25")

    # Ambiguous formats like 1,234 or 1.234 without config should raise AmbiguousNumberFormatError
    with pytest.raises(AmbiguousNumberFormatError):
        parse_money("1.234")
    with pytest.raises(AmbiguousNumberFormatError):
        parse_money("1,234")


def test_parse_date_flexible():
    # ISO
    assert parse_date_flexible("2026-05-02") == "2026-05-02"
    assert parse_date_flexible("2026/05/02") == "2026-05-02"

    # Austrian / German standard DD.MM.YYYY
    assert parse_date_flexible("02.05.2026") == "2026-05-02"
    assert parse_date_flexible("31.12.2025") == "2025-12-31"

    # European DD-MM-YYYY or DD/MM/YYYY
    assert parse_date_flexible("02-05-2026") == "2026-05-02"
    assert parse_date_flexible("25/06/2026") == "2026-06-25"

    # Invalid dates
    with pytest.raises(DateParseError):
        parse_date_flexible("99.99.2026")
    with pytest.raises(DateParseError):
        parse_date_flexible("invalid-date")
    with pytest.raises(DateParseError):
        parse_date_flexible("")
