"""
AGH (AdGuard Home) Service - Orchestration Layer

Coordinates AGH operations by forwarding to commands server operation functions.
Validates inputs lightly and returns (result, error) tuples.
"""

from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import handle_service_errors, log_service_operation
from services.commands_server_operations.agh_execute import (
    execute_get_categories,
    execute_create_category,
    execute_get_category_domains,
    execute_delete_category,
    execute_replace_category_domains,
    execute_get_device_effective_rules,
    execute_bulk_get_devices_rules,
    execute_set_device_rules,
    execute_set_devices_rules,
    execute_clear_device_rules,
    execute_clear_devices_rules,
)
from models.device_group import DeviceGroup
from managers.db_session_context import SessionContext
from sqlalchemy.orm import joinedload
from services.db_operations.agh_db import (
    get_all_content_control_rules as agh_db_get_all_rules,
    get_group_content_control_rule as agh_db_get_group_rule,
    upsert_group_content_control_rule as agh_db_upsert_group_rule,
    delete_group_content_control_rule as agh_db_delete_group_rule,
)
from services.task_registry import register_task

logger = get_logger('services.agh_service')


def resolve_group_params(user_id: str, router_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    AGH resolver: if params contains group_id, resolve current group member IPs
    and return a new params dict with 'devices' injected. Other params are unchanged.
    """
    group_id = params.get('group_id')
    if not group_id:
        return params

    session = SessionContext.get()
    group = (
        session.query(DeviceGroup)
        .options(joinedload(DeviceGroup.devices))
        .filter(
            DeviceGroup.id == group_id,
            DeviceGroup.user_id == user_id,
            DeviceGroup.router_id == router_id,
        )
        .first()
    )

    if not group:
        raise ValueError(f"Group not found or access denied: {group_id}")

    devices: List[Dict[str, Any]] = []
    for device in group.devices:
        # Enforce MAC presence for scheduler paths too
        if not getattr(device, 'mac', None):
            continue
        devices.append({
            'mac': str(device.mac),
            'ipv4': str(device.ip) if getattr(device, 'ip', None) else None,
        })

    return {**params, 'devices': devices}


@handle_service_errors("AGH: List categories")
def get_categories(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    log_service_operation("agh_get_categories", user_id, router_id, session_id)
    data, error = execute_get_categories(router_id, session_id)
    if error:
        return None, error
    return data, None


@handle_service_errors("AGH: Create category")
def create_category(user_id: str, router_id: str, session_id: str, category: str, domains: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not category:
        return None, "category is required"
    log_service_operation("agh_create_category", user_id, router_id, session_id, {"category": category, "domains": domains})
    data, error = execute_create_category(router_id, session_id, category, domains or [])
    if error:
        return None, error
    return data, None


@handle_service_errors("AGH: Get category domains")
def get_category_domains(user_id: str, router_id: str, session_id: str, category: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not category:
        return None, "category is required"
    log_service_operation("agh_get_category_domains", user_id, router_id, session_id, {"category": category})
    data, error = execute_get_category_domains(router_id, session_id, category)
    if error:
        return None, error
    return data, None


@handle_service_errors("AGH: Delete category")
def delete_category(user_id: str, router_id: str, session_id: str, category: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not category:
        return None, "category is required"
    log_service_operation("agh_delete_category", user_id, router_id, session_id, {"category": category})
    data, error = execute_delete_category(router_id, session_id, category)
    if error:
        return None, error
    return data, None


@handle_service_errors("AGH: Replace category domains")
def replace_category_domains(user_id: str, router_id: str, session_id: str, category: str, domains: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not category:
        return None, "category is required"
    log_service_operation("agh_replace_category_domains", user_id, router_id, session_id, {"category": category, "domains": domains})
    data, error = execute_replace_category_domains(router_id, session_id, category, domains or [])
    if error:
        return None, error
    return data, None


@handle_service_errors("AGH: Get device effective rules")
def get_device_effective_rules(user_id: str, router_id: str, session_id: str, mac: Optional[str], ip: Optional[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    # Enforce MAC
    if not mac:
        return None, "mac is required"
    log_service_operation("agh_get_device_effective_rules", user_id, router_id, session_id, {"mac": mac, "ip": ip})
    data, error = execute_get_device_effective_rules(router_id, session_id, mac, ip)
    if error:
        return None, error
    return data, None


@handle_service_errors("AGH: Bulk get devices rules")
def bulk_get_devices_rules(user_id: str, router_id: str, session_id: str, devices: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(devices, list):
        return None, "devices must be a list"
    # Enforce MAC per device and normalize ipv4
    normalized_devices: List[Dict[str, Any]] = []
    for device in devices or []:
        if not isinstance(device, dict):
            return None, "each device must be an object"
        mac = (device or {}).get('mac')
        if not mac:
            return None, "each device must include 'mac'"
        ipv4 = (device or {}).get('ipv4') or (device or {}).get('ip')
        normalized_devices.append({'mac': mac, 'ipv4': ipv4})
    log_service_operation("agh_bulk_get_devices_rules", user_id, router_id, session_id, {"count": len(devices or [])})
    data, error = execute_bulk_get_devices_rules(router_id, session_id, normalized_devices or [])
    if error:
        return None, error
    return data, None


@register_task("agh.set_device_rules")
@handle_service_errors("AGH: Set device rules")
def set_device_rules(user_id: str, router_id: str, session_id: str, device: Dict[str, Any], categories: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(device, dict):
        return None, "device must be an object"
    if not isinstance(categories, list):
        return None, "categories must be a list"
    # Enforce MAC and normalize ipv4
    mac = (device or {}).get('mac')
    if not mac:
        return None, "mac is required"
    ipv4 = (device or {}).get('ipv4') or (device or {}).get('ip')
    device_norm = {'mac': mac, 'ipv4': ipv4}
    log_service_operation("agh_set_device_rules", user_id, router_id, session_id, {"device": device_norm, "categories": categories})
    data, error = execute_set_device_rules(router_id, session_id, device_norm, categories or [])
    if error:
        return None, error
    return data, None


@register_task("agh.set_devices_rules", resolve_group_params)
@handle_service_errors("AGH: Set devices rules (bulk)")
def set_devices_rules(user_id: str, router_id: str, session_id: str, devices: List[Dict[str, Any]], categories: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(devices, list):
        return None, "devices must be a list"
    if not isinstance(categories, list):
        return None, "categories must be a list"
    # Enforce MAC per device and normalize ipv4; stop on first error
    normalized_devices: List[Dict[str, Any]] = []
    for device in devices or []:
        if not isinstance(device, dict):
            return None, "each device must be an object"
        mac = (device or {}).get('mac')
        if not mac:
            return None, "each device must include 'mac'"
        ipv4 = (device or {}).get('ipv4') or (device or {}).get('ip')
        normalized_devices.append({'mac': mac, 'ipv4': ipv4})
    log_service_operation("agh_set_devices_rules", user_id, router_id, session_id, {"count": len(normalized_devices or []), "categories": categories})
    data, error = execute_set_devices_rules(router_id, session_id, normalized_devices or [], categories or [])
    if error:
        return None, error
    return data, None


@register_task("agh.clear_device_rules")
@handle_service_errors("AGH: Clear device rules")
def clear_device_rules(user_id: str, router_id: str, session_id: str, device: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(device, dict):
        return None, "device must be an object"
    mac = (device or {}).get('mac')
    if not mac:
        return None, "mac is required"
    ipv4 = (device or {}).get('ipv4') or (device or {}).get('ip')
    device_norm = {'mac': mac, 'ipv4': ipv4}
    log_service_operation("agh_clear_device_rules", user_id, router_id, session_id, {"device": device_norm})
    data, error = execute_clear_device_rules(router_id, session_id, device_norm)
    if error:
        return None, error
    return data, None


@register_task("agh.clear_devices_rules", resolve_group_params)
@handle_service_errors("AGH: Clear devices rules (bulk)")
def clear_devices_rules(user_id: str, router_id: str, session_id: str, devices: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(devices, list):
        return None, "devices must be a list"
    # Enforce MAC per device and normalize ipv4; stop on first error
    normalized_devices: List[Dict[str, Any]] = []
    for device in devices or []:
        if not isinstance(device, dict):
            return None, "each device must be an object"
        mac = (device or {}).get('mac')
        if not mac:
            return None, "each device must include 'mac'"
        ipv4 = (device or {}).get('ipv4') or (device or {}).get('ip')
        normalized_devices.append({'mac': mac, 'ipv4': ipv4})
    log_service_operation("agh_clear_devices_rules", user_id, router_id, session_id, {"count": len(normalized_devices or [])})
    data, error = execute_clear_devices_rules(router_id, session_id, normalized_devices or [])
    if error:
        return None, error
    return data, None


# Part 1: Ensure orchestrator service functions exist for content control rules endpoints
@handle_service_errors("AGH: Get all content control rules")
def get_all_content_control_rules(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    log_service_operation("agh_get_all_content_control_rules", user_id, router_id, session_id)
    return agh_db_get_all_rules(user_id, router_id)


@handle_service_errors("AGH: Get group content control rules")
def get_group_content_control_rules(user_id: str, router_id: str, session_id: str, group_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    log_service_operation("agh_get_group_content_control_rules", user_id, router_id, session_id, {"group_id": group_id})
    return agh_db_get_group_rule(user_id, router_id, group_id)


@handle_service_errors("AGH: Set group content control rules")
def set_group_content_control_rules(
    user_id: str,
    router_id: str,
    session_id: str,
    group_id: str,
    blocked_categories: List[str],
    description: Optional[str] = None,
    is_active: bool = True,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    log_service_operation("agh_set_group_content_control_rules", user_id, router_id, session_id, {
        "group_id": group_id,
        "blocked_categories": blocked_categories,
        "is_active": is_active,
    })
    # 1) Persist rule in DB
    db_result, db_error = agh_db_upsert_group_rule(user_id, router_id, group_id, blocked_categories, description, is_active)
    if db_error:
        return None, db_error

    # 2) Resolve current group members and apply to router
    try:
        resolved = resolve_group_params(user_id, router_id, {"group_id": group_id})
        devices: List[Dict[str, Any]] = resolved.get("devices", [])
    except Exception as e:
        # Roll back DB on resolver failure
        agh_db_delete_group_rule(user_id, router_id, group_id)
        return None, f"Failed resolving group devices: {e}"

    if not devices:
        return db_result, None

    exec_result, exec_error = execute_set_devices_rules(router_id, session_id, devices, blocked_categories or [])
    if exec_error:
        # Compensating rollback
        agh_db_delete_group_rule(user_id, router_id, group_id)
        return None, exec_error

    return db_result, None


@handle_service_errors("AGH: Delete group content control rules")
def delete_group_content_control_rules(user_id: str, router_id: str, session_id: str, group_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    log_service_operation("agh_delete_group_content_control_rules", user_id, router_id, session_id, {"group_id": group_id})

    # Read previous rule for rollback if needed
    prev_rule, _ = agh_db_get_group_rule(user_id, router_id, group_id)

    # 1) Delete rule from DB (success if not exists)
    db_result, db_error = agh_db_delete_group_rule(user_id, router_id, group_id)
    if db_error:
        return None, db_error

    # 2) Resolve current group members and clear on router
    try:
        resolved = resolve_group_params(user_id, router_id, {"group_id": group_id})
        devices: List[Dict[str, Any]] = resolved.get("devices", [])
    except Exception as e:
        return None, f"Failed resolving group devices: {e}"

    if not devices:
        return db_result, None

    exec_result, exec_error = execute_clear_devices_rules(router_id, session_id, devices)
    if exec_error:
        # Compensating rollback: restore previous rule if existed
        if prev_rule:
            agh_db_upsert_group_rule(
                user_id,
                router_id,
                group_id,
                prev_rule.get("blocked_categories", []),
                prev_rule.get("description"),
                prev_rule.get("is_active", True),
            )
        return None, exec_error

    return db_result, None