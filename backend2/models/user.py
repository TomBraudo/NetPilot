from sqlalchemy import Column, String, Boolean, TIMESTAMP, ARRAY, Integer, Text, ForeignKey
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
    
    # New 2FA fields
    requires_2fa = Column(Boolean, default=False)
    twofa_enforced_at = Column(TIMESTAMP)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    routers = relationship("UserRouter", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")
    whitelists = relationship("UserWhitelist", back_populates="user", cascade="all, delete-orphan")
    blacklists = relationship("UserBlacklist", back_populates="user", cascade="all, delete-orphan")
    blacklisted_devices = relationship("BlacklistedDevice", back_populates="user", cascade="all, delete-orphan")
    blocked_devices = relationship("UserBlockedDevice", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan")
    twofa_settings = relationship("User2FASettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    twofa_attempts = relationship("User2FAAttempt", back_populates="user", cascade="all, delete-orphan")


class User2FASettings(BaseModel):
    __tablename__ = 'user_2fa_settings'
    
    user_id = Column(String(255), ForeignKey('users.id'), unique=True, nullable=False, index=True)
    is_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(255))  # Will be encrypted
    backup_codes = Column(ARRAY(String))
    sms_phone = Column(String(20))
    email_2fa_enabled = Column(Boolean, default=False)
    last_used_at = Column(TIMESTAMP)
    
    # Security fields
    setup_token = Column(String(255))
    setup_expires_at = Column(TIMESTAMP)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(TIMESTAMP)
    
    # Relationships
    user = relationship("User", back_populates="twofa_settings")


class User2FAAttempt(BaseModel):
    __tablename__ = 'user_2fa_attempts'
    
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False, index=True)
    attempt_type = Column(String(20), nullable=False)
    success = Column(Boolean, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="twofa_attempts") 