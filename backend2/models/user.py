from sqlalchemy import Column, String, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from models.base import BaseModel

class User(BaseModel):
    __tablename__ = 'users'
    
    google_id = Column(String(255), unique=True, index=True)  # From existing Google OAuth
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    avatar_url = Column(String(500))
    last_login = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    routers = relationship("UserRouter", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")
    whitelists = relationship("UserWhitelist", back_populates="user", cascade="all, delete-orphan")
    blacklists = relationship("UserBlacklist", back_populates="user", cascade="all, delete-orphan")
    blacklisted_devices = relationship("BlacklistedDevice", back_populates="user", cascade="all, delete-orphan")
    blocked_devices = relationship("UserBlockedDevice", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan") 