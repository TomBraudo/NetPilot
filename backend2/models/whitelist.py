from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET, MACADDR
from sqlalchemy.orm import relationship
from models.base import BaseModel

class UserWhitelist(BaseModel):
    __tablename__ = 'user_whitelists'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    router_id = Column(String(255), ForeignKey('user_routers.router_id'), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey('user_devices.id'))
    device_ip = Column(INET, nullable=False)
    device_mac = Column(MACADDR)
    device_name = Column(String(255))
    description = Column(Text)
    added_at = Column(TIMESTAMP)
    
    # Relationships
    user = relationship("User", back_populates="whitelists")
    router = relationship("UserRouter", back_populates="whitelists")
    device = relationship("UserDevice") 