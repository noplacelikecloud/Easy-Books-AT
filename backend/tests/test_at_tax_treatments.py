"""Tests for Austrian Tax Treatment Catalog and Effective-Dated Rules (PR 6: AT-05)."""
from decimal import Decimal
import pytest
from fastapi import HTTPException
from sqlmodel import Session

from localizations.at.tax_catalog import (
    init_at_tax_treatments,
    resolve_tax_treatment,
    AT_TAX_TREATMENTS_CATALOG,
)
from models import Tenant, User
from models_at import TaxTreatmentVersion


@pytest.fixture
def at_tax_env(client, admin_headers):
    """Sets up a tenant with Austrian profile and tax catalog."""
    res = client.post("/api/at/profile", headers=admin_headers, json={
        "legal_form": "gmbh",
        "profit_method": "ugb_double_entry",
        "vat_status": "regular",
        "vat_method": "accrual",
        "vat_filing_frequency": "monthly",
        "company_register_number": "FN 123456 a",
        "company_register_court": "HG Wien",
        "registered_seat": "Wien",
        "valid_from": "2026-01-01",
    })
    assert res.status_code == 200


def test_standard_tax_treatments_resolution(client, admin_headers, at_tax_env):
    """Tests standard 20%, 10%, 13% tax rate resolution and UVA Kennzahlen."""
    from db import get_session
    from main import app

    # Use test engine session
    with Session(app.state.engine) as session:
        user = session.query(User).filter(User.email == "owner@acme.test").first()
        init_at_tax_treatments(session, user.tenant_id)

        # 1. Standard 20%
        t20 = resolve_tax_treatment(session, user.tenant_id, "AT_STANDARD_20", "2026-03-01")
        assert t20.rate == Decimal("20.00")
        assert t20.uva_base_kz == "022"
        assert t20.uva_tax_kz == "022"

        # 2. Reduced 10%
        t10 = resolve_tax_treatment(session, user.tenant_id, "AT_REDUCED_10", "2026-03-01")
        assert t10.rate == Decimal("10.00")
        assert t10.uva_base_kz == "029"

        # 3. Reduced 13%
        t13 = resolve_tax_treatment(session, user.tenant_id, "AT_REDUCED_13", "2026-03-01")
        assert t13.rate == Decimal("13.00")
        assert t13.uva_base_kz == "006"


def test_4_9_percent_effective_date_and_classification_enforcement(client, admin_headers, at_tax_env):
    """The 4.9% rate is strictly effective from 2026-07-01 and blocked for gastronomy."""
    from main import app

    with Session(app.state.engine) as session:
        user = session.query(User).filter(User.email == "owner@acme.test").first()
        init_at_tax_treatments(session, user.tenant_id)

        # 1. Usage on 2026-06-30 (before effective date) MUST FAIL
        with pytest.raises(HTTPException) as exc1:
            resolve_tax_treatment(session, user.tenant_id, "AT_REDUCED_4_9", "2026-06-30")
        assert exc1.value.status_code == 400
        assert "gilt erst ab 01.07.2026" in exc1.value.detail

        # 2. Usage on 2026-07-01 with staple food succeeds
        t4_9 = resolve_tax_treatment(
            session, user.tenant_id, "AT_REDUCED_4_9", "2026-07-01", product_classification="staple_food"
        )
        assert t4_9.rate == Decimal("4.90")
        assert t4_9.uva_base_kz == "124"
        assert t4_9.uva_tax_kz == "125"

        # 3. Usage on 2026-07-01 with restaurant/gastronomy MUST FAIL
        with pytest.raises(HTTPException) as exc2:
            resolve_tax_treatment(
                session, user.tenant_id, "AT_REDUCED_4_9", "2026-07-01", product_classification="gastronomy"
            )
        assert exc2.value.status_code == 400
        assert "Gastronomie" in exc2.value.detail


def test_tax_treatment_direction_enforcement(client, admin_headers, at_tax_env):
    """Directional treatments reject incorrect direction (e.g. export on a purchase bill)."""
    from main import app

    with Session(app.state.engine) as session:
        user = session.query(User).filter(User.email == "owner@acme.test").first()
        init_at_tax_treatments(session, user.tenant_id)

        # AT_ZERO_EXPORT is sales only
        with pytest.raises(HTTPException) as exc:
            resolve_tax_treatment(session, user.tenant_id, "AT_ZERO_EXPORT", "2026-03-01", direction="purchases")
        assert exc.value.status_code == 400
        assert "nur für 'sales' zulässig" in exc.value.detail

        # Valid for sales
        t_export = resolve_tax_treatment(session, user.tenant_id, "AT_ZERO_EXPORT", "2026-03-01", direction="sales")
        assert t_export.rate == Decimal("0.00")
        assert t_export.uva_base_kz == "011"
