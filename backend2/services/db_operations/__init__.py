"""
Database Operations Module

Provides shared database session management and utilities for all DB operations.
This module centralizes database access patterns and ensures consistent session handling
across all database operation services.

Available Services:
- base: Core database utilities and session management

Usage:
    from services.db_operations import get_whitelist, add_device_to_whitelist
    from services.db_operations.base import get_db_session, with_db_session
"""

# Import base utilities for external use
from .base import (
    get_db_session,
    safe_dict_conversion,
    validate_uuid,
    handle_db_errors
)

# Removed whitelist DB operations

# Import network operations
from .network_db import (
    save_network_scan_result
)

# Define what's available when importing from this module
__all__ = [
    # Base utilities
    'get_db_session',
    'with_db_session',
    'safe_dict_conversion',
    'validate_uuid',
    'handle_db_errors',
    
    # Removed whitelist operations
    
    # Network operations
    'save_network_scan_result',
]
