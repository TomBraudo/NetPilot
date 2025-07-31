#!/usr/bin/env python3
"""
Test script to print the actual content of the whitelist table.
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
from models.whitelist import UserWhitelist
from models.base import Base

def load_env_config():
    """Load database configuration from .env file"""
    load_dotenv()
    
    config = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': os.getenv('DB_PORT', '5432'),
        'username': os.getenv('DB_USERNAME', 'netpilot_user'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME', 'netpilot_db')
    }
    
    if not config['password']:
        raise ValueError("DB_PASSWORD environment variable must be set")
    
    return config

def create_database_connection(config):
    """Create database connection using environment config"""
    database_url = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        echo=False  # Set to True for SQL debugging
    )
    
    SessionLocal = sessionmaker(bind=engine)
    return engine, SessionLocal

def print_whitelist_table_content():
    """Print all content from the user_whitelists table"""
    try:
        # Load configuration
        print("=== NetPilot Backend2 Whitelist Table Content ===")
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
        
        # Query whitelist table
        session = SessionLocal()
        try:
            # Get table info first
            with engine.connect() as conn:
                # Check if table exists
                table_exists = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'user_whitelists'
                    )
                """)).fetchone()[0]
                
                if not table_exists:
                    print("❌ Table 'user_whitelists' does not exist!")
                    return
                
                # Get table structure
                columns_result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'user_whitelists'
                    ORDER BY ordinal_position
                """))
                
                print("📋 Table Structure:")
                print("-" * 80)
                for row in columns_result:
                    print(f"  {row[0]:<20} | {row[1]:<15} | Nullable: {row[2]:<3} | Default: {row[3] or 'None'}")
                print()
            
            # Get row count
            count = session.query(UserWhitelist).count()
            print(f"📊 Total records in user_whitelists table: {count}")
            print()
            
            if count == 0:
                print("📋 Table is empty - no whitelist entries found.")
                return
            
            # Get all whitelist entries
            print("📋 Whitelist Table Content:")
            print("=" * 120)
            whitelist_entries = session.query(UserWhitelist).all()
            
            for i, entry in enumerate(whitelist_entries, 1):
                print(f"Record #{i}:")
                print(f"  ID: {entry.id}")
                print(f"  User ID: {entry.user_id}")
                print(f"  Router ID: {entry.router_id}")
                print(f"  Device IP: {entry.device_ip}")
                print(f"  Device MAC: {entry.device_mac}")
                print(f"  Device Name: {entry.device_name}")
                print(f"  Device ID: {entry.device_id}")
                print(f"  Description: {entry.description}")
                print(f"  Added At: {entry.added_at}")
                print(f"  Created At: {entry.created_at}")
                print(f"  Updated At: {entry.updated_at}")
                print("-" * 60)
            
            print()
            print("✅ Successfully retrieved whitelist table content!")
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

def print_related_tables():
    """Print related table information for context"""
    try:
        config = load_env_config()
        engine, SessionLocal = create_database_connection(config)
        
        print("\n=== Related Tables Information ===")
        
        with engine.connect() as conn:
            # Check related tables
            related_tables = ['users', 'user_devices', 'user_settings']
            
            for table_name in related_tables:
                try:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = count_result.fetchone()[0]
                    print(f"📊 {table_name}: {count} records")
                except Exception as e:
                    print(f"❌ {table_name}: Error - {str(e)}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error getting related tables info: {str(e)}")

if __name__ == "__main__":
    print_whitelist_table_content()
    print_related_tables()
