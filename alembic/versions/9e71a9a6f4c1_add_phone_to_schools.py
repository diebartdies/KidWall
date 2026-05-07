"""add phone to schools

Revision ID: 9e71a9a6f4c1
Revises: fab364c0fc47
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa


revision = "9e71a9a6f4c1"
down_revision = "fab364c0fc47"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("schools", sa.Column("phone", sa.String(), nullable=True))


def downgrade():
    op.drop_column("schools", "phone")
