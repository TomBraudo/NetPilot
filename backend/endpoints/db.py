from flask import Blueprint, request, jsonify
from utils.response_helpers import success, error
from db.device_repository import get_all_devices, update_device_name, clear_devices, get_device_by_mac
from db.device_groups_repository import get_all_groups, get_group_members, get_rules_for_device

db_bp = Blueprint('database', __name__)

''' 
    API endpoint to retrieve all devices from the database.
'''
@db_bp.route("/db/devices", methods=["GET"])
def get_devices():
    devices = get_all_devices()
    formatted_devices = []
    
    for d in devices:
        formatted_devices.append({
            "mac": d.get('mac', ''),
            "ip": d.get('ip', ''),
            "hostname": d.get('hostname', ''),
            "device_name": d.get('device_name', ''),
            "first_seen": d.get('first_seen', ''),
            "last_seen": d.get('last_seen', '')
        })
    
    return jsonify(success(data=formatted_devices))

''' 
    API endpoint to update a user-defined name for a device.
    Expects JSON: { "mac": "<mac_address>", "device_name": "<n>" }
'''
@db_bp.route("/db/device_name", methods=["PATCH"])
def update_device_name_route():
    data = request.get_json()
    mac = data.get("mac")
    device_name = data.get("device_name")
    
    if not mac or not device_name:
        return error("Missing 'mac' or 'device_name' in request body")
    
    device = get_device_by_mac(mac)
    if not device:
        return error("Device not found", status_code=404)
    
    # Get IP from device if it exists
    ip = device.get('ip', '')
    
    # Call update function with correct parameters
    success_status = update_device_name(mac, device_name)
    
    if success_status:
        return success("Device name updated successfully")
    else:
        return error("Failed to update device name", status_code=500)

''' 
    API endpoint to clear all device records from the database.
'''
@db_bp.route("/db/clear", methods=["DELETE"])
def clear_devices_route():
    clear_devices()
    return success("All devices cleared from the database")

'''
    API endpoint to retrieve all device groups.
'''
@db_bp.route("/db/groups", methods=["GET"])
def get_groups():
    groups = get_all_groups()
    formatted_groups = []
    
    for g in groups:
        formatted_groups.append({
            "id": g.doc_id,
            "name": g.get('name', ''),
            "description": g.get('description', '')
        })
    
    return jsonify(success(data=formatted_groups))

''' 
    API endpoint to retrieve all devices in a specific group.
    Expects query param: ?group_name=<group_name>
'''
@db_bp.route("/db/group_members", methods=["GET"])
def get_group_members_route():
    group_name = request.args.get("group_name")
    if not group_name:
        return error("Missing 'group_name' in query parameters")
    
    members = get_group_members(group_name)
    formatted_members = []
    
    for m in members:
        # Check if m is a tuple or a dictionary
        if isinstance(m, tuple):
            # If it's still a tuple, use indices
            mac = m[0] if len(m) > 0 else ''
            ip = m[1] if len(m) > 1 else ''
            hostname = m[2] if len(m) > 2 else 'Unknown'
        else:
            # If it's a dictionary, use keys
            mac = m.get('mac', '')
            ip = m.get('ip', '')
            hostname = m.get('hostname', 'Unknown')
        
        formatted_members.append({
            "mac": mac,
            "ip": ip,
            "hostname": hostname
        })
    
    return jsonify(success(data=formatted_members))

'''
    API endpoint to retrieve all rules for a specific device.
    Expects query params: ?mac=<mac_address>&ip=<ip_address>
'''
@db_bp.route("/db/device_rules", methods=["GET"])
def get_device_rules():
    mac = request.args.get("mac")
    ip = request.args.get("ip")
    
    if not mac:
        return error("Missing 'mac' in query parameters")
    
    if not ip:
        # For backward compatibility, try to fetch IP from device if not provided
        device = get_device_by_mac(mac)
        if device:
            ip = device.get('ip', '')
        else:
            return error("Could not determine IP for device")
    
    rules = get_rules_for_device(mac, ip)
    formatted_rules = []
    
    for r in rules:
        # Check if r is a tuple or a dictionary
        if isinstance(r, tuple):
            # If it's a tuple, use indices
            rule_name = r[0] if len(r) > 0 else ''
            rule_value = r[1] if len(r) > 1 else ''
        else:
            # If it's a dictionary, use keys
            rule_name = r.get('rule_name', '')
            rule_value = r.get('rule_value', '')
        
        formatted_rules.append({
            "name": rule_name,
            "value": rule_value
        })
    
    return jsonify(success(data=formatted_rules))