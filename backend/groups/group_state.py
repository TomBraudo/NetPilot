"""
GroupState dataclass for NetPilot Commands-Server Groups

Minimal group state stored in commands-server state file.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List
from .device_info import DeviceInfo
from .group_policy_summary import GroupPolicySummary


@dataclass
class GroupState:
    """
    Minimal group state stored in commands-server state file
    
    TC Class and Bandwidth Policy:
    - Each group gets a unique tc_class (e.g., "1:101") and mark_value (e.g., 101)
    - If policies.bandwidth_limit_mbps = None: No TC rule is set, unrestricted traffic
    - If policies.bandwidth_limit_mbps = <number>: TC rule limits all group members to that Mbps
    """
    group_id: int
    name: str
    active: bool
    device_count: int  # Number of devices (for optimization)
    devices: List[DeviceInfo]  # Current devices with IP/MAC for verification
    tc_class: str  # e.g., "1:101"
    mark_value: int  # e.g., 101
    policies: GroupPolicySummary
    infrastructure_created: bool
    last_sync: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "group_id": self.group_id,
            "name": self.name,
            "active": self.active,
            "device_count": self.device_count,
            "devices": [device.to_dict() for device in self.devices],
            "tc_class": self.tc_class,
            "mark_value": self.mark_value,
            "policies": self.policies.to_dict(),
            "infrastructure_created": self.infrastructure_created,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None
        }
