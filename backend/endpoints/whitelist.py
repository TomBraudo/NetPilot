from flask import Blueprint, request, jsonify
from db.whitelist_managenemt import get_whitelist, add_to_whitelist, remove_from_whitelist, is_whitelist_mode_active, activate_whitelist_mode, deactivate_whitelist_mode
from services.whitelist_bandwidth import (
    update_whitelist_interface, update_whitelist_limit_rate, update_whitelist_full_rate,
    add_single_device_to_tc, remove_single_device_from_tc, 
    activate_whitelist_mode as activate_router_whitelist, deactivate_whitelist_mode as deactivate_router_whitelist
)
from utils.response_helpers import success, error
from utils.logging_config import get_logger

# Get logger for whitelist endpoints
logger = get_logger('whitelist.endpoints')

whitelist_bp = Blueprint('whitelist', __name__)

@whitelist_bp.route('/whitelist', methods=['GET'])
def get_whitelist_route():
    try:
        logger.info("Getting whitelist devices")
        whitelist = get_whitelist()
        logger.info(f"Found {len(whitelist)} devices in whitelist")
        return jsonify(success(data=whitelist))
    except Exception as e:
        logger.error(f"Error getting whitelist: {str(e)}", exc_info=True)
        return jsonify(error(message=str(e)))

@whitelist_bp.route('/whitelist', methods=['POST'])
def add_to_whitelist_route():
    data = request.json
    ip = data.get('ip')
    name = data.get('name', None)
    description = data.get('description', None)
    
    logger.info(f"Adding device {ip} to whitelist with name: {name}")
    
    try:
        # First, add to database
        entry = add_to_whitelist(ip, name, description)
        
        # If successful and whitelist mode is active, update router immediately
        whitelist_mode = is_whitelist_mode_active()
        
        if whitelist_mode is True:
            logger.info(f"Whitelist mode is active, updating traffic control for {ip}")
            try:
                device_added = add_single_device_to_tc(ip)
                if not device_added:
                    # If adding to TC fails, still return success but with a warning
                    logger.warning(f"Failed to add {ip} to traffic control")
                    return jsonify(success(
                        message=f"Device {ip} added to whitelist but traffic control update failed", 
                        data=entry
                    ))
            except Exception as e:
                # If adding to TC fails with exception, still return success but with a warning
                logger.error(f"Exception adding {ip} to traffic control: {str(e)}", exc_info=True)
                return jsonify(success(
                    message=f"Device {ip} added to whitelist but traffic control update failed: {str(e)}", 
                    data=entry
                ))
        
        logger.info(f"Successfully added device {ip} to whitelist")
        return jsonify(success(message=f"Device {ip} added to whitelist", data=entry))
    except ValueError as e:
        logger.warning(f"Value error adding device to whitelist: {str(e)}")
        return jsonify(error(message=str(e)))
    except Exception as e:
        logger.error(f"Error adding device to whitelist: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to add device: {str(e)}"))

@whitelist_bp.route('/whitelist', methods=['DELETE'])
def remove_from_whitelist_route():
    data = request.json
    ip = data.get('ip')
    
    logger.info(f"Removing device {ip} from whitelist")
    
    try:
        # First, remove from database
        removed_ip = remove_from_whitelist(ip)
        
        # If successful and whitelist mode is active, update router immediately
        whitelist_mode = is_whitelist_mode_active()
        
        if whitelist_mode is True:
            logger.info(f"Whitelist mode is active, removing {ip} from traffic control")
            try:
                device_removed = remove_single_device_from_tc(ip)
                if not device_removed:
                    # If removing from TC fails, still return success but with a warning
                    logger.warning(f"Failed to remove {ip} from traffic control")
                    return jsonify(success(
                        message=f"Device {removed_ip} removed from whitelist but traffic control update failed"
                    ))
            except Exception as e:
                # If removing from TC fails with exception, still return success but with a warning
                logger.error(f"Exception removing {ip} from traffic control: {str(e)}", exc_info=True)
                return jsonify(success(
                    message=f"Device {removed_ip} removed from whitelist but traffic control update failed: {str(e)}"
                ))
        
        logger.info(f"Successfully removed device {ip} from whitelist")
        return jsonify(success(message=f"Device {removed_ip} removed from whitelist"))
    except ValueError as e:
        logger.warning(f"Value error removing device from whitelist: {str(e)}")
        return jsonify(error(message=str(e)))
    except Exception as e:
        logger.error(f"Error removing device from whitelist: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to remove device: {str(e)}"))

@whitelist_bp.route('/whitelist/mode', methods=['GET'])
def get_whitelist_mode_route():
    # Return in success format for the frontend
    logger.info("Getting whitelist mode status")
    is_active = is_whitelist_mode_active()
    logger.info(f"Whitelist mode is currently {'active' if is_active else 'inactive'}")
    return jsonify(success(data=is_active))

@whitelist_bp.route('/whitelist/mode', methods=['POST'])
def activate_whitelist_mode_route():
    # Get whitelist mode status
    logger.info("Attempting to activate whitelist mode")
    whitelist_mode = is_whitelist_mode_active()
    
    if whitelist_mode is True:
        logger.info("Whitelist mode is already active, aborting activation")
        return jsonify(error(message="Whitelist mode is already active"))
    
    try:
        # First, update the database setting
        logger.info("Updating database whitelist mode setting")
        db_result = activate_whitelist_mode()
        if not db_result:
            logger.error("Failed to activate whitelist mode in database")
            return jsonify(error(message="Failed to activate whitelist mode in database"))
        
        # Verify the mode is now active
        current_mode = is_whitelist_mode_active()
        if not current_mode:
            logger.error("Whitelist mode activation failed: setting is still inactive after update")
            return jsonify(error(message="Failed to activate whitelist mode: database update was not reflected"))
        
        # Then activate whitelist mode on the router
        logger.info("Activating whitelist mode on router")
        router_result = activate_router_whitelist()
        
        if router_result:
            logger.info("Whitelist mode successfully activated")
            return jsonify(success(message="Whitelist mode activated"))
        else:
            # If router update fails, revert database change
            logger.error("Router whitelist mode activation failed, reverting database change")
            deactivate_whitelist_mode()
            return jsonify(error(message="Failed to activate whitelist mode on router"))
    except Exception as e:
        logger.error(f"Error in activate_whitelist_mode_route: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to activate whitelist mode: {str(e)}"))

@whitelist_bp.route('/whitelist/mode', methods=['DELETE'])
def deactivate_whitelist_mode_route():
    # Get whitelist mode status
    logger.info("Attempting to deactivate whitelist mode")
    whitelist_mode = is_whitelist_mode_active()
    
    if whitelist_mode is False:
        logger.info("Whitelist mode is not active, aborting deactivation")
        return jsonify(error(message="Whitelist mode is not active"))
    
    try:
        # First, update the database setting
        logger.info("Updating database whitelist mode setting")
        db_result = deactivate_whitelist_mode()
        if not db_result:
            logger.error("Failed to deactivate whitelist mode in database")
            return jsonify(error(message="Failed to deactivate whitelist mode in database"))
        
        # Verify the mode is now inactive
        current_mode = is_whitelist_mode_active()
        if current_mode:
            logger.error("Whitelist mode deactivation failed: setting is still active after update")
            return jsonify(error(message="Failed to deactivate whitelist mode: database update was not reflected"))
        
        # Then deactivate whitelist mode on the router
        logger.info("Deactivating whitelist mode on router")
        router_result = deactivate_router_whitelist()
        
        if router_result:
            logger.info("Whitelist mode successfully deactivated")
            return jsonify(success(message="Whitelist mode deactivated"))
        else:
            # If router update fails, revert database change
            logger.error("Router whitelist mode deactivation failed, reverting database change")
            activate_whitelist_mode()
            return jsonify(error(message="Failed to deactivate whitelist mode on router"))
    except Exception as e:
        logger.error(f"Error in deactivate_whitelist_mode_route: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to deactivate whitelist mode: {str(e)}"))

@whitelist_bp.route('/whitelist/interface', methods=['POST'])
def update_whitelist_interface_route():
    data = request.json
    interface = data.get('interface')
    logger.info(f"Updating whitelist interface to {interface}")
    try:
        updated_interface = update_whitelist_interface(interface)
        logger.info(f"Whitelist interface successfully updated to {updated_interface}")
        return jsonify(success(message=f"Whitelist interface updated to {updated_interface}"))
    except Exception as e:
        logger.error(f"Failed to update interface: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to update interface: {str(e)}"))

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
    # Check if whitelist mode is active
    logger.info("Refreshing whitelist mode")
    whitelist_mode = is_whitelist_mode_active()
    logger.info(f"Current whitelist mode: {whitelist_mode}")
    
    if whitelist_mode is not True:
        logger.warning("Cannot refresh whitelist mode - mode is not active")
        return jsonify(error(message="Whitelist mode is not active"))
    
    try:
        # Refresh the router configuration with current whitelist
        logger.info("Refreshing router whitelist configuration")
        router_result = activate_router_whitelist()
        
        if router_result:
            logger.info("Whitelist mode refreshed successfully")
            return jsonify(success(message="Whitelist mode refreshed with current whitelist"))
        else:
            logger.error("Failed to refresh whitelist mode on router")
            return jsonify(error(message="Failed to refresh whitelist mode on router"))
    except Exception as e:
        logger.error(f"Error in refresh_whitelist_mode_route: {str(e)}", exc_info=True)
        return jsonify(error(message=f"Failed to refresh whitelist mode: {str(e)}"))


