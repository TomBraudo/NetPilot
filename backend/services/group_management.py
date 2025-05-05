import logging
from db.group_repository import set_group_blacklist_mode, get_group_blacklist_mode
from utils.response_helpers import success, error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def toggle_group_blacklist_mode(group_name, is_blacklist=None):
    """
    Toggle or set a group's blacklist/whitelist mode.
    
    Args:
        group_name: Name of the group
        is_blacklist: If provided, set to this value; if None, toggle current value
        
    Returns:
        Dictionary with success/error status and message
    """
    try:
        if not group_name:
            return error("Group name is required")
            
        # If is_blacklist is None, we're toggling
        if is_blacklist is None:
            current_mode = get_group_blacklist_mode(group_name)
            if current_mode is None:
                return error(f"Group not found: {group_name}")
                
            is_blacklist = not current_mode
            
        # Set the mode
        result = set_group_blacklist_mode(group_name, is_blacklist)
        
        if result:
            mode_str = "blacklist" if is_blacklist else "whitelist"
            return success(f"Group '{group_name}' set to {mode_str} mode")
        else:
            return error(f"Failed to set blacklist mode for group: {group_name}")
            
    except Exception as e:
        logger.error(f"Error toggling group blacklist mode: {str(e)}")
        return error(f"Error toggling group blacklist mode: {str(e)}")

def get_group_mode(group_name):
    """
    Get the current blacklist/whitelist mode of a group.
    
    Args:
        group_name: Name of the group
        
    Returns:
        Dictionary with success/error status and mode information
    """
    try:
        if not group_name:
            return error("Group name is required")
            
        mode = get_group_blacklist_mode(group_name)
        if mode is None:
            return error(f"Group not found: {group_name}")
            
        mode_str = "blacklist" if mode else "whitelist"
        return success(data={"group": group_name, "is_blacklist": mode, "mode": mode_str})
        
    except Exception as e:
        logger.error(f"Error getting group blacklist mode: {str(e)}")
        return error(f"Error getting group blacklist mode: {str(e)}") 