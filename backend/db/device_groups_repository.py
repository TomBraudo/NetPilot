import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TinyDB Query objects
# Group = Query() # Removed
# GroupMember = Query() # Removed
# Rule = Query() # Removed as 'rules' table is being removed
# DeviceRule = Query() # Removed
# Device = Query() # Removed as functions using it are commented out

# This function is no longer needed with TinyDB but kept as a no-op for compatibility
# def init_group_tables(): # Commented out
#     """No-op function for compatibility with existing code.""" # Commented out
#     pass # Commented out

# Assign a rule to a device, ensuring device and rule exist
# def set_rule_for_device(mac, ip, rule_name, rule_value="0"):
#     """Set a rule for a device using MAC as the primary key."""
#     try:
#         # Check if device exists
#         device = db_client.devices.get(Device.mac == mac)
#         
#         if not device:
#             # Create a basic device record if it doesn't exist
#             db_client.devices.insert({
#                 'mac': mac,
#                 'ip': ip,
#                 'hostname': "unknown",
#                 'device_name': None,
#                 'first_seen': datetime.utcnow().isoformat(),
#                 'last_seen': datetime.utcnow().isoformat()
#             })
#             logger.info(f"Created basic device record for {mac}")
#         
#         # Check if rule exists
#         # rule = db_client.rules.get(Rule.name == rule_name) # Rule definition check removed
#         # if not rule:
#         #     raise ValueError(f"Rule '{rule_name}' is not defined")
#         
#         # Update or insert rule
#         existing_rule = db_client.device_rules.get(
#             (DeviceRule.mac == mac) & 
#             (DeviceRule.rule_name == rule_name)
#         )
#         
#         if existing_rule:
#             db_client.device_rules.update(
#                 {'rule_value': rule_value}, 
#                 (DeviceRule.mac == mac) & 
#                 (DeviceRule.rule_name == rule_name)
#             )
#             logger.info(f"Updated rule {rule_name} for device {mac}")
#         else:
#             db_client.device_rules.insert({
#                 'mac': mac,
#                 'ip': ip,
#                 'rule_name': rule_name,
#                 'rule_value': rule_value
#             })
#             logger.info(f"Added rule {rule_name} for device {mac}")
#         
#         return True
#     except Exception as e:
#         logger.error(f"Error setting rule for device: {e}")
#         return False

# Remove a rule from a device
# def remove_rule_from_device(mac, ip, rule_name):
#     """Remove a rule from a device using MAC as the primary key."""
#     try:
#         db_client.device_rules.remove(
#             (DeviceRule.mac == mac) & 
#             (DeviceRule.rule_name == rule_name)
#         )
#         logger.info(f"Removed rule {rule_name} from device {mac}")
#         return True
#     except Exception as e:
#         logger.error(f"Error removing rule from device: {e}")
#         return False

# Assign a rule to all members of a group
# def set_rule_for_group(group_name, rule_name, rule_value):
#     """Set a rule for all devices in a group."""
#     try:
#         # Get group ID
#         group = db_client.device_groups.get(Group.name == group_name)
#         if not group:
#             raise ValueError("Group not found")
#         
#         # Get all group members
#         group_members = db_client.group_members.search(GroupMember.group_id == group.doc_id)
#         
#         # Apply rule to each device
#         # for member in group_members:
#         #     set_rule_for_device(member['mac'], member['ip'], rule_name, rule_value)
#         
#         return True
#     except Exception as e:
#         logger.error(f"Error setting rule for group: {e}")
#         return False

# Define a new rule type
# def create_rule_type(rule_name, rule_type, default_value=None, description=None):
#     """Create a new rule type."""
#     try:
#         # Check if rule exists
#         # existing_rule = db_client.rules.get(Rule.name == rule_name) # Rule definition check removed
#         
#         # if not existing_rule:
#         #     db_client.rules.insert({
#         #         'name': rule_name,
#         #         'type': rule_type,
#         #         'default': default_value,
#         #         'desc': description
#         #     })
#         
#         return True
#     except Exception as e:
#         logger.error(f"Error creating rule type: {e}")
#         return False

# Create a new group with a unique name
# def create_group(name): # Commented out
#     """Create a new device group.""" # Commented out
#     try: # Commented out
#         # Check if group exists # Commented out
#         if not db_client.device_groups.contains(Group.name == name): # Commented out
#             db_client.device_groups.insert({'name': name}) # Commented out
#         return True # Commented out
#     except Exception as e: # Commented out
#         logger.error(f"Error creating group: {e}") # Commented out
#         return False # Commented out

# Rename an existing group
# def rename_group(old_name, new_name): # Commented out
#     """Rename a device group.""" # Commented out
#     try: # Commented out
#         db_client.device_groups.update( # Commented out
#             {'name': new_name}, # Commented out
#             Group.name == old_name # Commented out
#         ) # Commented out
#         return True # Commented out
#     except Exception as e: # Commented out
#         logger.error(f"Error renaming group: {e}") # Commented out
#         return False # Commented out

# Move a device to a different group
# def move_device_to_group(mac, ip, group_name): # Commented out
#     """Move a device to a different group.""" # Commented out
#     try: # Commented out
#         # Check if device exists # Commented out
#         device = db_client.devices.get((Device.mac == mac) & (Device.ip == ip)) # Commented out
#         if not device: # Commented out
#             raise ValueError(f"Device with MAC {mac} and IP {ip} does not exist") # Commented out
#         # Get target group # Commented out
#         group = db_client.device_groups.get(Group.name == group_name) # Commented out
#         if not group: # Commented out
#             raise ValueError("Target group not found") # Commented out
#         # Check if device is already in a group # Commented out
#         member = db_client.group_members.get( # Commented out
#             (GroupMember.mac == mac) & (GroupMember.ip == ip) # Commented out
#         ) # Commented out
#         if member: # Commented out
#             # Update group membership # Commented out
#             db_client.group_members.update( # Commented out
#                 {'group_id': group.doc_id}, # Commented out
#                 (GroupMember.mac == mac) & (GroupMember.ip == ip) # Commented out
#             ) # Commented out
#         else: # Commented out
#             # Create new group membership # Commented out
#             db_client.group_members.insert({ # Commented out
#                 'mac': mac, # Commented out
#                 'ip': ip, # Commented out
#                 'group_id': group.doc_id # Commented out
#             }) # Commented out
#         return True # Commented out
#     except Exception as e: # Commented out
#         logger.error(f"Error moving device to group: {e}") # Commented out
#         return False # Commented out

# def get_rules_for_device(mac): # Already commented out
#     """
#     Get all rules for a device using MAC as the primary key.
#     Args:
#         mac (str): The device's MAC address
#     Returns:
#         list: List of rules for the device
#     """
#     # try:
#     #     return db_client.device_rules.search(DeviceRule.mac == mac)
#     # except Exception as e:
#     #     logger.error(f"Error getting rules for device: {e}")
#     #     return []
#     pass

# def get_all_groups(): # Commented out
#     """Get all device groups.""" # Commented out
#     try: # Commented out
#         return db_client.device_groups.all() # Commented out
#     except Exception as e: # Commented out
#         logger.error(f"Error getting groups: {e}") # Commented out
#         return [] # Commented out
    
# def get_group_members(group_id): # Commented out
#     """Get all members of a group.""" # Commented out
#     try: # Commented out
#         return db_client.group_members.search(GroupMember.group_id == group_id) # Commented out
#     except Exception as e: # Commented out
#         logger.error(f"Error getting group members: {e}") # Commented out
#         return [] # Commented out
    
# def delete_group(group_name): # Commented out
#     """Delete a group and move its members to 'general'""" # Commented out
#     try: # Commented out
#         # Get group to delete # Commented out
#         group = db_client.device_groups.get(Group.name == group_name) # Commented out
#         if not group: # Commented out
#             raise ValueError("Group not found") # Commented out
#         # Ensure it's not the only group # Commented out
#         group_count = len(db_client.device_groups.all()) # Commented out
#         if group_count <= 1: # Commented out
#             raise ValueError("Cannot delete the only group") # Commented out
#         # Get general group # Commented out
#         general_group = db_client.device_groups.get(Group.name == 'general') # Commented out
#         if not general_group: # Commented out
#             raise ValueError("'general' group not found") # Commented out
#         # Move devices to general group # Commented out
#         members = db_client.group_members.search(GroupMember.group_id == group.doc_id) # Commented out
#         for member in members: # Commented out
#             db_client.group_members.update( # Commented out
#                 {'group_id': general_group.doc_id}, # Commented out
#                 (GroupMember.mac == member['mac']) & (GroupMember.ip == member['ip']) # Commented out
#             ) # Commented out
#         # Delete the group # Commented out
#         db_client.device_groups.remove(doc_ids=[group.doc_id]) # Commented out
#         return True # Commented out
#     except Exception as e: # Commented out
#         logger.error(f"Error deleting group: {e}") # Commented out
#         return False # Commented out


