from flask import Blueprint, request, g
from utils.response_helpers import build_success_response, build_error_response
from utils.logging_config import get_logger
from utils.middleware import router_context_required
from services.device_service import (
    get_user_devices,
    create_or_update_device,
    bulk_create_or_update_devices,
    get_device_by_id,
    delete_device,
    validate_devices,
    update_device
)
import time

devices_bp = Blueprint('devices', __name__)
logger = get_logger('endpoints.devices')


@devices_bp.route('/', methods=['GET'])
@router_context_required
def get_devices():
    """Get all devices for the current user and router"""
    start_time = time.time()
    
    try:
        devices = get_user_devices(g.user_id, g.router_id)
        return build_success_response(devices, start_time)
    except Exception as e:
        logger.error(f"Failed to get devices: {str(e)}")
        return build_error_response(f"Failed to get devices: {str(e)}", 500, "GET_DEVICES_FAILED", start_time)


@devices_bp.route('/', methods=['POST'])
@router_context_required
def create_device():
    """Create or update a single device"""
    start_time = time.time()
    data = request.get_json() or {}
    
    ip = data.get('ip', '').strip()
    if not ip:
        return build_error_response("Device IP is required", 400, "INVALID_INPUT", start_time)
    
    try:
        device = create_or_update_device(
            g.user_id, 
            g.router_id, 
            ip=ip,
            mac=data.get('mac'),
            hostname=data.get('hostname'),
            device_name=data.get('device_name'),
            device_type=data.get('device_type') or data.get('type'),
            manufacturer=data.get('manufacturer')
        )
        return build_success_response(device, start_time)
    except ValueError as e:
        return build_error_response(str(e), 400, "INVALID_INPUT", start_time)
    except Exception as e:
        logger.error(f"Failed to create device: {str(e)}")
        return build_error_response(f"Failed to create device: {str(e)}", 500, "CREATE_DEVICE_FAILED", start_time)


@devices_bp.route('/bulk', methods=['POST'])
@router_context_required
def bulk_create_devices():
    """Create or update multiple devices from scan"""
    start_time = time.time()
    data = request.get_json() or {}
    
    devices_data = data.get('devices', [])
    if not devices_data:
        return build_error_response("Devices array is required", 400, "INVALID_INPUT", start_time)
    
    try:
        devices = bulk_create_or_update_devices(g.user_id, g.router_id, devices_data)
        return build_success_response(devices, start_time)
    except ValueError as e:
        return build_error_response(str(e), 400, "INVALID_INPUT", start_time)
    except Exception as e:
        logger.error(f"Failed to bulk create devices: {str(e)}")
        return build_error_response(f"Failed to bulk create devices: {str(e)}", 500, "BULK_CREATE_DEVICES_FAILED", start_time)


@devices_bp.route('/validate', methods=['POST'])
@router_context_required
def validate_devices_endpoint():
    """Validate that devices exist in database by IP or UUID"""
    start_time = time.time()
    data = request.get_json() or {}
    
    device_identifiers = data.get('devices', [])
    if not device_identifiers:
        return build_error_response("Devices array is required", 400, "INVALID_INPUT", start_time)
    
    try:
        validation_result = validate_devices(g.user_id, g.router_id, device_identifiers)
        
        # valid_devices are already dictionaries from the service
        valid_devices_dicts = validation_result['valid_devices']
        
        logger.info(f"Device validation: {validation_result['total_valid']} valid, {validation_result['total_invalid']} invalid")
        
        return build_success_response({
            'valid_devices': valid_devices_dicts,
            'invalid_devices': validation_result['invalid_devices'],
            'total_valid': validation_result['total_valid'],
            'total_invalid': validation_result['total_invalid']
        }, start_time)
        
    except Exception as e:
        logger.error(f"Failed to validate devices: {str(e)}")
        return build_error_response(f"Failed to validate devices: {str(e)}", 500, "VALIDATE_DEVICES_FAILED", start_time)


@devices_bp.route('/<device_id>', methods=['GET'])
@router_context_required
def get_device_endpoint(device_id):
    """Get a specific device"""
    start_time = time.time()
    
    try:
        result, error = get_device_by_id(g.user_id, g.router_id, device_id)
        if error:
            if "Device not found" in error:
                return build_error_response("Device not found", 404, "DEVICE_NOT_FOUND", start_time)
            return build_error_response(f"Failed to get device: {error}", 500, "GET_DEVICE_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Failed to get device: {str(e)}")
        return build_error_response(f"Failed to get device: {str(e)}", 500, "GET_DEVICE_FAILED", start_time)


@devices_bp.route('/<device_id>', methods=['PUT'])
@router_context_required
def update_device_endpoint(device_id):
    """Update a device"""
    start_time = time.time()
    data = request.get_json() or {}
    
    try:
        # Use the service layer to update the device
        result, error = update_device(g.user_id, g.router_id, device_id, data)
        if error:
            if "Device not found" in error:
                return build_error_response("Device not found", 404, "DEVICE_NOT_FOUND", start_time)
            return build_error_response(f"Failed to update device: {error}", 500, "UPDATE_DEVICE_FAILED", start_time)
        
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Failed to update device: {str(e)}")
        return build_error_response(f"Failed to update device: {str(e)}", 500, "UPDATE_DEVICE_FAILED", start_time)


@devices_bp.route('/<device_id>', methods=['DELETE'])
@router_context_required
def delete_device_endpoint(device_id):
    """Delete a device"""
    start_time = time.time()
    
    try:
        result = delete_device(g.user_id, g.router_id, device_id)
        
        # Handle different return types
        if result is None:
            return build_error_response("Device not found", 404, "DEVICE_NOT_FOUND", start_time)
        elif isinstance(result, str):
            # Error message
            return build_error_response(f"Failed to delete device: {result}", 500, "DELETE_DEVICE_FAILED", start_time)
        elif isinstance(result, tuple) and len(result) == 2:
            # Success: (success, deleted_group_ids)
            success, deleted_group_ids = result
            if success:
                response_data = {
                    "message": "Device deleted successfully",
                    "deleted_groups": deleted_group_ids
                }
                return build_success_response(response_data, start_time)
        
        # Fallback
        return build_success_response({"message": "Device deleted successfully"}, start_time)
        
    except Exception as e:
        logger.error(f"Failed to delete device: {str(e)}")
        return build_error_response(f"Failed to delete device: {str(e)}", 500, "DELETE_DEVICE_FAILED", start_time)
