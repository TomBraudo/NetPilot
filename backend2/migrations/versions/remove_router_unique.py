"""remove router unique constraint

Revision ID: remove_router_unique
Revises: 4439c564fa79
Create Date: 2025-07-29 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_router_unique'
down_revision = '4439c564fa79'
branch_labels = None
depends_on = None


def upgrade():
    # Drop foreign key constraints that depend on the unique constraint
    op.drop_constraint('user_devices_router_id_fkey', 'user_devices', type_='foreignkey')
    op.drop_constraint('user_settings_router_id_fkey', 'user_settings', type_='foreignkey')
    op.drop_constraint('user_whitelists_router_id_fkey', 'user_whitelists', type_='foreignkey')
    op.drop_constraint('user_blacklists_router_id_fkey', 'user_blacklists', type_='foreignkey')
    op.drop_constraint('user_blocked_devices_router_id_fkey', 'user_blocked_devices', type_='foreignkey')
    
    # Remove the unique constraint from router_id column
    op.drop_constraint('user_routers_router_id_key', 'user_routers', type_='unique')
    
    # Note: We don't recreate foreign key constraints because we want to allow
    # multiple users to have the same router_id. The relationships will be
    # handled in application code using user_id + router_id combinations.


def downgrade():
    # Add back the unique constraint (this might fail if there are duplicate router_ids)
    op.create_unique_constraint('user_routers_router_id_key', 'user_routers', ['router_id'])
    
    # Recreate foreign key constraints with unique requirement
    op.create_foreign_key('user_devices_router_id_fkey', 'user_devices', 'user_routers', ['router_id'], ['router_id'])
    op.create_foreign_key('user_settings_router_id_fkey', 'user_settings', 'user_routers', ['router_id'], ['router_id'])
    op.create_foreign_key('user_whitelists_router_id_fkey', 'user_whitelists', 'user_routers', ['router_id'], ['router_id'])
    op.create_foreign_key('user_blacklists_router_id_fkey', 'user_blacklists', 'user_routers', ['router_id'], ['router_id'])
    op.create_foreign_key('user_blocked_devices_router_id_fkey', 'user_blocked_devices', 'user_routers', ['router_id'], ['router_id']) 