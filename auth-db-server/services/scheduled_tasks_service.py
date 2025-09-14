"""
Scheduled Tasks Service - Main Orchestration Layer

This service acts as the conductor for scheduled task operations, coordinating between
database operations and business logic. It follows the 3-layer architecture:
1. This service (orchestration) - calls database operations
2. services/db_operations/scheduled_tasks_db.py - Database operations
3. No commands server operations needed for scheduled tasks
"""

from typing import Dict, Optional, List, Any, Tuple
from utils.logging_config import get_logger
from .base import (
    handle_service_errors,
    log_service_operation
)

# Database operations imports
from services.db_operations.scheduled_tasks_db import (
    st_db_create_task,
    st_db_list_tasks,
    st_db_delete_task,
    st_db_toggle_task,
    st_db_get_available_tasks,
    st_db_update_task_timing
)

logger = get_logger('services.scheduled_tasks_service')


@handle_service_errors("Create scheduled task")
def create_scheduled_task(user_id: str, router_id: str, service: str, task: str, 
                         params: Dict[str, Any], hour: Optional[int] = None, minute: Optional[int] = None, 
                         days_of_week: Optional[List[int]] = None, task_type: str = 'fixed', 
                         interval_minutes: Optional[int] = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Create a new scheduled task.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        service: Service name (e.g., 'bandwidth', 'agh')
        task: Task name (e.g., 'apply_group_limits')
        params: Task parameters as dictionary
        hour: Hour (0-23) - required for fixed tasks, ignored for interval tasks
        minute: Minute (0-59) - required for fixed tasks, ignored for interval tasks
        days_of_week: Optional list of weekdays (0-6, Monday=0)
        task_type: 'fixed' for time-based tasks, 'interval' for recurring tasks
        interval_minutes: Minutes between executions for interval tasks
        
    Returns:
        Tuple of (task_data_dict, error_message)
    """
    log_service_operation("create_scheduled_task", user_id, router_id, "scheduler", {
        "router_id": router_id,
        "service": service,
        "task": task,
        "hour": hour,
        "minute": minute,
        "days_of_week": days_of_week,
        "task_type": task_type,
        "interval_minutes": interval_minutes
    })
    
    # Call database operation
    result, error = st_db_create_task(user_id, router_id, service, task, params, hour, minute, days_of_week, task_type, interval_minutes)
    if error:
        log_service_operation("create_scheduled_task", user_id, router_id, "scheduler", 
                            {"router_id": router_id, "service": service, "task": task}, 
                            success=False, error=error)
        return None, error
    
    log_service_operation("create_scheduled_task", user_id, router_id, "scheduler", 
                         {"router_id": router_id, "service": service, "task": task}, 
                         success=True)
    return result, None


@handle_service_errors("List scheduled tasks")
def list_scheduled_tasks(user_id: str, router_id: Optional[str] = None, 
                        enabled: Optional[bool] = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    List user's scheduled tasks with optional filters.
    
    Args:
        user_id: User's UUID
        router_id: Optional router filter
        enabled: Optional enabled status filter
        
    Returns:
        Tuple of (tasks_data_dict, error_message)
    """
    log_service_operation("list_scheduled_tasks", user_id, "scheduler", "scheduler", {
        "router_id": router_id,
        "enabled": enabled
    })
    
    # Call database operation
    result, error = st_db_list_tasks(user_id, router_id, enabled)
    if error:
        log_service_operation("list_scheduled_tasks", user_id, "scheduler", "scheduler", 
                            {"router_id": router_id, "enabled": enabled}, 
                            success=False, error=error)
        return None, error
    
    log_service_operation("list_scheduled_tasks", user_id, "scheduler", "scheduler", 
                         {"router_id": router_id, "enabled": enabled}, 
                         success=True)
    return result, None


@handle_service_errors("Delete scheduled task")
def delete_scheduled_task(user_id: str, task_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Delete a scheduled task.
    
    Args:
        user_id: User's UUID
        task_id: Scheduled task UUID
        
    Returns:
        Tuple of (result_dict, error_message)
    """
    log_service_operation("delete_scheduled_task", user_id, "scheduler", "scheduler", {"task_id": task_id})
    
    # Call database operation
    result, error = st_db_delete_task(user_id, task_id)
    if error:
        log_service_operation("delete_scheduled_task", user_id, "scheduler", "scheduler", 
                            {"task_id": task_id}, success=False, error=error)
        return None, error
    
    log_service_operation("delete_scheduled_task", user_id, "scheduler", "scheduler", 
                         {"task_id": task_id}, success=True)
    return result, None


@handle_service_errors("Toggle scheduled task")
def toggle_scheduled_task(user_id: str, task_id: str, enabled: bool) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Enable or disable a scheduled task.
    
    Args:
        user_id: User's UUID
        task_id: Scheduled task UUID
        enabled: Whether to enable or disable the task
        
    Returns:
        Tuple of (result_dict, error_message)
    """
    log_service_operation("toggle_scheduled_task", user_id, "scheduler", "scheduler", {
        "task_id": task_id,
        "enabled": enabled
    })
    
    # Call database operation
    result, error = st_db_toggle_task(user_id, task_id, enabled)
    if error:
        log_service_operation("toggle_scheduled_task", user_id, "scheduler", "scheduler", 
                            {"task_id": task_id, "enabled": enabled}, 
                            success=False, error=error)
        return None, error
    
    log_service_operation("toggle_scheduled_task", user_id, "scheduler", "scheduler", 
                         {"task_id": task_id, "enabled": enabled}, 
                         success=True)
    return result, None


@handle_service_errors("Get available tasks")
def get_available_tasks() -> Tuple[Optional[Dict], Optional[str]]:
    """
    Get list of available tasks that can be scheduled.
    
    Returns:
        Tuple of (available_tasks_dict, error_message)
    """
    log_service_operation("get_available_tasks", "scheduler", "scheduler", "scheduler")
    
    # Call database operation
    result, error = st_db_get_available_tasks()
    if error:
        log_service_operation("get_available_tasks", "scheduler", "scheduler", "scheduler", 
                            success=False, error=error)
        return None, error
    
    log_service_operation("get_available_tasks", "scheduler", "scheduler", "scheduler", success=True)
    return result, None


@handle_service_errors("Update scheduled task timing")
def update_scheduled_task_timing(user_id: str, task_id: str, hour: Optional[int] = None, 
                                minute: Optional[int] = None, days_of_week: Optional[List[int]] = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Update only the timing fields of a scheduled task (safe update).
    
    Args:
        user_id: User's UUID
        task_id: Scheduled task UUID
        hour: Optional new hour (0-23)
        minute: Optional new minute (0-59)
        days_of_week: Optional new list of weekdays (0-6, Monday=0)
        
    Returns:
        Tuple of (result_dict, error_message)
    """
    log_service_operation("update_scheduled_task_timing", user_id, "scheduler", "scheduler", {
        "task_id": task_id,
        "hour": hour,
        "minute": minute,
        "days_of_week": days_of_week
    })
    
    # Call database operation
    result, error = st_db_update_task_timing(user_id, task_id, hour, minute, days_of_week)
    if error:
        log_service_operation("update_scheduled_task_timing", user_id, "scheduler", "scheduler", 
                            {"task_id": task_id, "hour": hour, "minute": minute, "days_of_week": days_of_week}, 
                            success=False, error=error)
        return None, error
    
    log_service_operation("update_scheduled_task_timing", user_id, "scheduler", "scheduler", 
                         {"task_id": task_id, "hour": hour, "minute": minute, "days_of_week": days_of_week}, 
                         success=True)
    return result, None
