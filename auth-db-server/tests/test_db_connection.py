#!/usr/bin/env python3
"""
Test database connection and model imports
"""
import os
import sys
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

try:
    from database.connection import db
    print("✅ Database connection module imported successfully")
    
    from models.base import Base
    print("✅ Base model imported successfully")
    
    from models.user import User
    print("✅ User model imported successfully")
    
    from models.session import UserSession
    print("✅ Session model imported successfully")
    
    from models.router import UserRouter
    print("✅ Router model imported successfully")
    
    from models.device import UserDevice
    print("✅ Device model imported successfully")
    
    from models.device_group import DeviceGroup
    print("✅ DeviceGroup model imported successfully")
    
    from models.blocked_device import UserBlockedDevice
    print("✅ BlockedDevice model imported successfully")
    
    from models.settings import UserSetting
    print("✅ Settings model imported successfully")
    
    # Test database connection
    print("\n🔌 Testing database connection...")
    engine = db.engine
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ Database connected successfully: {version}")
    
    # Test table creation
    print("\n🏗️ Testing table creation...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")
    
    print("\n🎉 All tests passed! Database is ready.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 