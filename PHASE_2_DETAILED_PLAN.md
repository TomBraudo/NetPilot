# Phase 2: Database Design & Setup - Detailed Implementation Plan
## PostgreSQL Migration with Multi-User Support

### Overview
This plan details the migration from TinyDB to PostgreSQL on your existing Google Cloud VM (34.38.207.87), with preparation for Google authentication and multi-user data isolation.

### Current State Analysis
Based on project scan, the current system uses:
- **TinyDB** with JSON storage for: devices, whitelists, blacklists, settings
- **Single-user architecture** - no user separation
- **Local file storage** in `/data/` directory

### Target Architecture
- **PostgreSQL** database on VM 34.38.207.87
- **Multi-user data isolation** with user-scoped tables
- **SQLAlchemy ORM** with Alembic migrations
- **Google OAuth preparation** (user ID structure compatible)
- **Dockerized deployment** with persistent volumes

---

## 2.1: PostgreSQL Setup on VM (34.38.207.87)

### 2.1.1: VM PostgreSQL Installation
```bash
# Connect to your VM
ssh -i your-key.pem user@34.38.207.87

# Update system
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL 15
sudo apt install postgresql-15 postgresql-client-15 postgresql-contrib-15 -y

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
sudo systemctl status postgresql
```

### 2.1.2: Database & User Setup
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user for NetPilot
CREATE DATABASE netpilot_db;
CREATE USER netpilot_user WITH ENCRYPTED PASSWORD 'your_secure_password_here';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE netpilot_db TO netpilot_user;
GRANT CREATE ON SCHEMA public TO netpilot_user;

# Enable UUID extension for user IDs (Google OAuth compatibility)
\c netpilot_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# Exit psql
\q
```

### 2.1.3: PostgreSQL Configuration
```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/15/main/postgresql.conf

# Add/modify these settings:
listen_addresses = 'localhost,34.38.207.87'  # Allow local and VM IP
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# Edit pg_hba.conf for authentication
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Add line for NetPilot user (before default entries):
host    netpilot_db     netpilot_user   127.0.0.1/32    md5
host    netpilot_db     netpilot_user   34.38.207.87/32 md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 2.1.4: Firewall & Security
```bash
# Open PostgreSQL port (internal only - for backend connection)
sudo ufw allow from 127.0.0.1 to any port 5432
sudo ufw allow from 34.38.207.87 to any port 5432

# Test connection
psql -h 127.0.0.1 -U netpilot_user -d netpilot_db -c "SELECT version();"
```

---

## 2.2: Database Schema Design

### 2.2.1: Multi-User Schema Architecture
```sql
-- Users table (prepared for Google OAuth)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    google_id VARCHAR(255) UNIQUE,          -- For future Google OAuth
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),                -- For Google profile picture
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    
    -- Indexes for performance
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Router associations per user
CREATE TABLE user_routers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) NOT NULL,        -- From agent tunnel system
    router_name VARCHAR(255),
    router_ip INET,                         -- PostgreSQL INET type for IP addresses
    tunnel_port INTEGER,
    cloud_vm_ip INET DEFAULT '34.38.207.87'::INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    
    UNIQUE(user_id, router_id)
);

-- User-specific devices (migrated from current devices.json)
CREATE TABLE user_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) REFERENCES user_routers(router_id) ON DELETE CASCADE,
    ip INET NOT NULL,
    mac MACADDR,                            -- PostgreSQL native MAC address type
    hostname VARCHAR(255),
    device_name VARCHAR(255),               -- User-customizable name
    device_type VARCHAR(100),               -- mobile, laptop, tv, router, etc.
    manufacturer VARCHAR(255),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, router_id, ip),
    UNIQUE(user_id, router_id, mac)
);

-- User-specific whitelists (migrated from current whitelist.json)
CREATE TABLE user_whitelists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) REFERENCES user_routers(router_id) ON DELETE CASCADE,
    device_id UUID REFERENCES user_devices(id) ON DELETE CASCADE,
    device_ip INET NOT NULL,
    device_mac MACADDR,
    device_name VARCHAR(255),
    description TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, router_id, device_ip)
);

-- User-specific blacklists (migrated from current blacklist.json)
CREATE TABLE user_blacklists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) REFERENCES user_routers(router_id) ON DELETE CASCADE,
    device_id UUID REFERENCES user_devices(id) ON DELETE CASCADE,
    device_ip INET NOT NULL,
    device_mac MACADDR,
    device_name VARCHAR(255),
    reason TEXT,
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    
    UNIQUE(user_id, router_id, device_ip)
);

-- User-specific blocked devices (active blocks from API calls)
CREATE TABLE user_blocked_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) REFERENCES user_routers(router_id) ON DELETE CASCADE,
    device_id UUID REFERENCES user_devices(id) ON DELETE CASCADE,
    device_ip INET NOT NULL,
    device_mac MACADDR,
    block_type VARCHAR(50) DEFAULT 'manual',     -- manual, whitelist, blacklist
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unblocked_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    
    UNIQUE(user_id, router_id, device_ip)
);

-- User settings and preferences
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) REFERENCES user_routers(router_id),
    setting_key VARCHAR(100) NOT NULL,
    setting_value JSONB,                    -- PostgreSQL JSONB for flexible settings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, router_id, setting_key)
);
```

### 2.2.2: Indexes for Performance
```sql
-- Performance indexes
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_routers_user_id ON user_routers(user_id);
CREATE INDEX idx_user_routers_router_id ON user_routers(router_id);
CREATE INDEX idx_user_devices_user_router ON user_devices(user_id, router_id);
CREATE INDEX idx_user_devices_ip ON user_devices(ip);
CREATE INDEX idx_user_devices_mac ON user_devices(mac);
CREATE INDEX idx_user_whitelists_user_router ON user_whitelists(user_id, router_id);
CREATE INDEX idx_user_blacklists_user_router ON user_blacklists(user_id, router_id);
CREATE INDEX idx_user_blocked_devices_active ON user_blocked_devices(user_id, router_id, is_active);
CREATE INDEX idx_user_settings_user_router ON user_settings(user_id, router_id);
```

---

## 2.3: SQLAlchemy Models Implementation

### 2.3.1: Project Structure Setup
```
backend/
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   ├── router.py
│   ├── device.py
│   ├── whitelist.py
│   ├── blacklist.py
│   ├── blocked_device.py
│   └── settings.py
├── database/
│   ├── __init__.py
│   ├── connection.py
│   └── session.py
└── migrations/  (Alembic)
```

### 2.3.2: Base Model (`models/base.py`)
```python
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
```

### 2.3.3: User Model (`models/user.py`)
```python
from sqlalchemy import Column, String, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from models.base import BaseModel

class User(BaseModel):
    __tablename__ = 'users'
    
    google_id = Column(String(255), unique=True, index=True)  # For future Google OAuth
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    avatar_url = Column(String(500))
    last_login = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    routers = relationship("UserRouter", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")
    whitelists = relationship("UserWhitelist", back_populates="user", cascade="all, delete-orphan")
    blacklists = relationship("UserBlacklist", back_populates="user", cascade="all, delete-orphan")
    blocked_devices = relationship("UserBlockedDevice", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan")
```

### 2.3.4: Device Model (`models/device.py`)
```python
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET, MACADDR
from sqlalchemy.orm import relationship
from models.base import BaseModel

class UserDevice(BaseModel):
    __tablename__ = 'user_devices'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    router_id = Column(String(255), ForeignKey('user_routers.router_id'), nullable=False)
    ip = Column(INET, nullable=False)
    mac = Column(MACADDR)
    hostname = Column(String(255))
    device_name = Column(String(255))  # User-customizable name
    device_type = Column(String(100))
    manufacturer = Column(String(255))
    first_seen = Column(TIMESTAMP, default=func.current_timestamp())
    last_seen = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="devices")
    router = relationship("UserRouter", back_populates="devices")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'router_id', 'ip', name='unique_user_router_ip'),
        UniqueConstraint('user_id', 'router_id', 'mac', name='unique_user_router_mac'),
    )
```

---

## 2.4: Database Connection & Configuration

### 2.4.1: Environment Configuration
```python
# database/connection.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from models.base import Base

class DatabaseConfig:
    def __init__(self):
        self.database_url = self._construct_database_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def _construct_database_url(self):
        """Construct PostgreSQL URL from environment variables"""
        host = os.getenv('DB_HOST', '127.0.0.1')
        port = os.getenv('DB_PORT', '5432')
        username = os.getenv('DB_USERNAME', 'netpilot_user')
        password = os.getenv('DB_PASSWORD')
        database = os.getenv('DB_NAME', 'netpilot_db')
        
        if not password:
            raise ValueError("DB_PASSWORD environment variable must be set")
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def _create_engine(self):
        """Create SQLAlchemy engine with PostgreSQL optimizations"""
        return create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before use
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true'  # SQL logging
        )
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()

# Create global database instance
db = DatabaseConfig()
```

### 2.4.2: Session Management
```python
# database/session.py
from contextlib import contextmanager
from database.connection import db

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = db.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_db():
    """Dependency for FastAPI/Flask"""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()
```

---

## 2.5: Alembic Migration Setup

### 2.5.1: Alembic Installation & Configuration
```bash
# Install Alembic
pip install alembic

# Initialize Alembic in backend directory
cd backend
alembic init migrations

# Edit alembic.ini
# sqlalchemy.url = postgresql://netpilot_user:password@127.0.0.1:5432/netpilot_db
```

### 2.5.2: Migration Environment Setup
```python
# migrations/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add parent directory to path for model imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.base import Base
from models import user, router, device, whitelist, blacklist, blocked_device, settings

# Alembic Config object
config = context.config

# Set database URL from environment
config.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL'))

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 2.5.3: Initial Migration Creation
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema with multi-user support"

# Review the generated migration file
# migrations/versions/001_initial_schema.py

# Apply migration
alembic upgrade head
```

---

## 2.6: Data Migration from TinyDB

### 2.6.1: Migration Script Structure
```python
# scripts/migrate_data.py
import json
import os
from datetime import datetime
from database.connection import db
from database.session import get_db_session
from models.user import User
from models.device import UserDevice
from models.whitelist import UserWhitelist
from models.blacklist import UserBlacklist

class TinyDBMigrator:
    def __init__(self):
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    def create_default_user(self, session):
        """Create a default user for migration"""
        default_user = User(
            email='default@netpilot.local',
            full_name='Default User',
            is_active=True
        )
        session.add(default_user)
        session.flush()  # Get ID
        return default_user
    
    def migrate_devices(self, session, user_id, router_id):
        """Migrate devices from devices.json"""
        devices_file = os.path.join(self.data_path, 'devices.json')
        if not os.path.exists(devices_file):
            return
        
        with open(devices_file, 'r') as f:
            devices_data = json.load(f)
        
        for device_data in devices_data:
            device = UserDevice(
                user_id=user_id,
                router_id=router_id,
                ip=device_data.get('ip'),
                mac=device_data.get('mac'),
                hostname=device_data.get('hostname', 'Unknown'),
                device_name=device_data.get('device_name'),
                device_type=device_data.get('device_type'),
                manufacturer=device_data.get('manufacturer'),
                first_seen=self._parse_timestamp(device_data.get('first_seen')),
                last_seen=self._parse_timestamp(device_data.get('last_seen'))
            )
            session.add(device)
    
    def migrate_whitelist(self, session, user_id, router_id):
        """Migrate whitelist from whitelist.json"""
        whitelist_file = os.path.join(self.data_path, 'whitelist.json')
        if not os.path.exists(whitelist_file):
            return
        
        with open(whitelist_file, 'r') as f:
            whitelist_data = json.load(f)
        
        for item in whitelist_data:
            whitelist_entry = UserWhitelist(
                user_id=user_id,
                router_id=router_id,
                device_ip=item.get('ip'),
                device_mac=item.get('mac'),
                device_name=item.get('name'),
                description=item.get('description', ''),
                added_at=self._parse_timestamp(item.get('added_at'))
            )
            session.add(whitelist_entry)
    
    def migrate_blacklist(self, session, user_id, router_id):
        """Migrate blacklist from blacklist.json"""
        blacklist_file = os.path.join(self.data_path, 'blacklist.json')
        if not os.path.exists(blacklist_file):
            return
        
        with open(blacklist_file, 'r') as f:
            blacklist_data = json.load(f)
        
        for item in blacklist_data:
            blacklist_entry = UserBlacklist(
                user_id=user_id,
                router_id=router_id,
                device_ip=item.get('ip'),
                device_mac=item.get('mac'),
                device_name=item.get('name'),
                reason=item.get('reason', ''),
                blocked_at=self._parse_timestamp(item.get('added_at'))
            )
            session.add(blacklist_entry)
    
    def _parse_timestamp(self, timestamp_str):
        """Parse timestamp string to datetime"""
        if not timestamp_str:
            return datetime.now()
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return datetime.now()
    
    def run_migration(self):
        """Run the complete migration"""
        with get_db_session() as session:
            # Create default user
            user = self.create_default_user(session)
            
            # Create default router (you'll need to customize this)
            default_router_id = 'default-router-001'
            
            # Migrate all data
            self.migrate_devices(session, user.id, default_router_id)
            self.migrate_whitelist(session, user.id, default_router_id)
            self.migrate_blacklist(session, user.id, default_router_id)
            
            print(f"Migration completed for user: {user.email}")

if __name__ == "__main__":
    migrator = TinyDBMigrator()
    migrator.run_migration()
```

---

## 2.7: Backend Integration & Updated Dependencies

### 2.7.1: Updated Requirements
```python
# Add to requirements.txt
sqlalchemy==2.0.23
alembic==1.13.1
psycopg2-binary==2.9.9
python-decouple==3.8  # For environment variables
```

### 2.7.2: Updated Flask App Configuration
```python
# server.py modifications
from flask import Flask
from flask_cors import CORS
from database.connection import db
from database.session import get_db_session
import os
from decouple import config

# Environment configuration
DATABASE_URL = config('DATABASE_URL')
os.environ['DATABASE_URL'] = DATABASE_URL

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize database
@app.before_first_request
def initialize_database():
    """Initialize database tables on first request"""
    db.create_tables()
    logger.info("Database tables initialized")

# Add session context to all requests
@app.before_request
def before_request():
    g.db_session = db.get_session()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db_session'):
        if exception:
            g.db_session.rollback()
        g.db_session.close()
```

---

## 2.8: Testing & Validation

### 2.8.1: Database Connection Test
```python
# tests/test_database.py
import pytest
from database.connection import db
from database.session import get_db_session
from models.user import User

def test_database_connection():
    """Test database connection"""
    with get_db_session() as session:
        result = session.execute("SELECT 1")
        assert result.scalar() == 1

def test_user_creation():
    """Test user model creation"""
    with get_db_session() as session:
        user = User(
            email='test@example.com',
            full_name='Test User'
        )
        session.add(user)
        session.commit()
        
        # Verify user was created
        found_user = session.query(User).filter_by(email='test@example.com').first()
        assert found_user is not None
        assert found_user.full_name == 'Test User'
```

### 2.8.2: Migration Validation
```bash
# Test migration rollback
alembic downgrade -1
alembic upgrade +1

# Verify schema
psql -h 127.0.0.1 -U netpilot_user -d netpilot_db -c "\dt"
```

---

## 2.9: Environment Configuration Files

### 2.9.1: Environment Variables (`.env`)
```bash
# Database Configuration
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USERNAME=netpilot_user
DB_PASSWORD=your_secure_password_here
DB_NAME=netpilot_db
DATABASE_URL=postgresql://netpilot_user:your_secure_password_here@127.0.0.1:5432/netpilot_db

# Application Configuration
FLASK_ENV=development
SECRET_KEY=your_secret_key_here

# Logging
DB_ECHO=false
LOG_LEVEL=INFO

# Future Google OAuth (Phase 3)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
```

---

## 2.10: Deployment & Monitoring

### 2.10.1: PostgreSQL Backup Strategy
```bash
#!/bin/bash
# scripts/backup_db.sh
BACKUP_DIR="/opt/netpilot/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/netpilot_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h 127.0.0.1 -U netpilot_user netpilot_db > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

### 2.10.2: Monitoring Script
```python
# scripts/monitor_db.py
import psycopg2
from datetime import datetime
import logging

def check_database_health():
    """Monitor database health"""
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="netpilot_db",
            user="netpilot_user",
            password=os.getenv('DB_PASSWORD')
        )
        
        cursor = conn.cursor()
        
        # Check connection count
        cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE datname='netpilot_db';")
        connections = cursor.fetchone()[0]
        
        # Check database size
        cursor.execute("SELECT pg_size_pretty(pg_database_size('netpilot_db'));")
        db_size = cursor.fetchone()[0]
        
        print(f"Database health check - Connections: {connections}, Size: {db_size}")
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False

if __name__ == "__main__":
    check_database_health()
```

---

## Implementation Timeline

### Week 1: Infrastructure Setup
- [ ] PostgreSQL installation on VM
- [ ] Database and user setup
- [ ] Basic connection testing

### Week 2: Schema & Models
- [ ] SQLAlchemy models implementation
- [ ] Alembic migration setup
- [ ] Initial schema creation

### Week 3: Data Migration
- [ ] TinyDB to PostgreSQL migration script
- [ ] Data validation and testing
- [ ] Backup procedures

### Week 4: Backend Integration
- [ ] Flask app PostgreSQL integration
- [ ] Updated repository layers
- [ ] API endpoint testing

### Success Criteria
- [ ] PostgreSQL running reliably on VM
- [ ] All current data migrated successfully
- [ ] Backend APIs working with PostgreSQL
- [ ] Multi-user data isolation verified
- [ ] Ready for Google OAuth integration (Phase 3)

This plan sets up a robust, scalable PostgreSQL foundation that's ready for your Phase 3 authentication implementation. 