"""
DeviceInfo dataclass for NetPilot Commands-Server Groups

Device information stored in state file for group management.
"""

from dataclasses import dataclass


@dataclass
class DeviceInfo:
    """Device information stored in state file"""
    ip: str
    mac: str

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "ip": self.ip,
            "mac": self.mac
        }
