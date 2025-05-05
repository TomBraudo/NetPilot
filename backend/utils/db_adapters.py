from db.device_repository import register_device as register_device_new
from db.device_repository import update_device_rules, get_device_by_ip
from db.group_repository import add_device_to_group, apply_rules_to_group

def register_device_adapter(ip, mac, hostname, device_type=None):
    """
    Adapter function that converts from old (ip, mac, hostname) order
    to new (mac, ip, hostname) order for the register_device function.
    """
    return register_device_new(mac, ip, hostname, device_type)

def apply_rule_adapter(ip, rule_name, value):
    """
    Adapter function to apply a rule using IP address.
    Converts IP to MAC and applies the rule.
    """
    device = get_device_by_ip(ip)
    if not device:
        return False
    
    # Create a rule dictionary with the specified rule
    rules = {}
    rules[rule_name] = value
    
    # Call the appropriate update function based on the rule
    return update_device_rules(device['mac'], **rules)

def remove_rule_adapter(ip, rule_name):
    """
    Adapter function to remove a rule using IP address.
    Converts IP to MAC and removes the rule.
    """
    device = get_device_by_ip(ip)
    if not device:
        return False
    
    # Create a rule dictionary with None for the specified rule
    rules = {}
    rules[rule_name] = None
    
    # Call the appropriate update function
    return update_device_rules(device['mac'], **rules) 