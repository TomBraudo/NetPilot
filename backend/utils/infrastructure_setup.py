"""
Infrastructure setup utilities for NetPilot router configuration.

This module contains functions for setting up and checking the persistent
infrastructure required for NetPilot's traffic management system.
"""

from enum import Enum
from utils.logging_config import get_logger

logger = get_logger('infrastructure_setup')


class InfrastructureComponent(Enum):
    """Minimal infra: monitoring only (nlbwmon daily tracking)."""
    MONITORING_SETUP = "monitoring_setup"


def _execute_command_with_router_manager(router_connection_manager, command: str):
    """Execute command with proper error handling using the provided router connection manager."""
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


def _setup_state_file(router_connection_manager):
    """Deprecated: state file not used in headless mode."""
    return True


def _setup_iptables_chains(router_connection_manager, setup_whitelist=True, setup_blacklist=True):
    """Deprecated: iptables chains not used (nft-qos only)."""
    return True


def _setup_tc_infrastructure(router_connection_manager, interfaces, unlimited_rate, limited_rate):
    """Deprecated: tc infrastructure not used (nft-qos only)."""
    return True


def _cleanup_legacy_infrastructure(router_connection_manager):
    """Deprecated: clean router assumed. No legacy cleanup."""
    return True


def _get_network_interfaces(router_connection_manager):
    """Deprecated: not needed for nft-qos-only path."""
    return [], None


def setup_persistent_infrastructure(missing_components=None):
    """
    Set up one-time persistent infrastructure:
    - TC infrastructure on all interfaces (same for both whitelist and blacklist)
    - Empty iptables chains (NETPILOT_WHITELIST, NETPILOT_BLACKLIST)
    - State file initialization
    
    This is the optimized part that only needs to be done once per session.
    Only sets up components that are specified in the missing_components list.
    
    Args:
        missing_components: List of InfrastructureComponent enums indicating which components need setup.
                          If None, all components will be set up (backward compatibility).
    
    Returns:
        tuple: (bool, str) - (True if successful, error message if failed)
    """
    from managers.router_connection_manager import RouterConnectionManager
    # Only monitoring is supported now
    if missing_components is None:
        missing_components = [InfrastructureComponent.MONITORING_SETUP]
    
    router_connection_manager = RouterConnectionManager()
    
    try:
        # Only monitoring infrastructure (ensure nlbwmon running, daily interval, retention<=35)
        if InfrastructureComponent.MONITORING_SETUP in missing_components:
            logger.info("Ensuring nlbwmon is installed, enabled, and running")
            router_connection_manager.execute("opkg update >/dev/null 2>&1 || true")
            router_connection_manager.execute("opkg status nlbwmon >/dev/null 2>&1 || opkg install -y nlbwmon >/dev/null 2>&1")
            router_connection_manager.execute("/etc/init.d/nlbwmon enable >/dev/null 2>&1 || true")
            router_connection_manager.execute("/etc/init.d/nlbwmon start >/dev/null 2>&1 || /etc/init.d/nlbwmon restart >/dev/null 2>&1 || true")

            logger.info("Configuring nlbwmon database_interval for daily tracking (YYYY-MM-DD/1)")
            router_connection_manager.execute("TODAY=$(date +%F); uci set nlbwmon.@nlbwmon[0].database_interval=\"$TODAY/1\" 2>/dev/null || true")
            router_connection_manager.execute("uci commit nlbwmon >/dev/null 2>&1 || true")
            router_connection_manager.execute("/etc/init.d/nlbwmon restart >/dev/null 2>&1 || true")

            # Enforce retention: keep at most 35 database files
            logger.info("Enforcing nlbwmon database retention (<=35 files)")
            out, _ = router_connection_manager.execute("uci -q get nlbwmon.@nlbwmon[0].database_directory | cat")
            db_dir = out.strip() if out else "/var/lib/nlbwmon"
            router_connection_manager.execute(f"mkdir -p {db_dir} >/dev/null 2>&1 || true")
            prune_cmd = (
                f"sh -c 'set -e; d={db_dir}; "
                "[ -d \"$d\" ] || exit 0; "
                "cnt=$(ls -1 \"$d\" 2>/dev/null | wc -l); "
                "if [ \"$cnt\" -gt 35 ]; then ls -1t \"$d\" 2>/dev/null | tail -n +36 | xargs -r -I{} sh -c \"rm -f \"$d\"/\"{}\"\"; fi'"
            )
            router_connection_manager.execute(prune_cmd)
        else:
            logger.info("Monitoring infrastructure is already set up correctly - skipping")
        
        # Log success message
        setup_components = [comp.value for comp in missing_components]
        if setup_components:
            logger.info(f"Infrastructure setup completed for components: {', '.join(setup_components)}")
        else:
            logger.info("No infrastructure setup needed - all components are already correct")
        
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to set up persistent infrastructure: {str(e)}")
        return False, f"Infrastructure setup failed: {str(e)}"


def check_existing_infrastructure():
    """
    Check if the required NetPilot infrastructure is already set up:
    - State file in new group-based format
    - TC classes on interfaces 
    - Iptables chains (NETPILOT_WHITELIST, NETPILOT_BLACKLIST)
    
    Returns:
        tuple: (bool, list[InfrastructureComponent], str) - (
            True if all infrastructure exists,
            list of missing/incorrect components,
            descriptive message
        )
    """
    from managers.router_connection_manager import RouterConnectionManager
    router_connection_manager = RouterConnectionManager()
    missing_components = []
    issues = []

    try:
        # 1) Verify nlbwmon running
        out, _ = router_connection_manager.execute("/etc/init.d/nlbwmon status 2>/dev/null | grep -qi running && echo running || echo stopped")
        if (out or '').strip() != 'running':
            missing_components.append(InfrastructureComponent.MONITORING_SETUP)
            issues.append("nlbwmon not running")

        # 2) Verify daily database_interval (YYYY-MM-DD/1)
        di_out, _ = router_connection_manager.execute("uci -q get nlbwmon.@nlbwmon[0].database_interval | cat")
        di_val = (di_out or '').strip()
        import re as _re
        if not di_val or not _re.match(r"^\d{4}-\d{2}-\d{2}/1$", di_val):
            if InfrastructureComponent.MONITORING_SETUP not in missing_components:
                missing_components.append(InfrastructureComponent.MONITORING_SETUP)
            issues.append("database_interval not set to daily (YYYY-MM-DD/1)")

        # 3) Verify retention <= 35
        dir_out, _ = router_connection_manager.execute("uci -q get nlbwmon.@nlbwmon[0].database_directory | cat")
        db_dir = dir_out.strip() if dir_out else "/var/lib/nlbwmon"
        cnt_out, _ = router_connection_manager.execute(f"ls -1 \"{db_dir}\" 2>/dev/null | wc -l")
        try:
            cnt = int((cnt_out or '0').strip())
        except Exception:
            cnt = 0
        if cnt > 35:
            if InfrastructureComponent.MONITORING_SETUP not in missing_components:
                missing_components.append(InfrastructureComponent.MONITORING_SETUP)
            issues.append(f"database files count {cnt} exceeds 35")

        if not missing_components:
            logger.info("Monitoring OK")
            return True, [], "Monitoring OK"
        else:
            component_names = [comp.value for comp in missing_components]
            message = f"Missing or incorrect components: {', '.join(component_names)}. Issues: {'; '.join(issues)}"
            return False, missing_components, message

    except Exception as e:
        logger.error(f"Error checking existing infrastructure: {str(e)}")
        return False, [InfrastructureComponent.MONITORING_SETUP], f"Infrastructure check failed: {str(e)}"
