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
    return jsonify(success(data=[{
        "mac": d[0],
        "ip": d[1],
        "hostname": d[2],
        "device_name": d[3],
        "first_seen": d[4],
        "last_seen": d[5]
    } for d in devices]))

''' 
    API endpoint to update a user-defined name for a device.
    Expects JSON: { "mac": "<mac_address>", "device_name": "<name>" }
'''
@db_bp.route("/db/device_name", methods=["PATCH"])
def update_device_name_route():
    data = request.get_json()
    mac = data.get("mac")
    device_name = data.get("device_name")
    if not mac or not device_name:
        return error("Missing 'mac' or 'device_name' in request body")
    success_status = update_device_name(mac, device_name)
    if success_status:
        return success("Device name updated successfully")
    else:
        return error("Device not found", status_code=404)

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
    return jsonify(success(data=groups))

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
    return jsonify(success(data=members))

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
        if device and len(device) > 1:
            ip = device[1]  # IP is at index 1
        else:
            return error("Could not determine IP for device")
    
    rules = get_rules_for_device(mac, ip)
    return jsonify(success(data=rules))