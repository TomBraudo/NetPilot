from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, INET, MACADDR
from sqlalchemy.orm import relationship
from models.base import BaseModel

class UserDevice(BaseModel):
    __tablename__ = 'user_devices'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    router_id = Column(String(255), nullable=False)
    ip = Column(INET, nullable=False)
    mac = Column(MACADDR)
    hostname = Column(String(255))
    device_name = Column(String(255))  # User-customizable name
    device_type = Column(String(100))
    manufacturer = Column(String(255))
    first_seen = Column(TIMESTAMP)
    last_seen = Column(TIMESTAMP)
    
    # Relationships
    user = relationship("User", back_populates="devices")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'router_id', 'ip', name='unique_user_router_ip'),
        UniqueConstraint('user_id', 'router_id', 'mac', name='unique_user_router_mac'),
    ) 