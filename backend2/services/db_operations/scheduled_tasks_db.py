"""
Scheduled Tasks Database Operations

This module handles all database operations for scheduled tasks.
All functions return (result, error) tuple format.
"""

from typing import Dict, Optional, List, Any, Tuple
from utils.logging_config import get_logger
from managers.db_session_context import SessionContext
from models.scheduled_task import ScheduledTask
from services.task_registry import get_task, list_tasks

logger = get_logger('services.db_operations.scheduled_tasks_db')


def st_db_create_task(user_id: str, router_id: str, service: str, task: str, 
                     params: Dict[str, Any], hour: int, minute: int, 
                     days_of_week: Optional[List[int]] = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Create a new scheduled task in the database.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        service: Service name
        task: Task name
        params: Task parameters
        hour: Hour (0-23)
        minute: Minute (0-59)
        days_of_week: Optional list of weekdays
        
    Returns:
        Tuple of (task_data_dict, error_message)
    """
    try:
        session = SessionContext.get()
        if not session:
            return None, "No database session available"
        
        # Validate that service.task exists in registry
        registry_entry = get_task(service, task)
        if not registry_entry:
            available_tasks = list_tasks()
            available_services = {f"{s}.{t}" for (s, t) in available_tasks.keys()}
            return None, f"Invalid service.task: {service}.{task}. Available: {', '.join(sorted(available_services))}"
        
        # Create the scheduled task
        scheduled_task = ScheduledTask(
            user_id=user_id,
            router_id=router_id,
            service=service,
            task=task,
            params=params,
            hour=hour,
            minute=minute,
            days_of_week=days_of_week,
            enabled=True
        )
        
        session.add(scheduled_task)
        session.commit()
        
        logger.info(f"Created scheduled task {scheduled_task.id}: {service}.{task} for user {user_id}")
        
        return {
            "id": str(scheduled_task.id),
            "service": service,
            "task": task,
            "hour": hour,
            "minute": minute,
            "days_of_week": days_of_week,
            "enabled": True,
            "created_at": scheduled_task.created_at.isoformat() if scheduled_task.created_at else None
        }, None
        
    except Exception as e:
        logger.error(f"Failed to create scheduled task: {e}", exc_info=True)
        try:
            session.rollback()
        except Exception:
            pass
        return None, f"Database error: {str(e)}"


def st_db_list_tasks(user_id: str, router_id: Optional[str] = None, 
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
    try:
        session = SessionContext.get()
        if not session:
            return None, "No database session available"
        
        query = session.query(ScheduledTask).filter(ScheduledTask.user_id == user_id)
        
        if router_id:
            query = query.filter(ScheduledTask.router_id == router_id)
        
        if enabled is not None:
            query = query.filter(ScheduledTask.enabled == enabled)
        
        scheduled_tasks = query.order_by(ScheduledTask.hour, ScheduledTask.minute).all()
        
        tasks_data = []
        for task in scheduled_tasks:
            tasks_data.append({
                "id": str(task.id),
                "router_id": task.router_id,
                "service": task.service,
                "task": task.task,
                "hour": task.hour,
                "minute": task.minute,
                "days_of_week": task.days_of_week,
                "enabled": task.enabled,
                "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
                "last_status": task.last_status,
                "last_error": task.last_error,
                "created_at": task.created_at.isoformat() if task.created_at else None
            })
        
        return {
            "tasks": tasks_data,
            "count": len(tasks_data)
        }, None
        
    except Exception as e:
        logger.error(f"Failed to list scheduled tasks: {e}", exc_info=True)
        return None, f"Database error: {str(e)}"


def st_db_delete_task(user_id: str, task_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Delete a scheduled task.
    
    Args:
        user_id: User's UUID
        task_id: Scheduled task UUID
        
    Returns:
        Tuple of (result_dict, error_message)
    """
    try:
        session = SessionContext.get()
        if not session:
            return None, "No database session available"
        
        scheduled_task = (
            session.query(ScheduledTask)
            .filter(
                ScheduledTask.id == task_id,
                ScheduledTask.user_id == user_id
            )
            .first()
        )
        
        if not scheduled_task:
            return None, "Scheduled task not found"
        
        # Store info for logging
        task_info = f"{scheduled_task.service}.{scheduled_task.task}"
        
        session.delete(scheduled_task)
        session.commit()
        
        logger.info(f"Deleted scheduled task {task_id}: {task_info} for user {user_id}")
        
        return {"message": "Scheduled task deleted successfully"}, None
        
    except Exception as e:
        logger.error(f"Failed to delete scheduled task {task_id}: {e}", exc_info=True)
        try:
            session.rollback()
        except Exception:
            pass
        return None, f"Database error: {str(e)}"


def st_db_toggle_task(user_id: str, task_id: str, enabled: bool) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Enable or disable a scheduled task.
    
    Args:
        user_id: User's UUID
        task_id: Scheduled task UUID
        enabled: Whether to enable or disable the task
        
    Returns:
        Tuple of (result_dict, error_message)
    """
    try:
        session = SessionContext.get()
        if not session:
            return None, "No database session available"
        
        scheduled_task = (
            session.query(ScheduledTask)
            .filter(
                ScheduledTask.id == task_id,
                ScheduledTask.user_id == user_id
            )
            .first()
        )
        
        if not scheduled_task:
            return None, "Scheduled task not found"
        
        # Update enabled status
        scheduled_task.enabled = enabled
        session.commit()
        
        status_text = "enabled" if enabled else "disabled"
        logger.info(f"{status_text.capitalize()} scheduled task {task_id}: {scheduled_task.service}.{scheduled_task.task} for user {user_id}")
        
        return {
            "message": f"Scheduled task {status_text} successfully",
            "enabled": enabled
        }, None
        
    except Exception as e:
        logger.error(f"Failed to toggle scheduled task {task_id}: {e}", exc_info=True)
        try:
            session.rollback()
        except Exception:
            pass
        return None, f"Database error: {str(e)}"


def st_db_get_available_tasks() -> Tuple[Optional[Dict], Optional[str]]:
    """
    Get list of available tasks that can be scheduled.
    
    Returns:
        Tuple of (available_tasks_dict, error_message)
    """
    try:
        available_tasks = list_tasks()
        
        tasks_data = []
        for (service, task), entry in available_tasks.items():
            tasks_data.append({
                "service": service,
                "task": task,
                "has_resolver": entry.get('resolver') is not None
            })
        
        return {
            "available_tasks": tasks_data,
            "count": len(tasks_data)
        }, None
        
    except Exception as e:
        logger.error(f"Failed to get available tasks: {e}", exc_info=True)
        return None, f"Registry error: {str(e)}"


def st_db_update_task_timing(user_id: str, task_id: str, hour: Optional[int] = None, 
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
    try:
        session = SessionContext.get()
        if not session:
            return None, "No database session available"
        
        # Find the scheduled task
        scheduled_task = (
            session.query(ScheduledTask)
            .filter(
                ScheduledTask.id == task_id,
                ScheduledTask.user_id == user_id
            )
            .first()
        )
        
        if not scheduled_task:
            return None, "Scheduled task not found"
        
        # Store original values for logging
        original_hour = scheduled_task.hour
        original_minute = scheduled_task.minute
        original_days = scheduled_task.days_of_week
        
        # Update only the provided fields
        if hour is not None:
            scheduled_task.hour = hour
        if minute is not None:
            scheduled_task.minute = minute
        if days_of_week is not None:
            scheduled_task.days_of_week = days_of_week
        
        session.commit()
        
        # Log the update
        changes = []
        if hour is not None and hour != original_hour:
            changes.append(f"hour: {original_hour} → {hour}")
        if minute is not None and minute != original_minute:
            changes.append(f"minute: {original_minute} → {minute}")
        if days_of_week is not None and days_of_week != original_days:
            changes.append(f"days_of_week: {original_days} → {days_of_week}")
        
        if changes:
            logger.info(f"Updated scheduled task {task_id} timing: {', '.join(changes)} for user {user_id}")
        
        return {
            "message": "Scheduled task timing updated successfully",
            "updated_fields": {
                "hour": scheduled_task.hour,
                "minute": scheduled_task.minute,
                "days_of_week": scheduled_task.days_of_week
            }
        }, None
        
    except Exception as e:
        logger.error(f"Failed to update scheduled task {task_id} timing: {e}", exc_info=True)
        try:
            session.rollback()
        except Exception:
            pass
        return None, f"Database error: {str(e)}"
