def apply_rule_with_blacklist_logic(rule_name, rule_value, group_name=None):
    """
    Apply a rule to devices based on blacklist/whitelist logic.
    
    Args:
        rule_name: Name of the rule to apply
        rule_value: Value to set for the rule
        group_name: Optional group name to apply rules specifically to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from db.device_repository import get_all_devices, update_device_rules, is_device_protected
        from db.group_repository import get_devices_in_group, get_group_blacklist_mode
        
        all_devices = get_all_devices()
        
        # If no group specified, apply to all devices
        if not group_name:
            for device in all_devices:
                mac = device.get('mac')
                update_device_rules(mac, **{rule_name: rule_value})
            return True
            
        # Check if group is blacklist or whitelist
        is_blacklist = get_group_blacklist_mode(group_name)
        if is_blacklist is None:
            return False  # Group not found
            
        # Get devices in the group
        group_devices = get_devices_in_group(group_name)
        group_macs = {device.get('mac') for device in group_devices}
        
        # Apply rules based on blacklist/whitelist logic
        for device in all_devices:
            mac = device.get('mac')
            
            # Skip protected devices for certain rules
            if rule_name == "block" and is_device_protected(mac):
                continue
            
            # For blacklist: apply rule to devices IN the group
            # For whitelist: apply rule to devices NOT IN the group
            if (is_blacklist and mac in group_macs) or (not is_blacklist and mac not in group_macs):
                update_device_rules(mac, **{rule_name: rule_value})
                
        return True
    except Exception as e:
        logger.error(f"Error applying rule with blacklist logic: {e}")
        return False 