from utils.logging_config import get_logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from managers.router_connection_manager import _RouterConnection

logger = get_logger('services.router_setup')

# Constants for iptables and tc
WHITELIST_CHAIN = "NETPILOT_WHITELIST"
BLACKLIST_CHAIN = "NETPILOT_BLACKLIST"
LAN_INTERFACE = "br-lan"  # Common LAN interface for OpenWrt

def _execute_command(conn: '_RouterConnection', command: str):
    """
    Executes a command on the router, handling common "already exists" errors
    for idempotency. Returns True on success/pre-existence, False on failure.
    """
    _, err = conn.exec_command(command, timeout=10)
    if err:
        # These errors are expected if infrastructure is already in place.
        # Treat them as success for idempotency, but log for debugging.
        if "File exists" in err or "chain already exists" in err or "Exclusivity flag on" in err:
            logger.debug(f"Infrastructure component already exists, command skipped: {command}")
            return True
        
        # This is not a failure, but the expected output for a non-existent rule check.
        # Return False to signal that the rule needs to be added.
        if "Bad rule" in err and "-C" in command:
            return False

        logger.error(f"Command '{command}' failed with error: {err}")
        return False
    return True

def setup_router_infrastructure(conn: '_RouterConnection'):
    """
    Sets up the necessary iptables chains and tc configurations for both
    whitelist and blacklist functionalities using the provided connection.
    This function is idempotent.
    """
    logger.info("Setting up router infrastructure for NetPilot...")

    # Define constants for marks and classes
    WHITELIST_LIMITED_MARK = "30"
    BLACKLIST_MARK = "10"
    LIMITED_RATE_CLASSID = "1:12"

    # 1. Create custom iptables chains
    _execute_command(conn, f"iptables -t mangle -N {WHITELIST_CHAIN}")
    _execute_command(conn, f"iptables -t mangle -N {BLACKLIST_CHAIN}")

    # 2. Setup base TC qdisc for rate limiting
    _execute_command(conn, f"tc qdisc add dev {LAN_INTERFACE} root handle 1: htb default 11")
    
    # 3. Add default/unlimited classes for both services
    _execute_command(conn, f"tc class add dev {LAN_INTERFACE} parent 1: classid 1:11 htb rate 1000mbit")
    _execute_command(conn, f"tc class add dev {LAN_INTERFACE} parent 1: classid {LIMITED_RATE_CLASSID} htb rate 1mbit")

    # 4. CRITICAL: Add TC filters to connect iptables marks to tc classes
    _execute_command(conn, f"tc filter add dev {LAN_INTERFACE} parent 1: protocol ip prio 2 handle {WHITELIST_LIMITED_MARK} fw flowid {LIMITED_RATE_CLASSID}")
    _execute_command(conn, f"tc filter add dev {LAN_INTERFACE} parent 1: protocol ip prio 1 handle {BLACKLIST_MARK} fw flowid {LIMITED_RATE_CLASSID}")

    # 5. Add jump rules to our chains from PREROUTING
    if not _execute_command(conn, f"iptables -t mangle -C PREROUTING -j {WHITELIST_CHAIN}"):
        _execute_command(conn, f"iptables -t mangle -A PREROUTING -j {WHITELIST_CHAIN}")
        
    if not _execute_command(conn, f"iptables -t mangle -C PREROUTING -j {BLACKLIST_CHAIN}"):
        _execute_command(conn, f"iptables -t mangle -A PREROUTING -j {BLACKLIST_CHAIN}")

    logger.info("Router infrastructure setup complete.")
    return True, None 