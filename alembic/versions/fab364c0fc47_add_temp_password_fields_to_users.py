#
# Alembic migration script
#


revision = 'fab364c0fc47'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users', sa.Column('temp_password_hash', sa.String(), nullable=True))
    op.add_column('users', sa.Column('temp_password_expires', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('users', 'temp_password_expires')
    op.drop_column('users', 'temp_password_hash')
