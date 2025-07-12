from flask import Blueprint, request, jsonify, g
from models.device import UserDevice
from models.user import User
from models.router import UserRouter
from sqlalchemy.orm import joinedload
from datetime import datetime
import time

devices_bp = Blueprint('devices', __name__)

@devices_bp.route('/', methods=['GET'])
def list_devices():
    """List all devices for the current user"""
    start_time = time.time()
    
    # Get user_id from query params or session
    user_id = request.args.get('user_id')
    router_id = request.args.get('router_id')
    
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    
    try:
        session = g.db_session
        
        # Build query
        query = session.query(UserDevice).filter_by(user_id=user_id)
        
        if router_id:
            query = query.filter_by(router_id=router_id)
        
        devices = query.all()
        
        # Convert to dict format
        device_list = []
        for device in devices:
            device_dict = device.to_dict()
            # Convert UUID to string for JSON serialization
            device_dict['id'] = str(device_dict['id'])
            device_dict['user_id'] = str(device_dict['user_id'])
            device_list.append(device_dict)
        
        return jsonify({
            'success': True,
            'devices': device_list,
            'count': len(device_list),
            'response_time': time.time() - start_time
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({
            'error': f'Failed to fetch devices: {str(e)}',
            'response_time': time.time() - start_time
        }), 500

@devices_bp.route('/', methods=['POST'])
def add_device():
    """Add a new device for the user"""
    start_time = time.time()
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['user_id', 'router_id', 'ip']
    if not all(field in data for field in required_fields):
        return jsonify({'error': f'Missing required fields: {required_fields}'}), 400
    
    try:
        session = g.db_session
        
        # Check if device already exists
        existing_device = session.query(UserDevice).filter_by(
            user_id=data['user_id'],
            router_id=data['router_id'],
            ip=data['ip']
        ).first()
        
        if existing_device:
            return jsonify({
                'error': 'Device already exists',
                'device_id': str(existing_device.id),
                'response_time': time.time() - start_time
            }), 409
        
        # Create new device
        device = UserDevice(
            user_id=data['user_id'],
            router_id=data['router_id'],
            ip=data['ip'],
            mac=data.get('mac'),
            hostname=data.get('hostname', 'Unknown'),
            device_name=data.get('device_name'),
            device_type=data.get('device_type'),
            manufacturer=data.get('manufacturer'),
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        
        session.add(device)
        session.commit()
        
        device_dict = device.to_dict()
        device_dict['id'] = str(device_dict['id'])
        device_dict['user_id'] = str(device_dict['user_id'])
        
        return jsonify({
            'success': True,
            'device': device_dict,
            'message': 'Device added successfully',
            'response_time': time.time() - start_time
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({
            'error': f'Failed to add device: {str(e)}',
            'response_time': time.time() - start_time
        }), 500

@devices_bp.route('/<device_id>', methods=['PUT'])
def update_device(device_id):
    """Update device information"""
    start_time = time.time()
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        session = g.db_session
        
        device = session.query(UserDevice).filter_by(id=device_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Update fields
        updateable_fields = ['device_name', 'device_type', 'manufacturer', 'hostname']
        for field in updateable_fields:
            if field in data:
                setattr(device, field, data[field])
        
        device.last_seen = datetime.utcnow()
        session.commit()
        
        device_dict = device.to_dict()
        device_dict['id'] = str(device_dict['id'])
        device_dict['user_id'] = str(device_dict['user_id'])
        
        return jsonify({
            'success': True,
            'device': device_dict,
            'message': 'Device updated successfully',
            'response_time': time.time() - start_time
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({
            'error': f'Failed to update device: {str(e)}',
            'response_time': time.time() - start_time
        }), 500

@devices_bp.route('/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Delete a device"""
    start_time = time.time()
    
    try:
        session = g.db_session
        
        device = session.query(UserDevice).filter_by(id=device_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        session.delete(device)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Device deleted successfully',
            'response_time': time.time() - start_time
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({
            'error': f'Failed to delete device: {str(e)}',
            'response_time': time.time() - start_time
        }), 500 