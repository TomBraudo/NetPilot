from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from models.base import BaseModel

class UserRouter(BaseModel):
    __tablename__ = 'user_routers'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    router_id = Column(String(255), nullable=False)
    router_name = Column(String(255))
    router_ip = Column(INET)
    tunnel_port = Column(Integer)
    cloud_vm_ip = Column(INET)
    last_seen = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="routers")
    # Note: Removed foreign key relationships to allow multiple users per router_id 