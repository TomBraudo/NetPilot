"""sync_database_with_models

Revision ID: 161a014cd0c1
Revises: c18de4026f72
Create Date: 2025-08-15 13:36:02.200021

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '161a014cd0c1'
down_revision: Union[str, None] = 'c18de4026f72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Sync database with current models:
    1. Fix device_group_devices foreign key to point to device_groups instead of user_device_groups
    2. Drop unused legacy tables: user_device_groups, user_blacklists, user_whitelists, blacklisted_devices
    """
    from sqlalchemy import inspect
    
    # Get database connection and inspector
    connection = op.get_bind()
    inspector = inspect(connection)
    existing_tables = inspector.get_table_names()
    
    # Step 1: Fix device_group_devices foreign key constraint
    if 'device_group_devices' in existing_tables:
        # Drop the incorrect foreign key constraint
        try:
            op.drop_constraint('device_group_devices_group_id_fkey', 'device_group_devices', type_='foreignkey')
        except Exception as e:
            print(f"Warning: Could not drop constraint device_group_devices_group_id_fkey: {e}")
        
        # Create the correct foreign key constraint pointing to device_groups
        op.create_foreign_key(
            'device_group_devices_group_id_fkey',
            'device_group_devices', 
            'device_groups',
            ['group_id'], 
            ['id']
        )
    
    # Step 2: Drop unused legacy tables
    legacy_tables = ['user_device_groups', 'user_blacklists', 'user_whitelists', 'blacklisted_devices']
    
    for table in legacy_tables:
        if table in existing_tables:
            print(f"Dropping legacy table: {table}")
            op.drop_table(table)


def downgrade() -> None:
    """
    WARNING: This downgrade will recreate legacy tables but they will be empty.
    Only use if you have a backup and understand the implications.
    """
    from sqlalchemy.dialects import postgresql
    
    # Recreate legacy tables (structure only, no data)
    
    # Recreate user_device_groups (the duplicate table)
    op.create_table('user_device_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('router_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate user_blacklists
    op.create_table('user_blacklists',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('router_id', sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate user_whitelists  
    op.create_table('user_whitelists',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('router_id', sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate blacklisted_devices
    op.create_table('blacklisted_devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Revert device_group_devices foreign key back to user_device_groups
    op.drop_constraint('device_group_devices_group_id_fkey', 'device_group_devices', type_='foreignkey')
    op.create_foreign_key(
        'device_group_devices_group_id_fkey',
        'device_group_devices',
        'user_device_groups', 
        ['group_id'],
        ['id']
    )
