"""
Bandwidth Commands Server Operations

This module forwards bandwidth-related operations to the Commands Server.
All functions return (result, error) tuples and are decorated to inject
the Commands Server manager and handle errors consistently.
"""

from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import with_commands_server, handle_commands_errors

logger = get_logger('services.commands_server_operations.bandwidth_execute')

base_path = "/api/bandwidth"


def _compact_body(body: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in body.items() if v is not None}


@with_commands_server
@handle_commands_errors("Bandwidth: Apply group limits")
def execute_apply_group_limits(
    commands_server,
    router_id: str,
    session_id: str,
    ips: List[str],
    download_kbytes: Optional[int] = None,
    upload_kbytes: Optional[int] = None,
    download_mbps: Optional[float] = None,
    upload_mbps: Optional[float] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/limits/group"
    body = _compact_body({
        "ips": ips or [],
        "download_kbytes": download_kbytes,
        "upload_kbytes": upload_kbytes,
        "download_mbps": download_mbps,
        "upload_mbps": upload_mbps,
    })
    return commands_server.execute_router_command(router_id, session_id, endpoint, "POST", None, body)


@with_commands_server
@handle_commands_errors("Bandwidth: Delete group limits")
def execute_delete_group_limits(
    commands_server,
    router_id: str,
    session_id: str,
    ips: List[str],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/limits/group"
    body = {"ips": ips or []}
    return commands_server.execute_router_command(router_id, session_id, endpoint, "DELETE", None, body)


@with_commands_server
@handle_commands_errors("Bandwidth: Apply device limit")
def execute_apply_device_limit(
    commands_server,
    router_id: str,
    session_id: str,
    ip: str,
    download_kbytes: Optional[int] = None,
    upload_kbytes: Optional[int] = None,
    download_mbps: Optional[float] = None,
    upload_mbps: Optional[float] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/limits/device"
    body = _compact_body({
        "ip": ip,
        "download_kbytes": download_kbytes,
        "upload_kbytes": upload_kbytes,
        "download_mbps": download_mbps,
        "upload_mbps": upload_mbps,
    })
    return commands_server.execute_router_command(router_id, session_id, endpoint, "POST", None, body)


@with_commands_server
@handle_commands_errors("Bandwidth: Delete device limit")
def execute_delete_device_limit(
    commands_server,
    router_id: str,
    session_id: str,
    ip: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/limits/device"
    body = {"ip": ip}
    return commands_server.execute_router_command(router_id, session_id, endpoint, "DELETE", None, body)


@with_commands_server
@handle_commands_errors("Bandwidth: Activate global limits")
def execute_activate_global_limits(
    commands_server,
    router_id: str,
    session_id: str,
    download_kbytes: int,
    upload_kbytes: int,
    lan_cidr: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/global/activate"
    body = _compact_body({
        "download_kbytes": download_kbytes,
        "upload_kbytes": upload_kbytes,
        "lan_cidr": lan_cidr,
    })
    return commands_server.execute_router_command(router_id, session_id, endpoint, "POST", None, body)


@with_commands_server
@handle_commands_errors("Bandwidth: Deactivate global limits")
def execute_deactivate_global_limits(
    commands_server,
    router_id: str,
    session_id: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/global/deactivate"
    return commands_server.execute_router_command(router_id, session_id, endpoint, "DELETE", None, None)


@with_commands_server
@handle_commands_errors("Bandwidth: Add to global whitelist")
def execute_add_global_whitelist(
    commands_server,
    router_id: str,
    session_id: str,
    ips: List[str],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/global/whitelist"
    body = {"ips": ips or []}
    return commands_server.execute_router_command(router_id, session_id, endpoint, "POST", None, body)


@with_commands_server
@handle_commands_errors("Bandwidth: Remove from global whitelist")
def execute_remove_global_whitelist(
    commands_server,
    router_id: str,
    session_id: str,
    ips: List[str],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    endpoint = f"{base_path}/global/whitelist"
    body = {"ips": ips or []}
    return commands_server.execute_router_command(router_id, session_id, endpoint, "DELETE", None, body)


