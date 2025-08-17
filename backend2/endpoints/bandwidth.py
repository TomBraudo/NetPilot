from flask import Blueprint, request, g
from utils.response_helpers import build_success_response, build_error_response
from utils.logging_config import get_logger
from utils.middleware import router_context_required
from services.bandwidth_service import (
    apply_group_limits,
    delete_group_limits,
    apply_device_limit,
    delete_device_limit,
    activate_global_limits,
    deactivate_global_limits,
)
import time

bandwidth_bp = Blueprint('bandwidth', __name__)
logger = get_logger('endpoints.bandwidth')


@bandwidth_bp.route('/limits/group', methods=['POST'])
@router_context_required
def limits_group_apply():
    start_time = time.time()
    data = request.get_json() or {}
    ips = data.get('ips') or []
    result, error = apply_group_limits(
        g.user_id, g.router_id, g.session_id,
        ips,
        data.get('download_kbytes'),
        data.get('upload_kbytes'),
        data.get('download_mbps'),
        data.get('upload_mbps'),
    )
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/limits/group', methods=['DELETE'])
@router_context_required
def limits_group_delete():
    start_time = time.time()
    data = request.get_json() or {}
    ips = data.get('ips') or []
    result, error = delete_group_limits(g.user_id, g.router_id, g.session_id, ips)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/limits/device', methods=['POST'])
@router_context_required
def limits_device_apply():
    start_time = time.time()
    data = request.get_json() or {}
    ip = data.get('ip')
    result, error = apply_device_limit(
        g.user_id, g.router_id, g.session_id,
        ip,
        data.get('download_kbytes'),
        data.get('upload_kbytes'),
        data.get('download_mbps'),
        data.get('upload_mbps'),
    )
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/limits/device', methods=['DELETE'])
@router_context_required
def limits_device_delete():
    start_time = time.time()
    data = request.get_json() or {}
    ip = data.get('ip')
    result, error = delete_device_limit(g.user_id, g.router_id, g.session_id, ip)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/global/activate', methods=['POST'])
@router_context_required
def global_activate():
    start_time = time.time()
    data = request.get_json() or {}
    result, error = activate_global_limits(
        g.user_id, g.router_id, g.session_id,
        data.get('download_kbytes'),
        data.get('upload_kbytes'),
        data.get('lan_cidr'),
    )
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


@bandwidth_bp.route('/global/deactivate', methods=['DELETE'])
@router_context_required
def global_deactivate():
    start_time = time.time()
    result, error = deactivate_global_limits(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)


# Removed global whitelist endpoints

# Database Rules Endpoints
@bandwidth_bp.route('/rules', methods=['GET'])
@router_context_required
def get_all_bandwidth_rules():
    """Get all bandwidth rules for a router"""
    start_time = time.time()
    try:
        from models import BandwidthRules
        from database.session import get_db_session
        
        with get_db_session() as session:
            rules = session.query(BandwidthRules).filter(
                BandwidthRules.router_id == g.router_id
            ).all()
            
            rules_data = [rule.to_dict() for rule in rules]
            return build_success_response(rules_data, start_time)
            
    except Exception as e:
        logger.error(f"Failed to get bandwidth rules: {e}")
        return build_error_response(f"Failed to get bandwidth rules: {str(e)}", 500, "DATABASE_ERROR", start_time)


@bandwidth_bp.route('/rules/group/<group_id>', methods=['GET'])
@router_context_required
def get_group_bandwidth_rules(group_id):
    """Get bandwidth rules for a specific group"""
    start_time = time.time()
    try:
        from models import BandwidthRules
        from database.session import get_db_session
        
        with get_db_session() as session:
            rule = session.query(BandwidthRules).filter(
                BandwidthRules.router_id == g.router_id,
                BandwidthRules.group_id == group_id
            ).first()
            
            if rule:
                return build_success_response(rule.to_dict(), start_time)
            else:
                return build_success_response(None, start_time)
                
    except Exception as e:
        logger.error(f"Failed to get group bandwidth rules: {e}")
        return build_error_response(f"Failed to get group bandwidth rules: {str(e)}", 500, "DATABASE_ERROR", start_time)


@bandwidth_bp.route('/rules/group/<group_id>', methods=['POST'])
@router_context_required
def set_group_bandwidth_rules(group_id):
    """Create or update bandwidth rules for a group"""
    start_time = time.time()
    try:
        from models import BandwidthRules, DeviceGroup
        from database.session import get_db_session
        
        data = request.get_json() or {}
        
        with get_db_session() as session:
            # Verify group exists and belongs to user
            group = session.query(DeviceGroup).filter(
                DeviceGroup.id == group_id,
                DeviceGroup.router_id == g.router_id,
                DeviceGroup.user_id == g.user_id
            ).first()
            
            if not group:
                return build_error_response("Group not found or access denied", 404, "NOT_FOUND", start_time)
            
            # Check if rule already exists
            existing_rule = session.query(BandwidthRules).filter(
                BandwidthRules.router_id == g.router_id,
                BandwidthRules.group_id == group_id
            ).first()
            
            if existing_rule:
                # Update existing rule
                existing_rule.download_limit_mbps = data.get('download_limit_mbps')
                existing_rule.upload_limit_mbps = data.get('upload_limit_mbps')
                existing_rule.description = data.get('description')
                existing_rule.is_active = data.get('is_active', True)
                session.commit()
                return build_success_response(existing_rule.to_dict(), start_time)
            else:
                # Create new rule
                new_rule = BandwidthRules(
                    group_id=group_id,
                    router_id=g.router_id,
                    download_limit_mbps=data.get('download_limit_mbps'),
                    upload_limit_mbps=data.get('upload_limit_mbps'),
                    description=data.get('description'),
                    is_active=data.get('is_active', True)
                )
                session.add(new_rule)
                session.commit()
                return build_success_response(new_rule.to_dict(), start_time)
                
    except Exception as e:
        logger.error(f"Failed to set group bandwidth rules: {e}")
        return build_error_response(f"Failed to set group bandwidth rules: {str(e)}", 500, "DATABASE_ERROR", start_time)


@bandwidth_bp.route('/rules/group/<group_id>', methods=['DELETE'])
@router_context_required
def delete_group_bandwidth_rules(group_id):
    """Delete bandwidth rules for a group"""
    start_time = time.time()
    try:
        from models import BandwidthRules
        from database.session import get_db_session
        
        with get_db_session() as session:
            rule = session.query(BandwidthRules).filter(
                BandwidthRules.router_id == g.router_id,
                BandwidthRules.group_id == group_id
            ).first()
            
            if rule:
                session.delete(rule)
                session.commit()
                return build_success_response({"message": "Bandwidth rules deleted successfully"}, start_time)
            else:
                return build_success_response({"message": "No rules found to delete"}, start_time)
                
    except Exception as e:
        logger.error(f"Failed to delete group bandwidth rules: {e}")
        return build_error_response(f"Failed to delete group bandwidth rules: {str(e)}", 500, "DATABASE_ERROR", start_time)


