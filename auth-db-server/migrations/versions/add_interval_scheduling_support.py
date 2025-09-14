"""add interval scheduling support

Revision ID: add_interval_scheduling_support
Revises: 346d0f1d4dc8
Create Date: 2025-08-21 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_interval_scheduling_support'
down_revision: Union[str, None] = '346d0f1d4dc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add interval scheduling support columns to scheduled_tasks table
    op.add_column('scheduled_tasks', sa.Column('task_type', sa.String(length=16), nullable=False, server_default='fixed'))
    op.add_column('scheduled_tasks', sa.Column('interval_minutes', sa.Integer(), nullable=True))
    
    # Modify existing columns to be nullable for interval tasks
    op.alter_column('scheduled_tasks', 'hour', nullable=True, existing_type=sa.Integer())
    op.alter_column('scheduled_tasks', 'minute', nullable=True, existing_type=sa.Integer())
    
    # Create index for interval tasks
    op.create_index('ix_scheduled_tasks_interval_type', 'scheduled_tasks', ['task_type', 'enabled'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_scheduled_tasks_interval_type', table_name='scheduled_tasks')
    
    # Remove interval scheduling columns
    op.drop_column('scheduled_tasks', 'interval_minutes')
    op.drop_column('scheduled_tasks', 'task_type')
    
    # Revert hour and minute columns to be non-nullable (this will fail if there are interval tasks)
    # Note: In a real deployment, you'd want to handle this more gracefully
    op.alter_column('scheduled_tasks', 'hour', nullable=False, existing_type=sa.Integer())
    op.alter_column('scheduled_tasks', 'minute', nullable=False, existing_type=sa.Integer())
