"""
BandwidthPolicy dataclass for NetPilot Commands-Server Groups

Traffic shaping policies.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BandwidthPolicy:
    """Traffic shaping policies"""
    limit_mbps: int
    burst_mbps: Optional[int] = None
    active: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "limit_mbps": self.limit_mbps,
            "burst_mbps": self.burst_mbps,
            "active": self.active
        }
