"""add_bandwidth_rules_table

Revision ID: 628b3f85824e
Revises: 161a014cd0c1
Create Date: 2025-08-16 16:39:16.061837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '628b3f85824e'
down_revision: Union[str, None] = '161a014cd0c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create bandwidth_rules table
    op.create_table('bandwidth_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('router_id', sa.String(length=255), nullable=False),
        sa.Column('download_limit_mbps', sa.Float(), nullable=True),
        sa.Column('upload_limit_mbps', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['device_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on group_id for better performance
    op.create_index(op.f('ix_bandwidth_rules_group_id'), 'bandwidth_rules', ['group_id'], unique=False)
    
    # Create index on router_id for better performance
    op.create_index(op.f('ix_bandwidth_rules_router_id'), 'bandwidth_rules', ['router_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_bandwidth_rules_router_id'), table_name='bandwidth_rules')
    op.drop_index(op.f('ix_bandwidth_rules_group_id'), table_name='bandwidth_rules')
    
    # Drop table
    op.drop_table('bandwidth_rules')
