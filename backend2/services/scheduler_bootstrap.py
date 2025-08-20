from decouple import config
from flask_apscheduler import APScheduler
from utils.logging_config import get_logger
from .task_registry import load_registry, get_task, resolve_params
from .scheduler_session_manager import ensure_active_session
from managers.transaction_manager import TransactionManager
from models.scheduled_task import ScheduledTask
from managers.db_session_context import SessionContext
import random
import time
from datetime import datetime, timezone
import pytz


logger = get_logger('scheduler.bootstrap')


def dispatcher_tick():
    """
    Main dispatcher function that runs every minute to execute scheduled tasks.
    
    This function:
    1. Computes current local time (Asia/Jerusalem) and selects enabled tasks due now
    2. Applies throttling: global concurrency cap, per-router single-flight lock, cooldown
    3. Adds randomized jitter/staggering for simultaneous tasks
    4. For each task: ensures session, resolves group targets, calls mapped service
    5. Captures and persists execution results
    """
    try:
        # Get current time in Asia/Jerusalem timezone
        tz = pytz.timezone(config('SCHEDULER_TIMEZONE', default='Asia/Jerusalem'))
        now = datetime.now(tz)
        current_hour = now.hour
        current_minute = now.minute
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        logger.debug(f"Dispatcher tick at {now.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday {current_weekday})")
        
        # Get enabled tasks due for current time
        # Create a session context for the dispatcher
        from database.connection import db
        session = db.get_session()
        SessionContext.set(session)
        
        try:
            due_tasks = (
                session.query(ScheduledTask)
                .filter(
                    ScheduledTask.enabled == True,
                    ScheduledTask.hour == current_hour,
                    ScheduledTask.minute == current_minute
                )
                .all()
            )
        finally:
            # Clean up session
            session.close()
            SessionContext.clear()
        
        # Filter by days_of_week if specified
        if due_tasks:
            filtered_tasks = []
            for task in due_tasks:
                if task.days_of_week is None or current_weekday in task.days_of_week:
                    filtered_tasks.append(task)
            due_tasks = filtered_tasks
        
        if not due_tasks:
            logger.debug("No tasks due at current time")
            return
            
        logger.info(f"Found {len(due_tasks)} tasks due for execution")
        
        # Apply throttling and execute tasks
        max_concurrent = config('MAX_CONCURRENT_SCHEDULED_TASKS', default=5, cast=int)
        min_router_gap = config('MIN_ROUTER_GAP_SECONDS', default=5, cast=int)
        
        # Track active executions per router
        active_routers = set()
        completed_count = 0
        
        for task in due_tasks:
            # Check global concurrency cap
            if completed_count >= max_concurrent:
                logger.info(f"Global concurrency cap reached ({max_concurrent}), deferring remaining tasks")
                break
                
            # Check per-router single-flight lock
            if task.router_id in active_routers:
                logger.debug(f"Router {task.router_id} already has active task, deferring {task.id}")
                continue
                
            # Check per-router cooldown
            if task.last_run_at:
                time_since_last = (now - task.last_run_at.replace(tzinfo=tz)).total_seconds()
                if time_since_last < min_router_gap:
                    logger.debug(f"Router {task.router_id} in cooldown ({time_since_last:.1f}s < {min_router_gap}s), deferring {task.id}")
                    continue
            
            # Add randomized jitter to avoid thundering herd
            jitter_ms = random.randint(50, 2000)
            time.sleep(jitter_ms / 1000.0)
            
            # Execute task
            success = execute_scheduled_task(task, now)
            if success:
                completed_count += 1
                active_routers.add(task.router_id)
                
        logger.info(f"Dispatcher completed: {completed_count}/{len(due_tasks)} tasks executed")
        
    except Exception as e:
        logger.error(f"Dispatcher tick failed: {e}", exc_info=True)


def execute_scheduled_task(task: ScheduledTask, execution_time: datetime) -> bool:
    """
    Execute a single scheduled task with proper session management and error handling.
    
    Args:
        task: The ScheduledTask to execute
        execution_time: When the task was executed
        
    Returns:
        bool: True if task executed successfully, False otherwise
    """
    logger.info(f"Executing scheduled task {task.id}: {task.service}.{task.task}")
    
    try:
        # Get task from registry
        registry_entry = get_task(task.service, task.task)
        if not registry_entry:
            error_msg = f"Task {task.service}.{task.task} not found in registry"
            logger.error(error_msg)
            update_task_status(task, execution_time, "ERROR", error_msg)
            return False
        
        # Ensure active session
        last_session_id = None
        if task.run_metadata and isinstance(task.run_metadata, dict):
            last_session_id = task.run_metadata.get('last_known_session_id')
            
        session_id, session_error = ensure_active_session(task.user_id, task.router_id, last_session_id)
        if session_error:
            error_msg = f"Failed to ensure active session: {session_error}"
            logger.error(error_msg)
            update_task_status(task, execution_time, "ERROR", error_msg)
            return False
        
        # Resolve parameters (including group targets if needed)
        # We need to ensure we have a proper session context for the resolver
        try:
            # Create a temporary session context for parameter resolution
            from database.connection import db
            temp_session = db.get_session()
            SessionContext.set(temp_session)
            
            try:
                resolved_params = resolve_params(task.service, task.task, task.user_id, task.router_id, task.params)
            finally:
                # Clean up temporary session
                temp_session.close()
                SessionContext.clear()
                
        except Exception as e:
            error_msg = f"Parameter resolution failed: {e}"
            logger.error(error_msg)
            update_task_status(task, execution_time, "ERROR", error_msg)
            return False
        
        # Execute the task using transaction manager
        def task_executor():
            try:
                # Call the registered service function
                service_func = registry_entry['call']
                result, error = service_func(task.user_id, task.router_id, session_id, **resolved_params)
                
                if error:
                    return None, error
                return result, None
            except Exception as e:
                return None, str(e)
        
        # Execute with transaction management
        result, error = TransactionManager.run(task_executor)
        
        if error:
            update_task_status(task, execution_time, "ERROR", error)
            return False
        
        # Update task status on success
        update_task_status(task, execution_time, "SUCCESS", None, session_id)
        logger.info(f"Task {task.id} executed successfully")
        return True
        
    except Exception as e:
        error_msg = f"Unexpected error during task execution: {e}"
        logger.error(error_msg, exc_info=True)
        update_task_status(task, execution_time, "ERROR", error_msg)
        return False


def update_task_status(task: ScheduledTask, execution_time: datetime, status: str, error: str = None, session_id: str = None):
    """
    Update task execution status in the database.
    
    Args:
        task: The ScheduledTask to update
        execution_time: When the task was executed
        status: Execution status (SUCCESS, ERROR)
        error: Error message if status is ERROR
        session_id: Session ID that was used (for metadata)
    """
    try:
        # Create a session context for status update
        from database.connection import db
        session = db.get_session()
        SessionContext.set(session)
        
        try:
            # Update task status
            task.last_run_at = execution_time
            task.last_status = status
            task.last_error = error
            
            # Update metadata with session info
            if not task.run_metadata:
                task.run_metadata = {}
            if session_id:
                task.run_metadata['last_known_session_id'] = session_id
                
            # Commit the status update
            session.commit()
            logger.debug(f"Updated task {task.id} status: {status}")
            
        finally:
            # Clean up session
            session.close()
            SessionContext.clear()
        
    except Exception as e:
        logger.error(f"Failed to update task {task.id} status: {e}")
        try:
            if 'session' in locals():
                session.rollback()
        except Exception:
            pass


def init_scheduler(app):
    """Initialize and start the APScheduler if enabled and this instance is the leader."""
    try:
        enabled = config('SCHEDULER_ENABLED', default=False, cast=bool)
        if not enabled:
            logger.info("Scheduler disabled by env (SCHEDULER_ENABLED=false)")
            return None

        # Optional single-runner guard for multi-instance deployments
        is_leader = config('SCHEDULER_IS_LEADER', default=True, cast=bool)
        if not is_leader:
            logger.info("Scheduler not started: this instance is not the leader (SCHEDULER_IS_LEADER=false)")
            return None

        tz_name = config('SCHEDULER_TIMEZONE', default='Asia/Jerusalem')

        # Configure and start scheduler
        scheduler = APScheduler()
        app.config['SCHEDULER_TIMEZONE'] = tz_name
        app.config['SCHEDULER_API_ENABLED'] = False

        # Reasonable defaults; will adjust later if needed
        app.config['APSCHEDULER_JOB_DEFAULTS'] = {
            'coalesce': True,  # coalesce missed runs into one
            'max_instances': 1,
            'misfire_grace_time': 30,
        }

        scheduler.init_app(app)

        # Load task registry (decorators execute on import)
        load_registry()

        # Register minute-based dispatcher (placeholder)
        scheduler.add_job(
            id='scheduler_dispatcher',
            func=dispatcher_tick,
            trigger='cron',
            minute='*',
            timezone=tz_name,
            replace_existing=True,
        )

        scheduler.start()
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['apscheduler'] = scheduler
        logger.info(f"Scheduler started with timezone {tz_name}")
        return scheduler
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}")
        return None


