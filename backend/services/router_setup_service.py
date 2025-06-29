from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
from services.router_state_manager import write_router_state, get_router_state

logger = get_logger('services.router_setup')
router_connection_manager = RouterConnectionManager()

# --- NFTABLES AND TC CONSTANTS ---
NFT_TABLE_NAME = "netpilot"
WHITELIST_DEVICES_CHAIN = "whitelist_devices"
WHITELIST_LIMIT_CHAIN = "whitelist_limit"
BLACKLIST_CHAIN = "blacklist"
GATE_CHAIN = "gate"
LAN_INTERFACE = "br-lan"

def _execute_command(command: str):
    """
    Executes a command on the router. For nft commands, idempotency is handled
    by ignoring 'already exists' errors.
    For tc, we also check for specific "already exists" errors.
    """
    full_command = f"nft {command}"
    if command.strip().startswith("tc"):
        full_command = command

    _, err = router_connection_manager.execute(full_command, timeout=10)

    # Idempotency checks for both tc and nft
    if err:
        error_lower = err.lower()
        # Allow 'file exists' and similar harmless errors, but treat syntax issues as real
        if "syntax error" in error_lower:
            logger.error(f"Syntax error while running: {full_command} — {err}")
            return False
        # Other idempotency messages
        error_lower = err.lower()
        if "file exists" in error_lower or \
           "exclusivity flag on" in error_lower or \
           "object already exists" in error_lower:
            logger.debug(f"Component already exists, command skipped: {full_command}")
            return True # This is not an error, it's idempotent success.

    # Generic error handling for other issues
    if err and "Error:" in err:
        logger.error(f"Command '{full_command}' failed with error: {err}")
        return False
    return True

def _ensure_state_file_exists():
    """Create the default state file on the router if it does not already exist."""
    STATE_FILE_PATH = "/etc/config/netpilot_state.json"
    # Use shell test to check for file existence on the router.
    out, _ = router_connection_manager.execute(f"[ -f {STATE_FILE_PATH} ] && echo exists || echo missing")
    if out.strip() == "missing":
        logger.info("State file missing on router – creating default state file")
        from services.router_state_manager import _get_default_state  # local import to avoid circular
        write_router_state(_get_default_state())

def setup_router_infrastructure():
    """
    Sets up the necessary nftables and tc configurations for all NetPilot
    functionalities. This function is idempotent and clears legacy iptables rules.
    """
    logger.info("Setting up router infrastructure using nftables...")

    # Ensure state file exists first, before we try to read rates from it
    _ensure_state_file_exists()

    # --- Legacy Cleanup ---
    # Forcefully remove all old iptables chains. Errors are ignored as they may not exist.
    legacy_chains = ["NETPILOT_GATE", "NETPILOT_WHITELIST", "NETPILOT_WL_DEVICES", "NETPILOT_WL_LIMIT", "NETPILOT_BLACKLIST"]
    router_connection_manager.execute(f"iptables -t mangle -D PREROUTING -j NETPILOT_GATE || true")
    for chain in legacy_chains:
        router_connection_manager.execute(f"iptables -t mangle -F {chain} || true")
        router_connection_manager.execute(f"iptables -t mangle -X {chain} || true")

    # --- NFTABLES SETUP ---
    # Constants for marks
    WHITELIST_LIMITED_MARK = "0x1e"  # 30
    BLACKLIST_MARK = "0xa"          # 10
    LIMITED_RATE_CLASSID = "1:12"
    
    # 1. Create the main table and base chains for NetPilot if they don't exist.
    if not _execute_command(f"add table inet {NFT_TABLE_NAME}"):
        return False, "Failed to create nft table"
    if not _execute_command(f"add chain inet {NFT_TABLE_NAME} {GATE_CHAIN} '{{ type filter hook prerouting priority mangle; }}'"):
        return False, "Failed to create gate chain"
    if not _execute_command(f"add chain inet {NFT_TABLE_NAME} {WHITELIST_DEVICES_CHAIN}"):
        return False, "Failed to create whitelist_devices chain"
    if not _execute_command(f"add chain inet {NFT_TABLE_NAME} {WHITELIST_LIMIT_CHAIN}"):
        return False, "Failed to create whitelist_limit chain"
    if not _execute_command(f"add chain inet {NFT_TABLE_NAME} {BLACKLIST_CHAIN}"):
        return False, "Failed to create blacklist chain"

    # 2. Add the permanent rate-limiting rule to the whitelist limit chain.
    # This chain should only mark packets that haven't been accepted by whitelist_devices
    # Since whitelisted devices use "accept" in whitelist_devices, this chain only sees non-whitelisted traffic
    if not _execute_command(f"add rule inet {NFT_TABLE_NAME} {WHITELIST_LIMIT_CHAIN} meta mark set {WHITELIST_LIMITED_MARK}"):
        return False, "Failed to add rate-limit rule"

    # --- TC SETUP (using rates from state file) ---
    # Get current state to use proper rates
    state = get_router_state()
    default_limited_rate = state['rates']['whitelist_limited']  # Default is 50mbit
    
    # 3. Setup base TC qdisc and classes
    if not _execute_command(f"tc qdisc add dev {LAN_INTERFACE} root handle 1: htb default 11"):
        return False, "Failed to add root qdisc"
    if not _execute_command(f"tc class add dev {LAN_INTERFACE} parent 1: classid 1:11 htb rate 1000mbit"):
        return False, "Failed to add tc full-speed class"
    if not _execute_command(f"tc class add dev {LAN_INTERFACE} parent 1: classid {LIMITED_RATE_CLASSID} htb rate {default_limited_rate}"):
        return False, "Failed to add tc limited class"

    # 4. Add TC filters to connect firewall marks to tc classes
    # Handle 30 (0x1e) = whitelisted devices that should be limited -> goes to limited class
    if not _execute_command(f"tc filter add dev {LAN_INTERFACE} parent 1: protocol ip prio 2 handle 30 fw flowid {LIMITED_RATE_CLASSID}"):
        return False, "Failed to add tc whitelist limited filter"
    # Handle 10 (0xa) = blacklisted devices -> goes to limited class  
    if not _execute_command(f"tc filter add dev {LAN_INTERFACE} parent 1: protocol ip prio 1 handle 10 fw flowid {LIMITED_RATE_CLASSID}"):
        return False, "Failed to add tc blacklist filter"
    # Default traffic (mark 0) and whitelisted devices should go to unlimited class 1:11 automatically via HTB default

    logger.info("Router infrastructure setup complete.")

    # Ensure state file is present
    _ensure_state_file_exists()
    return True, None 