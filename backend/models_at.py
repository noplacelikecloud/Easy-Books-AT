"""Austrian Compliance (UGB / UStG / BAO) SQLModel tables.

Includes:
- DocumentVersion & DocumentNumberSeries (PR 2: AT-01, AT-02)
- PeriodCloseHistory (PR 3: AT-08)
- AccountingProfileVersion, AccountRoleBinding, ReportLineMapping (PR 4: AT-05, AT-11, AT-15)
- TaxTreatmentVersion (PR 6: AT-05)
- TaxEvent, TaxPeriod, TaxAdjustment (PR 7, PR 8: AT-04, AT-10)
- SmallBusinessThresholdLedger (PR 9: AT-EAR-KU)
- TaxFiling, TaxFilingVersion, TaxFilingSubmissionLog (PR 10: AT-10)
- GoodsReceivedRecord (PR 12: Wareneingangsbuch)
- AtAssetValuation (PR 13: AT-12 Anlagen-Nebenrechnung)
- ArchiveObject, LegalHold (PR 14: AT-07 Archivierung & Aufbewahrung)
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Index, Numeric, String, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


class DocumentVersion(SQLModel, table=True):
    """Immutable snapshot of an invoice, bill, or credit/debit note upon finalization.

    § 190 Abs. 4 UGB, § 131 BAO: Belege dürfen nicht in einer Weise verändert
    werden, dass der ursprüngliche Inhalt nicht mehr feststellbar ist.
    """
    __tablename__ = "documentversion"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "document_type", "document_id", "version",
            name="uq_doc_version_tenant_document_version",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    document_type: str = Field(index=True)  # invoice | bill | credit_note | debit_note
    document_id: int = Field(index=True)
    version: int = Field(default=1)
    state: str = Field(default="finalized")  # draft | finalized | corrected | cancelled
    original_document_id: Optional[int] = None
    canonical_payload: str = Field(sa_column=Column(Text, nullable=False))
    payload_hash: str = Field(sa_column=Column(String(64), nullable=False))  # SHA-256
    pdf_path: Optional[str] = None
    pdf_hash: Optional[str] = None
    xml_path: Optional[str] = None
    xml_hash: Optional[str] = None
    series_name: Optional[str] = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    recorded_by_id: Optional[int] = None
    effective_date: Optional[str] = None
    reason: Optional[str] = None
    is_legacy: bool = Field(default=False)


class DocumentNumberSeries(SQLModel, table=True):
    """Consecutive, gap-free numbering series bound to fiscal/calendar year.

    § 131 BAO, § 11 Abs. 1 Z 6 UStG: Fortlaufende Nummerierung je Wirtschaftsjahr.
    """
    __tablename__ = "documentnumberseries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "document_type", "series_code", "year", name="uq_series_type_code_year"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    document_type: str = Field(index=True)  # invoice | bill | credit_note | debit_note
    series_code: str = Field(default="DEFAULT")
    year: int = Field(index=True)
    current_number: int = Field(default=0)
    prefix: str = Field(default="")
    format_pattern: Optional[str] = None  # e.g. "{prefix}-{year}-{seq:05d}"


class PeriodCloseHistory(SQLModel, table=True):
    """Audit log of period lock, close and reopening events (§ 190, 193 UGB)."""
    __tablename__ = "periodclosehistory"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    period_id: int = Field(index=True)
    action: str  # close | reopen | lock | unlock
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    performed_by_id: int
    reason: Optional[str] = None
    closing_balance_hash: Optional[str] = None
    manifest_payload: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))


class AccountingProfileVersion(SQLModel, table=True):
    """Effective-dated Austrian compliance profile."""
    __tablename__ = "accountingprofileversion"
    __table_args__ = (
        Index("ix_at_profile_tenant_dates", "tenant_id", "valid_from", "valid_to"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    jurisdiction: str = Field(default="AT")
    valid_from: str  # YYYY-MM-DD
    valid_to: Optional[str] = None  # YYYY-MM-DD
    legal_form: str = Field(default="gmbh")  # sole_proprietor | gmbh | flexco | og | kg | other
    profit_method: str = Field(default="ugb_double_entry")  # ugb_double_entry | ear
    vat_status: str = Field(default="standard")  # standard | small_business_exempt | opted_in
    vat_method: str = Field(default="accrual")  # accrual | cash
    vat_filing_frequency: str = Field(default="monthly")  # monthly | quarterly | annual_only
    fiscal_year_start: str = Field(default="01-01")
    tax_number: Optional[str] = None
    vat_id: Optional[str] = None  # ATU...
    company_register_number: Optional[str] = None  # FN...
    company_register_court: Optional[str] = None
    registered_seat: Optional[str] = None
    prior_year_turnover: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(18, 4)))
    capabilities: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))  # JSON
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_id: Optional[int] = None
    change_reason: Optional[str] = None
    superseded_at: Optional[datetime] = None
    superseded_by_id: Optional[int] = None


class AccountRoleBinding(SQLModel, table=True):
    """Semantic mapping of standard accounting roles to tenant accounts.

    Prevents hardcoded account numbers in Austrian postings (§ 190 UGB).
    """
    __tablename__ = "accountrolebinding"
    __table_args__ = (
        UniqueConstraint("tenant_id", "role_key", "valid_from", name="uq_account_role_binding"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    role_key: str = Field(index=True)
    account_id: int = Field(foreign_key="account.id")
    valid_from: str = Field(default="1900-01-01")
    valid_to: Optional[str] = None


class ReportLineMapping(SQLModel, table=True):
    """Mapping of accounts to statutory UGB / E1a financial statement line items."""
    __tablename__ = "reportlinemapping"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "account_id", "report_type", "line_code",
            name="uq_report_line_mapping",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    account_id: int = Field(foreign_key="account.id")
    report_type: str = Field(index=True)  # ugb_balance_sheet | ugb_income_statement | ear_e1a
    line_code: str = Field(index=True)
    line_name: str


class TaxTreatmentVersion(SQLModel, table=True):
    """Effective-dated VAT treatment definition per § 10, 11, 19, 21 UStG 1994."""
    __tablename__ = "taxtreatmentversion"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", "valid_from", name="uq_tax_treatment_code_date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    jurisdiction: str = Field(default="AT")
    code: str = Field(index=True)
    name: str
    direction: str = Field(default="both")  # sales | purchases | both
    treatment_type: str  # standard | reduced_10 | reduced_13 | reduced_4_9 | zero_rated | exempt | reverse_charge | intra_eu_supply | intra_eu_acquisition | export | import_vat | small_business_exempt
    rate: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    legal_notice: Optional[str] = None
    valid_from: str = Field(default="1900-01-01")
    valid_to: Optional[str] = None
    allowed_product_types: Optional[str] = None
    uva_base_kz: Optional[str] = None  # e.g. 022, 029, 006, 124, 011, 017, 021, 070
    uva_tax_kz: Optional[str] = None   # e.g. 022_tax, 125, 060, 065, 066
    zm_relevant: bool = Field(default=False)
    output_account_role: Optional[str] = None
    input_account_role: Optional[str] = None
    deductibility_rate: Decimal = Field(default=Decimal("1.0"), sa_column=Column(Numeric(18, 4)))


class TaxEvent(SQLModel, table=True):
    """Single immutable tax event backing all Austrian UVA/U1/ZM reports."""
    __tablename__ = "taxevent"
    __table_args__ = (
        Index("ix_tax_event_tenant_period", "tenant_id", "tax_period"),
        Index("ix_tax_event_tenant_date", "tenant_id", "tax_date"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_tax_event_idempotency"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    document_version_id: Optional[int] = None
    transaction_id: Optional[int] = Field(default=None, foreign_key="transaction.id", index=True)
    treatment_version_id: Optional[int] = Field(default=None, foreign_key="taxtreatmentversion.id")
    profile_version_id: Optional[int] = Field(default=None, foreign_key="accountingprofileversion.id")
    direction: str = Field(default="sales")  # sales | purchases
    source_doc_type: str = Field(index=True)  # invoice | bill | payment | advance | credit_note | debit_note | manual
    source_doc_id: int = Field(index=True)
    event_type: str  # invoice | bill | payment | advance | credit | debit | write_off | adjustment | acquisition | import
    original_event_id: Optional[int] = None
    service_date: str
    invoice_date: str
    payment_date: Optional[str] = None
    booking_date: str
    tax_date: str = Field(index=True)
    tax_period: str = Field(index=True)  # YYYY-MM or YYYY-Qx
    treatment_code: str = Field(index=True)
    currency: str = Field(default="EUR")
    exchange_rate: Decimal = Field(default=Decimal("1.0"), sa_column=Column(Numeric(18, 4)))
    base_amount: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    tax_amount: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    base_amount_eur: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    tax_amount_eur: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    output_tax: Decimal = Field(default=Decimal("0"), sa_column=Column(Numeric(18, 4)))
    reverse_charge_tax: Decimal = Field(default=Decimal("0"), sa_column=Column(Numeric(18, 4)))
    input_tax_deductible: Decimal = Field(default=Decimal("0"), sa_column=Column(Numeric(18, 4)))
    input_tax_non_deductible: Decimal = Field(default=Decimal("0"), sa_column=Column(Numeric(18, 4)))
    uva_base_kz: Optional[str] = None
    uva_tax_kz: Optional[str] = None
    zm_relevant: bool = Field(default=False)
    partner_country: Optional[str] = None
    partner_vat_id: Optional[str] = None
    state: str = Field(default="final")  # final | reversed
    idempotency_key: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaxPeriod(SQLModel, table=True):
    """Tax filing period (monthly or quarterly) per § 21 UStG."""
    __tablename__ = "taxperiod"
    __table_args__ = (
        UniqueConstraint("tenant_id", "period_key", name="uq_tax_period_tenant_key"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    period_key: str = Field(index=True)  # e.g. "2026-07", "2026-Q3"
    period_type: str = Field(default="month")  # month | quarter
    start_date: str
    end_date: str
    status: str = Field(default="open")  # open | filed | closed
    filed_at: Optional[datetime] = None


class TaxAdjustment(SQLModel, table=True):
    """Audit link for adjustments, skonto, bad debts and corrections."""
    __tablename__ = "taxadjustment"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    original_event_id: int = Field(index=True)
    new_event_id: int = Field(index=True)
    reason: str
    adjustment_type: str  # discount | bad_debt | correction | return


class SmallBusinessThresholdLedger(SQLModel, table=True):
    """Annual turnover tracker for § 6 Abs. 1 Z 27 UStG (55,000 EUR + 10% tolerance)."""
    __tablename__ = "smallbusinessthresholdledger"
    __table_args__ = (
        UniqueConstraint("tenant_id", "year", name="uq_ku_tenant_year"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    year: int = Field(index=True)
    qualifying_turnover: Decimal = Field(default=Decimal("0"), sa_column=Column(Numeric(18, 4)))
    threshold_amount: Decimal = Field(default=Decimal("55000.00"), sa_column=Column(Numeric(18, 4)))
    tolerance_amount: Decimal = Field(default=Decimal("60500.00"), sa_column=Column(Numeric(18, 4)))
    is_exceeded: bool = Field(default=False)
    exceeded_on_date: Optional[str] = None
    exceeded_by_invoice_id: Optional[int] = None
    opted_into_standard_vat: bool = Field(default=False)
    option_valid_from: Optional[str] = None


class TaxFiling(SQLModel, table=True):
    """Official VAT return filing (UVA U30, ZM, U1)."""
    __tablename__ = "taxfiling"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "filing_type", "period_key",
            name="uq_tax_filing_tenant_type_period",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    filing_type: str = Field(index=True)  # uva | u1 | zm
    period_key: str = Field(index=True)
    year: int = Field(index=True)
    version: int = Field(default=1)
    status: str = Field(default="draft")  # draft | finalized | submitted | superseded
    xml_payload: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    xml_hash: Optional[str] = None
    total_payable: Decimal = Field(default=Decimal("0"), sa_column=Column(Numeric(18, 4)))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finalized_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None


class TaxFilingVersion(SQLModel, table=True):
    """Snapshot of events included in a tax filing version."""
    __tablename__ = "taxfilingversion"
    __table_args__ = (
        UniqueConstraint("tax_filing_id", "version", name="uq_tax_filing_version"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    tax_filing_id: int = Field(foreign_key="taxfiling.id", index=True)
    version: int = Field(default=1)
    event_ids: str = Field(default="[]", sa_column=Column(Text, nullable=False))
    summary_data: str = Field(default="{}", sa_column=Column(Text, nullable=False))
    xml_payload: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    xml_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaxFilingSubmissionLog(SQLModel, table=True):
    """Audit log of FinanzOnline transmissions / XML downloads."""
    __tablename__ = "taxfilingsubmissionlog"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    tax_filing_id: int = Field(index=True)
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="success")  # success | error
    request_hash: Optional[str] = None
    response_payload: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    error_message: Optional[str] = None


class GoodsReceivedRecord(SQLModel, table=True):
    """Wareneingangsbuch record per § 127 BAO."""
    __tablename__ = "goodsreceivedrecord"
    __table_args__ = (
        Index("ix_goods_received_tenant_date", "tenant_id", "received_date"),
        UniqueConstraint("tenant_id", "calendar_year", "entry_number", name="uq_goods_received_entry_number"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    calendar_year: int = Field(index=True)
    entry_number: int = Field(index=True)
    received_date: str = Field(index=True)
    vendor_name: str
    vendor_address: Optional[str] = None
    description: str
    gross_amount: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    net_amount: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    vat_amount: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    bill_id: Optional[int] = None
    document_number: Optional[str] = None


class AtAssetValuation(SQLModel, table=True):
    """Austrian tax asset subsidiary ledger (Anlagenverzeichnis gem. § 7, 8 EStG)."""
    __tablename__ = "atassetvaluation"
    __table_args__ = (
        UniqueConstraint("tenant_id", "asset_id", name="uq_at_asset_tenant_asset"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    asset_id: int = Field(foreign_key="fixedasset.id", index=True)
    commissioning_date: str  # Inbetriebnahmedatum
    initial_cost_gross: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    input_vat_deducted: Decimal = Field(default=Decimal("0"), sa_column=Column(Numeric(18, 4)))
    initial_cost_tax: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    depreciation_method: str = Field(default="linear")  # linear | degressiv | gwg
    half_year_rule_applied: bool = Field(default=False)
    useful_life_years: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    tax_book_value: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    current_year_tax_depreciation: Decimal = Field(default=Decimal("0"), sa_column=Column(Numeric(18, 4)))
    is_gwg: bool = Field(default=False)
    asset_category: str = Field(default="other")  # pkw | gebaeude | gwg | software | maschinen | other


class AtAssetDepreciation(SQLModel, table=True):
    """Immutable annual tax-depreciation movement for an Austrian asset."""
    __tablename__ = "atassetdepreciation"
    __table_args__ = (
        UniqueConstraint("tenant_id", "valuation_id", "year", name="uq_at_asset_depreciation_year"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    valuation_id: int = Field(foreign_key="atassetvaluation.id", index=True)
    year: int = Field(index=True)
    opening_tax_book_value: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    depreciation_amount: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    closing_tax_book_value: Decimal = Field(sa_column=Column(Numeric(18, 4)))
    transaction_id: Optional[int] = Field(default=None, foreign_key="transaction.id")
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


class ArchiveObject(SQLModel, table=True):
    """Immutable archive record with 7-year retention rule per § 132 BAO."""
    __tablename__ = "archiveobject"
    __table_args__ = (
        Index("ix_archive_tenant_type_ref", "tenant_id", "object_type", "reference_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    object_type: str = Field(index=True)  # invoice_pdf | bill_scan | voucher_pdf | uva_xml | tax_export | audit_log
    reference_id: int = Field(index=True)
    file_path: str
    file_name: str
    mime_type: str
    file_size: int
    sha256_hash: str = Field(sa_column=Column(String(64), nullable=False))
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    retain_until: str  # YYYY-MM-DD
    legal_hold: bool = Field(default=False)
    legal_hold_reason: Optional[str] = None


class LegalHold(SQLModel, table=True):
    """Legal hold instruction overriding standard retention deletion (§ 132 BAO)."""
    __tablename__ = "legalhold"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    title: str
    reason: str
    instituted_at: datetime = Field(default_factory=datetime.utcnow)
    instituted_by_id: int
    is_active: bool = Field(default=True)


class ArchiveLegalHold(SQLModel, table=True):
    """Many-to-many assignment so independent legal holds cannot overwrite each other."""
    __tablename__ = "archivelegalhold"
    __table_args__ = (
        UniqueConstraint("archive_object_id", "legal_hold_id", name="uq_archive_legal_hold"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    archive_object_id: int = Field(foreign_key="archiveobject.id", index=True)
    legal_hold_id: int = Field(foreign_key="legalhold.id", index=True)
