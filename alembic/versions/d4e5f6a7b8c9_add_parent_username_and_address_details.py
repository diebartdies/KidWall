"""add parent username and address details

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_column(inspector, "users", "username"):
        op.add_column("users", sa.Column("username", sa.String(), nullable=True))
        op.create_index("ix_users_username", "users", ["username"], unique=True)

    parent_profile_columns = {
        "home_floor": sa.String(),
        "home_department": sa.String(),
        "work_postal": sa.String(),
    }
    for column_name, column_type in parent_profile_columns.items():
        if not _has_column(inspector, "parent_profiles", column_name):
            op.add_column("parent_profiles", sa.Column(column_name, column_type, nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_column(inspector, "parent_profiles", "work_postal"):
        op.drop_column("parent_profiles", "work_postal")
    if _has_column(inspector, "parent_profiles", "home_department"):
        op.drop_column("parent_profiles", "home_department")
    if _has_column(inspector, "parent_profiles", "home_floor"):
        op.drop_column("parent_profiles", "home_floor")
    if _has_column(inspector, "users", "username"):
        op.drop_index("ix_users_username", table_name="users")
        op.drop_column("users", "username")
