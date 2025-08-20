from utils.logging_config import get_logger
from flask import g
from services.commands_server_operations.agh_execute import (
    execute_clear_device_rules,
    execute_clear_devices_rules,
    execute_set_device_rules,
)
from services.commands_server_operations.bandwidth_execute import (
    execute_delete_device_limit,
    execute_delete_group_limits,
    execute_apply_device_limit,
)

logger = get_logger('services.device_group_service')


def get_user_device_groups(user_id, router_id):
    """Get all device groups for a user and router"""
    from services.db_operations.device_group_db import get_user_device_groups as db_get_groups
    return db_get_groups(user_id, router_id)


def create_device_group(user_id, router_id, name, description=None, device_ids=None):
    """Create a new device group"""
    from services.db_operations.device_group_db import create_device_group as db_create_group
    return db_create_group(user_id, router_id, name, description, device_ids)


def update_device_group(user_id, router_id, group_id, data):
    """Update a device group"""
    from services.db_operations.device_group_db import update_device_group as db_update_group
    return db_update_group(user_id, router_id, group_id, data)


def delete_device_group(user_id, router_id, group_id):
    """Delete a device group and clear related rules on the router for all its devices."""
    from services.db_operations.device_group_db import delete_device_group as db_delete_group
    deleted, ctx = db_delete_group(user_id, router_id, group_id)
    if not deleted:
        return False
    # Post-DB execute actions
    try:
        session_id = getattr(g, 'session_id', None)
        if ctx.get('should_clear_agh') and ctx.get('devices_for_agh'):
            execute_clear_devices_rules(router_id, session_id, ctx['devices_for_agh'])
        if ctx.get('should_clear_bandwidth') and ctx.get('ips_to_clear'):
            execute_delete_group_limits(router_id, session_id, ctx['ips_to_clear'])
    except Exception as e:
        logger.error(f"Post-delete group cleanup encountered an error for group {group_id}: {e}")
    return True


def add_device_to_group(user_id, router_id, group_id, device_id):
    """Add a device to a group and apply group rules to the device if active."""
    from services.db_operations.device_group_db import add_device_to_group as db_add_device
    ok, ctx = db_add_device(user_id, router_id, group_id, device_id)
    if not ok:
        return False
    try:
        session_id = getattr(g, 'session_id', None)
        if ctx.get('should_apply_agh') and (ctx.get('device_mac') or ctx.get('device_ip')):
            device_obj = {}
            if ctx.get('device_mac'):
                device_obj['mac'] = ctx['device_mac']
            if ctx.get('device_ip'):
                device_obj['ip'] = ctx['device_ip']
            execute_set_device_rules(router_id, session_id, device_obj, ctx.get('agh_categories', []))
        if ctx.get('should_apply_bandwidth') and ctx.get('device_ip'):
            execute_apply_device_limit(
                router_id,
                session_id,
                ctx['device_ip'],
                download_mbps=ctx.get('bw_download_mbps'),
                upload_mbps=ctx.get('bw_upload_mbps'),
            )
    except Exception as e:
        logger.error(f"Post-add apply encountered an error for device {device_id}: {e}")
    return True


def remove_device_from_group(user_id, router_id, group_id, device_id):
    """Remove a device from a group and clear per-device rules if group had active rules."""
    from services.db_operations.device_group_db import remove_device_from_group as db_remove_device
    ok, ctx = db_remove_device(user_id, router_id, group_id, device_id)
    if not ok:
        return False
    try:
        session_id = getattr(g, 'session_id', None)
        if ctx.get('should_clear_agh') and (ctx.get('device_mac') or ctx.get('device_ip')):
            device_obj = {}
            if ctx.get('device_mac'):
                device_obj['mac'] = ctx['device_mac']
            if ctx.get('device_ip'):
                device_obj['ip'] = ctx['device_ip']
            execute_clear_device_rules(router_id, session_id, device_obj)
        if ctx.get('should_clear_bandwidth') and ctx.get('device_ip'):
            execute_delete_device_limit(router_id, session_id, ctx['device_ip'])
    except Exception as e:
        logger.error(f"Post-removal cleanup encountered an error for device {device_id}: {e}")
    return True


def get_available_devices_for_group(user_id, router_id, group_id=None):
    """Get devices that are not in any group or not in the specified group"""
    from services.db_operations.device_group_db import get_available_devices_for_group as db_get_available
    return db_get_available(user_id, router_id, group_id)


def get_groups_containing_device(user_id, router_id, device_id):
    """Get all groups that contain a specific device"""
    from services.db_operations.device_group_db import get_groups_containing_device as db_groups_for_device
    return db_groups_for_device(user_id, router_id, device_id)


def cleanup_empty_groups(user_id, router_id):
    """Find and delete all groups with 0 devices"""
    from services.db_operations.device_group_db import cleanup_empty_groups as db_cleanup
    return db_cleanup(user_id, router_id)
