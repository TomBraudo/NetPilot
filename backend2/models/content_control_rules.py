from sqlalchemy import Column, String, Boolean, Text, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import BaseModel

class ContentControlRules(BaseModel):
    __tablename__ = 'content_control_rules'
    
    group_id = Column(UUID(as_uuid=True), ForeignKey('device_groups.id', ondelete='CASCADE'), nullable=False)
    router_id = Column(String(255), nullable=False)
    
    # Content categories to block
    blocked_categories = Column(ARRAY(String), default=[])  # Array of category IDs
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Optional description
    description = Column(Text, nullable=True)
    
    # Relationships
    group = relationship("DeviceGroup", back_populates="content_control_rules")
    
    def to_dict(self):
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict['group_id'] = str(self.group_id)
        return base_dict
