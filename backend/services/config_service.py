from utils.response_helpers import success
from utils.logging_config import get_logger
from utils.path_utils import get_data_folder
import os

logger = get_logger('services.config')

def set_admin_credentials(username, password):
    """
    Sets the admin credentials for the OpenWrt router.
    
    Args:
        username: New username
        password: New password
     
    Returns:
        Success or error message
    """
    try:
        # Check if username and password are provided
        if not username or not password:
            raise ValueError("Missing 'username' or 'password' in request body")

        config_path = os.path.join(get_data_folder(), ".env")
        with open(config_path, "w") as f:
            f.write(f"ROUTER_USERNAME={username}\nROUTER_PASSWORD={password}")

        return success(message="Admin credentials updated successfully")
    except Exception as e:
        logger.error(f"Error setting admin credentials: {str(e)}", exc_info=True)
        raise