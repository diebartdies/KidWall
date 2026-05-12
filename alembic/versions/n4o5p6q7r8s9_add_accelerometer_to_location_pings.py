"""add accelerometer to location pings

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2026-05-11 21:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "n4o5p6q7r8s9"
down_revision = "m3n4o5p6q7r8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("child_location_pings", sa.Column("accel_x", sa.Float(), nullable=True))
    op.add_column("child_location_pings", sa.Column("accel_y", sa.Float(), nullable=True))
    op.add_column("child_location_pings", sa.Column("accel_z", sa.Float(), nullable=True))


def downgrade():
    op.drop_column("child_location_pings", "accel_z")
    op.drop_column("child_location_pings", "accel_y")
    op.drop_column("child_location_pings", "accel_x")
