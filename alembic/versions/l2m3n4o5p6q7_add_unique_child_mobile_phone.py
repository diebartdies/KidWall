"""add unique child mobile phone

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa


revision = "l2m3n4o5p6q7"
down_revision = "k1l2m3n4o5p6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("children", sa.Column("mobile_phone", sa.String(), nullable=True))
    op.create_index("ix_children_mobile_phone", "children", ["mobile_phone"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_children_mobile_phone", table_name="children")
    op.drop_column("children", "mobile_phone")
