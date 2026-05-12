"""add parent country

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa


revision = "k1l2m3n4o5p6"
down_revision = "j0k1l2m3n4o5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("parent_profiles", sa.Column("country", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("parent_profiles", "country")
