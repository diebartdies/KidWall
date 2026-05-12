"""add merchant profiles

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-05-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "g7h8i9j0k1l2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "merchant_profiles"):
        op.create_table(
            "merchant_profiles",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("place_scope", sa.String(), nullable=True),
            sa.Column("business_name", sa.String(), nullable=True),
            sa.Column("address", sa.String(), nullable=True),
            sa.Column("personal_name", sa.String(), nullable=True),
            sa.Column("mobile_phone", sa.String(), nullable=True),
            sa.Column("country_code", sa.String(), nullable=True),
            sa.Column("transfer_account_type", sa.String(), nullable=True),
            sa.Column("transfer_account", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index(
            op.f("ix_merchant_profiles_id"),
            "merchant_profiles",
            ["id"],
            unique=False,
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "merchant_profiles"):
        indexes = {index["name"] for index in inspector.get_indexes("merchant_profiles")}
        if "ix_merchant_profiles_id" in indexes:
            op.drop_index(op.f("ix_merchant_profiles_id"), table_name="merchant_profiles")
        op.drop_table("merchant_profiles")
