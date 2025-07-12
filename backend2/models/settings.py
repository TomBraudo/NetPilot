from sqlalchemy import Column, String, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from models.base import BaseModel

class UserSetting(BaseModel):
    __tablename__ = 'user_settings'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    router_id = Column(String(255), ForeignKey('user_routers.router_id'))
    setting_key = Column(String(100), nullable=False)
    setting_value = Column(JSONB)  # PostgreSQL JSONB for flexible settings
    
    # Relationships
    user = relationship("User", back_populates="settings")
    router = relationship("UserRouter", back_populates="settings") 