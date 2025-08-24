from flask import Blueprint, request, g
from utils.response_helpers import build_success_response, build_error_response
from utils.logging_config import get_logger
from utils.middleware import router_context_required
from services.blocked_device_service import (
    get_user_blocked_devices,
    block_device,
    unblock_device,
    is_device_blocked,
    get_blocked_device_ids
)
import time

blocked_devices_bp = Blueprint('blocked_devices', __name__)
logger = get_logger('endpoints.blocked_devices')


@blocked_devices_bp.route('/blocked', methods=['GET'])
@router_context_required
def get_blocked_devices():
    """Get all blocked devices for the current user and router"""
    start_time = time.time()
    
    try:
        devices, error = get_user_blocked_devices(g.user_id, g.router_id, g.session_id)
        if error:
            return build_error_response(f"Failed to get blocked devices: {error}", 500, "GET_BLOCKED_DEVICES_FAILED", start_time)
        return build_success_response(devices, start_time)
    except Exception as e:
        logger.error(f"Failed to get blocked devices: {str(e)}")
        return build_error_response(f"Failed to get blocked devices: {str(e)}", 500, "GET_BLOCKED_DEVICES_FAILED", start_time)


@blocked_devices_bp.route('/blocked', methods=['POST'])
@router_context_required
def block_device_endpoint():
    """Block a device by IP/MAC or device_id"""
    start_time = time.time()
    data = request.get_json() or {}
    
    # Validate required fields
    device_ip = data.get('device_ip') or data.get('ip')
    device_id = data.get('device_id')
    
    if not device_ip and not device_id:
        return build_error_response("device_ip or device_id is required", 400, "INVALID_INPUT", start_time)
    
    try:
        result, error = block_device(g.user_id, g.router_id, g.session_id, data)
        if error:
            if "already blocked" in error.lower():
                return build_error_response(error, 409, "DEVICE_ALREADY_BLOCKED", start_time)
            elif "not found" in error.lower():
                return build_error_response(error, 404, "DEVICE_NOT_FOUND", start_time)
            elif "invalid" in error.lower():
                return build_error_response(error, 400, "INVALID_INPUT", start_time)
            return build_error_response(f"Failed to block device: {error}", 500, "BLOCK_DEVICE_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Failed to block device: {str(e)}")
        return build_error_response(f"Failed to block device: {str(e)}", 500, "BLOCK_DEVICE_FAILED", start_time)


@blocked_devices_bp.route('/blocked/<blocked_device_id>', methods=['DELETE'])
@router_context_required  
def unblock_device_endpoint(blocked_device_id):
    """Unblock a device"""
    start_time = time.time()
    
    try:
        result, error = unblock_device(g.user_id, g.router_id, g.session_id, blocked_device_id)
        if error:
            if "not found" in error.lower():
                return build_error_response(error, 404, "BLOCKED_DEVICE_NOT_FOUND", start_time)
            return build_error_response(f"Failed to unblock device: {error}", 500, "UNBLOCK_DEVICE_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Failed to unblock device: {str(e)}")
        return build_error_response(f"Failed to unblock device: {str(e)}", 500, "UNBLOCK_DEVICE_FAILED", start_time)


@blocked_devices_bp.route('/blocked/check', methods=['POST'])
@router_context_required
def check_device_blocked():
    """Check if a device is blocked"""
    start_time = time.time()
    data = request.get_json() or {}
    
    device_ip = data.get('device_ip') or data.get('ip')
    device_id = data.get('device_id')
    
    if not device_ip and not device_id:
        return build_error_response("device_ip or device_id is required", 400, "INVALID_INPUT", start_time)
    
    try:
        is_blocked, error = is_device_blocked(g.user_id, g.router_id, g.session_id, device_ip, device_id)
        if error:
            return build_error_response(f"Failed to check device status: {error}", 500, "CHECK_DEVICE_FAILED", start_time)
        
        result = {
            "is_blocked": is_blocked,
            "device_ip": device_ip,
            "device_id": device_id
        }
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Failed to check if device is blocked: {str(e)}")
        return build_error_response(f"Failed to check device status: {str(e)}", 500, "CHECK_DEVICE_FAILED", start_time)


@blocked_devices_bp.route('/blocked/ids', methods=['GET'])
@router_context_required
def get_blocked_device_ids_endpoint():
    """Get list of blocked device IDs for filtering"""
    start_time = time.time()
    
    try:
        device_ids, error = get_blocked_device_ids(g.user_id, g.router_id, g.session_id)
        if error:
            return build_error_response(f"Failed to get blocked device IDs: {error}", 500, "GET_BLOCKED_IDS_FAILED", start_time)
        return build_success_response(device_ids, start_time)
    except Exception as e:
        logger.error(f"Failed to get blocked device IDs: {str(e)}")
        return build_error_response(f"Failed to get blocked device IDs: {str(e)}", 500, "GET_BLOCKED_IDS_FAILED", start_time)
