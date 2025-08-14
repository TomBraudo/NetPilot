from database.session import get_db_session
from models.device_group import DeviceGroup
from models.device import UserDevice
from models.user import User
from sqlalchemy.orm import joinedload
from sqlalchemy import and_
from utils.logging_config import get_logger

logger = get_logger('services.device_group_service')


def get_user_device_groups(user_id, router_id):
    """Get all device groups for a user and router"""
    with get_db_session() as session:
        try:
            groups = session.query(DeviceGroup).options(
                joinedload(DeviceGroup.devices)
            ).filter(
                and_(
                    DeviceGroup.user_id == user_id,
                    DeviceGroup.router_id == router_id
                )
            ).all()
            
            logger.info(f"Retrieved {len(groups)} device groups for user {user_id}, router {router_id}")
            return groups
            
        except Exception as e:
            logger.error(f"Failed to get device groups: {str(e)}")
            session.rollback()
            raise


def create_device_group(user_id, router_id, name, description=None, device_ids=None):
    """Create a new device group"""
    with get_db_session() as session:
        try:
            # Check if group with same name exists for this user/router
            existing = session.query(DeviceGroup).filter(
                and_(
                    DeviceGroup.user_id == user_id,
                    DeviceGroup.router_id == router_id,
                    DeviceGroup.name == name
                )
            ).first()
            
            if existing:
                raise ValueError(f"Group with name '{name}' already exists")
            
            # Create the group
            group = DeviceGroup(
                user_id=user_id,
                router_id=router_id,
                name=name,
                description=description
            )
            
            session.add(group)
            session.flush()  # Get the ID
            
            # Add devices if provided
            if device_ids:
                devices = session.query(UserDevice).filter(
                    and_(
                        UserDevice.user_id == user_id,
                        UserDevice.router_id == router_id,
                        UserDevice.id.in_(device_ids)
                    )
                ).all()
                
                if len(devices) != len(device_ids):
                    raise ValueError("One or more devices not found")
                
                group.devices.extend(devices)
            
            session.commit()
            
            # Refresh to get the latest data with relationships
            session.refresh(group)
            logger.info(f"Created device group '{name}' with {len(device_ids or [])} devices")
            
            return group
            
        except Exception as e:
            logger.error(f"Failed to create device group: {str(e)}")
            session.rollback()
            raise


def update_device_group(user_id, router_id, group_id, data):
    """Update a device group"""
    with get_db_session() as session:
        try:
            group = session.query(DeviceGroup).filter(
                and_(
                    DeviceGroup.id == group_id,
                    DeviceGroup.user_id == user_id,
                    DeviceGroup.router_id == router_id
                )
            ).first()
            
            if not group:
                return None
            
            # Update fields if provided
            if 'name' in data:
                new_name = data['name'].strip()
                if not new_name:
                    raise ValueError("Group name cannot be empty")
                
                # Check if name conflicts with another group
                existing = session.query(DeviceGroup).filter(
                    and_(
                        DeviceGroup.user_id == user_id,
                        DeviceGroup.router_id == router_id,
                        DeviceGroup.name == new_name,
                        DeviceGroup.id != group_id
                    )
                ).first()
                
                if existing:
                    raise ValueError(f"Group with name '{new_name}' already exists")
                
                group.name = new_name
            
            if 'description' in data:
                group.description = data['description'].strip() if data['description'] else None
            
            session.commit()
            session.refresh(group)
            
            logger.info(f"Updated device group {group_id}")
            return group
            
        except Exception as e:
            logger.error(f"Failed to update device group: {str(e)}")
            session.rollback()
            raise


def delete_device_group(user_id, router_id, group_id):
    """Delete a device group"""
    with get_db_session() as session:
        try:
            group = session.query(DeviceGroup).filter(
                and_(
                    DeviceGroup.id == group_id,
                    DeviceGroup.user_id == user_id,
                    DeviceGroup.router_id == router_id
                )
            ).first()
            
            if not group:
                return False
            
            session.delete(group)
            session.commit()
            
            logger.info(f"Deleted device group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete device group: {str(e)}")
            session.rollback()
            raise


def add_device_to_group(user_id, router_id, group_id, device_id):
    """Add a device to a group"""
    with get_db_session() as session:
        try:
            # Get the group
            group = session.query(DeviceGroup).filter(
                and_(
                    DeviceGroup.id == group_id,
                    DeviceGroup.user_id == user_id,
                    DeviceGroup.router_id == router_id
                )
            ).first()
            
            if not group:
                return False
            
            # Get the device
            device = session.query(UserDevice).filter(
                and_(
                    UserDevice.id == device_id,
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id
                )
            ).first()
            
            if not device:
                return False
            
            # Check if device is already in the group
            if device in group.devices:
                raise ValueError("Device is already in this group")
            
            group.devices.append(device)
            session.commit()
            
            logger.info(f"Added device {device_id} to group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add device to group: {str(e)}")
            session.rollback()
            raise


def remove_device_from_group(user_id, router_id, group_id, device_id):
    """Remove a device from a group"""
    with get_db_session() as session:
        try:
            # Get the group
            group = session.query(DeviceGroup).options(
                joinedload(DeviceGroup.devices)
            ).filter(
                and_(
                    DeviceGroup.id == group_id,
                    DeviceGroup.user_id == user_id,
                    DeviceGroup.router_id == router_id
                )
            ).first()
            
            if not group:
                return False
            
            # Find the device in the group
            device_to_remove = None
            for device in group.devices:
                if str(device.id) == str(device_id):
                    device_to_remove = device
                    break
            
            if not device_to_remove:
                return False
            
            group.devices.remove(device_to_remove)
            session.commit()
            
            logger.info(f"Removed device {device_id} from group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove device from group: {str(e)}")
            session.rollback()
            raise


def get_available_devices_for_group(user_id, router_id, group_id=None):
    """Get devices that are not in any group or not in the specified group"""
    with get_db_session() as session:
        try:
            query = session.query(UserDevice).filter(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id
                )
            )
            
            if group_id:
                # Get devices not in this specific group
                group = session.query(DeviceGroup).filter(
                    and_(
                        DeviceGroup.id == group_id,
                        DeviceGroup.user_id == user_id,
                        DeviceGroup.router_id == router_id
                    )
                ).first()
                
                if group:
                    group_device_ids = [device.id for device in group.devices]
                    if group_device_ids:
                        query = query.filter(~UserDevice.id.in_(group_device_ids))
            
            devices = query.all()
            logger.info(f"Retrieved {len(devices)} available devices for group {group_id or 'new'}")
            return devices
            
        except Exception as e:
            logger.error(f"Failed to get available devices: {str(e)}")
            session.rollback()
            raise
