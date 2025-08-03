"""
AccessControlPolicy dataclass for NetPilot Commands-Server Groups

Website and content filtering policies.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class AccessControlPolicy:
    """Website and content filtering"""
    blocked_sites: List[str] = field(default_factory=list)
    blocked_categories: List[str] = field(default_factory=list)  
    allowed_sites_only: List[str] = field(default_factory=list)
    block_all_internet: bool = False
    active: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "blocked_sites": self.blocked_sites,
            "blocked_categories": self.blocked_categories,
            "allowed_sites_only": self.allowed_sites_only,
            "block_all_internet": self.block_all_internet,
            "active": self.active
        }
