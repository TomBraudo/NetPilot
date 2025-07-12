from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import BaseModel

class BlacklistedDevice(BaseModel):
    __tablename__ = 'blacklisted_devices'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    mac_address = Column(String(17), nullable=False)  # MAC address format: XX:XX:XX:XX:XX:XX
    device_name = Column(String(255))
    reason = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="blacklisted_devices") 