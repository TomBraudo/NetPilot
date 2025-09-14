from flask import Blueprint, jsonify, request, g
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from utils.middleware import router_context_required
from services.monitor_service import (
    get_current_devices_monitor,
    get_last_week_devices_monitor,
    get_last_month_devices_monitor,
    get_device_monitor_by_mac
)
import time

# Set up logging
logger = get_logger(__name__)

monitor_bp = Blueprint('monitor', __name__, url_prefix='/api/monitor')

@monitor_bp.route('/current', methods=['GET'])
@router_context_required
def get_current_monitor():
    """
    Get current devices monitoring data.
    
    Returns:
        JSON response with devices data or error
    """
    start_time = time.time()
    
    try:
        logger.info(f"Getting current monitor for user {g.user_id}")
        
        # Get current devices monitor data
        devices_data, error = get_current_devices_monitor(g.user_id, g.router_id, g.session_id)
        
        if error:
            logger.error(f"Failed to get current devices monitor: {error}")
            return build_error_response(f"Failed to get current devices monitor: {error}", 500, "MONITOR_ERROR", start_time)
        
        logger.info(f"Successfully retrieved current devices monitor data for {len(devices_data or [])} devices")
        
        response_data = {
            "data": devices_data or [],
            "metadata": {
                "routerId": g.router_id,
                "sessionId": g.session_id,
                "period": "current"
            }
        }
        
        return build_success_response(devices_data, start_time)
        
    except Exception as e:
        logger.error(f"Unexpected error in get_current_monitor: {str(e)}")
        return build_error_response("Internal server error", 500, "INTERNAL_ERROR", start_time)


@monitor_bp.route('/last-week', methods=['GET'])
@router_context_required
def get_last_week_monitor():
    """
    Get last week devices monitoring data.
    
    Returns:
        JSON response with devices data or error
    """
    start_time = time.time()
    
    try:
        logger.info(f"Getting last week monitor for user {g.user_id}")
        
        # Get last week devices monitor data
        devices_data, error = get_last_week_devices_monitor(g.user_id, g.router_id, g.session_id)
        
        if error:
            logger.error(f"Failed to get last week devices monitor: {error}")
            return build_error_response(f"Failed to get last week devices monitor: {error}", 500, "MONITOR_ERROR", start_time)
        
        logger.info(f"Successfully retrieved last week devices monitor data for {len(devices_data or [])} devices")
        
        response_data = {
            "data": devices_data or [],
            "metadata": {
                "routerId": g.router_id,
                "sessionId": g.session_id,
                "period": "last-week"
            }
        }
        
        return build_success_response(devices_data, start_time)
        
    except Exception as e:
        logger.error(f"Unexpected error in get_last_week_monitor: {str(e)}")
        return build_error_response("Internal server error", 500, "INTERNAL_ERROR", start_time)


@monitor_bp.route('/last-month', methods=['GET'])
@router_context_required
def get_last_month_monitor():
    """
    Get last month devices monitoring data.
    
    Returns:
        JSON response with devices data or error
    """
    start_time = time.time()
    
    try:
        logger.info(f"Getting last month monitor for user {g.user_id}")
        
        # Get last month devices monitor data
        devices_data, error = get_last_month_devices_monitor(g.user_id, g.router_id, g.session_id)
        
        if error:
            logger.error(f"Failed to get last month devices monitor: {error}")
            return build_error_response(f"Failed to get last month devices monitor: {error}", 500, "MONITOR_ERROR", start_time)
        
        logger.info(f"Successfully retrieved last month devices monitor data for {len(devices_data or [])} devices")
        
        response_data = {
            "data": devices_data or [],
            "metadata": {
                "routerId": g.router_id,
                "sessionId": g.session_id,
                "period": "last-month"
            }
        }
        
        return build_success_response(devices_data, start_time)
        
    except Exception as e:
        logger.error(f"Unexpected error in get_last_month_monitor: {str(e)}")
        return build_error_response("Internal server error", 500, "INTERNAL_ERROR", start_time)


@monitor_bp.route('/device/<mac>', methods=['GET'])
@router_context_required
def get_device_monitor(mac):
    """
    Get monitoring data for a specific device by MAC address.
    
    Args:
        mac: MAC address of the device
        
    Query Parameters:
        period: Time period (current, week, month) - defaults to 'current'
    
    Returns:
        JSON response with device data or error
    """
    start_time = time.time()
    
    try:
        period = request.args.get('period', 'current')
        
        logger.info(f"Getting device monitor for MAC {mac} with period {period} for user {g.user_id}")
        
        # Validate period parameter
        valid_periods = ["current", "week", "month"]
        if period not in valid_periods:
            logger.error(f"Invalid period '{period}'. Must be one of: {', '.join(valid_periods)}")
            return build_error_response(f"Invalid period. Must be one of: {', '.join(valid_periods)}", 400, "INVALID_PERIOD", start_time)
        
        # Get device monitor data
        device_data, error = get_device_monitor_by_mac(g.user_id, g.router_id, g.session_id, mac, period)
        
        if error:
            logger.error(f"Failed to get device monitor for MAC {mac}: {error}")
            return build_error_response(f"Failed to get device monitor: {error}", 500, "MONITOR_ERROR", start_time)
        
        if not device_data:
            logger.warning(f"No device found with MAC {mac}")
            return build_error_response("Device not found", 404, "DEVICE_NOT_FOUND", start_time)
        
        logger.info(f"Successfully retrieved device monitor data for MAC {mac}")
        
        response_data = {
            "data": device_data,
            "metadata": {
                "routerId": g.router_id,
                "sessionId": g.session_id,
                "period": period,
                "mac": mac
            }
        }

        return build_success_response(device_data, start_time)

    except Exception as e:
        logger.error(f"Unexpected error in get_device_monitor: {str(e)}")
        return build_error_response("Internal server error", 500, "INTERNAL_ERROR", start_time)
