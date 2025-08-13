from flask import Blueprint, request, g
from utils.response_helpers import build_success_response, build_error_response
from utils.logging_config import get_logger
from utils.middleware import router_context_required
from services.bandwidth_service import (
    apply_group_limits,
    delete_group_limits,
    apply_device_limit,
    delete_device_limit,
    activate_global_limits,
    deactivate_global_limits,
    add_global_whitelist,
    remove_global_whitelist,
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


@bandwidth_bp.route('/global/whitelist', methods=['POST'])
@router_context_required
def global_whitelist_add():
    start_time = time.time()
    data = request.get_json() or {}
    ips = data.get('ips') or []
    result, error = add_global_whitelist(g.user_id, g.router_id, g.session_id, ips)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/global/whitelist', methods=['DELETE'])
@router_context_required
def global_whitelist_remove():
    start_time = time.time()
    data = request.get_json() or {}
    ips = data.get('ips') or []
    result, error = remove_global_whitelist(g.user_id, g.router_id, g.session_id, ips)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


