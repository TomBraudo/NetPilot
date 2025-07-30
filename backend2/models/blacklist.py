from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET, MACADDR
from sqlalchemy.orm import relationship
from models.base import BaseModel

class UserBlacklist(BaseModel):
    __tablename__ = 'user_blacklists'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    router_id = Column(String(255), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey('user_devices.id'))
    device_ip = Column(INET, nullable=False)
    device_mac = Column(MACADDR)
    device_name = Column(String(255))
    reason = Column(Text)
    blocked_at = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="blacklists")
    device = relationship("UserDevice") 