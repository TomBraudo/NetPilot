from flask import Blueprint, request, jsonify, current_app, g
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
import time

logger = get_logger('session.endpoints')

session_bp = Blueprint('session', __name__)

def _setup_persistent_infrastructure():
    """
    Set up one-time persistent infrastructure:
    - TC infrastructure on all interfaces (same for both whitelist and blacklist)
    - Empty iptables chains (NETPILOT_WHITELIST, NETPILOT_BLACKLIST)
    - State file initialization
    
    This is the optimized part that only needs to be done once per session.
    """
    from managers.router_connection_manager import RouterConnectionManager
    from services.router_state_manager import write_router_state, get_router_state, _get_default_state
    
    router_connection_manager = RouterConnectionManager()
    
    def _execute_command(command: str):
        """Execute command with proper error handling."""
        _, err = router_connection_manager.execute(command, timeout=15)
        if err:
            error_lower = err.lower()
            if any(phrase in error_lower for phrase in [
                "file exists", "already exists", "cannot find", 
                "no such file", "chain already exists", "no chain/target/match",
                "bad rule", "does not exist"
            ]):
                return True
            logger.error(f"Command failed: {command} - Error: {err}")
            return False
        return True
    
    try:
        # 1. Ensure state file exists
        STATE_FILE_PATH = "/etc/config/netpilot_state.json"
        output, _ = router_connection_manager.execute(f"[ -f {STATE_FILE_PATH} ] && echo exists || echo missing")
        if output.strip() == "missing":
            logger.info("Creating default state file")
            write_router_state(_get_default_state())
        
        state = get_router_state()
        unlimited_rate = state['rates'].get('whitelist_full', '1000mbit')
        limited_rate = state['rates'].get('whitelist_limited', '50mbit')
        
        # 2. Get all network interfaces
        output, error = router_connection_manager.execute("ls /sys/class/net/")
        if error:
            return False, f"Failed to get network interfaces: {error}"
        
        interfaces = [iface.strip() for iface in output.split() if iface.strip() not in ['lo', '']]
        if not interfaces:
            return False, "No network interfaces found"
        
        logger.info(f"Setting up TC infrastructure on {len(interfaces)} interfaces")
        
        # 3. Set up TC infrastructure on all interfaces (one-time setup)
        for interface in interfaces:
            # Clean any existing TC setup first
            _execute_command(f"tc qdisc del dev {interface} root 2>/dev/null || true")
            
            # Set up HTB qdisc with default class (unlimited)
            if not _execute_command(f"tc qdisc add dev {interface} root handle 1: htb default 1"):
                return False, f"Failed to set up TC root qdisc on {interface}"
            
            # Class 1:1 - Unlimited traffic (default)
            if not _execute_command(f"tc class add dev {interface} parent 1: classid 1:1 htb rate {unlimited_rate}"):
                return False, f"Failed to set up unlimited class on {interface}"
            
            # Class 1:10 - Limited traffic 
            if not _execute_command(f"tc class add dev {interface} parent 1: classid 1:10 htb rate {limited_rate}"):
                return False, f"Failed to set up limited class on {interface}"
            
            # Filters for packet marking (same for both modes)
            if not _execute_command(f"tc filter add dev {interface} parent 1: protocol ip prio 1 handle 1 fw flowid 1:1"):
                return False, f"Failed to add unlimited filter on {interface}"
            
            if not _execute_command(f"tc filter add dev {interface} parent 1: protocol ip prio 2 handle 98 fw flowid 1:10"):
                return False, f"Failed to add limited filter on {interface}"
        
        # 4. Create empty iptables chains (will be populated by mode activation)
        _execute_command("iptables -t mangle -N NETPILOT_WHITELIST 2>/dev/null || true")
        _execute_command("iptables -t mangle -N NETPILOT_BLACKLIST 2>/dev/null || true")
        
        # 5. Clean up any legacy infrastructure
        _execute_command("nft delete table inet netpilot 2>/dev/null || true")
        
        logger.info(f"Persistent infrastructure set up successfully on {len(interfaces)} interfaces")
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to set up persistent infrastructure: {str(e)}")
        return False, f"Infrastructure setup failed: {str(e)}"

def _check_existing_infrastructure():
    """
    Check if the required NetPilot infrastructure is already set up:
    - TC classes on interfaces 
    - Iptables chains (NETPILOT_WHITELIST, NETPILOT_BLACKLIST)
    - State file existence
    
    Returns:
        tuple: (bool, str) - (True if all infrastructure exists, error message if not)
    """
    from managers.router_connection_manager import RouterConnectionManager
    from services.router_state_manager import get_router_state
    
    router_connection_manager = RouterConnectionManager()
    
    try:
        # 1. Check state file
        STATE_FILE_PATH = "/etc/config/netpilot_state.json"
        output, _ = router_connection_manager.execute(f"[ -f {STATE_FILE_PATH} ] && echo exists || echo missing")
        if output.strip() == "missing":
            logger.info("State file missing - infrastructure setup needed")
            return False, "State file not found"
        
        # 2. Check if iptables chains exist
        output, _ = router_connection_manager.execute("iptables -t mangle -L NETPILOT_WHITELIST -n 2>/dev/null && echo exists || echo missing")
        if output.strip() == "missing":
            logger.info("NETPILOT_WHITELIST chain missing - infrastructure setup needed")
            return False, "Iptables chains not found"

        output, _ = router_connection_manager.execute("iptables -t mangle -L NETPILOT_BLACKLIST -n 2>/dev/null && echo exists || echo missing")
        if output.strip() == "missing":
            logger.info("NETPILOT_BLACKLIST chain missing - infrastructure setup needed")
            return False, "Iptables chains not found"
        
        # 3. Check at least one interface has TC setup (we assume if one has it, all do)
        output, _ = router_connection_manager.execute("ls /sys/class/net/")
        interfaces = [iface.strip() for iface in output.split() if iface.strip() not in ['lo', '']]
        
        if interfaces:
            # Check the first interface that's not loopback
            test_interface = interfaces[0]
            output, _ = router_connection_manager.execute(f"tc class show dev {test_interface} | grep '1:1\|1:10' | wc -l")
            if not output.strip() or int(output.strip()) < 2:  # We expect at least 2 classes (1:1 and 1:10)
                logger.info(f"TC classes missing on {test_interface} - infrastructure setup needed")
                return False, "TC setup incomplete"
        else:
            return False, "No network interfaces found"
        
        logger.info("All required infrastructure found - skipping setup")
        return True, None
        
    except Exception as e:
        logger.error(f"Error checking existing infrastructure: {str(e)}")
        return False, f"Infrastructure check failed: {str(e)}"

@session_bp.route("/start", methods=["POST"])
def start_session():
    """
    Starts a new session for a router and sets up the required infrastructure.
    This endpoint now requires the session context from the middleware.
    """
    execution_start_time = time.time()
    
    # The session context (g.session_id, g.router_id) is now expected to be set
    # by the session_context_middleware before this function is called.
    logger = current_app.logger
    
    # Get the restart flag from JSON body
    data = request.get_json() or {}
    restart = data.get('restart', False)
    
    logger.info(f"Attempting to start session for router {g.router_id} with session ID {g.session_id} (restart={restart})")

    # If the session is already active, reject the request.
    if current_app.router_connection_manager.get_session_status(g.session_id):
        logger.warning(f"Session {g.session_id} is already active – rejecting start request")
        return build_error_response("Session is already active", 400, "SESSION_ALREADY_ACTIVE", execution_start_time)

    # 1. Mark the session as active in the RouterConnectionManager first.
    current_app.router_connection_manager.start_session(g.session_id)

    # 2. Set up one-time persistent infrastructure (TC and empty chains)
    logger.info("Setting up one-time persistent infrastructure...")
    
    try:
        # Test basic connectivity with short timeout
        output, err = current_app.router_connection_manager.execute("echo 'NetPilot ping'", timeout=5)
        if err:
            logger.error(f"Router reachability check failed: {err}")
            return build_error_response(f"Router not reachable: {err}", 500, "ROUTER_UNREACHABLE", execution_start_time)
        
        # Check existing infrastructure first
        infrastructure_exists, infra_error = _check_existing_infrastructure()
        
        # Only set up infrastructure if it doesn't exist OR if restart flag is True
        if infrastructure_exists and not restart:
            logger.info("Existing infrastructure found - skipping setup (restart=False)")
        else:
            if restart:
                logger.info("Restart flag set - rebuilding infrastructure")
            else:
                logger.info(f"Required infrastructure not found - setting up (error: {infra_error})")
                
            # Set up persistent infrastructure
            success_status, error_msg = _setup_persistent_infrastructure()
            if not success_status:
                logger.error(f"Failed to set up persistent infrastructure: {error_msg}")
                return build_error_response(f"Infrastructure setup failed: {error_msg}", 500, "INFRASTRUCTURE_SETUP_FAILED", execution_start_time)
        
        logger.info(f"Session established successfully for router {g.router_id} with persistent infrastructure")
        return build_success_response({
            "session_id": g.session_id,
            "router_reachable": True,
            "infrastructure_ready": True,
            "message": "Session established successfully"
        }, execution_start_time), 201  # 201 Created for successful session start
        
    except Exception as e:
        logger.error(f"Session setup failed: {str(e)}")
        return build_error_response(f"Session setup failed: {str(e)}", 500, "SESSION_SETUP_FAILED", execution_start_time)

@session_bp.route("/end", methods=["POST"])
def end_session():
    """
    Ends the session for a router, cleaning up its connections.
    """
    execution_start_time = time.time()
    logger = current_app.logger
    logger.info(f"Ending session {g.session_id} for router {g.router_id}")
    
    current_app.router_connection_manager.end_session(g.session_id)
    
    return build_success_response({"message": "Session ended"}, execution_start_time)

@session_bp.route("/refresh", methods=["POST"])
def refresh_session():
    """Refreshes a session's activity timer."""
    execution_start_time = time.time()
    data = request.get_json()
    session_id = data.get('sessionId') if data else None
    if not session_id:
        return build_error_response("sessionId is required", 400, "MISSING_SESSION_ID", execution_start_time)

    try:
        refreshed = current_app.router_connection_manager.refresh_session(session_id)
        if refreshed:
            logger.info(f"Session refreshed: {session_id}")
            return build_success_response({"message": f"Session {session_id} refreshed"}, execution_start_time)
        else:
            logger.warning(f"Attempted to refresh non-existent session: {session_id}")
            return build_error_response("Session not found", 404, "SESSION_NOT_FOUND", execution_start_time)
    except Exception as e:
        logger.error(f"Error refreshing session {session_id}: {e}", exc_info=True)
        return build_error_response(str(e), 500, "SESSION_REFRESH_ERROR", execution_start_time)

@session_bp.route("/status", methods=["GET"])
def get_all_sessions_status():
    """
    Retrieves the status of all active sessions being managed.
    This is an admin-level endpoint and does not require session context.
    """
    execution_start_time = time.time()
    status = current_app.router_connection_manager.get_all_sessions_status()
    return build_success_response({"message": "Retrieved all session statuses", "sessions": status}, execution_start_time)