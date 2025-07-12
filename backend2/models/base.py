from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, UUID, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns} 