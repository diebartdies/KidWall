#
# Alembic migration: geo tracking tables + anti-theft columns
#   - child_location_pings
#   - child_route_waypoints
#   - children.last_route_alert
#   - transactions.child_id + transactions.created_at
#

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # ── child_location_pings ──────────────────────────────────────────
    if 'child_location_pings' not in existing_tables:
        op.create_table(
            'child_location_pings',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('child_id', sa.Integer(), sa.ForeignKey('children.id'), nullable=False),
            sa.Column('lat', sa.Float(), nullable=False),
            sa.Column('lon', sa.Float(), nullable=False),
            sa.Column('recorded_at', sa.DateTime(), nullable=True),
        )

    # ── child_route_waypoints ─────────────────────────────────────────
    if 'child_route_waypoints' not in existing_tables:
        op.create_table(
            'child_route_waypoints',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('child_id', sa.Integer(), sa.ForeignKey('children.id'), nullable=False),
            sa.Column('seq', sa.Integer(), nullable=False),
            sa.Column('lat', sa.Float(), nullable=False),
            sa.Column('lon', sa.Float(), nullable=False),
        )

    # ── children: last_route_alert ────────────────────────────────────
    children_cols = [c['name'] for c in inspector.get_columns('children')]
    if 'last_route_alert' not in children_cols:
        op.add_column('children', sa.Column('last_route_alert', sa.DateTime(), nullable=True))

    # ── transactions: child_id + created_at ──────────────────────────
    if 'transactions' in existing_tables:
        txn_cols = [c['name'] for c in inspector.get_columns('transactions')]
        if 'child_id' not in txn_cols:
            op.add_column('transactions', sa.Column('child_id', sa.Integer(), nullable=True))
        if 'created_at' not in txn_cols:
            op.add_column('transactions', sa.Column('created_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_table('child_route_waypoints')
    op.drop_table('child_location_pings')
    with op.batch_alter_table('children') as batch_op:
        batch_op.drop_column('last_route_alert')
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.drop_column('child_id')
        batch_op.drop_column('created_at')
