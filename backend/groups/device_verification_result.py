"""
DeviceVerificationResult dataclass for NetPilot Commands-Server Groups

Result of device verification operations.
"""

from dataclasses import dataclass
from typing import List, Optional
from .device_info import DeviceInfo


@dataclass
class DeviceVerificationResult:
    """Result of device verification"""
    is_valid: bool
    added_devices: List[DeviceInfo]
    removed_devices: List[DeviceInfo]
    changed_devices: List[DeviceInfo]  # Devices with IP/MAC changes
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "is_valid": self.is_valid,
            "added_devices": [device.to_dict() for device in self.added_devices],
            "removed_devices": [device.to_dict() for device in self.removed_devices],
            "changed_devices": [device.to_dict() for device in self.changed_devices],
            "error_message": self.error_message
        }
