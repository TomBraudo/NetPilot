"""
StateFileManager for NetPilot Commands-Server Groups

Bandwidth Policy Behavior:
- bandwidth_limit_mbps = None: No TC rule is set, all packets flow through unrestricted
- bandwidth_limit_mbps = <number>: TC rule and iptables forwarding are applied to limit 
  all group members to the specified Mbps value
- TC class and mark value are automatically calculated as: group_id + 100
"""

import json
import re
import ipaddress
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import g, has_request_context
from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager


class StateFileManager:
    """
    Singleton manager for the commands-server state file.
    Handles all state file operations with thread-safe access.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        # If we're in a Flask request context and have a request-scoped instance, use it
        if has_request_context() and hasattr(g, 'state_manager'):
            return g.state_manager
        
        # Otherwise, use singleton pattern for backward compatibility
        if cls._instance is None:
            cls._instance = super(StateFileManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if StateFileManager._initialized:
            return
            
        self.logger = get_logger('managers.state_file')
        self.router_connection_manager = RouterConnectionManager()
        self.state_file_path = "/etc/config/netpilot_groups_state.json"
        
        StateFileManager._initialized = True
        self.logger.info("StateFileManager singleton initialized")
    
    @classmethod
    def create_request_scoped_instance(cls):
        """
        Create a new instance for request scope, bypassing singleton pattern.
        This prevents race conditions in multi-router environments.
        """
        instance = super(StateFileManager, cls).__new__(cls)
        instance.logger = get_logger('managers.state_file')
        instance.router_connection_manager = RouterConnectionManager()
        instance.state_file_path = "/etc/config/netpilot_groups_state.json"
        return instance
    
    @staticmethod
    def get_state_manager():
        """
        Get the request-scoped StateFileManager instance from Flask's g object.
        This should be used instead of direct instantiation to ensure proper request isolation.
        
        Returns:
            StateFileManager: The request-scoped instance created during request setup
        """
        if has_request_context() and hasattr(g, 'state_manager'):
            return g.state_manager
        else:
            raise RuntimeError("No request-scoped StateFileManager found. Ensure Flask request context exists and state_manager is initialized.")
    
    def create_default_format(self) -> Dict[str, Any]:
        """
        1. Creates the default format, returns it as dict.
        
        Returns:
            Dict[str, Any]: Default state format with Group 0 (Guest Group)
        """
        return {
            "groups": {
                "0": {
                    "name": "Guest Group",
                    "active": True,
                    "device_count": 0,
                    "devices": [],
                    "policies": {
                        "bandwidth": {
                            "limit_mbps": None,
                            "tc_class": "1:100",
                            "mark_value": 100
                        },
                        "access_control": {
                            "blocked_categories": [],
                            "blocked_sites": [],
                            "allowed_sites_only": [],
                            "block_all_internet": False
                        },
                        "time_based": {
                            "from": None,
                            "to": None
                        }
                    },
                    "last_sync": None
                }
            }
        }
    
    def write_state_to_router(self, Optional[state: Dict[str, Any]]) -> bool:
        """
        2. Writes the given state dictionary to the JSON file on the router. 
        If no state is provided (None), writes the default format instead.

        Args:
            state (Optional[Dict[str, Any]]): State dictionary to write. If None, the default format will be used.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if state is None:
                state = self.create_default_format()
            json_content = json.dumps(state, indent=2)
            escaped_content = json_content.replace('"', '\\"').replace('$', '\\$')
            
            command = f'echo "{escaped_content}" > {self.state_file_path}'
            output, error = self.router_connection_manager.execute(command)
            
            if error:
                self.logger.error(f"Error writing state file: {error}")
                return False
            
            self.logger.debug("State file written to router successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Exception writing state file: {e}")
            return False
    
    def load_state_from_router(self) -> Optional[Dict[str, Any]]:
        """
        3. Gets the state file from the router, returns it as dict.
        
        Returns:
            Optional[Dict[str, Any]]: State dict if successful, None if file doesn't exist or is corrupted
        """
        try:
            command = f"cat {self.state_file_path}"
            output, error = self.router_connection_manager.execute(command)
            
            if error or not output.strip():
                self.logger.info("State file not found or empty")
                return None
            
            state = json.loads(output.strip())
            self.logger.info("State loaded successfully from router")
            return state
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse state file JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")
            return None
    
    def get_group_from_state(self, group_id: int) -> Optional[Dict[str, Any]]:
        """
        4. Gets the state file from (3), takes input groupId, and returns the group object as dict.
        
        Args:
            group_id: Group ID to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Group dict if found, None if not found
        """
        try:
            state = self.load_state_from_router()
            if state is None:
                self.logger.warning("No state file exists")
                return None
            
            group_key = str(group_id)
            if group_key not in state.get("groups", {}):
                self.logger.warning(f"Group {group_id} not found in state")
                return None
            
            return state["groups"][group_key]
            
        except Exception as e:
            self.logger.error(f"Error getting group {group_id}: {e}")
            return None
    
    def validate_state_format(self, state: Dict[str, Any]) -> bool:
        """
        4. Gets the state file from (3), checks if the format is correct, and returns true or false.
        
        Args:
            state: State dictionary to validate
            
        Returns:
            bool: True if valid, False if invalid
        """
        try:
            if not isinstance(state, dict):
                return False
            
            # Check top-level keys
            required_top_keys = ["groups"]
            for key in required_top_keys:
                if key not in state:
                    return False
            
            # Validate groups structure
            groups = state.get("groups", {})
            if not isinstance(groups, dict):
                return False
            
            # Validate each group has proper structure
            required_group_keys = ["name", "active", "device_count", "devices", "policies", "last_sync"]
            
            for group_id, group_data in groups.items():
                if not isinstance(group_data, dict):
                    return False
                
                for key in required_group_keys:
                    if key not in group_data:
                        return False
                
                # Validate policy structure
                policies = group_data.get("policies", {})
                if not isinstance(policies, dict):
                    return False
                
                required_policy_sections = ["bandwidth", "access_control", "time_based"]
                for section in required_policy_sections:
                    if section not in policies:
                        return False
                    
                    if not isinstance(policies[section], dict):
                        return False
                
                # Validate devices list
                devices = group_data.get("devices", [])
                if not isinstance(devices, list):
                    return False
            
            # Ensure Group 0 exists with correct structure
            if "0" not in groups:
                return False
            elif groups["0"].get("name") != "Guest Group":
                return False
            
            return True
            
        except Exception:
            return False
    
    def update_group_devices(self, group_id: int, devices: List[Dict[str, str]]) -> bool:
        """
        5. Gets a list of devices, with mac and ip each, and a groupId, updates the group, 
        writes back to the router (overwrites the existing devices, the new lists should only have the input devices).
        
        Args:
            group_id: Group ID to update
            devices: List of device dicts with 'ip' and 'mac' keys
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate device format
            for device in devices:
                if not isinstance(device, dict) or 'ip' not in device or 'mac' not in device:
                    self.logger.error("Invalid device format - must have 'ip' and 'mac' keys")
                    return False
                
                # Validate IP format
                try:
                    ipaddress.ip_address(device['ip'])
                except ValueError:
                    self.logger.error(f"Invalid IP address format: {device['ip']}")
                    return False
                
                # Validate MAC format
                mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
                if not mac_pattern.match(device['mac']):
                    self.logger.error(f"Invalid MAC address format: {device['mac']}")
                    return False
            
            # Load current state
            state = self.load_state_from_router()
            if state is None:
                # Create default state if none exists
                state = self.create_default_format()
            
            group_key = str(group_id)
            
            # Create group if it doesn't exist
            if group_key not in state["groups"]:
                state["groups"][group_key] = {
                    "name": f"Group {group_id}",
                    "active": True,
                    "device_count": 0,
                    "devices": [],
                    "policies": {
                        "bandwidth": {
                            "limit_mbps": None,
                            "tc_class": f"1:{group_id + 100}",
                            "mark_value": group_id + 100
                        },
                        "access_control": {
                            "blocked_categories": [],
                            "blocked_sites": [],
                            "allowed_sites_only": [],
                            "block_all_internet": False
                        },
                        "time_based": {
                            "from": None,
                            "to": None
                        }
                    },
                    "last_sync": None
                }
            
            # Update devices (overwrite existing)
            state["groups"][group_key]["devices"] = devices
            state["groups"][group_key]["device_count"] = len(devices)
            state["groups"][group_key]["last_sync"] = datetime.now().isoformat()
            
            # Write back to router
            if self.write_state_to_router(state):
                self.logger.info(f"Group {group_id} devices updated successfully")
                return True
            else:
                self.logger.error(f"Failed to write group {group_id} devices to router")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating devices for group {group_id}: {e}")
            return False
    
    def delete_group_and_move_devices_to_group_0(self, group_id: int) -> bool:
        """
        6. Gets a groupId, deletes the group from the state file, put all the devices in that group in group 0 instead.
        
        Args:
            group_id: Group ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if group_id == 0:
                self.logger.warning("Cannot delete Group 0 (Guest Group) - it is protected")
                return False
            
            # Load current state
            state = self.load_state_from_router()
            if state is None:
                self.logger.warning("No state file exists - nothing to delete")
                return True  # Nothing to delete, consider success
            
            group_key = str(group_id)
            
            if group_key not in state.get("groups", {}):
                self.logger.warning(f"Group {group_id} not found in state")
                return True  # Already deleted, consider success
            
            # Get devices from the group to be deleted
            devices_to_move = state["groups"][group_key].get("devices", [])
            
            # Add devices to Group 0
            if devices_to_move:
                group_0_devices = state["groups"]["0"].get("devices", [])
                group_0_devices.extend(devices_to_move)
                state["groups"]["0"]["devices"] = group_0_devices
                state["groups"]["0"]["device_count"] = len(group_0_devices)
                state["groups"]["0"]["last_sync"] = datetime.now().isoformat()
                self.logger.info(f"Moved {len(devices_to_move)} devices from Group {group_id} to Group 0")
            
            # Delete the group
            del state["groups"][group_key]
            
            # Write back to router
            if self.write_state_to_router(state):
                self.logger.info(f"Group {group_id} deleted successfully")
                return True
            else:
                self.logger.error(f"Failed to delete group {group_id} from router")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting group {group_id}: {e}")
            return False

    def create_or_recreate_group(self, group_id: int, devices: List[Dict[str, str]], policies: Optional[Dict[str, Any]] = None, overwrite_policies: bool = True) -> bool:
        """
        7. Gets groupId, and devices, and optional policies, if the group exists, delete it, and then either way, 
        create a new group, with the devices, and the optional policies, whatever was passed, and empty otherwise.
        
        Args:
            group_id: Group ID to create/recreate
            devices: List of device dicts with 'ip' and 'mac' keys
            policies: Optional policies dict. If None, empty policies will be used.
            overwrite_policies: If True, the policies will be overwritten with the provided policies. If False, the policies will be merged with the existing policies.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if group_id == 0:
                self.logger.warning("Cannot recreate Group 0 (Guest Group) - it is protected")
                return False
            
            # Load current state
            state = self.load_state_from_router()
            if state is None:
                # Create default state if none exists
                state = self.create_default_format()
            
            group_key = str(group_id)
            
            # Delete existing group if it exists
            if group_key in state.get("groups", {}):
                self.logger.info(f"Deleting existing Group {group_id} before recreating")
                del state["groups"][group_key]
            
            # Create new group with provided devices and policies
            # Define default policies structure
            if overwrite_policies:
                default_policies = {
                    "bandwidth": {
                        "limit_mbps": None,
                        "tc_class": f"1:{group_id + 100}",
                        "mark_value": group_id + 100
                    },
                    "access_control": {
                        "blocked_categories": [],
                        "blocked_sites": [],
                        "allowed_sites_only": [],
                        "block_all_internet": False
                    },
                    "time_based": {
                        "from": None,
                        "to": None
                    }
                }
            else:
                default_policies = state["groups"][group_key].get("policies")

            # Merge provided policies with defaults if provided
            if policies is not None:
                for section in policies:
                    if section in default_policies:
                        default_policies[section].update(policies[section])
            
            merged_policies = default_policies
            
            new_group = {
                "name": f"Group {group_id}",
                "active": True,
                "device_count": len(devices),
                "devices": devices,
                "policies": merged_policies,
                "last_sync": datetime.now().isoformat()
            }
            
            # Add the new group to state
            state["groups"][group_key] = new_group
            
            # Write back to router
            if self.write_state_to_router(state):
                self.logger.info(f"Group {group_id} created/recreated successfully with {len(devices)} devices")
                return True
            else:
                self.logger.error(f"Failed to write group {group_id} to router")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating/recreating group {group_id}: {e}")
            return False

    def add_device_to_group(self, group_id: int, device: Dict[str, str]) -> bool:
        """
        8. Gets a groupId, and a device, with mac and ip each, and adds the device to the group.
        """
        try:
            state = self.load_state_from_router()
            if state is None:
                self.logger.warning("No state file exists - nothing to add device to")
                return False
        
            group_key = str(group_id)
            if group_key not in state["groups"]:
                self.logger.warning(f"Group {group_id} not found in state")
                return False
            
            devices = state["groups"][group_key].get("devices", [])
            devices.append(device)
            state["groups"][group_key]["devices"] = devices
        
            if self.write_state_to_router(state):
                self.logger.info(f"Device {device['mac']} added to Group {group_id} successfully")
                return True
            else:
                self.logger.error(f"Failed to add device {device['mac']} to Group {group_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding device {device['mac']} to Group {group_id}: {e}")