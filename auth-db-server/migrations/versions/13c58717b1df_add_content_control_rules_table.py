"""add_content_control_rules_table

Revision ID: 13c58717b1df
Revises: 628b3f85824e
Create Date: 2025-08-16 16:39:16.061837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '13c58717b1df'
down_revision: Union[str, None] = '628b3f85824e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create content_control_rules table
    op.create_table('content_control_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('router_id', sa.String(length=255), nullable=False),
        sa.Column('blocked_categories', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['device_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on group_id for better performance
    op.create_index(op.f('ix_content_control_rules_group_id'), 'content_control_rules', ['group_id'], unique=False)
    
    # Create index on router_id for better performance
    op.create_index(op.f('ix_content_control_rules_router_id'), 'content_control_rules', ['router_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_content_control_rules_router_id'), table_name='content_control_rules')
    op.drop_index(op.f('ix_content_control_rules_group_id'), table_name='content_control_rules')
    
    # Drop table
    op.drop_table('content_control_rules')
