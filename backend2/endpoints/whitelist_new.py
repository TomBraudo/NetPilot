from flask import Blueprint, request, jsonify, g
from models.whitelist import UserWhitelist
from models.device import UserDevice
from models.user import User
from models.router import UserRouter
from datetime import datetime
import time

whitelist_new_bp = Blueprint('whitelist_new', __name__)

@whitelist_new_bp.route('/', methods=['GET'])
def list_whitelist():
    """List all whitelisted devices for the current user"""
    start_time = time.time()
    
    user_id = request.args.get('user_id')
    router_id = request.args.get('router_id')
    
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    
    try:
        session = g.db_session
        
        # Build query
        query = session.query(UserWhitelist).filter_by(user_id=user_id)
        
        if router_id:
            query = query.filter_by(router_id=router_id)
        
        whitelist_items = query.all()
        
        # Convert to dict format
        whitelist_list = []
        for item in whitelist_items:
            item_dict = item.to_dict()
            # Convert UUID to string for JSON serialization
            item_dict['id'] = str(item_dict['id'])
            item_dict['user_id'] = str(item_dict['user_id'])
            if item_dict.get('device_id'):
                item_dict['device_id'] = str(item_dict['device_id'])
            whitelist_list.append(item_dict)
        
        return jsonify({
            'success': True,
            'whitelist': whitelist_list,
            'count': len(whitelist_list),
            'response_time': time.time() - start_time
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({
            'error': f'Failed to fetch whitelist: {str(e)}',
            'response_time': time.time() - start_time
        }), 500

@whitelist_new_bp.route('/add', methods=['POST'])
def add_to_whitelist():
    """Add a device to the whitelist"""
    start_time = time.time()
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['user_id', 'router_id', 'device_ip']
    if not all(field in data for field in required_fields):
        return jsonify({'error': f'Missing required fields: {required_fields}'}), 400
    
    try:
        session = g.db_session
        
        # Check if already whitelisted
        existing = session.query(UserWhitelist).filter_by(
            user_id=data['user_id'],
            router_id=data['router_id'],
            device_ip=data['device_ip']
        ).first()
        
        if existing:
            return jsonify({
                'error': 'Device already in whitelist',
                'whitelist_id': str(existing.id),
                'response_time': time.time() - start_time
            }), 409
        
        # Find the device if it exists
        device = session.query(UserDevice).filter_by(
            user_id=data['user_id'],
            router_id=data['router_id'],
            ip=data['device_ip']
        ).first()
        
        # Create whitelist entry
        whitelist_item = UserWhitelist(
            user_id=data['user_id'],
            router_id=data['router_id'],
            device_id=device.id if device else None,
            device_ip=data['device_ip'],
            device_mac=data.get('device_mac'),
            device_name=data.get('device_name'),
            description=data.get('description', ''),
            added_at=datetime.utcnow()
        )
        
        session.add(whitelist_item)
        session.commit()
        
        item_dict = whitelist_item.to_dict()
        item_dict['id'] = str(item_dict['id'])
        item_dict['user_id'] = str(item_dict['user_id'])
        if item_dict.get('device_id'):
            item_dict['device_id'] = str(item_dict['device_id'])
        
        return jsonify({
            'success': True,
            'whitelist_item': item_dict,
            'message': 'Device added to whitelist successfully',
            'response_time': time.time() - start_time
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({
            'error': f'Failed to add to whitelist: {str(e)}',
            'response_time': time.time() - start_time
        }), 500

@whitelist_new_bp.route('/remove', methods=['POST'])
def remove_from_whitelist():
    """Remove a device from the whitelist"""
    start_time = time.time()
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['user_id', 'router_id', 'device_ip']
    if not all(field in data for field in required_fields):
        return jsonify({'error': f'Missing required fields: {required_fields}'}), 400
    
    try:
        session = g.db_session
        
        whitelist_item = session.query(UserWhitelist).filter_by(
            user_id=data['user_id'],
            router_id=data['router_id'],
            device_ip=data['device_ip']
        ).first()
        
        if not whitelist_item:
            return jsonify({'error': 'Device not found in whitelist'}), 404
        
        session.delete(whitelist_item)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Device removed from whitelist successfully',
            'response_time': time.time() - start_time
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({
            'error': f'Failed to remove from whitelist: {str(e)}',
            'response_time': time.time() - start_time
        }), 500

@whitelist_new_bp.route('/<whitelist_id>', methods=['DELETE'])
def delete_whitelist_item(whitelist_id):
    """Delete a specific whitelist item by ID"""
    start_time = time.time()
    
    try:
        session = g.db_session
        
        whitelist_item = session.query(UserWhitelist).filter_by(id=whitelist_id).first()
        if not whitelist_item:
            return jsonify({'error': 'Whitelist item not found'}), 404
        
        session.delete(whitelist_item)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Whitelist item deleted successfully',
            'response_time': time.time() - start_time
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({
            'error': f'Failed to delete whitelist item: {str(e)}',
            'response_time': time.time() - start_time
        }), 500 