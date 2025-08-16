from flask import Blueprint, request
import time

from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response

from services.agh_service import (
    list_categories,
    get_category_domains,
    create_category,
    set_category_domains,
    get_client_effective_rules,
    get_clients_effective_rules,
    mark_device,
    mark_devices_for_categories,
    clear_device_rules,
    clear_devices_rules,
    delete_category,
)


agh_bp = Blueprint('agh', __name__)
logger = get_logger('endpoints.agh')


# ----------------------------- Categories -----------------------------

@agh_bp.route('/categories', methods=['GET'])
def get_categories_route():
    start_time = time.time()
    result, error = list_categories()
    if error:
        return build_error_response(f"Failed to list categories: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response({"categories": result or []}, start_time)


@agh_bp.route('/categories/<category>/domains', methods=['GET'])
def get_category_domains_route(category):
    start_time = time.time()
    domains, error = get_category_domains(category)
    if error:
        return build_error_response(f"Failed to get domains: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response({
        "category": category,
        "domains": domains or [],
        "count": len(domains or []),
    }, start_time)


@agh_bp.route('/categories', methods=['POST'])
def create_category_route():
    start_time = time.time()
    data = request.get_json() or {}
    category = (data.get('category') or '').strip()
    domains = data.get('domains') or []
    if not category:
        return build_error_response("Missing 'category'", 400, "BAD_REQUEST", start_time)
    if not isinstance(domains, list):
        return build_error_response("'domains' must be a list", 400, "BAD_REQUEST", start_time)
    result, error = create_category(category, domains)
    if error:
        return build_error_response(f"Failed to create category: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@agh_bp.route('/categories', methods=['DELETE'])
def delete_category_route():
    start_time = time.time()
    data = request.get_json() or {}
    category = (data.get('category') or '').strip()
    if not category:
        return build_error_response("Missing 'category'", 400, "BAD_REQUEST", start_time)
    result, error = delete_category(category)
    if error:
        return build_error_response(f"Failed to delete category: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/categories/<category>/domains', methods=['PUT'])
def patch_category_route(category):
    start_time = time.time()
    data = request.get_json() or {}
    domains = data.get('domains')
    if not isinstance(domains, list):
        return build_error_response("'domains' must be a list", 400, "BAD_REQUEST", start_time)
    result, error = set_category_domains(category, domains, mode="replace")
    if error:
        return build_error_response(f"Failed to set category domains: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


# ------------------------------ Rules (read) ------------------------------

@agh_bp.route('/device/rules', methods=['GET'])
def get_device_rules_route():
    start_time = time.time()
    mac = request.args.get('mac')
    ip = request.args.get('ip') or request.args.get('ipv4')
    if not mac and not ip:
        return build_error_response("Provide 'mac' or 'ip'", 400, "BAD_REQUEST", start_time)
    summary, error = get_client_effective_rules({"mac": mac, "ipv4": ip})
    if error:
        return build_error_response(f"Failed to get device rules: {error}", 500, "COMMAND_FAILED", start_time)
    # Return only categories per spec
    categories = (summary or {}).get('categories', []) if isinstance(summary, dict) else []
    return build_success_response({"categories": categories, "client": (summary or {}).get('client')}, start_time)


@agh_bp.route('/devices/rules', methods=['POST'])
def get_devices_rules_route():
    start_time = time.time()
    data = request.get_json() or {}
    devices = data.get('devices') or []
    if not isinstance(devices, list) or not devices:
        return build_error_response("'devices' must be a non-empty list", 400, "BAD_REQUEST", start_time)
    # Normalize device items to expected keys
    norm = []
    for d in devices:
        mac = (d or {}).get('mac')
        ip = (d or {}).get('ip') or (d or {}).get('ipv4')
        norm.append({"mac": mac, "ipv4": ip})
    results, error = get_clients_effective_rules(norm)
    if error:
        return build_error_response(f"Failed to get devices rules: {error}", 500, "COMMAND_FAILED", start_time)
    # Map to desired output: {input -> categories}
    out = []
    for item in results or []:
        res = item.get('result') or {}
        out.append({
            "input": item.get('input'),
            "categories": res.get('categories', []) if isinstance(res, dict) else [],
            "client": res.get('client') if isinstance(res, dict) else None,
        })
    return build_success_response({"results": out}, start_time)


# ------------------------------ Rules (write) ------------------------------

@agh_bp.route('/device/rules', methods=['POST'])
def set_device_rules_route():
    start_time = time.time()
    data = request.get_json() or {}
    dev = data.get('device') or {}
    categories = data.get('categories') or []
    if not isinstance(categories, list) or not categories:
        return build_error_response("'categories' must be a non-empty list", 400, "BAD_REQUEST", start_time)
    mac = dev.get('mac')
    ip = dev.get('ip') or dev.get('ipv4')
    if not mac and not ip:
        return build_error_response("device requires 'mac' or 'ip'", 400, "BAD_REQUEST", start_time)
    # Use bulk mark under the hood
    result, error = mark_device({"mac": mac, "ipv4": ip}, categories)
    if error:
        return build_error_response(f"Failed to set device rules: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/devices/rules/set', methods=['POST'])
def set_devices_rules_route():
    start_time = time.time()
    data = request.get_json() or {}
    devices = data.get('devices') or []
    categories = data.get('categories') or []
    if not isinstance(devices, list) or not devices:
        return build_error_response("'devices' must be a non-empty list", 400, "BAD_REQUEST", start_time)
    if not isinstance(categories, list) or not categories:
        return build_error_response("'categories' must be a non-empty list", 400, "BAD_REQUEST", start_time)
    # Normalize and apply
    norm = []
    for d in devices:
        mac = (d or {}).get('mac')
        ip = (d or {}).get('ip') or (d or {}).get('ipv4')
        norm.append({"mac": mac, "ipv4": ip})
    result, error = mark_devices_for_categories(norm, categories)
    if error:
        return build_error_response(f"Failed to set devices rules: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/device/rules', methods=['DELETE'])
def clear_device_rules_route():
    start_time = time.time()
    data = request.get_json() or {}
    dev = data.get('device') or {}
    mac = dev.get('mac')
    ip = dev.get('ip') or dev.get('ipv4')
    if not mac and not ip:
        return build_error_response("device requires 'mac' or 'ip'", 400, "BAD_REQUEST", start_time)
    result, error = clear_device_rules({"mac": mac, "ipv4": ip})
    if error:
        return build_error_response(f"Failed to clear device rules: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@agh_bp.route('/devices/rules', methods=['DELETE'])
def clear_devices_rules_route():
    start_time = time.time()
    data = request.get_json() or {}
    devices = data.get('devices') or []
    if not isinstance(devices, list) or not devices:
        return build_error_response("'devices' must be a non-empty list", 400, "BAD_REQUEST", start_time)
    norm = []
    for d in devices:
        mac = (d or {}).get('mac')
        ip = (d or {}).get('ip') or (d or {}).get('ipv4')
        norm.append({"mac": mac, "ipv4": ip})
    result, error = clear_devices_rules(norm)
    if error:
        return build_error_response(f"Failed to clear devices rules: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


