from decouple import config
from flask_apscheduler import APScheduler
from utils.logging_config import get_logger
from .task_registry import load_registry, get_task, resolve_params
from .scheduler_session_manager import ensure_active_session
from models.scheduled_task import ScheduledTask
from managers.db_session_context import SessionContext
import random
import time
from datetime import datetime, timezone
import pytz


logger = get_logger('scheduler.bootstrap')


def _task_to_dict(task: ScheduledTask) -> dict:
    """Convert a ScheduledTask to a dictionary for detached processing."""
    return {
        'id': task.id,
        'user_id': task.user_id,
        'router_id': task.router_id,
        'service': task.service,
        'task': task.task,
        'params': task.params,
        'task_type': task.task_type,
        'hour': task.hour,
        'minute': task.minute,
        'days_of_week': task.days_of_week,
        'interval_minutes': task.interval_minutes,
        'last_run_at': task.last_run_at,
        'enabled': task.enabled,
        'run_metadata': task.run_metadata,
    }


def _update_task_status_in_session(session, task_id: str, execution_time: datetime, status: str, error: str = None, session_id: str = None):
    """Update task status within an existing session."""
    try:
        # Get the task object in this session
        task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found when updating status")
            return
        
        # Update task status
        task.last_run_at = execution_time
        task.last_status = status
        task.last_error = error
        
        # Update metadata with session info
        if not task.run_metadata:
            task.run_metadata = {}
        if session_id:
            task.run_metadata['last_known_session_id'] = str(session_id)
            
        logger.debug(f"Updated task {task_id} status: {status}")
        
    except Exception as e:
        logger.error(f"Failed to update task {task_id} status: {e}")


def dispatcher_tick():
    """
    Main dispatcher function that runs every minute to execute scheduled tasks.
    
    Clean Architecture:
    1. TASK DISCOVERY: Open session → Query due tasks → Close session
    2. FOR EACH TASK: Open session → Execute task → Update status → Commit/Rollback → Close session
    """
    try:
        # Get current time in Asia/Jerusalem timezone
        tz = pytz.timezone(config('SCHEDULER_TIMEZONE', default='Asia/Jerusalem'))
        now = datetime.now(tz)
        current_hour = now.hour
        current_minute = now.minute
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        # Create round minute timestamp for last_run_at (ensures consistent 2-minute intervals)
        round_minute_time = now.replace(second=0, microsecond=0)
        
        logger.debug(f"Dispatcher tick at {now.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday {current_weekday})")
        logger.debug(f"Round minute time for last_run_at: {round_minute_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # ============ STEP 1: TASK DISCOVERY SESSION ============
        # Open a short-lived session to find tasks that need to run
        from database.connection import db
        discovery_session = db.get_session()
        
        try:
            # Get fixed-time tasks
            fixed_tasks = (
                discovery_session.query(ScheduledTask)
                .filter(
                    ScheduledTask.enabled == True,
                    # Support both NULL and 'fixed' for backward compatibility
                    (ScheduledTask.task_type == 'fixed') | (ScheduledTask.task_type.is_(None)),
                    ScheduledTask.hour == current_hour,
                    ScheduledTask.minute == current_minute
                )
                .all()
            )
            
            # Get interval-based tasks
            interval_tasks = (
                discovery_session.query(ScheduledTask)
                .filter(
                    ScheduledTask.enabled == True,
                    ScheduledTask.task_type == 'interval',
                    ScheduledTask.interval_minutes.isnot(None)
                )
                .all()
            )
            
            # Convert to simple data structures (detach from session)
            fixed_task_data = [_task_to_dict(task) for task in fixed_tasks]
            interval_task_data = [_task_to_dict(task) for task in interval_tasks]
            
        finally:
            # Close discovery session
            discovery_session.close()
            logger.debug("Closed task discovery session")
        
        # ============ STEP 2: FILTER INTERVAL TASKS ============
        # Filter interval tasks by time elapsed since last run
        due_interval_task_data = []
        for task_data in interval_task_data:
            if task_data['last_run_at'] is None:
                # Never run before, execute now
                due_interval_task_data.append(task_data)
                logger.debug(f"Interval task {task_data['id']} due: never run before")
            else:
                # Check if enough time has passed since last run
                # Convert last_run_at to scheduler timezone for proper comparison
                last_run_at = task_data['last_run_at']
                if last_run_at.tzinfo is None:
                    # Database timestamp is timezone-naive UTC, convert to scheduler timezone
                    last_run_utc = pytz.UTC.localize(last_run_at)
                    last_run_tz_aware = last_run_utc.astimezone(tz)
                else:
                    # Already timezone-aware, convert to scheduler timezone
                    last_run_tz_aware = last_run_at.astimezone(tz)
                
                time_since_last = (now - last_run_tz_aware).total_seconds()
                minutes_since_last = time_since_last / 60
                
                logger.debug(f"Interval task {task_data['id']} timezone conversion: DB={last_run_at} → Scheduler={last_run_tz_aware.strftime('%Y-%m-%d %H:%M:%S %Z')} → {minutes_since_last:.1f}min elapsed")
                
                if minutes_since_last >= task_data['interval_minutes']:
                    due_interval_task_data.append(task_data)
                    logger.debug(f"Interval task {task_data['id']} due: {minutes_since_last:.1f} minutes >= {task_data['interval_minutes']} minutes")
                else:
                    logger.debug(f"Interval task {task_data['id']} not due: {minutes_since_last:.1f} minutes < {task_data['interval_minutes']} minutes")
        
        # Combine both types of tasks
        due_task_data = fixed_task_data + due_interval_task_data
        
        # ============ STEP 3: FILTER BY WEEKDAY ============
        # Filter by days_of_week if specified
        if due_task_data:
            filtered_task_data = []
            for task_data in due_task_data:
                if task_data['days_of_week'] is None or current_weekday in task_data['days_of_week']:
                    filtered_task_data.append(task_data)
            due_task_data = filtered_task_data
        
        if not due_task_data:
            logger.debug("No tasks due at current time")
            return
            
        logger.info(f"Found {len(due_task_data)} tasks due for execution ({len(fixed_task_data)} fixed-time, {len(due_interval_task_data)} interval)")
        
        # ============ STEP 4: EXECUTE TASKS WITH INDIVIDUAL SESSIONS ============
        # Apply throttling and execute tasks
        max_concurrent = config('MAX_CONCURRENT_SCHEDULED_TASKS', default=5, cast=int)
        min_router_gap = config('MIN_ROUTER_GAP_SECONDS', default=5, cast=int)
        
        # Track active executions per router
        active_routers = set()
        completed_count = 0
        
        for task_data in due_task_data:
            # Check global concurrency cap
            if completed_count >= max_concurrent:
                logger.info(f"Global concurrency cap reached ({max_concurrent}), deferring remaining tasks")
                break
                
            # Check per-router single-flight lock
            if task_data['router_id'] in active_routers:
                logger.debug(f"Router {task_data['router_id']} already has active task, deferring {task_data['id']}")
                continue
                
            # Check per-router cooldown
            if task_data['last_run_at']:
                # Convert last_run_at to scheduler timezone for proper comparison
                last_run_at = task_data['last_run_at']
                if last_run_at.tzinfo is None:
                    # Database timestamp is timezone-naive UTC, convert to scheduler timezone
                    last_run_utc = pytz.UTC.localize(last_run_at)
                    last_run_tz_aware = last_run_utc.astimezone(tz)
                else:
                    # Already timezone-aware, convert to scheduler timezone
                    last_run_tz_aware = last_run_at.astimezone(tz)
                
                time_since_last = (now - last_run_tz_aware).total_seconds()
                if time_since_last < min_router_gap:
                    logger.debug(f"Router {task_data['router_id']} in cooldown ({time_since_last:.1f}s < {min_router_gap}s), deferring {task_data['id']}")
                    continue
            
            # Add randomized jitter to avoid thundering herd
            jitter_ms = random.randint(50, 2000)
            time.sleep(jitter_ms / 1000.0)
            
            # Execute task with its own isolated session (use round minute for consistent intervals)
            success = execute_scheduled_task_clean(task_data, round_minute_time)
            
            # Track execution
            active_routers.add(task_data['router_id'])
            completed_count += 1
            
            if success:
                logger.info(f"Task {task_data['id']} completed successfully")
            else:
                logger.error(f"Task {task_data['id']} failed")
                
        logger.info(f"Dispatcher completed: {completed_count} tasks executed")
        
    except Exception as e:
        logger.error(f"Dispatcher tick failed: {e}", exc_info=True)


def execute_scheduled_task_clean(task_data: dict, execution_time: datetime) -> bool:
    """
    Execute a single scheduled task with clean session management.
    
    Clean Architecture:
    - Open dedicated session for this task
    - Execute task from start to finish in same session
    - Update task status in same session
    - Commit on success / Rollback on error
    - Close session
    
    Args:
        task_data: Dictionary containing task information (detached from any session)
        execution_time: When the task was executed
        
    Returns:
        bool: True if task executed successfully, False otherwise
    """
    task_id = task_data['id']
    logger.info(f"Executing scheduled task {task_id}: {task_data['service']}.{task_data['task']}")
    
    # ============ OPEN DEDICATED SESSION FOR THIS TASK ============
    from database.connection import db
    task_session = db.get_session()
    
    try:
        # ============ STEP 1: GET TASK FROM REGISTRY ============
        registry_entry = get_task(task_data['service'], task_data['task'])
        if not registry_entry:
            error_msg = f"Task {task_data['service']}.{task_data['task']} not found in registry"
            logger.error(error_msg)
            _update_task_status_in_session(task_session, task_id, execution_time, "ERROR", error_msg)
            task_session.commit()
            return False
        
        # ============ STEP 2: ENSURE ACTIVE COMMANDS SERVER SESSION ============
        last_session_id = None
        if task_data['run_metadata'] and isinstance(task_data['run_metadata'], dict):
            last_session_id = task_data['run_metadata'].get('last_known_session_id')
            
        session_id, session_error = ensure_active_session(task_data['user_id'], task_data['router_id'], last_session_id)
        if session_error:
            error_msg = f"Failed to ensure active session: {session_error}"
            logger.error(error_msg)
            _update_task_status_in_session(task_session, task_id, execution_time, "ERROR", error_msg)
            task_session.commit()
            return False
        
        # ============ STEP 3: RESOLVE PARAMETERS ============
        # Set the task session in context so resolve_params uses it
        SessionContext.set(task_session)
        
        try:
            resolved_params = resolve_params(task_data['service'], task_data['task'], task_data['user_id'], task_data['router_id'], task_data['params'])
        except Exception as e:
            error_msg = f"Parameter resolution failed: {e}"
            logger.error(error_msg)
            _update_task_status_in_session(task_session, task_id, execution_time, "ERROR", error_msg)
            task_session.commit()
            return False
        
        # ============ STEP 4: EXECUTE TASK ============
        try:
            # Call the registered service function
            service_func = registry_entry['call']
            result, error = service_func(task_data['user_id'], task_data['router_id'], session_id, **resolved_params)
            
            if error:
                logger.error(f"Task {task_id} failed: {error}")
                _update_task_status_in_session(task_session, task_id, execution_time, "ERROR", error, session_id)
                task_session.rollback()
                return False
            else:
                logger.info(f"Task {task_id} completed successfully")
                _update_task_status_in_session(task_session, task_id, execution_time, "SUCCESS", None, session_id)
                task_session.commit()
                return True
                
        except Exception as e:
            error_msg = f"Task execution failed: {e}"
            logger.error(f"Task {task_id} execution failed: {e}", exc_info=True)
            _update_task_status_in_session(task_session, task_id, execution_time, "ERROR", error_msg, session_id)
            task_session.rollback()
            return False
        
    except Exception as e:
        logger.error(f"Task {task_id} session management failed: {e}", exc_info=True)
        try:
            task_session.rollback()
        except Exception:
            pass
        return False
        
    finally:
        # ============ CLEANUP: CLOSE SESSION ============
        try:
            task_session.close()
            logger.debug(f"Closed task {task_id} session")
        except Exception as e:
            logger.error(f"Failed to close task {task_id} session: {e}")
        
        # Clear session context
        SessionContext.clear()


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

        logger.info(f"Scheduler started successfully with timezone {tz_name}")
        return scheduler

    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)
        return None
