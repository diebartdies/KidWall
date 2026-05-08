#
# Alembic migration: add parent_profiles and emergency_contacts tables,
# replace 'role' column with 'relationship_to_child', add work_shift/work_hours
#

revision = 'a1b2c3d4e5f6'
down_revision = '9e71a9a6f4c1'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'parent_profiles' not in existing_tables:
        op.create_table(
            'parent_profiles',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
            sa.Column('relationship_to_child', sa.String(), nullable=True),
            sa.Column('home_address', sa.String(), nullable=True),
            sa.Column('home_postal', sa.String(), nullable=True),
            sa.Column('home_phone', sa.String(), nullable=True),
            sa.Column('mobile_phone', sa.String(), nullable=True),
            sa.Column('country_code', sa.String(), nullable=True),
            sa.Column('work_name', sa.String(), nullable=True),
            sa.Column('work_address', sa.String(), nullable=True),
            sa.Column('work_phone', sa.String(), nullable=True),
            sa.Column('work_shift', sa.String(), nullable=True),
            sa.Column('work_hours', sa.String(), nullable=True),
            sa.Column('workplace', sa.String(), nullable=True),
            sa.Column('email', sa.String(), nullable=True),
        )
    else:
        # Table exists — add any missing columns
        existing_cols = {c['name'] for c in inspector.get_columns('parent_profiles')}
        for col_name, col_type in [
            ('relationship_to_child', sa.String()),
            ('work_shift', sa.String()),
            ('work_hours', sa.String()),
            ('workplace', sa.String()),
            ('mobile_phone', sa.String()),
            ('country_code', sa.String()),
            ('home_address', sa.String()),
            ('home_postal', sa.String()),
            ('home_phone', sa.String()),
            ('work_name', sa.String()),
            ('work_address', sa.String()),
            ('work_phone', sa.String()),
            ('email', sa.String()),
        ]:
            if col_name not in existing_cols:
                op.add_column('parent_profiles', sa.Column(col_name, col_type, nullable=True))

        # Drop legacy 'role' column if present
        if 'role' in existing_cols:
            op.drop_column('parent_profiles', 'role')

    if 'emergency_contacts' not in existing_tables:
        op.create_table(
            'emergency_contacts',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('parent_profile_id', sa.Integer(), sa.ForeignKey('parent_profiles.id'), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('surname', sa.String(), nullable=True),
            sa.Column('relation', sa.String(), nullable=True),
            sa.Column('mobile', sa.String(), nullable=True),
            sa.Column('country_code', sa.String(), nullable=True),
            sa.Column('home_phone', sa.String(), nullable=True),
            sa.Column('work_phone', sa.String(), nullable=True),
            sa.Column('address', sa.String(), nullable=True),
            sa.Column('email', sa.String(), nullable=True),
        )


def downgrade():
    op.drop_table('emergency_contacts')
    op.drop_table('parent_profiles')
