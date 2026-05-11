"""add nces school import fields

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {
        "source": sa.String(),
        "source_year": sa.String(),
        "external_id": sa.String(),
        "sector": sa.String(),
        "district_id": sa.String(),
        "district_name": sa.String(),
        "postal_code": sa.String(),
        "website": sa.String(),
        "level": sa.String(),
        "low_grade": sa.String(),
        "high_grade": sa.String(),
        "locale_code": sa.String(),
        "county_name": sa.String(),
    }
    for column_name, column_type in columns.items():
        if not _has_column(inspector, "schools", column_name):
            op.add_column("schools", sa.Column(column_name, column_type, nullable=True))

    indexes = {index["name"] for index in inspector.get_indexes("schools")}
    if "ix_schools_source" not in indexes:
        op.create_index("ix_schools_source", "schools", ["source"], unique=False)
    if "ix_schools_external_id" not in indexes:
        op.create_index("ix_schools_external_id", "schools", ["external_id"], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("schools")}
    if "ix_schools_external_id" in indexes:
        op.drop_index("ix_schools_external_id", table_name="schools")
    if "ix_schools_source" in indexes:
        op.drop_index("ix_schools_source", table_name="schools")

    for column_name in [
        "county_name",
        "locale_code",
        "high_grade",
        "low_grade",
        "level",
        "website",
        "postal_code",
        "district_name",
        "district_id",
        "sector",
        "external_id",
        "source_year",
        "source",
    ]:
        if _has_column(inspector, "schools", column_name):
            op.drop_column("schools", column_name)
