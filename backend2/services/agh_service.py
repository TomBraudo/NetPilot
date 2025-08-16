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

logger = get_logger('services.agh_service')


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
    if not mac and not ip:
        return None, "either mac or ip must be provided"
    log_service_operation("agh_get_device_effective_rules", user_id, router_id, session_id, {"mac": mac, "ip": ip})
    data, error = execute_get_device_effective_rules(router_id, session_id, mac, ip)
    if error:
        return None, error
    return data, None


@handle_service_errors("AGH: Bulk get devices rules")
def bulk_get_devices_rules(user_id: str, router_id: str, session_id: str, devices: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(devices, list):
        return None, "devices must be a list"
    log_service_operation("agh_bulk_get_devices_rules", user_id, router_id, session_id, {"count": len(devices or [])})
    data, error = execute_bulk_get_devices_rules(router_id, session_id, devices or [])
    if error:
        return None, error
    return data, None


@handle_service_errors("AGH: Set device rules")
def set_device_rules(user_id: str, router_id: str, session_id: str, device: Dict[str, Any], categories: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(device, dict):
        return None, "device must be an object"
    if not isinstance(categories, list):
        return None, "categories must be a list"
    log_service_operation("agh_set_device_rules", user_id, router_id, session_id, {"device": device, "categories": categories})
    data, error = execute_set_device_rules(router_id, session_id, device or {}, categories or [])
    if error:
        return None, error
    return data, None


@handle_service_errors("AGH: Set devices rules (bulk)")
def set_devices_rules(user_id: str, router_id: str, session_id: str, devices: List[Dict[str, Any]], categories: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(devices, list):
        return None, "devices must be a list"
    if not isinstance(categories, list):
        return None, "categories must be a list"
    log_service_operation("agh_set_devices_rules", user_id, router_id, session_id, {"count": len(devices or []), "categories": categories})
    data, error = execute_set_devices_rules(router_id, session_id, devices or [], categories or [])
    if error:
        return None, error
    return data, None


@handle_service_errors("AGH: Clear device rules")
def clear_device_rules(user_id: str, router_id: str, session_id: str, device: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(device, dict):
        return None, "device must be an object"
    log_service_operation("agh_clear_device_rules", user_id, router_id, session_id, {"device": device})
    data, error = execute_clear_device_rules(router_id, session_id, device or {})
    if error:
        return None, error
    return data, None


@handle_service_errors("AGH: Clear devices rules (bulk)")
def clear_devices_rules(user_id: str, router_id: str, session_id: str, devices: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(devices, list):
        return None, "devices must be a list"
    log_service_operation("agh_clear_devices_rules", user_id, router_id, session_id, {"count": len(devices or [])})
    data, error = execute_clear_devices_rules(router_id, session_id, devices or [])
    if error:
        return None, error
    return data, None


