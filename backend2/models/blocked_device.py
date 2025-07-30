from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET, MACADDR
from sqlalchemy.orm import relationship
from models.base import BaseModel

class UserBlockedDevice(BaseModel):
    __tablename__ = 'user_blocked_devices'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    router_id = Column(String(255), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey('user_devices.id'))
    device_ip = Column(INET, nullable=False)
    device_mac = Column(MACADDR)
    block_type = Column(String(50), default='manual')  # manual, whitelist, blacklist
    blocked_at = Column(TIMESTAMP)
    unblocked_at = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="blocked_devices")
    device = relationship("UserDevice") 