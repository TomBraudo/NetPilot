"""
AGH (AdGuard Home) Commands Server Operations

This module forwards AGH-related operations to the Commands Server.
All functions return (result, error) tuples and are decorated to inject
the Commands Server manager and handle errors consistently.
"""

from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import with_commands_server, handle_commands_errors

logger = get_logger('services.commands_server_operations.agh_execute')

base_path = "/api/agh"


@with_commands_server
@handle_commands_errors("AGH: List categories")
def execute_get_categories(commands_server, router_id: str, session_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/categories"
    response_data, error = commands_server.execute_router_command(router_id, session_id, endpoint, "GET", None, None)
    if error:
        return None, error
    return response_data, None


@with_commands_server
@handle_commands_errors("AGH: Create category")
def execute_create_category(commands_server, router_id: str, session_id: str, category: str, domains: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/categories"
    body = {"category": category, "domains": domains or []}
    response_data, error = commands_server.execute_router_command(router_id, session_id, endpoint, "POST", None, body)
    if error:
        return None, error
    return response_data, None


@with_commands_server
@handle_commands_errors("AGH: Get category domains")
def execute_get_category_domains(commands_server, router_id: str, session_id: str, category: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/categories/{category}/domains"
    response_data, error = commands_server.execute_router_command(router_id, session_id, endpoint, "GET", None, None)
    if error:
        return None, error
    return response_data, None

@with_commands_server
@handle_commands_errors("AGH: Delete category")
def execute_delete_category(commands_server, router_id: str, session_id: str, category: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/categories"
    body = {"category": category}
    response_data, error = commands_server.execute_router_command(router_id, session_id, endpoint, "DELETE", None, body)
    if error:
        return None, error
    return response_data, None


@with_commands_server
@handle_commands_errors("AGH: Replace category domains")
def execute_replace_category_domains(commands_server, router_id: str, session_id: str, category: str, domains: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/categories/{category}/domains"
    body = {"domains": domains or []}
    response_data, error = commands_server.execute_router_command(router_id, session_id, endpoint, "PUT", None, body)
    if error:
        return None, error
    return response_data, None


@with_commands_server
@handle_commands_errors("AGH: Get device effective rules")
def execute_get_device_effective_rules(commands_server, router_id: str, session_id: str, mac: Optional[str], ip: Optional[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/device/rules"
    query = {}
    if mac:
        query["mac"] = mac
    if ip:
        query["ip"] = ip
    response_data, error = commands_server.execute_router_command(router_id, session_id, endpoint, "GET", query, None)
    if error:
        return None, error
    return response_data, None


@with_commands_server
@handle_commands_errors("AGH: Bulk get devices rules")
def execute_bulk_get_devices_rules(commands_server, router_id: str, session_id: str, devices: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/devices/rules"
    body = {"devices": devices or []}
    response_data, error = commands_server.execute_router_command(router_id, session_id, endpoint, "POST", None, body)
    if error:
        return None, error
    return response_data, None


@with_commands_server
@handle_commands_errors("AGH: Set device rules")
def execute_set_device_rules(commands_server, router_id: str, session_id: str, device: Dict[str, Any], categories: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/device/rules"
    body = {"device": device or {}, "categories": categories or []}
    response_data, error = commands_server.execute_router_command(router_id, session_id, endpoint, "POST", None, body)
    if error:
        return None, error
    return response_data, None


@with_commands_server
@handle_commands_errors("AGH: Set devices rules (bulk)")
def execute_set_devices_rules(commands_server, router_id: str, session_id: str, devices: List[Dict[str, Any]], categories: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/devices/rules/set"
    body = {"devices": devices or [], "categories": categories or []}
    response_data, error = commands_server.execute_router_command(router_id, session_id, endpoint, "POST", None, body)
    if error:
        return None, error
    return response_data, None


@with_commands_server
@handle_commands_errors("AGH: Clear device rules")
def execute_clear_device_rules(commands_server, router_id: str, session_id: str, device: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/device/rules"
    body = {"device": device or {}}
    response_data, error = commands_server.execute_router_command(router_id, session_id, endpoint, "DELETE", None, body)
    if error:
        return None, error
    return response_data, None


@with_commands_server
@handle_commands_errors("AGH: Clear devices rules (bulk)")
def execute_clear_devices_rules(commands_server, router_id: str, session_id: str, devices: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/devices/rules"
    body = {"devices": devices or []}
    response_data, error = commands_server.execute_router_command(router_id, session_id, endpoint, "DELETE", None, body)
    if error:
        return None, error
    return response_data, None


