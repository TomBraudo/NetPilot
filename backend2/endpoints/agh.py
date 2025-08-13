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
    result, error = set_device_rules(g.user_id, g.router_id, g.session_id, device, categories)
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
    result, error = set_devices_rules(g.user_id, g.router_id, g.session_id, devices, categories)
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
    result, error = clear_device_rules(g.user_id, g.router_id, g.session_id, device)
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
    result, error = clear_devices_rules(g.user_id, g.router_id, g.session_id, devices)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


