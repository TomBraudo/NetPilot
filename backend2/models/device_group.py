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
        return base_dict
