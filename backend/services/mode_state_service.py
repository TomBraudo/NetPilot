from utils.config_manager import config_manager
from utils.logging_config import get_logger
from utils.response_helpers import success

logger = get_logger('services.mode_state')

def get_current_mode_value():
    """Gets the current bandwidth mode string directly from config."""
    try:
        config = config_manager.load_config('bandwidth')
        return config.get('Mode', 'none')
    except Exception as e:
        logger.error(f"Error getting current mode value: {str(e)}", exc_info=True)
        # In case of error, returning 'none' might be safer than raising an unhandled exception
        # depending on how critical this information is and how callers handle exceptions.
        # For now, let's re-raise to be explicit about failures.
        raise

def set_current_mode_value(mode):
    """Sets the bandwidth mode string directly in config and returns a success/error object."""
    try:
        config = config_manager.load_config('bandwidth')
        config['Mode'] = mode
        config_manager.save_config('bandwidth', config)
        logger.info(f"Updated bandwidth mode to {mode}")
        return success(message=f"Bandwidth mode set to {mode}")
    except Exception as e:
        logger.error(f"Error setting bandwidth mode value: {str(e)}", exc_info=True)
        # Return an error object consistent with other service responses
        # raise # Or return error(str(e))
        # Matching the original set_mode's behavior of raising on error.
        raise 