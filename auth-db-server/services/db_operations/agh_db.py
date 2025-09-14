from typing import Any, Dict, List, Optional, Tuple
from utils.logging_config import get_logger
from services.db_operations.base import handle_db_errors
from managers.db_session_context import SessionContext


logger = get_logger('services.db_operations.agh_db')


# Content Control Rules DB Operations
@handle_db_errors("AGH DB: get all rules")
def get_all_content_control_rules(user_id: str, router_id: str) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    from models import ContentControlRules
    session = SessionContext.get()
    rules = session.query(ContentControlRules).filter(
        ContentControlRules.router_id == router_id
    ).all()
    rules_data = [rule.to_dict() for rule in rules]
    return rules_data, None


@handle_db_errors("AGH DB: get group rule")
def get_group_content_control_rule(user_id: str, router_id: str, group_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    from models import ContentControlRules
    session = SessionContext.get()
    rule = session.query(ContentControlRules).filter(
        ContentControlRules.router_id == router_id,
        ContentControlRules.group_id == group_id
    ).first()
    return (rule.to_dict() if rule else None), None


@handle_db_errors("AGH DB: upsert group rule")
def upsert_group_content_control_rule(
    user_id: str,
    router_id: str,
    group_id: str,
    blocked_categories: List[str],
    description: Optional[str],
    is_active: bool = True,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    from models import ContentControlRules, DeviceGroup
    session = SessionContext.get()
    # Verify group exists and belongs to user/router
    group = session.query(DeviceGroup).filter(
        DeviceGroup.id == group_id,
        DeviceGroup.router_id == router_id,
        DeviceGroup.user_id == user_id,
    ).first()
    if not group:
        return None, "Group not found or access denied"

    existing_rule = session.query(ContentControlRules).filter(
        ContentControlRules.router_id == router_id,
        ContentControlRules.group_id == group_id
    ).first()

    if existing_rule:
        existing_rule.blocked_categories = blocked_categories or []
        existing_rule.description = description
        existing_rule.is_active = is_active
        return existing_rule.to_dict(), None
    else:
        new_rule = ContentControlRules(
            group_id=group_id,
            router_id=router_id,
            blocked_categories=blocked_categories or [],
            description=description,
            is_active=is_active,
        )
        session.add(new_rule)
        session.flush()
        return new_rule.to_dict(), None


@handle_db_errors("AGH DB: delete group rule")
def delete_group_content_control_rule(user_id: str, router_id: str, group_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    from models import ContentControlRules
    session = SessionContext.get()
    rule = session.query(ContentControlRules).filter(
        ContentControlRules.router_id == router_id,
        ContentControlRules.group_id == group_id
    ).first()
    if rule:
        session.delete(rule)
        return {"message": "Content control rules deleted successfully"}, None
    else:
        return {"message": "No rules found to delete"}, None



