from flask import Blueprint, request, g
from utils.response_helpers import build_success_response, build_error_response
from utils.logging_config import get_logger
from utils.middleware import router_context_required
from services.bandwidth_service import (
    apply_group_limits,
    delete_group_limits,
    apply_device_limit,
    delete_device_limit,
    get_all_rules_db,
    get_group_rule_db,
    set_group_rule_db,
    delete_group_rule_db,
)
import time

bandwidth_bp = Blueprint('bandwidth', __name__)
logger = get_logger('endpoints.bandwidth')


@bandwidth_bp.route('/limits/group', methods=['POST'])
@router_context_required
def limits_group_apply():
    start_time = time.time()
    data = request.get_json() or {}
    ips = data.get('ips') or []
    result, error = apply_group_limits(
        g.user_id, g.router_id, g.session_id,
        ips,
        data.get('download_kbytes'),
        data.get('upload_kbytes'),
        data.get('download_mbps'),
        data.get('upload_mbps'),
    )
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/limits/group', methods=['DELETE'])
@router_context_required
def limits_group_delete():
    start_time = time.time()
    data = request.get_json() or {}
    ips = data.get('ips') or []
    result, error = delete_group_limits(g.user_id, g.router_id, g.session_id, ips)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/limits/device', methods=['POST'])
@router_context_required
def limits_device_apply():
    start_time = time.time()
    data = request.get_json() or {}
    ip = data.get('ip')
    result, error = apply_device_limit(
        g.user_id, g.router_id, g.session_id,
        ip,
        data.get('download_kbytes'),
        data.get('upload_kbytes'),
        data.get('download_mbps'),
        data.get('upload_mbps'),
    )
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/limits/device', methods=['DELETE'])
@router_context_required
def limits_device_delete():
    start_time = time.time()
    data = request.get_json() or {}
    ip = data.get('ip')
    result, error = delete_device_limit(g.user_id, g.router_id, g.session_id, ip)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/global/activate', methods=['POST'])
@router_context_required
def global_activate():
    start_time = time.time()
    data = request.get_json() or {}
    result, error = activate_global_limits(
        g.user_id, g.router_id, g.session_id,
        data.get('download_kbytes'),
        data.get('upload_kbytes'),
        data.get('lan_cidr'),
    )
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/global/deactivate', methods=['DELETE'])
@router_context_required
def global_deactivate():
    start_time = time.time()
    result, error = deactivate_global_limits(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


# Removed global whitelist endpoints

# Database Rules Endpoints
@bandwidth_bp.route('/rules', methods=['GET'])
@router_context_required
def get_all_bandwidth_rules():
    """Get all bandwidth rules for a router"""
    start_time = time.time()
    result, error = get_all_rules_db(g.user_id, g.router_id, g.session_id)
    if error:
        logger.error(f"Failed to get bandwidth rules: {error}")
        return build_error_response(f"Failed to get bandwidth rules: {error}", 500, "DATABASE_ERROR", start_time)
    return build_success_response(result or [], start_time)


@bandwidth_bp.route('/rules/group/<group_id>', methods=['GET'])
@router_context_required
def get_group_bandwidth_rules(group_id):
    """Get bandwidth rules for a specific group"""
    start_time = time.time()
    result, error = get_group_rule_db(g.user_id, g.router_id, g.session_id, group_id)
    if error:
        logger.error(f"Failed to get group bandwidth rules: {error}")
        return build_error_response(f"Failed to get group bandwidth rules: {error}", 500, "DATABASE_ERROR", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/rules/group/<group_id>', methods=['POST'])
@bandwidth_bp.route('/rules/group/<group_id>', methods=['PUT'])
@router_context_required
def set_group_bandwidth_rules(group_id):
    """Create or update bandwidth rules for a group"""
    start_time = time.time()
    data = request.get_json() or {}
    result, error = set_group_rule_db(
        g.user_id,
        g.router_id,
        g.session_id,
        group_id,
        data.get('download_limit_mbps'),
        data.get('upload_limit_mbps'),
        data.get('description'),
        bool(data.get('is_active', True)),
    )
    if error:
        logger.error(f"Failed to set group bandwidth rules: {error}")
        return build_error_response(f"Failed to set group bandwidth rules: {error}", 500, "DATABASE_ERROR", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/rules/group/<group_id>', methods=['DELETE'])
@router_context_required
def delete_group_bandwidth_rules(group_id):
    """Delete bandwidth rules for a group"""
    start_time = time.time()
    result, error = delete_group_rule_db(g.user_id, g.router_id, g.session_id, group_id)
    if error:
        logger.error(f"Failed to delete group bandwidth rules: {error}")
        return build_error_response(f"Failed to delete group bandwidth rules: {error}", 500, "DATABASE_ERROR", start_time)
    # If DB op returns None (no rule), still respond successfully
    return build_success_response(result or {"message": "Deleted (if existed)"}, start_time)


