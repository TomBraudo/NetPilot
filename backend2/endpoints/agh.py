from flask import Blueprint, request, g
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from utils.middleware import router_context_required
from services.agh_service import (
    get_categories,
    create_category,
    get_category_domains,
    replace_category_domains,
    get_device_effective_rules,
    bulk_get_devices_rules,
    set_device_rules,
    set_devices_rules,
    clear_device_rules,
    clear_devices_rules,
    delete_category,
)
import time

agh_bp = Blueprint('agh', __name__)
logger = get_logger('endpoints.agh')


@agh_bp.route('/categories', methods=['GET'])
@router_context_required
def list_categories():
    start_time = time.time()
    result, error = get_categories(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/categories', methods=['POST'])
@router_context_required
def create_category_route():
    start_time = time.time()
    data = request.get_json() or {}
    category = data.get('category')
    domains = data.get('domains', [])
    if not category or not isinstance(domains, list):
        return build_error_response("'category' and array 'domains' are required", 400, "BAD_REQUEST", start_time)
    result, error = create_category(g.user_id, g.router_id, g.session_id, category, domains)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/categories/<category>/domains', methods=['GET'])
@router_context_required
def get_category_domains_route(category):
    start_time = time.time()
    result, error = get_category_domains(g.user_id, g.router_id, g.session_id, category)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@agh_bp.route('/categories', methods=['DELETE'])
@router_context_required
def delete_category_route():
    start_time = time.time()
    data = request.get_json() or {}
    category = data.get('category')
    if not category:
        return build_error_response("Missing 'category'", 400, "BAD_REQUEST", start_time)
    result, error = delete_category(g.user_id, g.router_id, g.session_id, category)
    if error:
        return build_error_response(f"Failed to delete category: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/categories/<category>/domains', methods=['PUT'])
@router_context_required
def replace_category_domains_route(category):
    start_time = time.time()
    data = request.get_json() or {}
    domains = data.get('domains')
    if not isinstance(domains, list):
        return build_error_response("'domains' must be an array", 400, "BAD_REQUEST", start_time)
    result, error = replace_category_domains(g.user_id, g.router_id, g.session_id, category, domains)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/device/rules', methods=['GET'])
@router_context_required
def get_device_rules_route():
    start_time = time.time()
    mac = request.args.get('mac')
    ip = request.args.get('ip')
    if not mac and not ip:
        return build_error_response("Either 'mac' or 'ip' must be provided", 400, "BAD_REQUEST", start_time)
    result, error = get_device_effective_rules(g.user_id, g.router_id, g.session_id, mac, ip)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/devices/rules', methods=['POST'])
@router_context_required
def bulk_get_devices_rules_route():
    start_time = time.time()
    data = request.get_json() or {}
    devices = data.get('devices')
    if not isinstance(devices, list):
        return build_error_response("'devices' must be an array", 400, "BAD_REQUEST", start_time)
    result, error = bulk_get_devices_rules(g.user_id, g.router_id, g.session_id, devices)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/device/rules', methods=['POST'])
@router_context_required
def set_device_rules_route():
    start_time = time.time()
    data = request.get_json() or {}
    device = data.get('device')
    categories = data.get('categories')
    if not isinstance(device, dict) or not isinstance(categories, list):
        return build_error_response("'device' must be an object and 'categories' must be an array", 400, "BAD_REQUEST", start_time)
    # Normalize device keys to match commands server expectations
    device_norm = {
        'mac': (device or {}).get('mac'),
        'ipv4': (device or {}).get('ip') or (device or {}).get('ipv4')
    }
    result, error = set_device_rules(g.user_id, g.router_id, g.session_id, device_norm, categories)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/devices/rules/set', methods=['POST'])
@router_context_required
def set_devices_rules_route():
    start_time = time.time()
    data = request.get_json() or {}
    devices = data.get('devices')
    categories = data.get('categories')
    if not isinstance(devices, list) or not isinstance(categories, list):
        return build_error_response("'devices' and 'categories' must be arrays", 400, "BAD_REQUEST", start_time)
    # Normalize device objects: ensure 'ipv4' key and include mac when provided
    normalized_devices = []
    for d in devices or []:
        if not isinstance(d, dict):
            continue
        mac = (d or {}).get('mac')
        ipv4 = (d or {}).get('ip') or (d or {}).get('ipv4')
        if mac or ipv4:
            normalized_devices.append({'mac': mac, 'ipv4': ipv4})
    if not normalized_devices:
        return build_error_response("No valid devices provided (need 'mac' and/or 'ip')", 400, "BAD_REQUEST", start_time)
    result, error = set_devices_rules(g.user_id, g.router_id, g.session_id, normalized_devices, categories)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/device/rules', methods=['DELETE'])
@router_context_required
def clear_device_rules_route():
    start_time = time.time()
    data = request.get_json() or {}
    device = data.get('device')
    if not isinstance(device, dict):
        return build_error_response("'device' must be an object", 400, "BAD_REQUEST", start_time)
    device_norm = {
        'mac': (device or {}).get('mac'),
        'ipv4': (device or {}).get('ip') or (device or {}).get('ipv4')
    }
    result, error = clear_device_rules(g.user_id, g.router_id, g.session_id, device_norm)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/devices/rules', methods=['DELETE'])
@router_context_required
def clear_devices_rules_route():
    start_time = time.time()
    data = request.get_json() or {}
    devices = data.get('devices')
    if not isinstance(devices, list):
        return build_error_response("'devices' must be an array", 400, "BAD_REQUEST", start_time)
    normalized_devices = []
    for d in devices or []:
        if not isinstance(d, dict):
            continue
        mac = (d or {}).get('mac')
        ipv4 = (d or {}).get('ip') or (d or {}).get('ipv4')
        if mac or ipv4:
            normalized_devices.append({'mac': mac, 'ipv4': ipv4})
    result, error = clear_devices_rules(g.user_id, g.router_id, g.session_id, normalized_devices)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


# Database Rules Endpoints
@agh_bp.route('/rules', methods=['GET'])
@router_context_required
def get_all_content_control_rules():
    """Get all content control rules for a router"""
    start_time = time.time()
    try:
        from models import ContentControlRules
        from database.session import get_db_session
        
        with get_db_session() as session:
            rules = session.query(ContentControlRules).filter(
                ContentControlRules.router_id == g.router_id
            ).all()
            
            rules_data = [rule.to_dict() for rule in rules]
            return build_success_response(rules_data, start_time)
            
    except Exception as e:
        logger.error(f"Failed to get content control rules: {e}")
        return build_error_response(f"Failed to get content control rules: {str(e)}", 500, "DATABASE_ERROR", start_time)


@agh_bp.route('/rules/group/<group_id>', methods=['GET'])
@router_context_required
def get_group_content_control_rules(group_id):
    """Get content control rules for a specific group"""
    start_time = time.time()
    try:
        from models import ContentControlRules
        from database.session import get_db_session
        
        with get_db_session() as session:
            rule = session.query(ContentControlRules).filter(
                ContentControlRules.router_id == g.router_id,
                ContentControlRules.group_id == group_id
            ).first()
            
            if rule:
                return build_success_response(rule.to_dict(), start_time)
            else:
                return build_success_response(None, start_time)
                
    except Exception as e:
        logger.error(f"Failed to get group content control rules: {e}")
        return build_error_response(f"Failed to get group content control rules: {str(e)}", 500, "DATABASE_ERROR", start_time)


@agh_bp.route('/rules/group/<group_id>', methods=['POST'])
@router_context_required
def set_group_content_control_rules(group_id):
    """Create or update content control rules for a group"""
    start_time = time.time()
    try:
        from models import ContentControlRules, DeviceGroup
        from database.session import get_db_session
        
        data = request.get_json() or {}
        
        with get_db_session() as session:
            # Verify group exists and belongs to user
            group = session.query(DeviceGroup).filter(
                DeviceGroup.id == group_id,
                DeviceGroup.router_id == g.router_id,
                DeviceGroup.user_id == g.user_id
            ).first()
            
            if not group:
                return build_error_response("Group not found or access denied", 404, "NOT_FOUND", start_time)
            
            # Check if rule already exists
            existing_rule = session.query(ContentControlRules).filter(
                ContentControlRules.router_id == g.router_id,
                ContentControlRules.group_id == group_id
            ).first()
            
            if existing_rule:
                # Update existing rule
                existing_rule.blocked_categories = data.get('blocked_categories', [])
                existing_rule.description = data.get('description')
                existing_rule.is_active = data.get('is_active', True)
                session.commit()
                return build_success_response(existing_rule.to_dict(), start_time)
            else:
                # Create new rule
                new_rule = ContentControlRules(
                    group_id=group_id,
                    router_id=g.router_id,
                    blocked_categories=data.get('blocked_categories', []),
                    description=data.get('description'),
                    is_active=data.get('is_active', True)
                )
                session.add(new_rule)
                session.commit()
                return build_success_response(new_rule.to_dict(), start_time)
                
    except Exception as e:
        logger.error(f"Failed to set group content control rules: {e}")
        return build_error_response(f"Failed to set group content control rules: {str(e)}", 500, "DATABASE_ERROR", start_time)


@agh_bp.route('/rules/group/<group_id>', methods=['DELETE'])
@router_context_required
def delete_group_content_control_rules(group_id):
    """Delete content control rules for a group"""
    start_time = time.time()
    try:
        from models import ContentControlRules
        from database.session import get_db_session
        
        with get_db_session() as session:
            rule = session.query(ContentControlRules).filter(
                ContentControlRules.router_id == g.router_id,
                ContentControlRules.group_id == group_id
            ).first()
            
            if rule:
                session.delete(rule)
                session.commit()
                return build_success_response({"message": "Content control rules deleted successfully"}, start_time)
            else:
                return build_success_response({"message": "No rules found to delete"}, start_time)
                
    except Exception as e:
        logger.error(f"Failed to delete group content control rules: {e}")
        return build_error_response(f"Failed to delete group content control rules: {str(e)}", 500, "DATABASE_ERROR", start_time)


