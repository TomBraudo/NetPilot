from typing import Any, Dict, List, Optional, Tuple
from utils.logging_config import get_logger
from managers.db_session_context import SessionContext
from sqlalchemy.orm import joinedload
from sqlalchemy import and_

logger = get_logger('services.db_operations.device_group_db')


def get_user_device_groups(user_id: str, router_id: str) -> List[Dict[str, Any]]:
    from models.device_group import DeviceGroup

    session = SessionContext.get()
    groups = (
        session.query(DeviceGroup)
        .options(joinedload(DeviceGroup.devices))
        .filter(and_(DeviceGroup.user_id == user_id, DeviceGroup.router_id == router_id))
        .all()
    )
    return [group.to_dict() for group in groups]


def create_device_group(user_id: str, router_id: str, name: str, description: Optional[str], device_ids: Optional[List[str]]) -> Dict[str, Any]:
    from models.device_group import DeviceGroup
    from models.device import UserDevice

    session = SessionContext.get()

    existing = (
        session.query(DeviceGroup)
        .filter(and_(DeviceGroup.user_id == user_id, DeviceGroup.router_id == router_id, DeviceGroup.name == name))
        .first()
    )
    if existing:
        raise ValueError(f"Group with name '{name}' already exists")

    group = DeviceGroup(user_id=user_id, router_id=router_id, name=name, description=description)

    if device_ids:
        devices = (
            session.query(UserDevice)
            .filter(and_(UserDevice.user_id == user_id, UserDevice.router_id == router_id, UserDevice.id.in_(device_ids)))
            .all()
        )
        if len(devices) != len(device_ids):
            raise ValueError("One or more devices not found")
        group.devices.extend(devices)

    session.add(group)
    session.flush()

    group = (
        session.query(DeviceGroup)
        .options(joinedload(DeviceGroup.devices))
        .filter(DeviceGroup.id == group.id)
        .first()
    )
    return group.to_dict()


def update_device_group(user_id: str, router_id: str, group_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    from models.device_group import DeviceGroup

    session = SessionContext.get()
    group = (
        session.query(DeviceGroup)
        .filter(and_(DeviceGroup.id == group_id, DeviceGroup.user_id == user_id, DeviceGroup.router_id == router_id))
        .first()
    )
    if not group:
        return None

    if 'name' in data:
        new_name = (data['name'] or '').strip()
        if not new_name:
            raise ValueError("Group name cannot be empty")

        existing = (
            session.query(DeviceGroup)
            .filter(
                and_(
                    DeviceGroup.user_id == user_id,
                    DeviceGroup.router_id == router_id,
                    DeviceGroup.name == new_name,
                    DeviceGroup.id != group_id,
                )
            )
            .first()
        )
        if existing:
            raise ValueError(f"Group with name '{new_name}' already exists")
        group.name = new_name

    if 'description' in data:
        group.description = data['description'].strip() if data['description'] else None

    session.flush()

    group = (
        session.query(DeviceGroup)
        .options(joinedload(DeviceGroup.devices))
        .filter(DeviceGroup.id == group_id)
        .first()
    )
    return group.to_dict()


def delete_device_group(user_id: str, router_id: str, group_id: str) -> Tuple[bool, Dict[str, Any]]:
    """Delete group and return execute context for post-commit actions."""
    from models.device_group import DeviceGroup
    from models.bandwidth_rules import BandwidthRules
    from models.content_control_rules import ContentControlRules

    session = SessionContext.get()

    group = (
        session.query(DeviceGroup)
        .options(joinedload(DeviceGroup.devices))
        .filter(and_(DeviceGroup.id == group_id, DeviceGroup.user_id == user_id, DeviceGroup.router_id == router_id))
        .first()
    )
    if not group:
        return False, {}

    ips_to_clear: List[str] = []
    devices_for_agh: List[Dict[str, Any]] = []
    for dev in group.devices:
        ip_str = str(dev.ip) if getattr(dev, 'ip', None) else None
        mac_str = str(dev.mac) if getattr(dev, 'mac', None) else None
        if ip_str:
            ips_to_clear.append(ip_str)
        device_obj: Dict[str, Any] = {}
        if mac_str:
            device_obj['mac'] = mac_str
        if ip_str:
            device_obj['ip'] = ip_str
        if device_obj:
            devices_for_agh.append(device_obj)

    should_clear_agh = False
    should_clear_bandwidth = False

    content_rules = (
        session.query(ContentControlRules)
        .filter(
            and_(
                ContentControlRules.group_id == group_id,
                ContentControlRules.router_id == router_id,
                ContentControlRules.is_active.is_(True),
            )
        )
        .first()
    )
    if content_rules and content_rules.blocked_categories and len(content_rules.blocked_categories) > 0:
        should_clear_agh = True

    bandwidth_rules = (
        session.query(BandwidthRules)
        .filter(
            and_(
                BandwidthRules.group_id == group_id,
                BandwidthRules.router_id == router_id,
                BandwidthRules.is_active.is_(True),
            )
        )
        .first()
    )
    if bandwidth_rules and (
        bandwidth_rules.download_limit_mbps is not None or bandwidth_rules.upload_limit_mbps is not None
    ):
        should_clear_bandwidth = True

    session.delete(group)

    return True, {
        'ips_to_clear': ips_to_clear,
        'devices_for_agh': devices_for_agh,
        'should_clear_agh': should_clear_agh,
        'should_clear_bandwidth': should_clear_bandwidth,
    }


def add_device_to_group(user_id: str, router_id: str, group_id: str, device_id: str) -> Tuple[bool, Dict[str, Any]]:
    from models.device_group import DeviceGroup
    from models.device import UserDevice
    from models.bandwidth_rules import BandwidthRules
    from models.content_control_rules import ContentControlRules

    session = SessionContext.get()

    group = (
        session.query(DeviceGroup)
        .filter(and_(DeviceGroup.id == group_id, DeviceGroup.user_id == user_id, DeviceGroup.router_id == router_id))
        .first()
    )
    if not group:
        return False, {}

    device = (
        session.query(UserDevice)
        .filter(and_(UserDevice.id == device_id, UserDevice.user_id == user_id, UserDevice.router_id == router_id))
        .first()
    )
    if not device:
        return False, {}

    if device in group.devices:
        raise ValueError("Device is already in this group")

    device_ip = str(device.ip) if getattr(device, 'ip', None) else None
    device_mac = str(device.mac) if getattr(device, 'mac', None) else None

    should_apply_agh = False
    agh_categories: List[str] = []
    content_rules = (
        session.query(ContentControlRules)
        .filter(
            and_(
                ContentControlRules.group_id == group_id,
                ContentControlRules.router_id == router_id,
                ContentControlRules.is_active.is_(True),
            )
        )
        .first()
    )
    if content_rules and content_rules.blocked_categories and len(content_rules.blocked_categories) > 0:
        should_apply_agh = True
        agh_categories = list(content_rules.blocked_categories or [])

    should_apply_bandwidth = False
    bw_download_mbps = None
    bw_upload_mbps = None
    bandwidth_rules = (
        session.query(BandwidthRules)
        .filter(
            and_(
                BandwidthRules.group_id == group_id,
                BandwidthRules.router_id == router_id,
                BandwidthRules.is_active.is_(True),
            )
        )
        .first()
    )
    if bandwidth_rules and (
        bandwidth_rules.download_limit_mbps is not None or bandwidth_rules.upload_limit_mbps is not None
    ):
        should_apply_bandwidth = True
        bw_download_mbps = bandwidth_rules.download_limit_mbps
        bw_upload_mbps = bandwidth_rules.upload_limit_mbps

    group.devices.append(device)

    return True, {
        'device_ip': device_ip,
        'device_mac': device_mac,
        'should_apply_agh': should_apply_agh,
        'agh_categories': agh_categories,
        'should_apply_bandwidth': should_apply_bandwidth,
        'bw_download_mbps': bw_download_mbps,
        'bw_upload_mbps': bw_upload_mbps,
    }


def remove_device_from_group(user_id: str, router_id: str, group_id: str, device_id: str) -> Tuple[bool, Dict[str, Any]]:
    from models.device_group import DeviceGroup
    from models.bandwidth_rules import BandwidthRules
    from models.content_control_rules import ContentControlRules

    session = SessionContext.get()

    group = (
        session.query(DeviceGroup)
        .options(joinedload(DeviceGroup.devices))
        .filter(and_(DeviceGroup.id == group_id, DeviceGroup.user_id == user_id, DeviceGroup.router_id == router_id))
        .first()
    )
    if not group:
        return False, {}

    device_to_remove = None
    for device in group.devices:
        if str(device.id) == str(device_id):
            device_to_remove = device
            break
    if not device_to_remove:
        return False, {}

    device_ip = str(device_to_remove.ip) if getattr(device_to_remove, 'ip', None) else None
    device_mac = str(device_to_remove.mac) if getattr(device_to_remove, 'mac', None) else None

    should_clear_agh = False
    should_clear_bandwidth = False

    content_rules = (
        session.query(ContentControlRules)
        .filter(
            and_(
                ContentControlRules.group_id == group_id,
                ContentControlRules.router_id == router_id,
                ContentControlRules.is_active.is_(True),
            )
        )
        .first()
    )
    if content_rules and content_rules.blocked_categories and len(content_rules.blocked_categories) > 0:
        should_clear_agh = True

    bandwidth_rules = (
        session.query(BandwidthRules)
        .filter(
            and_(
                BandwidthRules.group_id == group_id,
                BandwidthRules.router_id == router_id,
                BandwidthRules.is_active.is_(True),
            )
        )
        .first()
    )
    if bandwidth_rules and (
        bandwidth_rules.download_limit_mbps is not None or bandwidth_rules.upload_limit_mbps is not None
    ):
        should_clear_bandwidth = True

    group.devices.remove(device_to_remove)

    return True, {
        'device_ip': device_ip,
        'device_mac': device_mac,
        'should_clear_agh': should_clear_agh,
        'should_clear_bandwidth': should_clear_bandwidth,
    }


def get_available_devices_for_group(user_id: str, router_id: str, group_id: Optional[str] = None):
    from models.device_group import DeviceGroup
    from models.device import UserDevice

    session = SessionContext.get()
    query = session.query(UserDevice).filter(and_(UserDevice.user_id == user_id, UserDevice.router_id == router_id))
    if group_id:
        group = (
            session.query(DeviceGroup)
            .filter(and_(DeviceGroup.id == group_id, DeviceGroup.user_id == user_id, DeviceGroup.router_id == router_id))
            .first()
        )
        if group:
            group_device_ids = [device.id for device in group.devices]
            if group_device_ids:
                query = query.filter(~UserDevice.id.in_(group_device_ids))
    return query.all()


def get_groups_containing_device(user_id: str, router_id: str, device_id: str):
    from models.device_group import DeviceGroup

    session = SessionContext.get()
    groups = (
        session.query(DeviceGroup)
        .options(joinedload(DeviceGroup.devices))
        .filter(and_(DeviceGroup.user_id == user_id, DeviceGroup.router_id == router_id))
        .all()
    )
    containing = []
    for group in groups:
        if any(str(device.id) == str(device_id) for device in group.devices):
            containing.append(group)
    return containing


def cleanup_empty_groups(user_id: str, router_id: str) -> List[str]:
    from models.device_group import DeviceGroup

    session = SessionContext.get()
    groups = (
        session.query(DeviceGroup)
        .options(joinedload(DeviceGroup.devices))
        .filter(and_(DeviceGroup.user_id == user_id, DeviceGroup.router_id == router_id))
        .all()
    )
    deleted_group_ids: List[str] = []
    for group in groups:
        if len(group.devices) == 0:
            deleted_group_ids.append(str(group.id))
            session.delete(group)
    return deleted_group_ids


