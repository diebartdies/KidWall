"""add payment gateway ledger

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


ledgerownertype = postgresql.ENUM(
    "parent", "child", "merchant", "platform", "provider", name="ledgerownertype", create_type=False
)
ledgeraccounttype = postgresql.ENUM(
    "wallet", "receivable", "fee", "clearing", "payout", name="ledgeraccounttype", create_type=False
)
ledgertransactiontype = postgresql.ENUM(
    "deposit", "child_purchase", "merchant_payout", "refund", "adjustment",
    name="ledgertransactiontype", create_type=False
)
ledgertransactionstatus = postgresql.ENUM(
    "pending", "posted", "failed", "reversed", name="ledgertransactionstatus", create_type=False
)
paymentprovider = postgresql.ENUM("mercadopago", "stripe", "bank_manual", name="paymentprovider", create_type=False)
externalpaymentstatus = postgresql.ENUM(
    "pending", "confirmed", "failed", "refunded", name="externalpaymentstatus", create_type=False
)
externalpayoutstatus = postgresql.ENUM(
    "pending", "processing", "paid", "failed", name="externalpayoutstatus", create_type=False
)


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for enum_type in [
        ledgerownertype,
        ledgeraccounttype,
        ledgertransactiontype,
        ledgertransactionstatus,
        paymentprovider,
        externalpaymentstatus,
        externalpayoutstatus,
    ]:
        enum_type.create(bind, checkfirst=True)

    if not _has_table(inspector, "ledger_accounts"):
        op.create_table(
            "ledger_accounts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("owner_type", ledgerownertype, nullable=False),
            sa.Column("owner_id", sa.Integer(), nullable=True),
            sa.Column("account_type", ledgeraccounttype, nullable=False),
            sa.Column("currency", sa.String(), nullable=False, server_default="ARS"),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_ledger_accounts_id"), "ledger_accounts", ["id"], unique=False)

    if not _has_table(inspector, "ledger_transactions"):
        op.create_table(
            "ledger_transactions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("type", ledgertransactiontype, nullable=False),
            sa.Column("status", ledgertransactionstatus, nullable=False, server_default="posted"),
            sa.Column("external_reference", sa.String(), nullable=True),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_ledger_transactions_id"), "ledger_transactions", ["id"], unique=False)
        op.create_index(
            op.f("ix_ledger_transactions_external_reference"),
            "ledger_transactions",
            ["external_reference"],
            unique=False,
        )

    if not _has_table(inspector, "ledger_entries"):
        op.create_table(
            "ledger_entries",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("transaction_id", sa.Integer(), nullable=False),
            sa.Column("account_id", sa.Integer(), nullable=False),
            sa.Column("amount_cents", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["account_id"], ["ledger_accounts.id"]),
            sa.ForeignKeyConstraint(["transaction_id"], ["ledger_transactions.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_ledger_entries_id"), "ledger_entries", ["id"], unique=False)

    if not _has_table(inspector, "merchant_payout_methods"):
        op.create_table(
            "merchant_payout_methods",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("merchant_id", sa.Integer(), nullable=False),
            sa.Column("provider", paymentprovider, nullable=False),
            sa.Column("provider_account_id", sa.String(), nullable=True),
            sa.Column("label", sa.String(), nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="pending"),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["merchant_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_merchant_payout_methods_id"), "merchant_payout_methods", ["id"], unique=False)

    if not _has_table(inspector, "external_payments"):
        op.create_table(
            "external_payments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("parent_id", sa.Integer(), nullable=False),
            sa.Column("provider", paymentprovider, nullable=False),
            sa.Column("external_id", sa.String(), nullable=True),
            sa.Column("amount_cents", sa.Integer(), nullable=False),
            sa.Column("currency", sa.String(), nullable=False, server_default="ARS"),
            sa.Column("status", externalpaymentstatus, nullable=False, server_default="pending"),
            sa.Column("ledger_transaction_id", sa.Integer(), nullable=True),
            sa.Column("raw_response_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("confirmed_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"]),
            sa.ForeignKeyConstraint(["parent_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_external_payments_id"), "external_payments", ["id"], unique=False)
        op.create_index(op.f("ix_external_payments_external_id"), "external_payments", ["external_id"], unique=False)

    if not _has_table(inspector, "external_payouts"):
        op.create_table(
            "external_payouts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("merchant_id", sa.Integer(), nullable=False),
            sa.Column("payout_method_id", sa.Integer(), nullable=True),
            sa.Column("provider", paymentprovider, nullable=False),
            sa.Column("external_id", sa.String(), nullable=True),
            sa.Column("amount_cents", sa.Integer(), nullable=False),
            sa.Column("currency", sa.String(), nullable=False, server_default="ARS"),
            sa.Column("status", externalpayoutstatus, nullable=False, server_default="pending"),
            sa.Column("ledger_transaction_id", sa.Integer(), nullable=True),
            sa.Column("raw_response_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("paid_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"]),
            sa.ForeignKeyConstraint(["merchant_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["payout_method_id"], ["merchant_payout_methods.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_external_payouts_id"), "external_payouts", ["id"], unique=False)
        op.create_index(op.f("ix_external_payouts_external_id"), "external_payouts", ["external_id"], unique=False)


def downgrade():
    for table_name in [
        "external_payouts",
        "external_payments",
        "merchant_payout_methods",
        "ledger_entries",
        "ledger_transactions",
        "ledger_accounts",
    ]:
        op.drop_table(table_name)

    externalpayoutstatus.drop(op.get_bind(), checkfirst=True)
    externalpaymentstatus.drop(op.get_bind(), checkfirst=True)
    paymentprovider.drop(op.get_bind(), checkfirst=True)
    ledgertransactionstatus.drop(op.get_bind(), checkfirst=True)
    ledgertransactiontype.drop(op.get_bind(), checkfirst=True)
    ledgeraccounttype.drop(op.get_bind(), checkfirst=True)
    ledgerownertype.drop(op.get_bind(), checkfirst=True)
