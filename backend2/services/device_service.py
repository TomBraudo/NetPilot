from database.session import get_db_session
from models.device import UserDevice
from models.user import User
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, func
from utils.logging_config import get_logger
from datetime import datetime

logger = get_logger('services.device_service')


def get_user_devices(user_id, router_id):
    """Get all devices for a user and router"""
    with get_db_session() as session:
        try:
            devices = session.query(UserDevice).filter(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id
                )
            ).all()
            
            # Convert to dict while still in session to avoid detachment issues
            devices_dicts = [device.to_dict() for device in devices]
            
            logger.info(f"Retrieved {len(devices)} devices for user {user_id}, router {router_id}")
            return devices_dicts
            
        except Exception as e:
            logger.error(f"Failed to get devices: {str(e)}")
            session.rollback()
            raise


def create_or_update_device(user_id, router_id, ip, mac=None, hostname=None, device_name=None, device_type=None, manufacturer=None):
    """Create a new device or update existing one"""
    with get_db_session() as session:
        try:
            # Check if device already exists by IP
            existing_device = session.query(UserDevice).filter(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id,
                    UserDevice.ip == ip
                )
            ).first()
            
            current_time = datetime.utcnow()
            
            if existing_device:
                # Update existing device
                existing_device.last_seen = current_time
                if mac:
                    existing_device.mac = mac
                if hostname:
                    existing_device.hostname = hostname
                if device_name:
                    existing_device.device_name = device_name
                if device_type:
                    existing_device.device_type = device_type
                if manufacturer:
                    existing_device.manufacturer = manufacturer
                
                session.commit()
                session.refresh(existing_device)
                
                # Convert to dict while still in session
                device_dict = existing_device.to_dict()
                session.expunge(existing_device)
                
                logger.info(f"Updated existing device {ip} for user {user_id}")
                return device_dict
            else:
                # Create new device
                new_device = UserDevice(
                    user_id=user_id,
                    router_id=router_id,
                    ip=ip,
                    mac=mac,
                    hostname=hostname,
                    device_name=device_name,
                    device_type=device_type,
                    manufacturer=manufacturer,
                    first_seen=current_time,
                    last_seen=current_time
                )
                
                session.add(new_device)
                session.commit()
                session.refresh(new_device)
                
                # Convert to dict while still in session
                device_dict = new_device.to_dict()
                session.expunge(new_device)
                
                logger.info(f"Created new device {ip} for user {user_id}")
                return device_dict
            
        except Exception as e:
            logger.error(f"Failed to create/update device: {str(e)}")
            session.rollback()
            raise


def bulk_create_or_update_devices(user_id, router_id, devices_data):
    """Create or update multiple devices from scan data"""
    with get_db_session() as session:
        try:
            created_devices = []
            current_time = datetime.utcnow()
            
            for device_data in devices_data:
                ip = device_data.get('ip')
                if not ip:
                    continue
                    
                mac = device_data.get('mac')
                hostname = device_data.get('hostname')
                device_type = device_data.get('type') or device_data.get('device_type')
                
                # Check if device already exists
                existing_device = session.query(UserDevice).filter(
                    and_(
                        UserDevice.user_id == user_id,
                        UserDevice.router_id == router_id,
                        UserDevice.ip == ip
                    )
                ).first()
                
                if existing_device:
                    # Update existing device
                    existing_device.last_seen = current_time
                    if mac:
                        existing_device.mac = mac
                    if hostname:
                        existing_device.hostname = hostname
                    if device_type:
                        existing_device.device_type = device_type
                    
                    created_devices.append(existing_device)
                else:
                    # Create new device
                    new_device = UserDevice(
                        user_id=user_id,
                        router_id=router_id,
                        ip=ip,
                        mac=mac,
                        hostname=hostname,
                        device_type=device_type,
                        first_seen=current_time,
                        last_seen=current_time
                    )
                    
                    session.add(new_device)
                    created_devices.append(new_device)
            
            session.commit()
            
            # Refresh all devices to get their IDs while session is still active
            for device in created_devices:
                session.refresh(device)
            
            # Convert to dicts while still in session to avoid detachment issues
            devices_dicts = [device.to_dict() for device in created_devices]
            
            logger.info(f"Bulk created/updated {len(created_devices)} devices for user {user_id}")
            return devices_dicts
            
        except Exception as e:
            logger.error(f"Failed to bulk create/update devices: {str(e)}")
            session.rollback()
            raise


def get_device_by_id(user_id, router_id, device_id):
    """Get a device by ID"""
    with get_db_session() as session:
        try:
            device = session.query(UserDevice).filter(
                and_(
                    UserDevice.id == device_id,
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id
                )
            ).first()
            
            # Convert to dict while still in session to avoid detachment issues
            if device:
                return device.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get device by ID: {str(e)}")
            session.rollback()
            raise


def delete_device(user_id, router_id, device_id):
    """Delete a device"""
    with get_db_session() as session:
        try:
            device = session.query(UserDevice).filter(
                and_(
                    UserDevice.id == device_id,
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id
                )
            ).first()
            
            if not device:
                return False
            
            session.delete(device)
            session.commit()
            
            logger.info(f"Deleted device {device_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete device: {str(e)}")
            session.rollback()
            raise


def get_devices_by_ips(user_id, router_id, ips):
    """Get devices by their IP addresses"""
    with get_db_session() as session:
        try:
            devices = session.query(UserDevice).filter(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id,
                    UserDevice.ip.in_(ips)
                )
            ).all()
            
            return devices
            
        except Exception as e:
            logger.error(f"Failed to get devices by IPs: {str(e)}")
            session.rollback()
            raise


def validate_devices(user_id, router_id, device_identifiers):
    """Validate that devices exist in database by IP or UUID"""
    with get_db_session() as session:
        try:
            from utils.response_helpers import is_uuid
            
            logger.info(f"Starting device validation for {len(device_identifiers)} identifiers")
            
            valid_devices = []
            invalid_devices = []
            
            # Process all identifiers first, collecting device objects
            device_objects = []
            
            for identifier in device_identifiers:
                logger.info(f"Processing identifier: {identifier}")
                
                if is_uuid(identifier):
                    # Check by UUID
                    device = session.query(UserDevice).filter(
                        and_(
                            UserDevice.id == identifier,
                            UserDevice.user_id == user_id,
                            UserDevice.router_id == router_id
                        )
                    ).first()
                    
                    if device:
                        logger.info(f"Found device by UUID: {device.id}")
                        device_objects.append(device)
                    else:
                        logger.info(f"No device found for UUID: {identifier}")
                        invalid_devices.append(identifier)
                else:
                    # Check by IP
                    devices = session.query(UserDevice).filter(
                        and_(
                            UserDevice.user_id == user_id,
                            UserDevice.router_id == router_id,
                            UserDevice.ip == identifier
                        )
                    ).all()
                    
                    if devices:
                        logger.info(f"Found {len(devices)} devices by IP: {identifier}")
                        device_objects.extend(devices)
                    else:
                        logger.info(f"No devices found for IP: {identifier}")
                        invalid_devices.append(identifier)
            
            # Convert all device objects to dictionaries while still in session
            for device in device_objects:
                try:
                    device_dict = device.to_dict()
                    valid_devices.append(device_dict)
                    logger.info(f"Successfully converted device {device.id} to dict")
                except Exception as e:
                    logger.error(f"Failed to convert device {device.id} to dict: {e}")
                    # If conversion fails, mark as invalid
                    if hasattr(device, 'id'):
                        invalid_devices.append(device.id)
                    elif hasattr(device, 'ip'):
                        invalid_devices.append(device.ip)
            
            logger.info(f"Device validation complete: {len(valid_devices)} valid, {len(invalid_devices)} invalid")
            
            return {
                'valid_devices': valid_devices,
                'invalid_devices': invalid_devices,
                'total_valid': len(valid_devices),
                'total_invalid': len(invalid_devices)
            }
            
        except Exception as e:
            logger.error(f"Failed to validate devices: {str(e)}")
            session.rollback()
            raise
