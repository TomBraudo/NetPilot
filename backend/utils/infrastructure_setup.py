"""
Infrastructure setup utilities for NetPilot router configuration.

This module contains functions for setting up and checking the persistent
infrastructure required for NetPilot's traffic management system.
"""

from enum import Enum
from utils.logging_config import get_logger

logger = get_logger('infrastructure_setup')


class InfrastructureComponent(Enum):
    """Infrastructure components for NetPilot."""
    MONITORING_SETUP = "monitoring_setup"
    AGH_CATEGORIES_SETUP = "agh_categories_setup"
    TIME_BASED_SCRIPTS_SETUP = "time_based_scripts_setup"


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


def _setup_agh_default_categories(router_connection_manager):
    """
    Set up default AGH categories if they don't exist on the router.
    
    This function:
    1. Ensures the AGH categories directory exists on the router
    2. Checks which default categories are missing
    3. Copies default category files for missing categories only
    4. Never overwrites existing category files (preserves user customizations)
    
    Args:
        router_connection_manager: RouterConnectionManager instance
    
    Returns:
        bool: True if successful, False if failed
    """
    import os
    import tempfile
    
    # Category directory on router (from agh_service/common.py)
    CATEGORY_DIR = "/opt/AdGuardHome/categories"
    
    # Default categories to set up
    default_categories = [
        "social_media",
        "entertainment", 
        "gaming",
        "adult_gambling"
    ]
    
    try:
        # Ensure category directory exists on router
        logger.info(f"Ensuring AGH category directory exists: {CATEGORY_DIR}")
        _, err = router_connection_manager.execute(f"mkdir -p {CATEGORY_DIR} 2>/dev/null || true")
        if err:
            logger.error(f"Failed to create AGH category directory: {err}")
            return False
        
        # Check which categories already exist on router
        existing_categories = []
        out, _ = router_connection_manager.execute(f"ls -1 {CATEGORY_DIR}/*.txt 2>/dev/null | xargs -r basename -s .txt | cat")
        if out:
            existing_categories = [cat.strip() for cat in out.splitlines() if cat.strip()]
        
        logger.info(f"Found existing categories on router: {existing_categories}")
        
        # Determine which categories need to be created
        categories_to_create = [cat for cat in default_categories if cat not in existing_categories]
        
        if not categories_to_create:
            logger.info("All default AGH categories already exist - no setup needed")
            return True
            
        logger.info(f"Creating missing default categories: {categories_to_create}")
        
        # Get path to default category files
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_categories_dir = os.path.join(os.path.dirname(current_dir), 'services', 'agh_service', 'default_categories')
        logger.info(f"Looking for default category files in: {default_categories_dir}")
        
        if not os.path.exists(default_categories_dir):
            logger.error(f"Default categories directory does not exist: {default_categories_dir}")
            return False
        
        # Copy each missing category file
        for category in categories_to_create:
            local_file_path = os.path.join(default_categories_dir, f"{category}.txt")
            remote_file_path = f"{CATEGORY_DIR}/{category}.txt"
            
            if not os.path.exists(local_file_path):
                logger.warning(f"Default category file not found: {local_file_path}")
                continue
                
            logger.info(f"Copying default category file: {category}.txt (size: {os.path.getsize(local_file_path)} bytes)")
            try:
                # Use simple content-based copy approach - read file and write via SSH command
                with open(local_file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read().strip()
                
                # Create the file using heredoc - this handles all special characters safely
                # This is much more reliable than complex SFTP operations
                copy_command = f"""cat > {remote_file_path} << 'EOF_NETPILOT'
{file_content}
EOF_NETPILOT"""
                
                copy_out, copy_err = router_connection_manager.execute(copy_command, timeout=10)
                if copy_err:
                    logger.error(f"Failed to copy category file {category}.txt: {copy_err}")
                    return False
                
                # Verify the file was created and has content
                verify_out, verify_err = router_connection_manager.execute(f"[ -s {remote_file_path} ] && echo 'ok' || echo 'fail'", timeout=5)
                if verify_err or (verify_out or '').strip() != 'ok':
                    logger.error(f"Category file {category}.txt was not successfully created or is empty")
                    return False
                    
                logger.info(f"Successfully created default category: {category}")
                
            except Exception as copy_exception:
                logger.error(f"Exception during copy of {category}.txt: {str(copy_exception)}")
                return False
            
        logger.info("AGH default categories setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to set up AGH default categories: {str(e)}")
        return False


def _setup_time_based_scripts(router_connection_manager):
    """Ensure /root/netlimit exists and required scripts are installed on the router.

    Scripts:
        - add_devices.sh
        - del_devices.sh
        - update_firewall.sh

    Returns:
        bool: True on success, False on failure
    """
    import os

    NETLIMIT_DIR = "/root/netlimit"
    required_scripts = [
        "add_devices.sh",
        "del_devices.sh",
        "update_firewall.sh",
    ]

    try:
        # Ensure directory exists and has restrictive permissions
        logger.info(f"Ensuring netlimit directory exists: {NETLIMIT_DIR}")
        router_connection_manager.execute(f"mkdir -p {NETLIMIT_DIR} >/dev/null 2>&1 || true")
        router_connection_manager.execute(f"chmod 700 {NETLIMIT_DIR} >/dev/null 2>&1 || true")

        # Local scripts directory (backend/services/time_based_scripts)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(os.path.dirname(current_dir), 'services', 'time_based_scripts')
        if not os.path.isdir(scripts_dir):
            logger.error(f"Time-based scripts directory not found: {scripts_dir}")
            return False

        # Copy any missing or zero-size scripts
        from managers.router_connection_manager import RouterConnectionManager
        rcm = RouterConnectionManager()

        for script in required_scripts:
            local_path = os.path.join(scripts_dir, script)
            remote_path = f"{NETLIMIT_DIR}/{script}"

            if not os.path.isfile(local_path):
                logger.error(f"Local script missing: {local_path}")
                return False

            # Check if remote script exists and is non-empty
            out, _ = router_connection_manager.execute(f"[ -s {remote_path} ] && echo ok || echo missing")
            needs_copy = (out or '').strip() != 'ok'

            if needs_copy:
                logger.info(f"Copying script to router: {script}")
                success, copy_err = rcm.copy_file(local_path, remote_path, make_executable=True, normalize_crlf=True)
                if not success:
                    logger.error(f"Failed to copy {script}: {copy_err}")
                    return False
            else:
                logger.info(f"Script already present: {remote_path}")

        logger.info("Time-based scripts setup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to set up time-based scripts: {str(e)}")
        return False


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
    # Default to both monitoring and AGH categories setup
    if missing_components is None:
        missing_components = [
            InfrastructureComponent.MONITORING_SETUP,
            InfrastructureComponent.AGH_CATEGORIES_SETUP,
            InfrastructureComponent.TIME_BASED_SCRIPTS_SETUP,
        ]
    
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

        # AGH categories setup (ensure default categories exist)
        if InfrastructureComponent.AGH_CATEGORIES_SETUP in missing_components:
            logger.info("Setting up AGH default categories")
            success = _setup_agh_default_categories(router_connection_manager)
            if not success:
                return False, "AGH categories setup failed"
        else:
            logger.info("AGH categories infrastructure is already set up correctly - skipping")

        # Ensure time-based netlimit scripts exist on router
        if InfrastructureComponent.TIME_BASED_SCRIPTS_SETUP in missing_components:
            logger.info("Setting up time-based netlimit scripts on router")
            success = _setup_time_based_scripts(router_connection_manager)
            if not success:
                return False, "Time-based scripts setup failed"
        else:
            logger.info("Time-based scripts already present - skipping")
        
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

        # 4) Verify AGH default categories exist
        CATEGORY_DIR = "/opt/AdGuardHome/categories"
        default_categories = ["social_media", "entertainment", "gaming", "adult_gambling"]
        
        # Check if category directory exists
        cat_dir_out, _ = router_connection_manager.execute(f"[ -d {CATEGORY_DIR} ] && echo yes || echo no")
        if (cat_dir_out or '').strip() != 'yes':
            missing_components.append(InfrastructureComponent.AGH_CATEGORIES_SETUP)
            issues.append("AGH categories directory does not exist")
        else:
            # Check if default categories exist
            existing_cats_out, _ = router_connection_manager.execute(f"ls -1 {CATEGORY_DIR}/*.txt 2>/dev/null | xargs -r basename -s .txt | cat")
            existing_categories = [cat.strip() for cat in (existing_cats_out or '').splitlines() if cat.strip()]
            missing_default_categories = [cat for cat in default_categories if cat not in existing_categories]
            
            if missing_default_categories:
                if InfrastructureComponent.AGH_CATEGORIES_SETUP not in missing_components:
                    missing_components.append(InfrastructureComponent.AGH_CATEGORIES_SETUP)
                issues.append(f"missing default categories: {', '.join(missing_default_categories)}")

        # 5) Verify /root/netlimit dir and scripts
        NETLIMIT_DIR = "/root/netlimit"
        scripts_ok = True
        dir_out, _ = router_connection_manager.execute(f"[ -d {NETLIMIT_DIR} ] && echo yes || echo no")
        if (dir_out or '').strip() != 'yes':
            scripts_ok = False
            missing_components.append(InfrastructureComponent.TIME_BASED_SCRIPTS_SETUP)
            issues.append("netlimit directory missing")
        else:
            required_scripts = ["add_devices.sh", "del_devices.sh", "update_firewall.sh"]
            for s in required_scripts:
                chk_out, _ = router_connection_manager.execute(f"[ -s {NETLIMIT_DIR}/{s} ] && echo ok || echo missing")
                if (chk_out or '').strip() != 'ok':
                    scripts_ok = False
                    if InfrastructureComponent.TIME_BASED_SCRIPTS_SETUP not in missing_components:
                        missing_components.append(InfrastructureComponent.TIME_BASED_SCRIPTS_SETUP)
                    issues.append(f"missing script: {s}")

        if not missing_components:
            logger.info("All infrastructure components OK")
            return True, [], "All infrastructure components OK"
        else:
            component_names = [comp.value for comp in missing_components]
            message = f"Missing or incorrect components: {', '.join(component_names)}. Issues: {'; '.join(issues)}"
            return False, missing_components, message

    except Exception as e:
        logger.error(f"Error checking existing infrastructure: {str(e)}")
        return False, [InfrastructureComponent.MONITORING_SETUP, InfrastructureComponent.AGH_CATEGORIES_SETUP], f"Infrastructure check failed: {str(e)}"
