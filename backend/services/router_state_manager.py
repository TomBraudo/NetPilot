import json
from utils.logging_config import get_logger
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from managers.router_connection_manager import _RouterConnection

logger = get_logger('services.router_state')

STATE_FILE_PATH = "/etc/config/netpilot_state.json"

def _get_default_state() -> Dict[str, Any]:
    """Returns the default structure for the state file."""
    return {
        "active_mode": "none",
        "rates": {
            "whitelist": {
                "full_rate": "1000mbit",
                "limited_rate": "50000kbit"
            },
            "blacklist": {
                "limited_rate": "50000kbit"
            }
        },
        "devices": {
            "whitelist": [],
            "blacklist": []
        }
    }

def get_router_state(conn: '_RouterConnection') -> Dict[str, Any]:
    """
    Reads the state file from the router.
    If the file doesn't exist, it returns a default state.
    """
    command = f"cat {STATE_FILE_PATH}"
    out, err = conn.exec_command(command)
    
    if err or not out:
        logger.warning(f"State file not found or empty on router. Using default state.")
        return _get_default_state()
    
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        logger.error("Failed to decode state file from router. Using default state.")
        return _get_default_state()

def write_router_state(conn: '_RouterConnection', state: Dict[str, Any]):
    """
    Writes the provided state object as a JSON file to the router.
    This is a full overwrite.
    """
    json_string = json.dumps(state)
    # Use single quotes to ensure the JSON string is treated as a single argument
    command = f"echo '{json_string}' > {STATE_FILE_PATH}"
    
    _, err = conn.exec_command(command)
    if err:
        logger.error(f"Failed to write state file to router: {err}")
        return False
    return True 