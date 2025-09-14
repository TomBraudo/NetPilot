from typing import Optional, Tuple

from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager


# Module logger and shared router connection manager
logger = get_logger('services.agh_service')
router_connection_manager = RouterConnectionManager()


# Shared constants
CATEGORY_DIR = "/opt/AdGuardHome/categories"
RULES_STAGING_REMOTE = "/tmp/netpilot_agh_rules.json"
CLIENT_STAGING_REMOTE = "/tmp/netpilot_agh_client.json"
RESP_STAGING_REMOTE = "/tmp/netpilot_agh_resp.json"


def _execute(command: str, timeout: int = 30) -> Tuple[Optional[str], Optional[str]]:
    """Execute a command on the router via the shared connection manager."""
    return router_connection_manager.execute(command, timeout=timeout)


