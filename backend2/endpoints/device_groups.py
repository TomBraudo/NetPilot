from flask import Blueprint, request, g
from utils.response_helpers import build_success_response, build_error_response
from utils.logging_config import get_logger
from utils.middleware import router_context_required
from services.device_group_service import (
    get_user_device_groups,
    create_device_group,
    update_device_group,
    delete_device_group,
    add_device_to_group,
    remove_device_from_group
)
import time

device_groups_bp = Blueprint('device_groups', __name__)
logger = get_logger('endpoints.device_groups')


@device_groups_bp.route('/groups', methods=['GET'])
@router_context_required
def get_groups():
    """Get all device groups for the current user and router"""
    start_time = time.time()
    
    try:
        groups = get_user_device_groups(g.user_id, g.router_id)
        return build_success_response([group.to_dict() for group in groups], start_time)
    except Exception as e:
        logger.error(f"Failed to get device groups: {str(e)}")
        return build_error_response(f"Failed to get device groups: {str(e)}", 500, "GET_GROUPS_FAILED", start_time)


@device_groups_bp.route('/groups', methods=['POST'])
@router_context_required
def create_group():
    """Create a new device group"""
    start_time = time.time()
    data = request.get_json() or {}
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    device_ids = data.get('device_ids', [])
    
    if not name:
        return build_error_response("Group name is required", 400, "INVALID_INPUT", start_time)
    
    try:
        group = create_device_group(g.user_id, g.router_id, name, description, device_ids)
        return build_success_response(group.to_dict(), start_time)
    except ValueError as e:
        return build_error_response(str(e), 400, "INVALID_INPUT", start_time)
    except Exception as e:
        logger.error(f"Failed to create device group: {str(e)}")
        return build_error_response(f"Failed to create device group: {str(e)}", 500, "CREATE_GROUP_FAILED", start_time)


@device_groups_bp.route('/groups/<group_id>', methods=['PUT'])
@router_context_required
def update_group(group_id):
    """Update a device group"""
    start_time = time.time()
    data = request.get_json() or {}
    
    try:
        group = update_device_group(g.user_id, g.router_id, group_id, data)
        if not group:
            return build_error_response("Group not found", 404, "GROUP_NOT_FOUND", start_time)
        return build_success_response(group.to_dict(), start_time)
    except ValueError as e:
        return build_error_response(str(e), 400, "INVALID_INPUT", start_time)
    except Exception as e:
        logger.error(f"Failed to update device group: {str(e)}")
        return build_error_response(f"Failed to update device group: {str(e)}", 500, "UPDATE_GROUP_FAILED", start_time)


@device_groups_bp.route('/groups/<group_id>', methods=['DELETE'])
@router_context_required
def delete_group(group_id):
    """Delete a device group"""
    start_time = time.time()
    
    try:
        success = delete_device_group(g.user_id, g.router_id, group_id)
        if not success:
            return build_error_response("Group not found", 404, "GROUP_NOT_FOUND", start_time)
        return build_success_response({"message": "Group deleted successfully"}, start_time)
    except Exception as e:
        logger.error(f"Failed to delete device group: {str(e)}")
        return build_error_response(f"Failed to delete device group: {str(e)}", 500, "DELETE_GROUP_FAILED", start_time)


@device_groups_bp.route('/groups/<group_id>/devices', methods=['POST'])
@router_context_required
def add_device_to_group_endpoint(group_id):
    """Add a device to a group"""
    start_time = time.time()
    data = request.get_json() or {}
    
    device_id = data.get('device_id')
    if not device_id:
        return build_error_response("Device ID is required", 400, "INVALID_INPUT", start_time)
    
    try:
        success = add_device_to_group(g.user_id, g.router_id, group_id, device_id)
        if not success:
            return build_error_response("Group or device not found", 404, "NOT_FOUND", start_time)
        return build_success_response({"message": "Device added to group successfully"}, start_time)
    except ValueError as e:
        return build_error_response(str(e), 400, "INVALID_INPUT", start_time)
    except Exception as e:
        logger.error(f"Failed to add device to group: {str(e)}")
        return build_error_response(f"Failed to add device to group: {str(e)}", 500, "ADD_DEVICE_FAILED", start_time)


@device_groups_bp.route('/groups/<group_id>/devices/<device_id>', methods=['DELETE'])
@router_context_required
def remove_device_from_group_endpoint(group_id, device_id):
    """Remove a device from a group"""
    start_time = time.time()
    
    try:
        success = remove_device_from_group(g.user_id, g.router_id, group_id, device_id)
        if not success:
            return build_error_response("Group or device not found", 404, "NOT_FOUND", start_time)
        return build_success_response({"message": "Device removed from group successfully"}, start_time)
    except Exception as e:
        logger.error(f"Failed to remove device from group: {str(e)}")
        return build_error_response(f"Failed to remove device from group: {str(e)}", 500, "REMOVE_DEVICE_FAILED", start_time)
