from decouple import config
from flask_apscheduler import APScheduler
from utils.logging_config import get_logger
from .task_registry import load_registry


logger = get_logger('scheduler.bootstrap')


def dispatcher_tick():
    """Placeholder dispatcher tick. Phase 7 will implement the real logic."""
    logger.debug("Scheduler dispatcher tick (placeholder)")


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


