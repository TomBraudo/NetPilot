"""add device groups

Revision ID: device_groups_001
Revises: 83f8895b24c2
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'device_groups_001'
down_revision = '83f8895b24c2'
branch_labels = None
depends_on = None


def upgrade():
    # Create device_groups table
    op.create_table('device_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('router_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create device_group_devices association table
    op.create_table('device_group_devices',
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['user_devices.id'], ),
        sa.ForeignKeyConstraint(['group_id'], ['device_groups.id'], ),
        sa.PrimaryKeyConstraint('group_id', 'device_id')
    )


def downgrade():
    op.drop_table('device_group_devices')
    op.drop_table('device_groups')
