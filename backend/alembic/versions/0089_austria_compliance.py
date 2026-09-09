"""austria_compliance — Austrian UGB / UStG / BAO compliance models (PR-1 to PR-18).

Revision ID: 0089_austria_compliance
Revises: 0088_device_tokens
Create Date: 2026-09-08
"""
from datetime import datetime
import hashlib
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlmodel import SQLModel
import models_at  # noqa: F401

revision: str = "0089_austria_compliance"
down_revision: Union[str, Sequence[str], None] = "0088_device_tokens"
branch_labels = None
depends_on = None

NEW_AT_TABLES = [
    "documentversion",
    "documentnumberseries",
    "periodclosehistory",
    "accountingprofileversion",
    "accountrolebinding",
    "reportlinemapping",
    "taxtreatmentversion",
    "taxevent",
    "taxperiod",
    "taxadjustment",
    "smallbusinessthresholdledger",
    "taxfiling",
    "taxfilingversion",
    "taxfilingsubmissionlog",
    "goodsreceivedrecord",
    "atassetvaluation",
    "atassetdepreciation",
    "archiveobject",
    "legalhold",
    "archivelegalhold",
]


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    def add_cols_if_missing(table_name: str, cols: list[sa.Column]):
        if not insp.has_table(table_name):
            return
        existing = {c["name"] for c in insp.get_columns(table_name)}
        with op.batch_alter_table(table_name) as batch:
            for col in cols:
                if col.name not in existing:
                    batch.add_column(col)

    add_cols_if_missing("accountingperiod", [
        sa.Column("close_status", sa.String(), nullable=False, server_default="open"),
        sa.Column("reopen_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_reopened_at", sa.DateTime(), nullable=True),
        sa.Column("last_reopened_by_id", sa.Integer(), nullable=True),
        sa.Column("reopen_reason", sa.String(), nullable=True),
        sa.Column("snapshot_hash", sa.String(), nullable=True),
    ])

    party_cols = [
        sa.Column("legal_form", sa.String(), nullable=True),
        sa.Column("registered_seat", sa.String(), nullable=True),
        sa.Column("company_register_number", sa.String(), nullable=True),
        sa.Column("company_register_court", sa.String(), nullable=True),
        sa.Column("tax_number", sa.String(), nullable=True),
        sa.Column("uid", sa.String(), nullable=True),
        sa.Column("uid_verification_status", sa.String(), nullable=True),
        sa.Column("uid_verified_at", sa.DateTime(), nullable=True),
        sa.Column("uid_verification_method", sa.String(), nullable=True),
        sa.Column("is_business", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("address_street", sa.String(), nullable=True),
        sa.Column("address_zip", sa.String(), nullable=True),
        sa.Column("address_city", sa.String(), nullable=True),
        sa.Column("address_country", sa.String(), nullable=True, server_default="AT"),
    ]
    add_cols_if_missing("customer", party_cols)
    add_cols_if_missing("vendor", [
        sa.Column("legal_form", sa.String(), nullable=True),
        sa.Column("registered_seat", sa.String(), nullable=True),
        sa.Column("company_register_number", sa.String(), nullable=True),
        sa.Column("company_register_court", sa.String(), nullable=True),
        sa.Column("tax_number", sa.String(), nullable=True),
        sa.Column("uid", sa.String(), nullable=True),
        sa.Column("uid_verification_status", sa.String(), nullable=True),
        sa.Column("uid_verified_at", sa.DateTime(), nullable=True),
        sa.Column("uid_verification_method", sa.String(), nullable=True),
        sa.Column("is_business", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("address_street", sa.String(), nullable=True),
        sa.Column("address_zip", sa.String(), nullable=True),
        sa.Column("address_city", sa.String(), nullable=True),
        sa.Column("address_country", sa.String(), nullable=True, server_default="AT"),
    ])

    doc_cols = [
        sa.Column("lifecycle_status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("delivery_status", sa.String(), nullable=False, server_default="not_sent"),
        sa.Column("settlement_status", sa.String(), nullable=False, server_default="unpaid"),
        sa.Column("service_date_start", sa.String(), nullable=True),
        sa.Column("service_date_end", sa.String(), nullable=True),
        sa.Column("tax_treatment_code", sa.String(), nullable=True),
        sa.Column("correction_reason", sa.String(), nullable=True),
    ]
    add_cols_if_missing("invoice", doc_cols + [sa.Column("original_invoice_id", sa.Integer(), nullable=True)])
    add_cols_if_missing("bill", doc_cols + [sa.Column("original_bill_id", sa.Integer(), nullable=True)])

    line_cols = [
        sa.Column("service_date", sa.String(), nullable=True),
        sa.Column("tax_treatment_code", sa.String(), nullable=True),
        sa.Column("tax_treatment_snapshot", sa.Text(), nullable=True),
    ]
    add_cols_if_missing("invoiceline", line_cols)
    add_cols_if_missing("billline", [
        sa.Column("service_date", sa.String(), nullable=True),
        sa.Column("tax_treatment_code", sa.String(), nullable=True),
        sa.Column("tax_treatment_snapshot", sa.Text(), nullable=True),
    ])

    note_cols = [
        sa.Column("lifecycle_status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("original_document_id", sa.Integer(), nullable=True),
        sa.Column("original_document_type", sa.String(), nullable=True),
        sa.Column("tax_treatment_code", sa.String(), nullable=True),
    ]
    add_cols_if_missing("creditnote", note_cols)
    add_cols_if_missing("debitnote", [
        sa.Column("lifecycle_status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("original_document_id", sa.Integer(), nullable=True),
        sa.Column("original_document_type", sa.String(), nullable=True),
        sa.Column("tax_treatment_code", sa.String(), nullable=True),
    ])
    note_line_cols = [
        sa.Column("tax_treatment_code", sa.String(), nullable=True),
        sa.Column("tax_rate", sa.Numeric(18, 4), nullable=True),
        sa.Column("tax_amount", sa.Numeric(18, 4), nullable=False, server_default="0"),
    ]
    add_cols_if_missing("creditnoteline", note_line_cols)
    add_cols_if_missing("debitnoteline", note_line_cols)

    for table_name in NEW_AT_TABLES:
        table = SQLModel.metadata.tables.get(table_name)
        if table is not None:
            table.create(bind, checkfirst=True)

    # A posted or externally issued legacy document must never become an
    # editable draft merely because the lifecycle column is new.
    for table_name in ("invoice", "bill"):
        if not insp.has_table(table_name):
            continue
        table = sa.Table(table_name, sa.MetaData(), autoload_with=bind)
        finalized = sa.or_(
            table.c.transaction_id.is_not(None),
            table.c.status.not_in(("draft",)),
        )
        bind.execute(table.update().where(finalized).values(lifecycle_status="finalized"))
    if insp.has_table("accountingperiod"):
        period = sa.Table("accountingperiod", sa.MetaData(), autoload_with=bind)
        bind.execute(
            period.update().where(period.c.is_locked == sa.true()).values(close_status="closed")
        )

    # Abort before establishing statutory number uniqueness if existing data
    # is ambiguous. Silent renumbering would destroy external references.
    for table_name in ("invoice", "bill", "creditnote", "debitnote"):
        if not insp.has_table(table_name):
            continue
        table = sa.Table(table_name, sa.MetaData(), autoload_with=bind)
        if "tenant_id" not in table.c or "number" not in table.c:
            continue
        duplicates = bind.execute(
            sa.select(table.c.tenant_id, table.c.number, sa.func.count().label("count"))
            .group_by(table.c.tenant_id, table.c.number)
            .having(sa.func.count() > 1)
        ).all()
        if duplicates:
            raise RuntimeError(f"Doppelte Belegnummern in {table_name}: {duplicates[:10]}")
        index_name = f"uq_{table_name}_tenant_number"
        existing_indexes = {idx["name"] for idx in sa.inspect(bind).get_indexes(table_name)}
        existing_constraints = {uc["name"] for uc in sa.inspect(bind).get_unique_constraints(table_name)}
        if index_name not in existing_indexes | existing_constraints:
            op.create_index(index_name, table_name, ["tenant_id", "number"], unique=True)

    # Preserve a cryptographically hashed baseline for every legacy finalized
    # invoice/bill. The snapshot explicitly identifies itself as legacy because
    # the historical tax and party state cannot be reconstructed completely.
    doc_versions = sa.Table("documentversion", sa.MetaData(), autoload_with=bind)
    for table_name, date_column in (("invoice", "issue_date"), ("bill", "bill_date")):
        if not insp.has_table(table_name):
            continue
        table = sa.Table(table_name, sa.MetaData(), autoload_with=bind)
        rows = bind.execute(sa.select(table).where(table.c.lifecycle_status == "finalized")).mappings().all()
        for row in rows:
            already = bind.execute(sa.select(doc_versions.c.id).where(
                doc_versions.c.tenant_id == row["tenant_id"],
                doc_versions.c.document_type == table_name,
                doc_versions.c.document_id == row["id"],
            )).first()
            if already:
                continue
            payload = {
                "document_type": table_name,
                "id": row["id"],
                "tenant_id": row["tenant_id"],
                "number": row.get("number"),
                date_column: str(row.get(date_column)),
                "subtotal": str(row.get("subtotal", "0")),
                "gst_amount": str(row.get("gst_amount", "0")),
                "total": str(row.get("total", "0")),
                "currency": row.get("currency"),
                "transaction_id": row.get("transaction_id"),
                "legacy_snapshot": True,
            }
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            bind.execute(doc_versions.insert().values(
                tenant_id=row["tenant_id"], document_type=table_name,
                document_id=row["id"], version=1, state="finalized",
                canonical_payload=canonical,
                payload_hash=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                recorded_at=datetime.utcnow(), effective_date=str(row.get(date_column)),
                reason="Automatisch erzeugte Legacy-Baseline bei AT-Migration",
                is_legacy=True,
            ))


def downgrade() -> None:
    bind = op.get_bind()

    inspector = sa.inspect(bind)
    for table_name in ("invoice", "bill", "creditnote", "debitnote"):
        if not inspector.has_table(table_name):
            continue
        index_name = f"uq_{table_name}_tenant_number"
        existing_indexes = {idx["name"] for idx in sa.inspect(bind).get_indexes(table_name)}
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name=table_name)

    for table_name in reversed(NEW_AT_TABLES):
        if bind.dialect.has_table(bind, table_name):
            op.drop_table(table_name)

    columns_by_table = {
        "accountingperiod": (
            "snapshot_hash", "reopen_reason", "last_reopened_by_id",
            "last_reopened_at", "reopen_count", "close_status",
        ),
        "customer": (
            "address_country", "address_city", "address_zip", "address_street",
            "is_business", "uid_verification_method", "uid_verified_at",
            "uid_verification_status", "uid", "tax_number",
            "company_register_court", "company_register_number",
            "registered_seat", "legal_form",
        ),
        "vendor": (
            "address_country", "address_city", "address_zip", "address_street",
            "is_business", "uid_verification_method", "uid_verified_at",
            "uid_verification_status", "uid", "tax_number",
            "company_register_court", "company_register_number",
            "registered_seat", "legal_form",
        ),
        "invoice": (
            "original_invoice_id", "correction_reason", "tax_treatment_code",
            "service_date_end", "service_date_start", "settlement_status",
            "delivery_status", "lifecycle_status",
        ),
        "bill": (
            "original_bill_id", "correction_reason", "tax_treatment_code",
            "service_date_end", "service_date_start", "settlement_status",
            "delivery_status", "lifecycle_status",
        ),
        "invoiceline": ("tax_treatment_snapshot", "tax_treatment_code", "service_date"),
        "billline": ("tax_treatment_snapshot", "tax_treatment_code", "service_date"),
        "creditnote": (
            "tax_treatment_code", "original_document_type",
            "original_document_id", "lifecycle_status",
        ),
        "debitnote": (
            "tax_treatment_code", "original_document_type",
            "original_document_id", "lifecycle_status",
        ),
        "creditnoteline": ("tax_amount", "tax_rate", "tax_treatment_code"),
        "debitnoteline": ("tax_amount", "tax_rate", "tax_treatment_code"),
    }
    for table_name, column_names in columns_by_table.items():
        if not sa.inspect(bind).has_table(table_name):
            continue
        table_inspector = sa.inspect(bind)
        existing = {column["name"] for column in table_inspector.get_columns(table_name)}
        removable = set(column_names) & existing
        with op.batch_alter_table(table_name) as batch:
            # SQLite batch mode recreates the table and otherwise attempts to
            # restore reflected indexes after their indexed AT column has been
            # removed. Drop every affected index as part of the same batch.
            for index in table_inspector.get_indexes(table_name):
                if index.get("name") and removable.intersection(index.get("column_names") or ()):
                    batch.drop_index(index["name"])
            for column_name in column_names:
                if column_name in existing:
                    batch.drop_column(column_name)
