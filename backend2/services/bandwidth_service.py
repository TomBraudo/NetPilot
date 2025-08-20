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
from models.device_group import DeviceGroup
from managers.db_session_context import SessionContext
from sqlalchemy.orm import joinedload
from services.db_operations.bandwidth_db import (
    get_all_bandwidth_rules as bw_db_get_all_rules,
    get_group_bandwidth_rule as bw_db_get_group_rule,
    upsert_group_bandwidth_rule as bw_db_upsert_group_rule,
    delete_group_bandwidth_rule as bw_db_delete_group_rule,
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



def resolve_group_params(user_id: str, router_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bandwidth resolver: if params contains group_id, resolve current group member IPs
    and return a new params dict with 'ips' injected. Other params are unchanged.
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

    ips: List[str] = []
    for device in group.devices:
        ip_value = getattr(device, 'ip', None)
        if ip_value:
            ip_str = str(ip_value).strip()
            if ip_str:
                ips.append(ip_str)

    # Deduplicate while preserving order
    seen = set()
    deduped_ips = [ip for ip in ips if not (ip in seen or seen.add(ip))]

    merged = dict(params)
    merged['ips'] = deduped_ips
    return merged


# Database-backed bandwidth rules (moved from endpoints)
def get_all_rules_db(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    log_service_operation("bandwidth_db_get_all_rules", user_id, router_id, session_id)
    return bw_db_get_all_rules(user_id, router_id)


def get_group_rule_db(user_id: str, router_id: str, session_id: str, group_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    log_service_operation("bandwidth_db_get_group_rule", user_id, router_id, session_id, {"group_id": group_id})
    return bw_db_get_group_rule(user_id, router_id, group_id)


def set_group_rule_db(
    user_id: str,
    router_id: str,
    session_id: str,
    group_id: str,
    download_limit_mbps: Optional[float],
    upload_limit_mbps: Optional[float],
    description: Optional[str] = None,
    is_active: bool = True,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    log_service_operation("bandwidth_db_upsert_group_rule", user_id, router_id, session_id, {
        "group_id": group_id,
        "download_limit_mbps": download_limit_mbps,
        "upload_limit_mbps": upload_limit_mbps,
        "is_active": is_active,
    })
    return bw_db_upsert_group_rule(user_id, router_id, group_id, download_limit_mbps, upload_limit_mbps, description, is_active)


def delete_group_rule_db(user_id: str, router_id: str, session_id: str, group_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    log_service_operation("bandwidth_db_delete_group_rule", user_id, router_id, session_id, {"group_id": group_id})
    return bw_db_delete_group_rule(user_id, router_id, group_id)




