"""
TimeBasedPolicy dataclass for NetPilot Commands-Server Groups

Time-sensitive policy overrides (handled by commands-server cron).
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from .policy_action import PolicyAction


@dataclass
class TimeBasedPolicy:
    """Time-sensitive policy overrides (handled by commands-server cron)"""
    name: str
    start_time: str  # "22:00"
    end_time: str    # "08:00" 
    days: List[str]  # ["monday", "tuesday", ...]
    action: PolicyAction
    parameters: Dict[str, Any]
    active: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "days": self.days,
            "action": self.action.value,  # Convert enum to string
            "parameters": self.parameters,
            "active": self.active
        }
