from flask import Blueprint, request, jsonify
from services.whitelist_bandwidth import (
    get_whitelist_ips,
    add_single_device_to_tc,
    remove_single_device_from_tc,
    update_whitelist_limit_rate,
    update_whitelist_full_rate,
    activate_whitelist_mode,
    deactivate_whitelist_mode,
    remove_from_whitelist,
    get_whitelist,
    add_to_whitelist,
    clear_whitelist
)
from services.bandwidth_mode import set_mode, get_current_mode
from utils.response_helpers import success, error
from utils.logging_config import get_logger
from db.tinydb_client import db_client
from tinydb import Query
from db.device_repository import get_mac_from_ip

# Get logger for whitelist endpoints
logger = get_logger('whitelist.endpoints')

whitelist_bp = Blueprint('whitelist', __name__)

@whitelist_bp.route('/whitelist', methods=['GET'])
def get_whitelist_route():
    """Get the current whitelist"""
    try:
        whitelist = get_whitelist()
        return jsonify({'success': True, 'whitelist': whitelist})
    except Exception as e:
        logger.error(f"Error getting whitelist: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@whitelist_bp.route('/whitelist', methods=['POST'])
def add_to_whitelist_route():
    """Add a device to the whitelist"""
    try:
        data = request.get_json()
        if not data or 'ip' not in data:
            return jsonify({'success': False, 'error': 'IP address is required'}), 400
            
        ip = data['ip']
        name = data.get('name')
        description = data.get('description')
        
        # Get MAC address for the IP
        mac = get_mac_from_ip(ip)
        if not mac:
            return jsonify({'success': False, 'error': 'Device not found in network'}), 404
        
        add_to_whitelist(ip, name, description)
        return jsonify({'success': True, 'message': f'Device {ip} added to whitelist'})
    except Exception as e:
        logger.error(f"Error adding device to whitelist: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@whitelist_bp.route('/whitelist/<ip>', methods=['DELETE'])
def remove_from_whitelist_route(ip):
    """Remove a device from the whitelist"""
    try:
        # Get MAC address for the IP
        mac = get_mac_from_ip(ip)
        if not mac:
            return jsonify({'success': False, 'error': 'Device not found in network'}), 404
            
        remove_from_whitelist(ip)
        return jsonify({'success': True, 'message': f'Device {ip} removed from whitelist'})
    except Exception as e:
        logger.error(f"Error removing device from whitelist: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@whitelist_bp.route('/whitelist/clear', methods=['POST'])
def clear_whitelist_route():
    """Clear all devices from the whitelist"""
    try:
        clear_whitelist()
        return jsonify({'success': True, 'message': 'Whitelist cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing whitelist: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@whitelist_bp.route('/whitelist/activate', methods=['POST'])
def activate_whitelist_route():
    """Activate whitelist mode"""
    try:
        set_mode('whitelist')
        return jsonify({'success': True, 'message': 'Whitelist mode activated'})
    except Exception as e:
        logger.error(f"Error activating whitelist mode: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@whitelist_bp.route('/whitelist/deactivate', methods=['POST'])
def deactivate_whitelist_route():
    """Deactivate whitelist mode"""
    try:
        set_mode('none')
        return jsonify({'success': True, 'message': 'Whitelist mode deactivated'})
    except Exception as e:
        logger.error(f"Error deactivating whitelist mode: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@whitelist_bp.route('/whitelist/mode', methods=['GET'])
def get_whitelist_mode_route():
    logger.info("Getting whitelist mode status")
    current_mode = get_current_mode()
    is_active = current_mode == "whitelist"
    logger.info(f"Whitelist mode is currently {'active' if is_active else 'inactive'}")
    return jsonify(success(data=is_active))

@whitelist_bp.route('/whitelist/mode', methods=['POST'])
def activate_whitelist_mode_route():
    logger.info("Attempting to activate whitelist mode")
    current_mode = get_current_mode()
    
    if current_mode == "whitelist":
        logger.info("Whitelist mode is already active, aborting activation")
        return jsonify(error(message="Whitelist mode is already active"))
    
    try:
        # Switch to whitelist mode
        set_mode("whitelist")
        
        # Activate whitelist mode on the router
        logger.info("Activating whitelist mode on router")
        router_result = activate_whitelist_mode()
        
        if router_result:
            logger.info("Whitelist mode successfully activated")
            return jsonify(success(message="Whitelist mode activated"))
        else:
            # If router update fails, revert mode change
            logger.error("Router whitelist mode activation failed, reverting mode change")
            set_mode("none")
            return jsonify(error(message="Failed to activate whitelist mode on router"))
    except Exception as e:
        logger.error(f"Error in activate_whitelist_mode_route: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to activate whitelist mode: {str(e)}"))

@whitelist_bp.route('/whitelist/mode', methods=['DELETE'])
def deactivate_whitelist_mode_route():
    logger.info("Attempting to deactivate whitelist mode")
    current_mode = get_current_mode()
    
    if current_mode != "whitelist":
        logger.info("Whitelist mode is not active, aborting deactivation")
        return jsonify(error(message="Whitelist mode is not active"))
    
    try:
        # Deactivate whitelist mode on the router
        logger.info("Deactivating whitelist mode on router")
        router_result = deactivate_whitelist_mode()
        
        if router_result:
            # Set mode to none
            set_mode("none")
            logger.info("Whitelist mode successfully deactivated")
            return jsonify(success(message="Whitelist mode deactivated"))
        else:
            logger.error("Failed to deactivate whitelist mode on router")
            return jsonify(error(message="Failed to deactivate whitelist mode on router"))
    except Exception as e:
        logger.error(f"Error in deactivate_whitelist_mode_route: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to deactivate whitelist mode: {str(e)}"))

@whitelist_bp.route('/whitelist/limit_rate', methods=['POST'])
def update_whitelist_limit_rate_route():
    data = request.json
    rate = data.get('rate')
    logger.info(f"Updating whitelist limit rate to {rate}")
    try:
        updated_rate = update_whitelist_limit_rate(rate)
        logger.info(f"Whitelist limit rate successfully updated to {updated_rate}")
        return jsonify(success(message=f"Whitelist limit rate updated to {updated_rate}"))
    except Exception as e:
        logger.error(f"Failed to update limit rate: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to update limit rate: {str(e)}"))

@whitelist_bp.route('/whitelist/full_rate', methods=['POST'])
def update_whitelist_full_rate_route():
    data = request.json
    rate = data.get('rate')
    logger.info(f"Updating whitelist full rate to {rate}")
    try:
        updated_rate = update_whitelist_full_rate(rate)
        logger.info(f"Whitelist full rate successfully updated to {updated_rate}")
        return jsonify(success(message=f"Whitelist full rate updated to {updated_rate}"))
    except Exception as e:
        logger.error(f"Failed to update full rate: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to update full rate: {str(e)}"))

@whitelist_bp.route('/whitelist/mode/refresh', methods=['POST'])
def refresh_whitelist_mode_route():
    """
    Refreshes the whitelist mode with the current whitelist IPs
    """
    logger.info("Refreshing whitelist mode")
    current_mode = get_current_mode()
    logger.info(f"Current mode: {current_mode}")
    
    if current_mode != "whitelist":
        logger.warning("Cannot refresh whitelist mode - mode is not active")
        return jsonify(error(message="Whitelist mode is not active"))
    
    try:
        # Refresh the router configuration with current whitelist
        logger.info("Refreshing router whitelist configuration")
        router_result = activate_whitelist_mode()
        
        if router_result:
            logger.info("Whitelist mode refreshed successfully")
            return jsonify(success(message="Whitelist mode refreshed with current whitelist"))
        else:
            logger.error("Failed to refresh whitelist mode on router")
            return jsonify(error(message="Failed to refresh whitelist mode on router"))
    except Exception as e:
        logger.error(f"Error in refresh_whitelist_mode_route: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to refresh whitelist mode: {str(e)}"))


