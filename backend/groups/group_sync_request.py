"""
GroupSyncRequest dataclass for NetPilot Commands-Server Groups

API request format from upper layer to commands-server.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from .bandwidth_policy import BandwidthPolicy
from .access_control_policy import AccessControlPolicy
from .time_based_policy import TimeBasedPolicy


@dataclass
class GroupSyncRequest:
    """API request format from upper layer to commands-server"""
    group_id: int
    name: str
    device_ips: List[str]  # Current device IPs for this group
    device_macs: List[str]  # Current device MACs for this group
    
    # Policy Components (sent from upper layer)
    bandwidth_policy: Optional[BandwidthPolicy] = None
    access_control_policy: Optional[AccessControlPolicy] = None
    time_based_policies: List[TimeBasedPolicy] = field(default_factory=list)
    
    active: bool = True
    force_sync: bool = False  # Force full sync even if no changes detected

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "group_id": self.group_id,
            "name": self.name,
            "device_ips": self.device_ips,
            "device_macs": self.device_macs,
            "bandwidth_policy": self.bandwidth_policy.to_dict() if self.bandwidth_policy else None,
            "access_control_policy": self.access_control_policy.to_dict() if self.access_control_policy else None,
            "time_based_policies": [policy.to_dict() for policy in self.time_based_policies],
            "active": self.active,
            "force_sync": self.force_sync
        }
