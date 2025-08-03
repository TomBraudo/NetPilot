"""
Command type enumeration for router operations
"""

from enum import Enum


class CommandType(Enum):
    """Enumeration for different types of router commands"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
