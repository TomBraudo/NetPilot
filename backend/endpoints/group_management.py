from flask import Blueprint, request, jsonify
from services.group_management import toggle_group_blacklist_mode, get_group_mode
from utils.response_helpers import error

group_mgmt_bp = Blueprint('group_mgmt', __name__)

'''
    API endpoint to toggle a group between blacklist and whitelist modes
    Expects JSON: {
        "group_name": "string",
        "is_blacklist": boolean  # Optional, if not provided, toggles current value
    }
'''
@group_mgmt_bp.route("/api/groups/set_mode", methods=["POST"])
def toggle_group_mode_route():
    data = request.get_json()
    
    if not data:
        return jsonify(error("Missing request body"))
        
    group_name = data.get("group_name")
    is_blacklist = data.get("is_blacklist")  # This can be None
    
    if not group_name:
        return jsonify(error("Missing 'group_name' in request body"))
        
    return jsonify(toggle_group_blacklist_mode(group_name, is_blacklist))

'''
    API endpoint to get the current blacklist/whitelist mode of a group
    Expects query param: ?group_name=<group_name>
'''
@group_mgmt_bp.route("/api/groups/get_mode", methods=["GET"])
def get_group_mode_route():
    group_name = request.args.get("group_name")
    
    if not group_name:
        return jsonify(error("Missing 'group_name' query parameter"))
        
    return jsonify(get_group_mode(group_name)) 