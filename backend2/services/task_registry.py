from typing import Callable, Dict, Optional, Tuple
import importlib
import os
from utils.logging_config import get_logger


logger = get_logger('scheduler.registry')

# Registry keyed by (service, task)
_REGISTRY: Dict[Tuple[str, str], Dict[str, object]] = {}


def _parse_name(name: str) -> Tuple[str, str]:
    """Parse a unique name in the form 'service.task' into tuple."""
    if not isinstance(name, str) or '.' not in name:
        raise ValueError("Task name must be a string in the form 'service.task'")
    service, task = name.split('.', 1)
    service = service.strip()
    task = task.strip()
    if not service or not task:
        raise ValueError("Invalid task name; empty service or task")
    return service, task


def register_task(name: str, resolver: Optional[Callable] = None) -> Callable:
    """
    Decorator: register a function under the unique name 'service.task'.
    Optionally attach a resolver: (user_id, router_id, params) -> params'.
    """

    service, task = _parse_name(name)

    def _decorator(func: Callable) -> Callable:
        key = (service, task)
        if key in _REGISTRY:
            raise ValueError(f"Duplicate task registration for {service}.{task}")
        _REGISTRY[key] = {
            'call': func,
            'resolver': resolver,
        }
        logger.info(f"Registered task {service}.{task} -> {func.__module__}.{func.__name__}")
        return func

    return _decorator


def get_task(service: str, task: str) -> Optional[Dict[str, object]]:
    return _REGISTRY.get((service, task))


def resolve_params(service: str, task: str, user_id: str, router_id: str, params: dict) -> dict:
    entry = get_task(service, task)
    if not entry:
        raise KeyError(f"Task not found: {service}.{task}")
    resolver = entry.get('resolver')  # type: ignore
    if callable(resolver):
        try:
            return resolver(user_id, router_id, params)
        except Exception as e:
            logger.error(f"Resolver failed for {service}.{task}: {e}")
            raise
    return params


def load_registry() -> None:
    """
    Import modules so their @register_task decorators run.
    Modules can be provided via env SCHEDULER_TASK_MODULES as a comma-separated list.
    Defaults to a small set of known service modules; import errors are logged and ignored.
    """
    modules_env = os.getenv('SCHEDULER_TASK_MODULES', '')
    modules = [m.strip() for m in modules_env.split(',') if m.strip()] or [
        'services.bandwidth_service',
        'services.agh_service',
    ]

    for mod in modules:
        try:
            importlib.import_module(mod)
            logger.info(f"Loaded task module: {mod}")
        except Exception as e:
            logger.warning(f"Failed to load task module {mod}: {e}")


def list_tasks() -> Dict[Tuple[str, str], Dict[str, object]]:
    return dict(_REGISTRY)


