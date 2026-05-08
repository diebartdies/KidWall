#
# Alembic migration: add wallet_buckets table
#

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'wallet_buckets' not in inspector.get_table_names():
        op.create_table(
            'wallet_buckets',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('child_id', sa.Integer(), sa.ForeignKey('children.id'), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('allocated', sa.Float(), default=0.0),
            sa.Column('spent', sa.Float(), default=0.0),
            sa.Column('alert_threshold_pct', sa.Integer(), default=80),
            sa.Column('alert_sent', sa.Integer(), default=0),
        )


def downgrade():
    op.drop_table('wallet_buckets')
