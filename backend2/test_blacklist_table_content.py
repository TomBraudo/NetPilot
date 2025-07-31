#!/usr/bin/env python3
"""
Test script to print the actual content of the blacklist table.
Uses backend2 .env database credentials.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the backend2 directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import models
from models.blacklist import UserBlacklist
from models.base import Base

def load_env_config():
    """Load database configuration from .env file"""
    # Load environment variables from .env file
    load_dotenv()
    
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'netpilot'),
        'username': os.getenv('DB_USERNAME', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }

def create_database_connection(config):
    """Create database connection using environment config"""
    connection_string = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    
    engine = create_engine(connection_string)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal

def print_blacklist_table_content():
    """Print all content from the user_blacklists table"""
    try:
        # Load configuration
        print("=== NetPilot Backend2 Blacklist Table Content ===")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        config = load_env_config()
        print(f"Connecting to database: {config['database']} at {config['host']}:{config['port']}")
        print(f"Using username: {config['username']}")
        print()
        
        # Create database connection
        engine, SessionLocal = create_database_connection(config)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"PostgreSQL Version: {version}")
        print()
        
        # Query blacklist table
        session = SessionLocal()
        try:
            # Get table info first
            with engine.connect() as conn:
                # Check if table exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'user_blacklists'
                    );
                """))
                table_exists = result.fetchone()[0]
                
                if not table_exists:
                    print("❌ Table 'user_blacklists' does not exist!")
                    print("\nAvailable tables:")
                    result = conn.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name;
                    """))
                    tables = result.fetchall()
                    for table in tables:
                        print(f"  - {table[0]}")
                    return
                
                print("✅ Table 'user_blacklists' exists!")
                
                # Get table schema
                print("\nTable Schema:")
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'user_blacklists'
                    ORDER BY ordinal_position;
                """))
                columns = result.fetchall()
                for col in columns:
                    print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}) default: {col[3]}")
            
            # Get blacklist entries using SQLAlchemy ORM
            print(f"\n=== Blacklist Table Content ===")
            blacklist_entries = session.query(UserBlacklist).all()
            
            if blacklist_entries:
                print(f"Found {len(blacklist_entries)} blacklist entries:")
                print()
                
                for i, entry in enumerate(blacklist_entries, 1):
                    print(f"Entry {i}:")
                    print(f"  ID: {entry.id}")
                    print(f"  User ID: {entry.user_id}")
                    print(f"  Router ID: {entry.router_id}")
                    print(f"  Device IP: {entry.device_ip}")
                    print(f"  Device MAC: {entry.device_mac}")
                    print(f"  Device Name: {entry.device_name}")
                    print(f"  Description: {entry.description}")
                    print(f"  Added At: {entry.added_at}")
                    print(f"  Created At: {entry.created_at}")
                    print(f"  Updated At: {entry.updated_at}")
                    print()
            else:
                print("No blacklist entries found in the table.")
                
        finally:
            session.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def print_related_tables():
    """Print related table information for context"""
    try:
        config = load_env_config()
        engine, SessionLocal = create_database_connection(config)
        
        print("\n=== Related Tables Information ===")
        
        with engine.connect() as conn:
            # Check users table
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"Users table: {user_count} entries")
            
            # Check user_devices table  
            result = conn.execute(text("SELECT COUNT(*) FROM user_devices"))
            device_count = result.fetchone()[0]
            print(f"User devices table: {device_count} entries")
            
            # Check user_routers table
            result = conn.execute(text("SELECT COUNT(*) FROM user_routers"))
            router_count = result.fetchone()[0]  
            print(f"User routers table: {router_count} entries")
            
            # Check user_whitelists table for comparison
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_whitelists'
                );
            """))
            whitelist_exists = result.fetchone()[0]
            
            if whitelist_exists:
                result = conn.execute(text("SELECT COUNT(*) FROM user_whitelists"))
                whitelist_count = result.fetchone()[0]
                print(f"User whitelists table: {whitelist_count} entries")
            else:
                print("User whitelists table: does not exist")
                
    except Exception as e:
        print(f"❌ Error getting related tables info: {e}")

if __name__ == "__main__":
    print_blacklist_table_content()
    print_related_tables()
