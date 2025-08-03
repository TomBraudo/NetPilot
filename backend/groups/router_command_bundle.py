"""
RouterCommandBundle dataclass for NetPilot Commands-Server Groups

Complete set of router commands for a group policy.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class RouterCommandBundle:
    """Complete set of router commands for a group policy"""
    group_id: int
    
    # Command categories
    tc_commands: List[str] = field(default_factory=list)
    iptables_commands: List[str] = field(default_factory=list)
    dns_commands: List[str] = field(default_factory=list)
    cron_commands: List[str] = field(default_factory=list)
    cleanup_commands: List[str] = field(default_factory=list)
    
    # Metadata
    requires_reboot: bool = False
    estimated_duration_ms: int = 0
    dependencies: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "group_id": self.group_id,
            "tc_commands": self.tc_commands,
            "iptables_commands": self.iptables_commands,
            "dns_commands": self.dns_commands,
            "cron_commands": self.cron_commands,
            "cleanup_commands": self.cleanup_commands,
            "requires_reboot": self.requires_reboot,
            "estimated_duration_ms": self.estimated_duration_ms,
            "dependencies": self.dependencies
        }
