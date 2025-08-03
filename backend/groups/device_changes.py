"""
DeviceChanges dataclass for NetPilot Commands-Server Groups

Device changes between current and new state.
"""

from dataclasses import dataclass
from typing import List, Tuple
from .device_info import DeviceInfo


@dataclass
class DeviceChanges:
    """Device changes between current and new state"""
    added: List[DeviceInfo]
    removed: List[DeviceInfo] 
    ip_changed: List[Tuple[DeviceInfo, DeviceInfo]]  # (old, new)
    mac_changed: List[Tuple[DeviceInfo, DeviceInfo]]  # (old, new)
    unchanged: List[DeviceInfo]

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "added": [device.to_dict() for device in self.added],
            "removed": [device.to_dict() for device in self.removed],
            "ip_changed": [{"old": old.to_dict(), "new": new.to_dict()} for old, new in self.ip_changed],
            "mac_changed": [{"old": old.to_dict(), "new": new.to_dict()} for old, new in self.mac_changed],
            "unchanged": [device.to_dict() for device in self.unchanged]
        }
