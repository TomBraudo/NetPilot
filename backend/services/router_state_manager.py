import json
from utils.logging_config import get_logger
from typing import TYPE_CHECKING, Dict, Any
from managers.router_connection_manager import RouterConnectionManager

if TYPE_CHECKING:
    from managers.router_connection_manager import _RouterConnection

logger = get_logger('services.router_state')
router_connection_manager = RouterConnectionManager()

STATE_FILE_PATH = "/etc/config/netpilot_state.json"

def _get_default_state() -> Dict[str, Any]:
    """Returns the default structure for the state file."""
    return {
        "active_mode": "none",
        "rates": {
            "whitelist_full": "1000mbit",
            "whitelist_limited": "50mbit",
            "blacklist_limited": "50mbit"
        },
        "devices": {
            "whitelist": [],
            "blacklist": []
        }
    }

def get_router_state() -> Dict[str, Any]:
    """
    Reads the state file from the router.
    If the file doesn't exist, it returns a default state.
    """
    command = f"cat {STATE_FILE_PATH}"
    out, err = router_connection_manager.execute(command)
    
    if err or not out:
        logger.warning(f"State file not found or empty on router. Using default state.")
        return _get_default_state()
    
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        logger.error("Failed to decode state file from router. Using default state.")
        return _get_default_state()

def write_router_state(state: Dict[str, Any]):
    """
    Writes the provided state object as a JSON file to the router.
    This is a full overwrite.
    """
    json_string = json.dumps(state)
    # Use single quotes to ensure the JSON string is treated as a single argument
    command = f"echo '{json_string}' > {STATE_FILE_PATH}"
    
    _, err = router_connection_manager.execute(command)
    if err:
        logger.error(f"Failed to write state file to router: {err}")
        return False
    return True 