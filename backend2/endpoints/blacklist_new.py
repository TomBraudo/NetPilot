from flask import Blueprint, request, g
from sqlalchemy import text
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
import time
import uuid
from datetime import datetime

blacklist_bp = Blueprint('blacklist_new', __name__)
logger = get_logger('endpoints.blacklist_new')

@blacklist_bp.route("/", methods=["GET"])
def get_blacklist():
    """Get all blacklisted devices for the current user."""
    start_time = time.time()
    try:
        # Get user ID from session (assuming it's stored in g.user_id)
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return build_error_response("User not authenticated", 401, "UNAUTHORIZED", start_time)

        # Query blacklisted devices for the current user
        query = text("""
            SELECT id, mac_address, device_name, reason, created_at, updated_at
            FROM blacklisted_devices 
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """)
        
        result = g.db.execute(query, {"user_id": user_id})
        devices = []
        
        for row in result:
            devices.append({
                "id": str(row.id),
                "mac_address": row.mac_address,
                "device_name": row.device_name,
                "reason": row.reason,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            })
        
        return build_success_response({
            "devices": devices,
            "count": len(devices)
        }, start_time)
        
    except Exception as e:
        logger.error(f"Error fetching blacklist: {str(e)}", exc_info=True)
        return build_error_response("Failed to fetch blacklist", 500, "DATABASE_ERROR", start_time)

@blacklist_bp.route("/", methods=["POST"])
def add_to_blacklist():
    """Add a device to the blacklist."""
    start_time = time.time()
    try:
        # Get user ID from session
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return build_error_response("User not authenticated", 401, "UNAUTHORIZED", start_time)

        data = request.get_json()
        if not data:
            return build_error_response("Request body is required", 400, "BAD_REQUEST", start_time)

        mac_address = data.get('mac_address')
        device_name = data.get('device_name', '')
        reason = data.get('reason', '')

        if not mac_address:
            return build_error_response("MAC address is required", 400, "BAD_REQUEST", start_time)

        # Check if device is already blacklisted
        check_query = text("""
            SELECT id FROM blacklisted_devices 
            WHERE user_id = :user_id AND mac_address = :mac_address
        """)
        
        existing = g.db.execute(check_query, {
            "user_id": user_id,
            "mac_address": mac_address
        }).fetchone()
        
        if existing:
            return build_error_response("Device is already blacklisted", 409, "CONFLICT", start_time)

        # Insert new blacklisted device
        insert_query = text("""
            INSERT INTO blacklisted_devices (id, user_id, mac_address, device_name, reason, created_at, updated_at)
            VALUES (:id, :user_id, :mac_address, :device_name, :reason, :created_at, :updated_at)
            RETURNING id, mac_address, device_name, reason, created_at, updated_at
        """)
        
        device_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        result = g.db.execute(insert_query, {
            "id": device_id,
            "user_id": user_id,
            "mac_address": mac_address,
            "device_name": device_name,
            "reason": reason,
            "created_at": now,
            "updated_at": now
        })
        
        g.db.commit()
        
        # Get the inserted record
        row = result.fetchone()
        device = {
            "id": str(row.id),
            "mac_address": row.mac_address,
            "device_name": row.device_name,
            "reason": row.reason,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None
        }
        
        logger.info(f"Device {mac_address} added to blacklist for user {user_id}")
        return build_success_response(device, start_time)
        
    except Exception as e:
        g.db.rollback()
        logger.error(f"Error adding device to blacklist: {str(e)}", exc_info=True)
        return build_error_response("Failed to add device to blacklist", 500, "DATABASE_ERROR", start_time)

@blacklist_bp.route("/<device_id>", methods=["PUT"])
def update_blacklist_device(device_id):
    """Update a blacklisted device."""
    start_time = time.time()
    try:
        # Get user ID from session
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return build_error_response("User not authenticated", 401, "UNAUTHORIZED", start_time)

        data = request.get_json()
        if not data:
            return build_error_response("Request body is required", 400, "BAD_REQUEST", start_time)

        device_name = data.get('device_name')
        reason = data.get('reason')

        # Check if device exists and belongs to user
        check_query = text("""
            SELECT id FROM blacklisted_devices 
            WHERE id = :device_id AND user_id = :user_id
        """)
        
        existing = g.db.execute(check_query, {
            "device_id": device_id,
            "user_id": user_id
        }).fetchone()
        
        if not existing:
            return build_error_response("Device not found", 404, "NOT_FOUND", start_time)

        # Update the device
        update_query = text("""
            UPDATE blacklisted_devices 
            SET device_name = :device_name, reason = :reason, updated_at = :updated_at
            WHERE id = :device_id AND user_id = :user_id
            RETURNING id, mac_address, device_name, reason, created_at, updated_at
        """)
        
        now = datetime.utcnow()
        
        result = g.db.execute(update_query, {
            "device_id": device_id,
            "user_id": user_id,
            "device_name": device_name,
            "reason": reason,
            "updated_at": now
        })
        
        g.db.commit()
        
        # Get the updated record
        row = result.fetchone()
        device = {
            "id": str(row.id),
            "mac_address": row.mac_address,
            "device_name": row.device_name,
            "reason": row.reason,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None
        }
        
        logger.info(f"Blacklisted device {device_id} updated for user {user_id}")
        return build_success_response(device, start_time)
        
    except Exception as e:
        g.db.rollback()
        logger.error(f"Error updating blacklisted device: {str(e)}", exc_info=True)
        return build_error_response("Failed to update device", 500, "DATABASE_ERROR", start_time)

@blacklist_bp.route("/<device_id>", methods=["DELETE"])
def remove_from_blacklist(device_id):
    """Remove a device from the blacklist."""
    start_time = time.time()
    try:
        # Get user ID from session
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return build_error_response("User not authenticated", 401, "UNAUTHORIZED", start_time)

        # Check if device exists and belongs to user
        check_query = text("""
            SELECT id, mac_address FROM blacklisted_devices 
            WHERE id = :device_id AND user_id = :user_id
        """)
        
        existing = g.db.execute(check_query, {
            "device_id": device_id,
            "user_id": user_id
        }).fetchone()
        
        if not existing:
            return build_error_response("Device not found", 404, "NOT_FOUND", start_time)

        # Delete the device
        delete_query = text("""
            DELETE FROM blacklisted_devices 
            WHERE id = :device_id AND user_id = :user_id
        """)
        
        g.db.execute(delete_query, {
            "device_id": device_id,
            "user_id": user_id
        })
        
        g.db.commit()
        
        logger.info(f"Device {existing.mac_address} removed from blacklist for user {user_id}")
        return build_success_response({
            "message": "Device removed from blacklist",
            "device_id": device_id
        }, start_time)
        
    except Exception as e:
        g.db.rollback()
        logger.error(f"Error removing device from blacklist: {str(e)}", exc_info=True)
        return build_error_response("Failed to remove device from blacklist", 500, "DATABASE_ERROR", start_time)

@blacklist_bp.route("/<device_id>", methods=["GET"])
def get_blacklist_device(device_id):
    """Get a specific blacklisted device."""
    start_time = time.time()
    try:
        # Get user ID from session
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return build_error_response("User not authenticated", 401, "UNAUTHORIZED", start_time)

        # Query the specific device
        query = text("""
            SELECT id, mac_address, device_name, reason, created_at, updated_at
            FROM blacklisted_devices 
            WHERE id = :device_id AND user_id = :user_id
        """)
        
        result = g.db.execute(query, {
            "device_id": device_id,
            "user_id": user_id
        })
        
        row = result.fetchone()
        if not row:
            return build_error_response("Device not found", 404, "NOT_FOUND", start_time)

        device = {
            "id": str(row.id),
            "mac_address": row.mac_address,
            "device_name": row.device_name,
            "reason": row.reason,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None
        }
        
        return build_success_response(device, start_time)
        
    except Exception as e:
        logger.error(f"Error fetching blacklisted device: {str(e)}", exc_info=True)
        return build_error_response("Failed to fetch device", 500, "DATABASE_ERROR", start_time) 