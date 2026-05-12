"""add child school schedule

Revision ID: m3n4o5p6q7r8
Revises: l2m3n4o5p6q7
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa


revision = "m3n4o5p6q7r8"
down_revision = "l2m3n4o5p6q7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("children", sa.Column("school_id", sa.String(), nullable=True))
    op.add_column("children", sa.Column("school_name", sa.String(), nullable=True))
    op.add_column("children", sa.Column("shift", sa.String(), nullable=True))
    op.add_column("children", sa.Column("shift_start", sa.String(), nullable=True))
    op.add_column("children", sa.Column("shift_end", sa.String(), nullable=True))
    op.add_column("children", sa.Column("activities_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("children", "activities_json")
    op.drop_column("children", "shift_end")
    op.drop_column("children", "shift_start")
    op.drop_column("children", "shift")
    op.drop_column("children", "school_name")
    op.drop_column("children", "school_id")
