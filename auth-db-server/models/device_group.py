from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, Table, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from models.base import BaseModel

# Association table for many-to-many relationship between groups and devices
device_group_devices = Table(
    'device_group_devices',
    BaseModel.metadata,
    Column('group_id', UUID(as_uuid=True), ForeignKey('device_groups.id'), primary_key=True),
    Column('device_id', UUID(as_uuid=True), ForeignKey('user_devices.id'), primary_key=True)
)

class DeviceGroup(BaseModel):
    __tablename__ = 'device_groups'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    router_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="device_groups")
    devices = relationship("UserDevice", secondary=device_group_devices, back_populates="device_groups")
    bandwidth_rules = relationship("BandwidthRules", back_populates="group", cascade="all, delete-orphan")
    content_control_rules = relationship("ContentControlRules", back_populates="group", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary with device information"""
        base_dict = super().to_dict()
        base_dict['devices'] = [
            {
                'id': str(device.id),
                'ip': str(device.ip),
                'mac': str(device.mac) if device.mac else None,
                'hostname': device.hostname,
                'device_name': device.device_name,
                'device_type': device.device_type,
                'manufacturer': device.manufacturer
            } for device in self.devices
        ]
        
        # Add bandwidth rules info
        if self.bandwidth_rules:
            base_dict['bandwidth_rules'] = [
                {
                    'id': str(rule.id),
                    'download_limit_mbps': rule.download_limit_mbps,
                    'upload_limit_mbps': rule.upload_limit_mbps,
                    'is_active': rule.is_active,
                    'description': rule.description
                } for rule in self.bandwidth_rules if rule.is_active
            ]
        else:
            base_dict['bandwidth_rules'] = []
            
        # Add content control rules info
        if self.content_control_rules:
            base_dict['content_control_rules'] = [
                {
                    'id': str(rule.id),
                    'blocked_categories': rule.blocked_categories,
                    'is_active': rule.is_active,
                    'description': rule.description
                } for rule in self.content_control_rules if rule.is_active
            ]
        else:
            base_dict['content_control_rules'] = []
            
        return base_dict
