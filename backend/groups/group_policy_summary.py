"""
GroupPolicySummary dataclass for NetPilot Commands-Server Groups

Essential policy information for router operations.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GroupPolicySummary:
    """
    Essential policy information for router operations
    
    Bandwidth Policy Behavior:
    - bandwidth_limit_mbps = None: No TC rule is set, all packets flow through unrestricted
    - bandwidth_limit_mbps = <number>: TC rule and iptables forwarding are applied to limit 
      all group members to the specified Mbps value
    """
    bandwidth_limit_mbps: Optional[int] = None
    blocked_categories: List[str] = field(default_factory=list)
    blocked_sites: List[str] = field(default_factory=list)
    allowed_sites_only: List[str] = field(default_factory=list)
    block_all_internet: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "bandwidth_limit_mbps": self.bandwidth_limit_mbps,
            "blocked_categories": self.blocked_categories,
            "blocked_sites": self.blocked_sites,
            "allowed_sites_only": self.allowed_sites_only,
            "block_all_internet": self.block_all_internet
        }
