"""add child home inheritance fields

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-05-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "j0k1l2m3n4o5"
down_revision = "i9j0k1l2m3n4"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _has_column(inspector, "children", "lives_with_parent"):
        op.add_column(
            "children",
            sa.Column("lives_with_parent", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    if not _has_column(inspector, "children", "home_address"):
        op.add_column("children", sa.Column("home_address", sa.String(), nullable=True))
    if not _has_column(inspector, "children", "home_phone"):
        op.add_column("children", sa.Column("home_phone", sa.String(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for column_name in ["home_phone", "home_address", "lives_with_parent"]:
        if _has_column(inspector, "children", column_name):
            op.drop_column("children", column_name)
