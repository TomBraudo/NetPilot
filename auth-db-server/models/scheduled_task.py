from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from models.base import BaseModel


class ScheduledTask(BaseModel):
    __tablename__ = 'scheduled_tasks'

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    router_id = Column(String(255), nullable=False, index=True)

    # Routing to the correct function
    service = Column(String(64), nullable=False)  # e.g., 'bandwidth', 'agh'
    task = Column(String(128), nullable=False)    # e.g., 'apply_group_limits'

    # Task parameters (immutable post-creation); dynamic group resolution happens at runtime
    params = Column(JSONB, nullable=False)

    # Scheduling fields (Asia/Jerusalem local time semantics)
    hour = Column(Integer, nullable=True)  # Changed to nullable for interval tasks
    minute = Column(Integer, nullable=True)  # Changed to nullable for interval tasks
    days_of_week = Column(ARRAY(Integer), nullable=True)  # 0-6 for Mon-Sun (or Sun-Sat per app policy)

    # Interval-based scheduling support
    task_type = Column(String(16), nullable=False, default='fixed')  # 'fixed' or 'interval'
    interval_minutes = Column(Integer, nullable=True)  # e.g., 60 for "every hour"

    enabled = Column(Boolean, nullable=False, default=True)

    # Operational metadata and execution results
    run_metadata = Column(JSONB, nullable=True)  # e.g., { last_known_session_id }
    last_run_at = Column(TIMESTAMP, nullable=True)
    last_status = Column(String(32), nullable=True)
    last_error = Column(Text, nullable=True)

    __table_args__ = (
        Index('ix_scheduled_tasks_enabled_time', 'enabled', 'hour', 'minute'),
        Index('ix_scheduled_tasks_user_router', 'user_id', 'router_id'),
    )


