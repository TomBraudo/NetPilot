from sqlalchemy import Column, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import BaseModel

class BandwidthRules(BaseModel):
    __tablename__ = 'bandwidth_rules'
    
    group_id = Column(UUID(as_uuid=True), ForeignKey('device_groups.id', ondelete='CASCADE'), nullable=False)
    router_id = Column(String(255), nullable=False)
    
    # Bandwidth limits in Mbps
    download_limit_mbps = Column(Float, nullable=True)  # NULL means no limit
    upload_limit_mbps = Column(Float, nullable=True)    # NULL means no limit
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Optional description
    description = Column(Text, nullable=True)
    
    # Relationships
    group = relationship("DeviceGroup", back_populates="bandwidth_rules")
    
    def to_dict(self):
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict['group_id'] = str(self.group_id)
        return base_dict
