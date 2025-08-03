"""
PolicyAction enum for NetPilot Commands-Server Groups

Available actions for time-based policies.
"""

from enum import Enum


class PolicyAction(Enum):
    """Available actions for time-based policies"""
    BANDWIDTH_LIMIT = "bandwidth_limit"
    BLOCK_INTERNET = "block_internet"
    ACTIVATE_BLACKLIST = "activate_blacklist"
    BLOCK_SITES = "block_sites"
    ALLOW_SITES_ONLY = "allow_sites_only"
