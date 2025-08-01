"""
Commands Server Operations Module

Provides commands server communication and operations for router management.
This module centralizes commands server interactions and ensures consistent
communication patterns across all commands server operation services.

Architecture Pattern:
This module is part of a 3-layer service architecture:
1. services/<service>.py - Main service orchestration (calls db + commands)
2. services/db_operations/<service>_db.py - Database operations
3. services/commands-server_operations/<service>_execute.py - Router command execution

Available Services:
- whitelist_execute: Whitelist router command operations
- session_execute: Session router command operations
- base: Core commands server utilities and communication management

Usage:
    from services.commands_server_operations import execute_whitelist_enable, execute_start_session
    from services.commands_server_operations.base import with_commands_server, handle_commands_errors
    
Example Implementation:
    @with_commands_server
    @handle_commands_errors("Enable whitelist mode")
    def execute_whitelist_enable(commands_server, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        return commands_server.execute_router_command(router_id, session_id, "whitelist", "enable")
"""

# Import base utilities for external use
from .base import (
    with_commands_server,
    handle_commands_errors,
    validate_router_connection,
    format_command_response,
    log_command_execution
)

# Import whitelist operations
from .whitelist_execute import (
    execute_get_whitelist,
    execute_add_device_to_whitelist,
    execute_remove_device_from_whitelist,
    execute_set_whitelist_rate_limit,
    execute_activate_whitelist_mode,
    execute_deactivate_whitelist_mode
)

# Import network operations
from .network_execute import (
    execute_scan_network
)

# Define what's available when importing from this module
__all__ = [
    # Base utilities
    'with_commands_server',
    'handle_commands_errors',
    'validate_router_connection',
    'format_command_response',
    'log_command_execution',
    
    # Whitelist operations
    'execute_get_whitelist',
    'execute_add_device_to_whitelist',
    'execute_remove_device_from_whitelist',
    'execute_set_whitelist_rate_limit',
    'execute_activate_whitelist_mode',
    'execute_deactivate_whitelist_mode',
    
    # Session operations
    'execute_start_session',
    'execute_end_session',
    'execute_refresh_session',
    
    # Network operations
    'execute_scan_network',

    # WiFi management operations
    'execute_get_wifi_name'
    'execute_update_wifi_name'
]
