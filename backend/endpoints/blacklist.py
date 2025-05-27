from flask import Blueprint, request, jsonify
from services.blacklist_bandwidth import (
    get_blacklist_ips,
    add_single_device_to_blacklist,
    remove_single_device_from_blacklist,
    update_blacklist_limit_rate,
    update_blacklist_full_rate,
    activate_blacklist_mode,
    deactivate_blacklist_mode,
    remove_from_blacklist,
    add_to_blacklist,
    get_blacklist,
    clear_blacklist
)
from services.bandwidth_mode import set_mode, get_current_mode
from utils.response_helpers import success, error
from utils.logging_config import get_logger
from db.device_repository import get_mac_from_ip

# Get logger for blacklist endpoints
logger = get_logger('blacklist.endpoints')

blacklist_bp = Blueprint('blacklist', __name__)

@blacklist_bp.route('/blacklist', methods=['GET'])
def get_blacklist_route():
    """Get the current blacklist"""
    try:
        blacklist = get_blacklist()
        return jsonify({'success': True, 'blacklist': blacklist})
    except Exception as e:
        logger.error(f"Error getting blacklist: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@blacklist_bp.route('/blacklist', methods=['POST'])
def add_to_blacklist_route():
    """Add a device to the blacklist"""
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
        
        add_to_blacklist(ip, name, description)
        return jsonify({'success': True, 'message': f'Device {ip} added to blacklist'})
    except Exception as e:
        logger.error(f"Error adding device to blacklist: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@blacklist_bp.route('/blacklist/<ip>', methods=['DELETE'])
def remove_from_blacklist_route(ip):
    """Remove a device from the blacklist"""
    try:
        # Get MAC address for the IP
        mac = get_mac_from_ip(ip)
        if not mac:
            return jsonify({'success': False, 'error': 'Device not found in network'}), 404
            
        remove_from_blacklist(ip)
        return jsonify({'success': True, 'message': f'Device {ip} removed from blacklist'})
    except Exception as e:
        logger.error(f"Error removing device from blacklist: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@blacklist_bp.route('/blacklist/clear', methods=['POST'])
def clear_blacklist_route():
    """Clear all devices from the blacklist"""
    try:
        clear_blacklist()
        return jsonify({'success': True, 'message': 'Blacklist cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing blacklist: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@blacklist_bp.route('/blacklist/activate', methods=['POST'])
def activate_blacklist_route():
    """Activate blacklist mode"""
    try:
        set_mode('blacklist')
        return jsonify({'success': True, 'message': 'Blacklist mode activated'})
    except Exception as e:
        logger.error(f"Error activating blacklist mode: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@blacklist_bp.route('/blacklist/deactivate', methods=['POST'])
def deactivate_blacklist_route():
    """Deactivate blacklist mode"""
    try:
        set_mode('none')
        return jsonify({'success': True, 'message': 'Blacklist mode deactivated'})
    except Exception as e:
        logger.error(f"Error deactivating blacklist mode: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@blacklist_bp.route('/blacklist/mode', methods=['GET'])
def get_blacklist_mode_route():
    logger.info("Getting blacklist mode status")
    current_mode = get_current_mode()
    is_active = current_mode == "blacklist"
    logger.info(f"Blacklist mode is currently {'active' if is_active else 'inactive'}")
    return jsonify(success(data=is_active))

@blacklist_bp.route('/blacklist/mode', methods=['POST'])
def activate_blacklist_mode_route():
    logger.info("Attempting to activate blacklist mode")
    current_mode = get_current_mode()
    
    if current_mode == "blacklist":
        logger.info("Blacklist mode is already active, aborting activation")
        return jsonify(error(message="Blacklist mode is already active"))
    
    try:
        # Switch to blacklist mode
        set_mode("blacklist")
        
        # Activate blacklist mode on the router
        logger.info("Activating blacklist mode on router")
        router_result = activate_blacklist_mode()
        
        if router_result:
            logger.info("Blacklist mode successfully activated")
            return jsonify(success(message="Blacklist mode activated"))
        else:
            # If router update fails, revert mode change
            logger.error("Router blacklist mode activation failed, reverting mode change")
            set_mode("none")
            return jsonify(error(message="Failed to activate blacklist mode on router"))
    except Exception as e:
        logger.error(f"Error in activate_blacklist_mode_route: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to activate blacklist mode: {str(e)}"))

@blacklist_bp.route('/blacklist/mode', methods=['DELETE'])
def deactivate_blacklist_mode_route():
    logger.info("Attempting to deactivate blacklist mode")
    current_mode = get_current_mode()
    
    if current_mode != "blacklist":
        logger.info("Blacklist mode is not active, aborting deactivation")
        return jsonify(error(message="Blacklist mode is not active"))
    
    try:
        # Deactivate blacklist mode on the router
        logger.info("Deactivating blacklist mode on router")
        router_result = deactivate_blacklist_mode()
        
        if router_result:
            # Set mode to none
            set_mode("none")
            logger.info("Blacklist mode successfully deactivated")
            return jsonify(success(message="Blacklist mode deactivated"))
        else:
            logger.error("Failed to deactivate blacklist mode on router")
            return jsonify(error(message="Failed to deactivate blacklist mode on router"))
    except Exception as e:
        logger.error(f"Error in deactivate_blacklist_mode_route: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to deactivate blacklist mode: {str(e)}"))

@blacklist_bp.route('/blacklist/limit_rate', methods=['POST'])
def update_blacklist_limit_rate_route():
    data = request.json
    rate = data.get('rate')
    logger.info(f"Updating blacklist limit rate to {rate}")
    try:
        updated_rate = update_blacklist_limit_rate(rate)
        logger.info(f"Blacklist limit rate successfully updated to {updated_rate}")
        return jsonify(success(message=f"Blacklist limit rate updated to {updated_rate}"))
    except Exception as e:
        logger.error(f"Failed to update limit rate: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to update limit rate: {str(e)}"))

@blacklist_bp.route('/blacklist/full_rate', methods=['POST'])
def update_blacklist_full_rate_route():
    data = request.json
    rate = data.get('rate')
    logger.info(f"Updating blacklist full rate to {rate}")
    try:
        updated_rate = update_blacklist_full_rate(rate)
        logger.info(f"Blacklist full rate successfully updated to {updated_rate}")
        return jsonify(success(message=f"Blacklist full rate updated to {updated_rate}"))
    except Exception as e:
        logger.error(f"Failed to update full rate: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to update full rate: {str(e)}"))

@blacklist_bp.route('/blacklist/mode/refresh', methods=['POST'])
def refresh_blacklist_mode_route():
    """
    Refreshes the blacklist mode with the current blacklist IPs
    """
    logger.info("Refreshing blacklist mode")
    current_mode = get_current_mode()
    logger.info(f"Current mode: {current_mode}")
    
    if current_mode != "blacklist":
        logger.warning("Cannot refresh blacklist mode - mode is not active")
        return jsonify(error(message="Blacklist mode is not active"))
    
    try:
        # Refresh the router configuration with current blacklist
        logger.info("Refreshing router blacklist configuration")
        router_result = activate_blacklist_mode()
        
        if router_result:
            logger.info("Blacklist mode refreshed successfully")
            return jsonify(success(message="Blacklist mode refreshed with current blacklist"))
        else:
            logger.error("Failed to refresh blacklist mode on router")
            return jsonify(error(message="Failed to refresh blacklist mode on router"))
    except Exception as e:
        logger.error(f"Error in refresh_blacklist_mode_route: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to refresh blacklist mode: {str(e)}")) 