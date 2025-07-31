#!/usr/bin/env python3
"""
Test script to check the database connection and verify blacklist table setup.
Uses backend2 .env database credentials.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env
load_dotenv()

def test_database_connection():
    """Test database connection and check blacklist tables"""
    
    # Database connection parameters from .env
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USERNAME'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    print("Database Configuration:")
    print(f"Host: {db_config['host']}")
    print(f"Port: {db_config['port']}")
    print(f"Database: {db_config['database']}")
    print(f"User: {db_config['user']}")
    print(f"Password: {'*' * len(db_config['password']) if db_config['password'] else 'None'}")
    print("-" * 50)
    
    try:
        # Connect to database
        print("Attempting to connect to database...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("✅ Database connection successful!")
        
        # Check if user_blacklists table exists
        print("\n1. Checking if 'user_blacklists' table exists...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_blacklists'
            );
        """)
        result = cursor.fetchone()
        if result:
            # For RealDictRow, access by column name
            table_exists = result['exists'] if 'exists' in result else result[0]
        else:
            table_exists = False
        
        if table_exists:
            print("✅ Table 'user_blacklists' exists!")
            
            # Get table schema
            print("\n2. Getting table schema...")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'user_blacklists'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            print("Table Schema:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']}) default: {col['column_default']}")
            
            # Get table content
            print("\n3. Getting table content...")
            cursor.execute("SELECT COUNT(*) FROM user_blacklists;")
            count_result = cursor.fetchone()
            count = count_result['count'] if 'count' in count_result else count_result[0]
            print(f"Total rows in user_blacklists: {count}")
            
            if count > 0:
                print("\nFirst 10 rows:")
                cursor.execute("SELECT * FROM user_blacklists LIMIT 10;")
                rows = cursor.fetchall()
                for i, row in enumerate(rows, 1):
                    print(f"Row {i}: {dict(row)}")
            else:
                print("Table is empty.")
                
        else:
            print("❌ Table 'user_blacklists' does not exist!")
        
        # Check for other blacklist-related tables
        print("\n4. Checking for other blacklist-related tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%blacklist%';
        """)
        blacklist_tables = cursor.fetchall()
        
        if blacklist_tables:
            print("Found blacklist-related tables:")
            for table in blacklist_tables:
                print(f"  - {table['table_name']}")
        else:
            print("No blacklist-related tables found.")
        
        # Check all existing tables
        print("\n5. All existing tables in database:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        all_tables = cursor.fetchall()
        
        if all_tables:
            print("Existing tables:")
            for table in all_tables:
                print(f"  - {table['table_name']}")
        else:
            print("No tables found in database.")
            
        # Check for any data in user-related tables
        print("\n6. Checking user-related tables for context...")
        user_tables = ['users', 'user_devices', 'user_routers']
        for table_name in user_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            result = cursor.fetchone()
            # Handle RealDictRow properly
            exists = result['exists'] if result and 'exists' in result else (result[0] if result else False)
            
            if exists:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count_result = cursor.fetchone()
                count = count_result['count'] if 'count' in count_result else count_result[0]
                print(f"  - {table_name}: {count} rows")
            else:
                print(f"  - {table_name}: table does not exist")
        
        cursor.close()
        conn.close()
        print("\n✅ Database test completed successfully!")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("=== NetPilot Backend2 Blacklist Database Test ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    test_database_connection()
