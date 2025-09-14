from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import BaseModel

class UserSession(BaseModel):
    __tablename__ = 'user_sessions'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(TIMESTAMP, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions") 