"""
StateFileManager for NetPilot Commands-Server Groups

Manages the group-based state file with singleton pattern for centralized access.
This will replace the existing state file format completely.

Bandwidth Policy Behavior:
- bandwidth_limit_mbps = None: No TC rule is set, all packets flow through unrestricted
- bandwidth_limit_mbps = <number>: TC rule and iptables forwarding are applied to limit 
  all group members to the specified Mbps value
"""

import json
import os
import re
import ipaddress
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
from groups.group_state import GroupState
from groups.device_info import DeviceInfo
from groups.device_verification_result import DeviceVerificationResult
from groups.device_changes import DeviceChanges
from groups.group_policy_summary import GroupPolicySummary


class StateFileManager:
    """
    Singleton manager for the commands-server state file.
    Handles all state file operations with thread-safe access.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateFileManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if StateFileManager._initialized:
            return
            
        self.logger = get_logger('managers.state_file')
        self.router_connection_manager = RouterConnectionManager()
        self.state_file_path = "/etc/config/netpilot_groups_state.json"
        self._cached_state = None
        self._cache_timestamp = None
        
        StateFileManager._initialized = True
        self.logger.info("StateFileManager singleton initialized")
    
    def load_state(self) -> Dict[str, Any]:
        """
        Load current state from router state file.
        Returns default state if file doesn't exist or is corrupted.
        """
        try:
            command = f"cat {self.state_file_path}"
            output, error = self.router_connection_manager.execute(command)
            
            if error or not output.strip():
                self.logger.warning("State file not found or empty. Creating default state.")
                default_state = self._get_default_state()
                self._write_state_to_router(default_state)
                return default_state
            
            state = json.loads(output.strip())
            self._validate_state_structure(state)
            self._cached_state = state
            self._cache_timestamp = datetime.now()
            
            self.logger.info("State loaded successfully from router")
            return state
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse state file JSON: {e}")
            default_state = self._get_default_state()
            self._write_state_to_router(default_state)
            return default_state
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")
            return self._get_default_state()
    
    def save_group_state(self, group_id: int, group_state: GroupState) -> bool:
        """
        Update or create group state in the state file.
        
        Args:
            group_id: Group ID to update
            group_state: GroupState object to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            current_state = self.load_state()
            
            # Convert GroupState to dict format for JSON storage
            group_dict = {
                "name": group_state.name,
                "active": group_state.active,
                "device_count": group_state.device_count,
                "devices": [device.to_dict() for device in group_state.devices],
                "tc_class": group_state.tc_class,
                "mark_value": group_state.mark_value,
                "policies": group_state.policies.to_dict(),
                "infrastructure_created": group_state.infrastructure_created,
                "last_sync": group_state.last_sync.isoformat() if group_state.last_sync else None
            }
            
            current_state["groups"][str(group_id)] = group_dict
            
            if self._write_state_to_router(current_state):
                self._cached_state = current_state
                self._cache_timestamp = datetime.now()
                self.logger.info(f"Group {group_id} state saved successfully")
                return True
            else:
                self.logger.error(f"Failed to write group {group_id} state to router")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving group {group_id} state: {e}")
            return False
    
    def delete_group_state(self, group_id: int) -> bool:
        """
        Remove group from state file and release its TC class.
        Group 0 (Guest Group) cannot be deleted.
        
        Args:
            group_id: Group ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if group_id == 0:
                self.logger.warning("Cannot delete Group 0 (Guest Group) - it is protected")
                return False
            
            current_state = self.load_state()
            group_key = str(group_id)
            
            if group_key not in current_state.get("groups", {}):
                self.logger.warning(f"Group {group_id} not found in state")
                return True  # Already deleted, consider success
            
            # Get TC class and mark value before deletion
            group_data = current_state["groups"][group_key]
            tc_class = group_data.get("tc_class")
            mark_value = group_data.get("mark_value")
            
            # Remove the group
            del current_state["groups"][group_key]
            
            # Release TC class back to available pool
            if tc_class and mark_value:
                self._release_tc_class_internal(current_state, tc_class, mark_value)
            
            if self._write_state_to_router(current_state):
                self._cached_state = current_state
                self._cache_timestamp = datetime.now()
                self.logger.info(f"Group {group_id} deleted successfully")
                return True
            else:
                self.logger.error(f"Failed to delete group {group_id} from router")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting group {group_id}: {e}")
            return False
    
    def get_group_state(self, group_id: int) -> Optional[GroupState]:
        """
        Get specific group state from the state file.
        
        Args:
            group_id: Group ID to retrieve
            
        Returns:
            GroupState object or None if not found
        """
        try:
            current_state = self.load_state()
            group_key = str(group_id)
            
            if group_key not in current_state.get("groups", {}):
                self.logger.warning(f"Group {group_id} not found in state")
                return None
            
            group_data = current_state["groups"][group_key]
            
            # Convert devices from dict to DeviceInfo objects
            devices = [
                DeviceInfo(ip=device["ip"], mac=device["mac"])
                for device in group_data["devices"]
            ]
            
            # Convert policies from dict to GroupPolicySummary
            policies_data = group_data["policies"]
            policies = GroupPolicySummary(
                bandwidth_limit_mbps=policies_data.get("bandwidth_limit_mbps"),
                blocked_categories=policies_data.get("blocked_categories", []),
                blocked_sites=policies_data.get("blocked_sites", []),
                allowed_sites_only=policies_data.get("allowed_sites_only", []),
                block_all_internet=policies_data.get("block_all_internet", False)
            )
            
            # Parse last_sync datetime
            last_sync = None
            if group_data.get("last_sync"):
                last_sync = datetime.fromisoformat(group_data["last_sync"].replace('Z', '+00:00'))
            
            return GroupState(
                group_id=group_id,
                name=group_data["name"],
                active=group_data["active"],
                device_count=group_data["device_count"],
                devices=devices,
                tc_class=group_data["tc_class"],
                mark_value=group_data["mark_value"],
                policies=policies,
                infrastructure_created=group_data["infrastructure_created"],
                last_sync=last_sync
            )
            
        except Exception as e:
            self.logger.error(f"Error getting group {group_id} state: {e}")
            return None
    
    def verify_devices(self, group_id: int, device_ips: List[str], device_macs: List[str]) -> DeviceVerificationResult:
        """
        Verify incoming device list against stored state.
        
        Args:
            group_id: Group ID to verify against
            device_ips: List of device IP addresses
            device_macs: List of device MAC addresses
            
        Returns:
            DeviceVerificationResult with validation results
        """
        try:
            # Validate IP and MAC formats first
            validation_error = self._validate_device_formats(device_ips, device_macs)
            if validation_error:
                return DeviceVerificationResult(
                    is_valid=False,
                    added_devices=[],
                    removed_devices=[],
                    changed_devices=[],
                    error_message=validation_error
                )
            
            # Check for duplicates across all groups
            duplicate_error = self._check_device_duplicates(group_id, device_ips, device_macs)
            if duplicate_error:
                return DeviceVerificationResult(
                    is_valid=False,
                    added_devices=[],
                    removed_devices=[],
                    changed_devices=[],
                    error_message=duplicate_error
                )
            
            # Get current group state
            current_group = self.get_group_state(group_id)
            if not current_group:
                # New group - all devices are additions
                new_devices = [
                    DeviceInfo(ip=ip, mac=mac) 
                    for ip, mac in zip(device_ips, device_macs)
                ]
                return DeviceVerificationResult(
                    is_valid=True,
                    added_devices=new_devices,
                    removed_devices=[],
                    changed_devices=[]
                )
            
            # Calculate device changes
            changes = self.get_device_changes(group_id, [
                DeviceInfo(ip=ip, mac=mac) 
                for ip, mac in zip(device_ips, device_macs)
            ])
            
            return DeviceVerificationResult(
                is_valid=True,
                added_devices=changes.added,
                removed_devices=changes.removed,
                changed_devices=changes.ip_changed + changes.mac_changed
            )
            
        except Exception as e:
            self.logger.error(f"Error verifying devices for group {group_id}: {e}")
            return DeviceVerificationResult(
                is_valid=False,
                added_devices=[],
                removed_devices=[],
                changed_devices=[],
                error_message=f"Internal error during device verification: {str(e)}"
            )
    
    def update_group_devices(self, group_id: int, devices: List[DeviceInfo]) -> bool:
        """
        Update device list for a group in the state file.
        
        Args:
            group_id: Group ID to update
            devices: New list of DeviceInfo objects
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            current_group = self.get_group_state(group_id)
            if not current_group:
                self.logger.error(f"Group {group_id} not found for device update")
                return False
            
            # Update the device list and count
            current_group.devices = devices
            current_group.device_count = len(devices)
            current_group.last_sync = datetime.now()
            
            return self.save_group_state(group_id, current_group)
            
        except Exception as e:
            self.logger.error(f"Error updating devices for group {group_id}: {e}")
            return False
    
    def get_device_changes(self, group_id: int, new_devices: List[DeviceInfo]) -> DeviceChanges:
        """
        Calculate which devices were added/removed/changed.
        
        Args:
            group_id: Group ID to compare against
            new_devices: New device list to compare
            
        Returns:
            DeviceChanges object with detected changes
        """
        try:
            current_group = self.get_group_state(group_id)
            if not current_group:
                # New group - all devices are additions
                return DeviceChanges(
                    added=new_devices,
                    removed=[],
                    ip_changed=[],
                    mac_changed=[],
                    unchanged=[]
                )
            
            current_devices = current_group.devices
            added = []
            removed = []
            ip_changed = []
            mac_changed = []
            unchanged = []
            
            # Create lookup maps for efficient comparison
            current_by_ip = {device.ip: device for device in current_devices}
            current_by_mac = {device.mac: device for device in current_devices}
            new_by_ip = {device.ip: device for device in new_devices}
            new_by_mac = {device.mac: device for device in new_devices}
            
            # Find added devices (in new but not in current)
            for new_device in new_devices:
                if (new_device.ip not in current_by_ip and 
                    new_device.mac not in current_by_mac):
                    added.append(new_device)
            
            # Find removed devices (in current but not in new)
            for current_device in current_devices:
                if (current_device.ip not in new_by_ip and 
                    current_device.mac not in new_by_mac):
                    removed.append(current_device)
            
            # Find changed devices (IP or MAC changed)
            for new_device in new_devices:
                # Check for IP changes (same MAC, different IP)
                if new_device.mac in current_by_mac:
                    current_device = current_by_mac[new_device.mac]
                    if current_device.ip != new_device.ip:
                        ip_changed.append((current_device, new_device))
                        continue
                
                # Check for MAC changes (same IP, different MAC)
                if new_device.ip in current_by_ip:
                    current_device = current_by_ip[new_device.ip]
                    if current_device.mac != new_device.mac:
                        mac_changed.append((current_device, new_device))
                        continue
                
                # Check for unchanged devices (same IP and MAC)
                if (new_device.ip in current_by_ip and 
                    current_by_ip[new_device.ip].mac == new_device.mac):
                    unchanged.append(new_device)
            
            return DeviceChanges(
                added=added,
                removed=removed,
                ip_changed=ip_changed,
                mac_changed=mac_changed,
                unchanged=unchanged
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating device changes for group {group_id}: {e}")
            return DeviceChanges(
                added=[],
                removed=[],
                ip_changed=[],
                mac_changed=[],
                unchanged=[]
            )
    
    def allocate_tc_class(self) -> Tuple[str, int]:
        """
        Allocate next available TC class and mark value.
        
        Returns:
            Tuple of (tc_class, mark_value) or (None, None) if none available
        """
        try:
            current_state = self.load_state()
            infrastructure = current_state.get("infrastructure", {})
            available_classes = infrastructure.get("available_classes", [])
            next_mark_value = infrastructure.get("next_mark_value", 102)
            
            if not available_classes:
                # Generate more classes if needed (up to limit of ~900)
                if next_mark_value > 999:
                    self.logger.error("No more TC classes available (limit reached)")
                    return None, None
                
                # Add next available class
                tc_class = f"1:{next_mark_value}"
                mark_value = next_mark_value
                
                # Update infrastructure state
                infrastructure["next_mark_value"] = next_mark_value + 1
                current_state["infrastructure"] = infrastructure
                
                self._write_state_to_router(current_state)
                self._cached_state = current_state
                self._cache_timestamp = datetime.now()
                
                self.logger.info(f"Allocated new TC class: {tc_class} (mark: {mark_value})")
                return tc_class, mark_value
            
            else:
                # Use from available pool
                tc_class = available_classes.pop(0)
                mark_value = int(tc_class.split(':')[1])
                
                # Update state
                infrastructure["available_classes"] = available_classes
                current_state["infrastructure"] = infrastructure
                
                self._write_state_to_router(current_state)
                self._cached_state = current_state
                self._cache_timestamp = datetime.now()
                
                self.logger.info(f"Allocated TC class from pool: {tc_class} (mark: {mark_value})")
                return tc_class, mark_value
                
        except Exception as e:
            self.logger.error(f"Error allocating TC class: {e}")
            return None, None
    
    def release_tc_class(self, tc_class: str, mark_value: int) -> bool:
        """
        Release TC class back to available pool.
        
        Args:
            tc_class: TC class to release (e.g., "1:101")
            mark_value: Mark value to release
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            current_state = self.load_state()
            return self._release_tc_class_internal(current_state, tc_class, mark_value)
            
        except Exception as e:
            self.logger.error(f"Error releasing TC class {tc_class}: {e}")
            return False
    
    def _release_tc_class_internal(self, state: Dict[str, Any], tc_class: str, mark_value: int) -> bool:
        """
        Internal method to release TC class back to available pool.
        Modifies the state dict in place.
        """
        try:
            # Don't release Group 0's class (1:100, mark 100)
            if mark_value == 100:
                self.logger.info("Not releasing TC class for Group 0 (protected)")
                return True
            
            infrastructure = state.get("infrastructure", {})
            available_classes = infrastructure.get("available_classes", [])
            
            if tc_class not in available_classes:
                available_classes.append(tc_class)
                available_classes.sort(key=lambda x: int(x.split(':')[1]))  # Sort by mark value
                
                infrastructure["available_classes"] = available_classes
                state["infrastructure"] = infrastructure
                
                if self._write_state_to_router(state):
                    self._cached_state = state
                    self._cache_timestamp = datetime.now()
                    self.logger.info(f"Released TC class {tc_class} back to pool")
                    return True
                else:
                    return False
            else:
                self.logger.info(f"TC class {tc_class} already in available pool")
                return True
                
        except Exception as e:
            self.logger.error(f"Error in _release_tc_class_internal: {e}")
            return False
    
    def _get_default_state(self) -> Dict[str, Any]:
        """
        Returns the default group-based state file structure.
        Includes Group 0 (Guest Group) with default configuration.
        
        Default Bandwidth Policy:
        - Group 0 starts with bandwidth_limit_mbps: None (unrestricted)
        - Future services will apply TC rules only when bandwidth_limit_mbps has a numeric value
        """
        return {
            "groups": {
                "0": {
                    "name": "Guest Group",
                    "active": True,
                    "device_count": 0,
                    "devices": [],
                    "tc_class": "1:100",
                    "mark_value": 100,
                    "policies": {
                        "bandwidth_limit_mbps": None,  # No TC rule - unrestricted
                        "blocked_categories": [],
                        "blocked_sites": [],
                        "allowed_sites_only": [],
                        "block_all_internet": False
                    },
                    "infrastructure_created": False,
                    "last_sync": None
                }
            },
            "infrastructure": {
                "base_setup_complete": False,
                "available_classes": [],
                "next_mark_value": 101
            }
        }
    
    def _write_state_to_router(self, state: Dict[str, Any]) -> bool:
        """
        Write state to router state file.
        
        Args:
            state: State dictionary to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
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
    
    def _validate_state_structure(self, state: Dict[str, Any]) -> None:
        """
        Validate that state has required structure.
        Raises exception if invalid.
        """
        if not isinstance(state, dict):
            raise ValueError("State must be a dictionary")
        
        if "groups" not in state:
            raise ValueError("State missing 'groups' key")
        
        if "infrastructure" not in state:
            raise ValueError("State missing 'infrastructure' key")
        
        # Ensure Group 0 exists
        if "0" not in state["groups"]:
            self.logger.warning("Group 0 missing from state - adding default Guest Group")
            state["groups"]["0"] = self._get_default_state()["groups"]["0"]
    
    def _validate_device_formats(self, device_ips: List[str], device_macs: List[str]) -> Optional[str]:
        """
        Validate IP and MAC address formats.
        
        Returns:
            Error message if invalid, None if valid
        """
        if len(device_ips) != len(device_macs):
            return "Device IP and MAC lists must have same length"
        
        # Validate IP addresses
        for ip in device_ips:
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                return f"Invalid IP address format: {ip}"
        
        # Validate MAC addresses
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        for mac in device_macs:
            if not mac_pattern.match(mac):
                return f"Invalid MAC address format: {mac}"
        
        return None
    
    def _check_device_duplicates(self, group_id: int, device_ips: List[str], device_macs: List[str]) -> Optional[str]:
        """
        Check for duplicate devices across groups.
        
        Returns:
            Error message if duplicates found, None if valid
        """
        try:
            current_state = self.load_state()
            
            for other_group_id, group_data in current_state.get("groups", {}).items():
                if int(other_group_id) == group_id:
                    continue  # Skip self
                
                other_devices = group_data.get("devices", [])
                for other_device in other_devices:
                    other_ip = other_device.get("ip")
                    other_mac = other_device.get("mac")
                    
                    if other_ip in device_ips:
                        return f"IP {other_ip} already exists in Group {other_group_id}"
                    
                    if other_mac in device_macs:
                        return f"MAC {other_mac} already exists in Group {other_group_id}"
            
            return None
            
        except Exception as e:
            return f"Error checking duplicates: {str(e)}"

    def create_default_state(self) -> bool:
        """
        Create the default new formatted state file, replacing any existing state file.
        This is used during infrastructure setup to replace the old format.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            default_state = self._get_default_state()
            if self._write_state_to_router(default_state):
                self._cached_state = default_state
                self._cache_timestamp = datetime.now()
                self.logger.info("Default group-based state file created successfully")
                return True
            else:
                self.logger.error("Failed to create default state file")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating default state: {e}")
            return False

    def check_state_format(self) -> bool:
        """
        Check if the state file is in the new group-based format.
        Returns True if and only if the state file exists and has the correct format,
        including Group 0 (Guest Group).
        
        Returns:
            bool: True if state file is in new format, False otherwise
        """
        try:
            command = f"cat {self.state_file_path}"
            output, error = self.router_connection_manager.execute(command)
            
            if error or not output.strip():
                self.logger.info("State file not found - old format or missing")
                return False
            
            try:
                state = json.loads(output.strip())
            except json.JSONDecodeError:
                self.logger.info("State file exists but contains invalid JSON - old format")
                return False
            
            # Check for new format structure
            if not isinstance(state, dict):
                return False
                
            if "groups" not in state or "infrastructure" not in state:
                self.logger.info("State file missing groups or infrastructure keys - old format")
                return False
            
            # Check if Group 0 exists with correct structure
            groups = state.get("groups", {})
            if "0" not in groups:
                self.logger.info("State file missing Group 0 - old format")
                return False
            
            group_0 = groups["0"]
            required_group_keys = ["name", "active", "device_count", "devices", "tc_class", 
                                 "mark_value", "policies", "infrastructure_created", "last_sync"]
            
            for key in required_group_keys:
                if key not in group_0:
                    self.logger.info(f"Group 0 missing required key '{key}' - old format")
                    return False
            
            # Check infrastructure structure
            infrastructure = state.get("infrastructure", {})
            required_infra_keys = ["base_setup_complete", "available_classes", "next_mark_value"]
            
            for key in required_infra_keys:
                if key not in infrastructure:
                    self.logger.info(f"Infrastructure missing required key '{key}' - old format")
                    return False
            
            # Validate Group 0 has correct default values
            if (group_0.get("name") != "Guest Group" or 
                group_0.get("tc_class") != "1:100" or 
                group_0.get("mark_value") != 100):
                self.logger.info("Group 0 has incorrect default values - old format")
                return False
            
            self.logger.info("State file verified as new group-based format")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking state format: {e}")
            return False

    @staticmethod
    def reset_instance():
        """Reset singleton instance for testing"""
        StateFileManager._instance = None
        StateFileManager._initialized = False
