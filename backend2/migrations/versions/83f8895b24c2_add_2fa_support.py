"""add_2fa_support

Revision ID: 83f8895b24c2
Revises: 6a63def03834
Create Date: 2025-08-02 10:59:20.386729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '83f8895b24c2'
down_revision: Union[str, None] = '6a63def03834'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_2fa_settings table
    op.create_table('user_2fa_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('totp_secret', sa.String(length=255), nullable=True),
        sa.Column('backup_codes', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('sms_phone', sa.String(length=20), nullable=True),
        sa.Column('email_2fa_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('last_used_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('setup_token', sa.String(length=255), nullable=True),
        sa.Column('setup_expires_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('failed_attempts', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('locked_until', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create user_2fa_attempts table
    op.create_table('user_2fa_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attempt_type', sa.String(length=20), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add indexes for performance
    op.create_index('idx_2fa_attempts_user_time', 'user_2fa_attempts', ['user_id', 'created_at'])
    op.create_index('idx_2fa_attempts_failed', 'user_2fa_attempts', ['user_id', 'success', 'created_at'])

    # Add 2FA columns to existing users table
    op.add_column('users', sa.Column('requires_2fa', sa.Boolean(), server_default=sa.text('false'), nullable=True))
    op.add_column('users', sa.Column('twofa_enforced_at', sa.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    # Remove columns from users table
    op.drop_column('users', 'twofa_enforced_at')
    op.drop_column('users', 'requires_2fa')
    
    # Drop indexes
    op.drop_index('idx_2fa_attempts_failed', table_name='user_2fa_attempts')
    op.drop_index('idx_2fa_attempts_user_time', table_name='user_2fa_attempts')
    
    # Drop tables
    op.drop_table('user_2fa_attempts')
    op.drop_table('user_2fa_settings')
