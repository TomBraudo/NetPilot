from typing import List, Optional, Tuple, Dict
import re

from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager


logger = get_logger('services.time_based')
router_connection_manager = RouterConnectionManager()


def _execute(command: str, timeout: int = 30) -> Tuple[Optional[str], Optional[str]]:
    """Execute a shell command on the router via the shared connection manager."""
    return router_connection_manager.execute(command, timeout=timeout)


def _is_valid_group_name(group_id: str) -> bool:
    """Allow safe group identifiers to avoid shell injection in paths and cron tags."""
    return bool(re.fullmatch(r"[A-Za-z0-9_-]+", group_id))


def _is_valid_days_spec(days_spec: str) -> bool:
    """Validate a crontab day-of-week spec like '1-5' or '1,3,5' or '0-7'."""
    return bool(re.fullmatch(r"[0-7](?:-[0-7])?(?:,[0-7](?:-[0-7])?)*", days_spec))


def _coerce_hour(hour: int | str) -> Optional[str]:
    """Convert hour to a valid crontab hour field (0-23). Returns None if invalid."""
    try:
        value = int(str(hour).strip())
    except Exception:
        return None
    if 0 <= value <= 23:
        return str(value)
    return None


def _sanitize_macs(members: List[str]) -> List[str]:
    """Keep only MAC-like tokens to avoid command injection; allow hex pairs with colons or dashes."""
    safe: List[str] = []
    for mac in members or []:
        token = mac.strip()
        if re.fullmatch(r"(?i)[0-9a-f]{2}([:-][0-9a-f]{2}){5}", token):
            safe.append(token.lower())
    return safe


def create_time_rules(
    group_id: str,
    members: List[str],
    activate_days: str,
    start_hour: int | str,
    deactivate_days: str,
    stop_hour: int | str,
) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Create/update time-based blocking rules for a group:
    - Persist members in /root/netlimit/<GROUP>/devices.txt (deduped)
    - Install crontab entries for block/unblock windows
    """
    if not _is_valid_group_name(group_id):
        return None, "Invalid group_id. Allowed characters: A-Za-z0-9_-"

    if not _is_valid_days_spec(activate_days):
        return None, "Invalid activate_days. Use 0-7, commas and ranges (e.g., 1-5 or 1,3,5)."
    if not _is_valid_days_spec(deactivate_days):
        return None, "Invalid deactivate_days. Use 0-7, commas and ranges (e.g., 1-5 or 1,3,5)."

    start_h = _coerce_hour(start_hour)
    stop_h = _coerce_hour(stop_hour)
    if start_h is None or stop_h is None:
        return None, "Invalid hour. Use an integer 0-23."

    safe_macs = _sanitize_macs(members or [])

    # 1) Ensure group directory and devices file exist and add members (deduped)
    add_cmd = "/root/netlimit/add_devices.sh " + group_id
    if safe_macs:
        add_cmd += " " + " ".join(safe_macs)
    _, err = _execute(add_cmd)
    if err:
        return None, f"Failed to add devices: {err}"

    # 2) Install/replace cron entries for block and unblock windows (tagged)
    block_line = (
        f"(crontab -l 2>/dev/null | grep -v \"# netlimit_{group_id}_block\") | "
        f"{{ cat; echo \"0 {start_h} * * {activate_days} /root/netlimit/update_firewall.sh {group_id} block # netlimit_{group_id}_block\"; }} | "
        f"crontab -"
    )
    _, err = _execute(block_line)
    if err:
        return None, f"Failed to set block schedule: {err}"

    unblock_line = (
        f"(crontab -l 2>/dev/null | grep -v \"# netlimit_{group_id}_unblock\") | "
        f"{{ cat; echo \"0 {stop_h} * * {deactivate_days} /root/netlimit/update_firewall.sh {group_id} unblock # netlimit_{group_id}_unblock\"; }} | "
        f"crontab -"
    )
    _, err = _execute(unblock_line)
    if err:
        return None, f"Failed to set unblock schedule: {err}"

    return {
        "group": group_id,
        "members_added": safe_macs,
        "activate_days": activate_days,
        "start_hour": int(start_h),
        "deactivate_days": deactivate_days,
        "stop_hour": int(stop_h),
    }, None


def delete_time_rules(group_id: str) -> Tuple[Optional[bool], Optional[str]]:
    """Remove this group's cron schedules and ensure rules are unblocked."""
    if not _is_valid_group_name(group_id):
        return None, "Invalid group_id. Allowed characters: A-Za-z0-9_-"

    purge_cmd = f"crontab -l 2>/dev/null | grep -v \"# netlimit_{group_id}_\" | crontab -"
    _, err = _execute(purge_cmd)
    if err:
        return None, f"Failed to remove schedules: {err}"

    _, err = _execute(f"/root/netlimit/update_firewall.sh {group_id} unblock")
    if err:
        return None, f"Failed to unblock firewall rules: {err}"

    return True, None


def add_devices_to_group(group_id: str, members: List[str]) -> Tuple[Optional[Dict], Optional[str]]:
    """Add devices (deduped) to a group's device list and refresh rules."""
    if not _is_valid_group_name(group_id):
        return None, "Invalid group_id. Allowed characters: A-Za-z0-9_-"

    safe_macs = _sanitize_macs(members or [])
    add_cmd = "/root/netlimit/add_devices.sh " + group_id
    if safe_macs:
        add_cmd += " " + " ".join(safe_macs)

    _, err = _execute(add_cmd)
    if err:
        return None, f"Failed to add devices: {err}"

    _, err = _execute(f"/root/netlimit/update_firewall.sh {group_id} refresh")
    if err:
        return None, f"Failed to refresh firewall rules: {err}"

    return {"group": group_id, "added": safe_macs}, None


def remove_devices_from_group(group_id: str, members: List[str]) -> Tuple[Optional[Dict], Optional[str]]:
    """Remove devices from a group's device list and refresh rules."""
    if not _is_valid_group_name(group_id):
        return None, "Invalid group_id. Allowed characters: A-Za-z0-9_-"

    safe_macs = _sanitize_macs(members or [])
    if not safe_macs:
        # Nothing to do
        _, err = _execute(f"/root/netlimit/update_firewall.sh {group_id} refresh")
        if err:
            return None, f"Failed to refresh firewall rules: {err}"
        return {"group": group_id, "removed": []}, None

    del_cmd = "/root/netlimit/del_devices.sh " + group_id + " " + " ".join(safe_macs)
    _, err = _execute(del_cmd)
    if err:
        return None, f"Failed to remove devices: {err}"

    _, err = _execute(f"/root/netlimit/update_firewall.sh {group_id} refresh")
    if err:
        return None, f"Failed to refresh firewall rules: {err}"

    return {"group": group_id, "removed": safe_macs}, None


def add_device_to_group(group_id: str, mac: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Add a single device to a group's device list and refresh rules."""
    if not _is_valid_group_name(group_id):
        return None, "Invalid group_id. Allowed characters: A-Za-z0-9_-"

    safe = _sanitize_macs([mac])
    if not safe:
        return None, "Invalid MAC address"

    add_cmd = f"/root/netlimit/add_devices.sh {group_id} {safe[0]}"
    _, err = _execute(add_cmd)
    if err:
        return None, f"Failed to add device: {err}"

    _, err = _execute(f"/root/netlimit/update_firewall.sh {group_id} refresh")
    if err:
        return None, f"Failed to refresh firewall rules: {err}"

    return {"group": group_id, "added": safe}, None


def remove_device_from_group(group_id: str, mac: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Remove a single device from a group's device list and refresh rules."""
    if not _is_valid_group_name(group_id):
        return None, "Invalid group_id. Allowed characters: A-Za-z0-9_-"

    safe = _sanitize_macs([mac])
    if not safe:
        # Still refresh to ensure consistency
        _, err = _execute(f"/root/netlimit/update_firewall.sh {group_id} refresh")
        if err:
            return None, f"Failed to refresh firewall rules: {err}"
        return {"group": group_id, "removed": []}, None

    del_cmd = f"/root/netlimit/del_devices.sh {group_id} {safe[0]}"
    _, err = _execute(del_cmd)
    if err:
        return None, f"Failed to remove device: {err}"

    _, err = _execute(f"/root/netlimit/update_firewall.sh {group_id} refresh")
    if err:
        return None, f"Failed to refresh firewall rules: {err}"

    return {"group": group_id, "removed": safe}, None
