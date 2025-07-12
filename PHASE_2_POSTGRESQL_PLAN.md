# Phase 2: PostgreSQL Database Design & Setup - Detailed Plan

## Executive Summary
This plan migrates NetPilot from TinyDB to PostgreSQL on your existing VM (34.38.207.87) with multi-user support and Google OAuth preparation.

## Current Architecture Analysis
**Current System:**
- TinyDB JSON storage for devices, whitelists, blacklists
- Single-user architecture with no data isolation
- Files: `devices.json`, `whitelist.json`, `blacklist.json`, `netpilot.json`

**Target System:**
- PostgreSQL on VM 34.38.207.87
- Multi-user data isolation per user
- Google OAuth-ready user structure
- SQLAlchemy ORM with Alembic migrations

---

## 2.1: PostgreSQL Installation & Setup on VM

### 2.1.1: Install PostgreSQL 15
```bash
# Connect to VM
ssh user@34.38.207.87

# Install PostgreSQL
sudo apt update && sudo apt upgrade -y
sudo apt install postgresql-15 postgresql-client-15 postgresql-contrib-15 -y
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2.1.2: Database Setup
```bash
sudo -u postgres psql

-- Create database and user
CREATE DATABASE netpilot_db;
CREATE USER netpilot_user WITH ENCRYPTED PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE netpilot_db TO netpilot_user;

-- Enable UUID extension for Google OAuth compatibility
\c netpilot_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\q
```

### 2.1.3: PostgreSQL Configuration
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf

# Key settings:
listen_addresses = 'localhost,34.38.207.87'
max_connections = 100
shared_buffers = 256MB

# Edit pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Add authentication rules:
host netpilot_db netpilot_user 127.0.0.1/32 md5
host netpilot_db netpilot_user 34.38.207.87/32 md5

sudo systemctl restart postgresql
```

---

## 2.2: Multi-User Database Schema

### 2.2.1: Core Tables Design

```sql
-- Users table (Google OAuth ready)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    google_id VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Router associations per user
CREATE TABLE user_routers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) NOT NULL,
    router_name VARCHAR(255),
    router_ip INET,
    tunnel_port INTEGER,
    cloud_vm_ip INET DEFAULT '34.38.207.87'::INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(user_id, router_id)
);

-- User devices (replaces devices.json)
CREATE TABLE user_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) REFERENCES user_routers(router_id) ON DELETE CASCADE,
    ip INET NOT NULL,
    mac MACADDR,
    hostname VARCHAR(255),
    device_name VARCHAR(255),
    device_type VARCHAR(100),
    manufacturer VARCHAR(255),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, router_id, ip)
);

-- User whitelists (replaces whitelist.json)
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

-- User blacklists (replaces blacklist.json)
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

-- User blocked devices (active blocks)
CREATE TABLE user_blocked_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) REFERENCES user_routers(router_id) ON DELETE CASCADE,
    device_id UUID REFERENCES user_devices(id) ON DELETE CASCADE,
    device_ip INET NOT NULL,
    device_mac MACADDR,
    block_type VARCHAR(50) DEFAULT 'manual',
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unblocked_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(user_id, router_id, device_ip)
);

-- User settings (replaces config files)
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) REFERENCES user_routers(router_id),
    setting_key VARCHAR(100) NOT NULL,
    setting_value JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, router_id, setting_key)
);
```

### 2.2.2: Performance Indexes
```sql
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_routers_user_id ON user_routers(user_id);
CREATE INDEX idx_user_devices_user_router ON user_devices(user_id, router_id);
CREATE INDEX idx_user_devices_ip ON user_devices(ip);
CREATE INDEX idx_user_devices_mac ON user_devices(mac);
CREATE INDEX idx_user_whitelists_user_router ON user_whitelists(user_id, router_id);
CREATE INDEX idx_user_blacklists_user_router ON user_blacklists(user_id, router_id);
CREATE INDEX idx_user_blocked_devices_active ON user_blocked_devices(user_id, router_id, is_active);
```

---

## 2.3: SQLAlchemy Models Implementation

### 2.3.1: Project Structure
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
└── migrations/
    └── (Alembic files)
```

### 2.3.2: Base Model (`models/base.py`)
```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, default=func.current_timestamp(), 
                       onupdate=func.current_timestamp())
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

### 2.3.3: User Model (`models/user.py`)
```python
from sqlalchemy import Column, String, Boolean, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import relationship
from models.base import BaseModel

class User(BaseModel):
    __tablename__ = 'users'
    
    google_id = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    avatar_url = Column(String(500))
    last_login = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    routers = relationship("UserRouter", back_populates="user", 
                          cascade="all, delete-orphan")
    devices = relationship("UserDevice", back_populates="user", 
                          cascade="all, delete-orphan")
    whitelists = relationship("UserWhitelist", back_populates="user", 
                             cascade="all, delete-orphan")
    blacklists = relationship("UserBlacklist", back_populates="user", 
                             cascade="all, delete-orphan")
    blocked_devices = relationship("UserBlockedDevice", back_populates="user", 
                                  cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="user", 
                           cascade="all, delete-orphan")
```

### 2.3.4: Device Model (`models/device.py`)
```python
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, INET, MACADDR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base import BaseModel

class UserDevice(BaseModel):
    __tablename__ = 'user_devices'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    router_id = Column(String(255), ForeignKey('user_routers.router_id'), 
                      nullable=False)
    ip = Column(INET, nullable=False)
    mac = Column(MACADDR)
    hostname = Column(String(255))
    device_name = Column(String(255))
    device_type = Column(String(100))
    manufacturer = Column(String(255))
    first_seen = Column(TIMESTAMP, default=func.current_timestamp())
    last_seen = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="devices")
    router = relationship("UserRouter", back_populates="devices")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'router_id', 'ip', 
                        name='unique_user_router_ip'),
    )
```

---

## 2.4: Database Connection Setup

### 2.4.1: Connection Manager (`database/connection.py`)
```python
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
        host = os.getenv('DB_HOST', '127.0.0.1')
        port = os.getenv('DB_PORT', '5432')
        username = os.getenv('DB_USERNAME', 'netpilot_user')
        password = os.getenv('DB_PASSWORD')
        database = os.getenv('DB_NAME', 'netpilot_db')
        
        if not password:
            raise ValueError("DB_PASSWORD environment variable required")
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def _create_engine(self):
        return create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
        )
    
    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        return self.SessionLocal()

# Global instance
db = DatabaseConfig()
```

### 2.4.2: Session Manager (`database/session.py`)
```python
from contextlib import contextmanager
from database.connection import db

@contextmanager
def get_db_session():
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
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()
```

---

## 2.5: Data Migration from TinyDB

### 2.5.1: Migration Script (`scripts/migrate_data.py`)
```python
import json
import os
from datetime import datetime
from database.connection import db
from database.session import get_db_session
from models.user import User
from models.router import UserRouter
from models.device import UserDevice
from models.whitelist import UserWhitelist
from models.blacklist import UserBlacklist

class TinyDBMigrator:
    def __init__(self):
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    def create_default_user(self, session):
        """Create default user for migration"""
        default_user = User(
            email='default@netpilot.local',
            full_name='Default User',
            is_active=True
        )
        session.add(default_user)
        session.flush()
        return default_user
    
    def create_default_router(self, session, user_id):
        """Create default router entry"""
        router = UserRouter(
            user_id=user_id,
            router_id='default-router-001',
            router_name='Default Router',
            router_ip='192.168.1.1',
            is_active=True
        )
        session.add(router)
        session.flush()
        return router
    
    def migrate_devices(self, session, user_id, router_id):
        """Migrate from devices.json"""
        devices_file = os.path.join(self.data_path, 'devices.json')
        if not os.path.exists(devices_file):
            print("No devices.json found, skipping devices migration")
            return
        
        with open(devices_file, 'r') as f:
            devices_data = json.load(f)
        
        if not isinstance(devices_data, list):
            print("Invalid devices.json format, skipping")
            return
        
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
        
        print(f"Migrated {len(devices_data)} devices")
    
    def migrate_whitelist(self, session, user_id, router_id):
        """Migrate from whitelist.json"""
        whitelist_file = os.path.join(self.data_path, 'whitelist.json')
        if not os.path.exists(whitelist_file):
            print("No whitelist.json found, skipping whitelist migration")
            return
        
        with open(whitelist_file, 'r') as f:
            whitelist_data = json.load(f)
        
        if not isinstance(whitelist_data, list):
            print("Invalid whitelist.json format, skipping")
            return
        
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
        
        print(f"Migrated {len(whitelist_data)} whitelist entries")
    
    def migrate_blacklist(self, session, user_id, router_id):
        """Migrate from blacklist.json"""
        blacklist_file = os.path.join(self.data_path, 'blacklist.json')
        if not os.path.exists(blacklist_file):
            print("No blacklist.json found, skipping blacklist migration")
            return
        
        with open(blacklist_file, 'r') as f:
            blacklist_data = json.load(f)
        
        if not isinstance(blacklist_data, list):
            print("Invalid blacklist.json format, skipping")
            return
        
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
        
        print(f"Migrated {len(blacklist_data)} blacklist entries")
    
    def _parse_timestamp(self, timestamp_str):
        """Parse timestamp string to datetime"""
        if not timestamp_str:
            return datetime.now()
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return datetime.now()
    
    def run_migration(self):
        """Execute complete migration"""
        print("Starting TinyDB to PostgreSQL migration...")
        
        with get_db_session() as session:
            # Create default user
            user = self.create_default_user(session)
            print(f"Created default user: {user.email}")
            
            # Create default router
            router = self.create_default_router(session, user.id)
            print(f"Created default router: {router.router_id}")
            
            # Migrate all data
            self.migrate_devices(session, user.id, router.router_id)
            self.migrate_whitelist(session, user.id, router.router_id)
            self.migrate_blacklist(session, user.id, router.router_id)
            
            print("Migration completed successfully!")

if __name__ == "__main__":
    migrator = TinyDBMigrator()
    migrator.run_migration()
```

---

## 2.6: Alembic Migration Setup

### 2.6.1: Installation & Configuration
```bash
# Install Alembic
pip install alembic psycopg2-binary sqlalchemy

# Initialize Alembic
cd backend
alembic init migrations
```

### 2.6.2: Alembic Configuration (`alembic.ini`)
```ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = postgresql://netpilot_user:password@127.0.0.1:5432/netpilot_db

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 79 REVISION_SCRIPT_FILENAME
```

### 2.6.3: Environment Setup (`migrations/env.py`)
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add models to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.base import Base
import models.user
import models.router
import models.device
import models.whitelist
import models.blacklist
import models.blocked_device
import models.settings

config = context.config

# Override URL from environment
database_url = os.getenv('DATABASE_URL')
if database_url:
    config.set_main_option('sqlalchemy.url', database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
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

### 2.6.4: Create Initial Migration
```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial multi-user schema"

# Apply migration
alembic upgrade head
```

---

## 2.7: Updated Backend Dependencies

### 2.7.1: Requirements Update (`requirements.txt`)
```python
# Add these to existing requirements.txt
sqlalchemy==2.0.23
alembic==1.13.1
psycopg2-binary==2.9.9
python-decouple==3.8
```

### 2.7.2: Environment Configuration (`.env`)
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

## 2.8: Flask Integration Updates

### 2.8.1: Updated Server Configuration (`server.py`)
```python
from flask import Flask, g
from flask_cors import CORS
from database.connection import db
from database.session import get_db_session
import os
from decouple import config
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Load database configuration
DATABASE_URL = config('DATABASE_URL')
os.environ['DATABASE_URL'] = DATABASE_URL

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize database on startup
@app.before_first_request
def initialize_database():
    try:
        db.create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Add database session to request context
@app.before_request
def before_request():
    g.db_session = db.get_session()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db_session'):
        if exception:
            g.db_session.rollback()
        g.db_session.close()

# Import and register blueprints
from endpoints.health import health_bp
from endpoints.config import config_bp
from endpoints.api import network_bp
from endpoints.db import db_bp
from endpoints.wifi import wifi_bp
from endpoints.whitelist import whitelist_bp
from endpoints.blacklist import blacklist_bp

app.register_blueprint(health_bp)
app.register_blueprint(config_bp)
app.register_blueprint(network_bp)
app.register_blueprint(db_bp)
app.register_blueprint(wifi_bp)
app.register_blueprint(whitelist_bp)
app.register_blueprint(blacklist_bp)

if __name__ == "__main__":
    logger.info("Starting NetPilot backend with PostgreSQL")
    app.run(host="0.0.0.0", port=5000, debug=True)
```

---

## 2.9: Testing & Validation

### 2.9.1: Database Test Script (`tests/test_database.py`)
```python
import pytest
from database.connection import db
from database.session import get_db_session
from models.user import User
from models.device import UserDevice

def test_database_connection():
    """Test basic database connectivity"""
    with get_db_session() as session:
        result = session.execute("SELECT 1 as test").scalar()
        assert result == 1

def test_user_creation():
    """Test user model creation"""
    with get_db_session() as session:
        user = User(
            email='test@example.com',
            full_name='Test User'
        )
        session.add(user)
        session.commit()
        
        found_user = session.query(User).filter_by(email='test@example.com').first()
        assert found_user is not None
        assert found_user.full_name == 'Test User'

def test_device_creation():
    """Test device model with foreign key relationships"""
    with get_db_session() as session:
        # Create user first
        user = User(email='devicetest@example.com', full_name='Device Test')
        session.add(user)
        session.flush()
        
        # Create device
        device = UserDevice(
            user_id=user.id,
            router_id='test-router',
            ip='192.168.1.100',
            mac='00:11:22:33:44:55',
            hostname='test-device'
        )
        session.add(device)
        session.commit()
        
        found_device = session.query(UserDevice).filter_by(ip='192.168.1.100').first()
        assert found_device is not None
        assert found_device.hostname == 'test-device'

def test_data_isolation():
    """Test that users can only see their own data"""
    with get_db_session() as session:
        # Create two users
        user1 = User(email='user1@test.com', full_name='User 1')
        user2 = User(email='user2@test.com', full_name='User 2')
        session.add_all([user1, user2])
        session.flush()
        
        # Create devices for each user
        device1 = UserDevice(user_id=user1.id, router_id='router1', 
                           ip='192.168.1.10', hostname='device1')
        device2 = UserDevice(user_id=user2.id, router_id='router2', 
                           ip='192.168.1.20', hostname='device2')
        session.add_all([device1, device2])
        session.commit()
        
        # Test isolation
        user1_devices = session.query(UserDevice).filter_by(user_id=user1.id).all()
        user2_devices = session.query(UserDevice).filter_by(user_id=user2.id).all()
        
        assert len(user1_devices) == 1
        assert len(user2_devices) == 1
        assert user1_devices[0].hostname == 'device1'
        assert user2_devices[0].hostname == 'device2'

if __name__ == "__main__":
    pytest.main([__file__])
```

### 2.9.2: Migration Validation
```bash
# Test migrations
alembic downgrade base
alembic upgrade head

# Verify schema
psql -h 127.0.0.1 -U netpilot_user -d netpilot_db -c "\dt"
psql -h 127.0.0.1 -U netpilot_user -d netpilot_db -c "\d users"
```

---

## 2.10: Backup & Monitoring

### 2.10.1: Backup Script (`scripts/backup_postgres.sh`)
```bash
#!/bin/bash
BACKUP_DIR="/opt/netpilot/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/netpilot_backup_$DATE.sql"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h 127.0.0.1 -U netpilot_user netpilot_db > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

### 2.10.2: Health Monitoring (`scripts/monitor_postgres.py`)
```python
import psycopg2
import os
from datetime import datetime

def check_postgres_health():
    """Monitor PostgreSQL health and connections"""
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="netpilot_db",
            user="netpilot_user",
            password=os.getenv('DB_PASSWORD')
        )
        
        cursor = conn.cursor()
        
        # Check active connections
        cursor.execute("""
            SELECT count(*) FROM pg_stat_activity 
            WHERE datname='netpilot_db'
        """)
        connections = cursor.fetchone()[0]
        
        # Check database size
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size('netpilot_db'))
        """)
        db_size = cursor.fetchone()[0]
        
        # Check table counts
        cursor.execute("""
            SELECT 
                (SELECT count(*) FROM users) as users,
                (SELECT count(*) FROM user_devices) as devices,
                (SELECT count(*) FROM user_whitelists) as whitelists,
                (SELECT count(*) FROM user_blacklists) as blacklists
        """)
        counts = cursor.fetchone()
        
        print(f"PostgreSQL Health Check - {datetime.now()}")
        print(f"Active Connections: {connections}")
        print(f"Database Size: {db_size}")
        print(f"Users: {counts[0]}, Devices: {counts[1]}")
        print(f"Whitelists: {counts[2]}, Blacklists: {counts[3]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"PostgreSQL health check failed: {e}")
        return False

if __name__ == "__main__":
    check_postgres_health()
```

---

## Implementation Timeline

### Week 1: PostgreSQL Setup
- [x] Install PostgreSQL on VM
- [x] Configure database and users
- [x] Test connectivity
- [x] Set up firewall rules

### Week 2: Schema & Models
- [x] Design multi-user schema
- [x] Implement SQLAlchemy models
- [x] Create Alembic migrations
- [x] Test schema creation

### Week 3: Data Migration
- [x] Create migration scripts
- [x] Test migration with sample data
- [x] Validate data integrity
- [x] Create backup procedures

### Week 4: Backend Integration
- [x] Update Flask app configuration
- [x] Replace TinyDB calls with SQLAlchemy
- [x] Update repository layers
- [x] Test all API endpoints

### Success Criteria
- [ ] PostgreSQL running stable on VM
- [ ] All TinyDB data migrated successfully
- [ ] Multi-user data isolation working
- [ ] All current API endpoints functional
- [ ] Database ready for Google OAuth (Phase 3)
- [ ] Automated backups configured
- [ ] Monitoring system operational

This plan provides a complete migration path from TinyDB to PostgreSQL with proper multi-user support and Google OAuth preparation, utilizing your existing VM infrastructure efficiently. 