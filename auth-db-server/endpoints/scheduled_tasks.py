"""
Scheduled Tasks Endpoint

Provides minimal CRUD operations for scheduled tasks:
- create: Create new scheduled task
- delete: Delete existing scheduled task
- list: List user's scheduled tasks
- enable/disable: Toggle task status

Tasks are immutable after creation to preserve the delicate parameter format.
"""

from flask import Blueprint, request, g
from utils.response_helpers import build_success_response, build_error_response
from utils.logging_config import get_logger
from services.scheduled_tasks_service import (
    create_scheduled_task,
    list_scheduled_tasks,
    delete_scheduled_task,
    toggle_scheduled_task,
    get_available_tasks,
    update_scheduled_task_timing
)
import time

logger = get_logger('endpoints.scheduled_tasks')

scheduled_tasks_bp = Blueprint('scheduled_tasks', __name__)


@scheduled_tasks_bp.route('/scheduled-tasks', methods=['POST'])
def create_scheduled_task_endpoint():
    """Create a new scheduled task."""
    start_time = time.time()
    try:
        data = request.get_json()
        if not data:
            return build_error_response("Request body is required", 400, "MISSING_BODY", start_time)
        
        # Extract and validate required fields
        user_id = g.user_id
        router_id = data.get('router_id')
        service = data.get('service')
        task = data.get('task')
        params = data.get('params', {})
        hour = data.get('hour')
        minute = data.get('minute')
        days_of_week = data.get('days_of_week')  # Optional
        task_type = data.get('task_type', 'fixed')  # Default to 'fixed' for backward compatibility
        interval_minutes = data.get('interval_minutes')  # Optional
        
        # Validate basic required fields
        if not all([router_id, service, task]):
            return build_error_response("Missing required fields: router_id, service, task", 400, "MISSING_FIELDS", start_time)
        
        # Validate task type and type-specific fields
        if task_type == 'fixed':
            if hour is None or minute is None:
                return build_error_response("Fixed tasks require both hour and minute", 400, "MISSING_TIME_FIELDS", start_time)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return build_error_response("Invalid time: hour must be 0-23, minute must be 0-59", 400, "INVALID_TIME", start_time)
        elif task_type == 'interval':
            if interval_minutes is None or not isinstance(interval_minutes, int) or interval_minutes <= 0:
                return build_error_response("Interval tasks require a positive integer interval_minutes", 400, "INVALID_INTERVAL", start_time)
        else:
            return build_error_response("task_type must be 'fixed' or 'interval'", 400, "INVALID_TASK_TYPE", start_time)
        
        # Validate days_of_week if provided
        if days_of_week is not None:
            if not isinstance(days_of_week, list):
                return build_error_response("days_of_week must be a list", 400, "INVALID_DAYS_FORMAT", start_time)
            if not all(0 <= day <= 6 for day in days_of_week):
                return build_error_response("days_of_week values must be 0-6 (Monday=0, Sunday=6)", 400, "INVALID_DAYS_RANGE", start_time)
        
        # Validate params is a dict
        if not isinstance(params, dict):
            return build_error_response("params must be a dictionary", 400, "INVALID_PARAMS_FORMAT", start_time)
        
        # Call service
        result, error = create_scheduled_task(user_id, router_id, service, task, params, hour, minute, days_of_week, task_type, interval_minutes)
        if error:
            return build_error_response(f"Failed to create scheduled task: {error}", 500, "SERVICE_ERROR", start_time)
        
        return build_success_response(result, start_time)
        
    except Exception as e:
        logger.error(f"Failed to create scheduled task: {e}", exc_info=True)
        return build_error_response(f"Failed to create scheduled task: {str(e)}", 500, "INTERNAL_ERROR", start_time)


@scheduled_tasks_bp.route('/scheduled-tasks', methods=['GET'])
def list_scheduled_tasks_endpoint():
    """List user's scheduled tasks."""
    start_time = time.time()
    try:
        user_id = g.user_id
        
        # Extract optional filters
        router_id = request.args.get('router_id')
        enabled = request.args.get('enabled')
        
        # Convert enabled string to boolean if provided
        enabled_bool = None
        if enabled is not None:
            if enabled.lower() == 'true':
                enabled_bool = True
            elif enabled.lower() == 'false':
                enabled_bool = False
            else:
                return build_error_response("enabled must be 'true' or 'false'", 400, "INVALID_ENABLED_FORMAT", start_time)
        
        # Call service
        result, error = list_scheduled_tasks(user_id, router_id, enabled_bool)
        if error:
            return build_error_response(f"Failed to list scheduled tasks: {error}", 500, "SERVICE_ERROR", start_time)
        
        return build_success_response(result, start_time)
        
    except Exception as e:
        logger.error(f"Failed to list scheduled tasks: {e}", exc_info=True)
        return build_error_response(f"Failed to list scheduled tasks: {str(e)}", 500, "INTERNAL_ERROR", start_time)


@scheduled_tasks_bp.route('/scheduled-tasks/<task_id>', methods=['DELETE'])
def delete_scheduled_task_endpoint(task_id: str):
    """Delete a scheduled task."""
    start_time = time.time()
    try:
        user_id = g.user_id
        
        # Call service
        result, error = delete_scheduled_task(user_id, task_id)
        if error:
            status_code = 404 if "not found" in error.lower() else 400
            error_code = "TASK_NOT_FOUND" if status_code == 404 else "DELETE_FAILED"
            return build_error_response(f"Failed to delete scheduled task: {error}", status_code, error_code, start_time)
        
        return build_success_response(result, start_time)
        
    except Exception as e:
        logger.error(f"Failed to delete scheduled task {task_id}: {e}", exc_info=True)
        return build_error_response(f"Failed to delete scheduled task: {str(e)}", 500, "INTERNAL_ERROR", start_time)


@scheduled_tasks_bp.route('/scheduled-tasks/<task_id>/toggle', methods=['POST'])
def toggle_scheduled_task_endpoint(task_id: str):
    """Enable or disable a scheduled task."""
    start_time = time.time()
    try:
        user_id = g.user_id
        data = request.get_json() or {}
        enabled = data.get('enabled')
        
        if enabled is None:
            return build_error_response("enabled field is required", 400, "MISSING_ENABLED", start_time)
        
        if not isinstance(enabled, bool):
            return build_error_response("enabled must be a boolean", 400, "INVALID_ENABLED_TYPE", start_time)
        
        # Call service
        result, error = toggle_scheduled_task(user_id, task_id, enabled)
        if error:
            status_code = 404 if "not found" in error.lower() else 400
            error_code = "TASK_NOT_FOUND" if status_code == 404 else "TOGGLE_FAILED"
            return build_error_response(f"Failed to toggle scheduled task: {error}", status_code, error_code, start_time)
        
        return build_success_response(result, start_time)
        
    except Exception as e:
        logger.error(f"Failed to toggle scheduled task {task_id}: {e}", exc_info=True)
        return build_error_response(f"Failed to toggle scheduled task: {str(e)}", 500, "INTERNAL_ERROR", start_time)


@scheduled_tasks_bp.route('/scheduled-tasks/<task_id>', methods=['PUT'])
def update_scheduled_task_timing_endpoint(task_id: str):
    """Update only the timing fields of a scheduled task (safe update)."""
    start_time = time.time()
    try:
        user_id = g.user_id
        data = request.get_json()
        if not data:
            return build_error_response("Request body is required", 400, "MISSING_BODY", start_time)
        
        # Extract optional timing fields
        hour = data.get('hour')
        minute = data.get('minute')
        days_of_week = data.get('days_of_week')
        
        # Validate that at least one field is provided
        if all(field is None for field in [hour, minute, days_of_week]):
            return build_error_response("At least one timing field must be provided: hour, minute, or days_of_week", 400, "NO_FIELDS_PROVIDED", start_time)
        
        # Validate hour if provided
        if hour is not None:
            if not isinstance(hour, int) or not (0 <= hour <= 23):
                return build_error_response("hour must be an integer between 0-23", 400, "INVALID_HOUR", start_time)
        
        # Validate minute if provided
        if minute is not None:
            if not isinstance(minute, int) or not (0 <= minute <= 59):
                return build_error_response("minute must be an integer between 0-59", 400, "INVALID_MINUTE", start_time)
        
        # Validate days_of_week if provided
        if days_of_week is not None:
            if not isinstance(days_of_week, list):
                return build_error_response("days_of_week must be a list", 400, "INVALID_DAYS_FORMAT", start_time)
            if not all(isinstance(day, int) and 0 <= day <= 6 for day in days_of_week):
                return build_error_response("days_of_week values must be integers 0-6 (Monday=0, Sunday=6)", 400, "INVALID_DAYS_RANGE", start_time)
        
        # Call service
        result, error = update_scheduled_task_timing(user_id, task_id, hour, minute, days_of_week)
        if error:
            status_code = 404 if "not found" in error.lower() else 400
            error_code = "TASK_NOT_FOUND" if status_code == 404 else "UPDATE_FAILED"
            return build_error_response(f"Failed to update scheduled task timing: {error}", status_code, error_code, start_time)
        
        return build_success_response(result, start_time)
        
    except Exception as e:
        logger.error(f"Failed to update scheduled task {task_id} timing: {e}", exc_info=True)
        return build_error_response(f"Failed to update scheduled task timing: {str(e)}", 500, "INTERNAL_ERROR", start_time)


@scheduled_tasks_bp.route('/scheduled-tasks/available-tasks', methods=['GET'])
def get_available_tasks_endpoint():
    """Get list of available tasks that can be scheduled."""
    start_time = time.time()
    try:
        # Call service
        result, error = get_available_tasks()
        if error:
            return build_error_response(f"Failed to get available tasks: {error}", 500, "SERVICE_ERROR", start_time)
        
        return build_success_response(result, start_time)
        
    except Exception as e:
        logger.error(f"Failed to get available tasks: {e}", exc_info=True)
        return build_error_response(f"Failed to get available tasks: {str(e)}", 500, "INTERNAL_ERROR", start_time)
