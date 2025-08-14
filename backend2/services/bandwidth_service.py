"""
Bandwidth Service - Orchestration Layer

Coordinates bandwidth operations by forwarding to commands server operation functions.
Validates inputs and returns (result, error) tuples.
"""

from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import handle_service_errors, log_service_operation
from services.commands_server_operations.bandwidth_execute import (
    execute_apply_group_limits,
    execute_delete_group_limits,
    execute_apply_device_limit,
    execute_delete_device_limit,
    execute_activate_global_limits,
    execute_deactivate_global_limits,
)

logger = get_logger('services.bandwidth_service')


def _validate_ips(ips: List[str]) -> Optional[str]:
    if not isinstance(ips, list) or any((not isinstance(ip, str) or not ip) for ip in ips):
        return "ips must be a non-empty array of strings"
    return None


@handle_service_errors("Bandwidth: Apply group limits")
def apply_group_limits(user_id: str, router_id: str, session_id: str, ips: List[str],
                      download_kbytes: Optional[int] = None, upload_kbytes: Optional[int] = None,
                      download_mbps: Optional[float] = None, upload_mbps: Optional[float] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    err = _validate_ips(ips)
    if err:
        return None, err
    log_service_operation("bandwidth_apply_group_limits", user_id, router_id, session_id, {
        "ips": ips,
        "download_kbytes": download_kbytes,
        "upload_kbytes": upload_kbytes,
        "download_mbps": download_mbps,
        "upload_mbps": upload_mbps,
    })
    return execute_apply_group_limits(router_id, session_id, ips, download_kbytes, upload_kbytes, download_mbps, upload_mbps)


@handle_service_errors("Bandwidth: Delete group limits")
def delete_group_limits(user_id: str, router_id: str, session_id: str, ips: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    err = _validate_ips(ips)
    if err:
        return None, err
    log_service_operation("bandwidth_delete_group_limits", user_id, router_id, session_id, {"ips": ips})
    return execute_delete_group_limits(router_id, session_id, ips)


@handle_service_errors("Bandwidth: Apply device limit")
def apply_device_limit(user_id: str, router_id: str, session_id: str, ip: str,
                       download_kbytes: Optional[int] = None, upload_kbytes: Optional[int] = None,
                       download_mbps: Optional[float] = None, upload_mbps: Optional[float] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not ip:
        return None, "ip is required"
    log_service_operation("bandwidth_apply_device_limit", user_id, router_id, session_id, {
        "ip": ip,
        "download_kbytes": download_kbytes,
        "upload_kbytes": upload_kbytes,
        "download_mbps": download_mbps,
        "upload_mbps": upload_mbps,
    })
    return execute_apply_device_limit(router_id, session_id, ip, download_kbytes, upload_kbytes, download_mbps, upload_mbps)


@handle_service_errors("Bandwidth: Delete device limit")
def delete_device_limit(user_id: str, router_id: str, session_id: str, ip: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not ip:
        return None, "ip is required"
    log_service_operation("bandwidth_delete_device_limit", user_id, router_id, session_id, {"ip": ip})
    return execute_delete_device_limit(router_id, session_id, ip)


@handle_service_errors("Bandwidth: Activate global limits")
def activate_global_limits(user_id: str, router_id: str, session_id: str, download_kbytes: int, upload_kbytes: int,
                          lan_cidr: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(download_kbytes, int) or not isinstance(upload_kbytes, int):
        return None, "download_kbytes and upload_kbytes must be integers"
    log_service_operation("bandwidth_activate_global", user_id, router_id, session_id, {
        "download_kbytes": download_kbytes,
        "upload_kbytes": upload_kbytes,
        "lan_cidr": lan_cidr,
    })
    return execute_activate_global_limits(router_id, session_id, download_kbytes, upload_kbytes, lan_cidr)


@handle_service_errors("Bandwidth: Deactivate global limits")
def deactivate_global_limits(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    log_service_operation("bandwidth_deactivate_global", user_id, router_id, session_id)
    return execute_deactivate_global_limits(router_id, session_id)


# Removed global whitelist operations


