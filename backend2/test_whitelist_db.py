#!/usr/bin/env python3
"""
Test script to connect to the database and check whitelist table content
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test database connection and check whitelist tables"""
    
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
        
        # Check if user_whitelists table exists
        print("\n1. Checking if 'user_whitelists' table exists...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_whitelists'
            );
        """)
        result = cursor.fetchone()
        if result:
            # For RealDictRow, access by column name
            table_exists = result['exists'] if 'exists' in result else result[0]
        else:
            table_exists = False
        
        if table_exists:
            print("✅ Table 'user_whitelists' exists!")
            
            # Get table schema
            print("\n2. Getting table schema...")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'user_whitelists'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            print("Table Schema:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']}) default: {col['column_default']}")
            
            # Get table content
            print("\n3. Getting table content...")
            cursor.execute("SELECT COUNT(*) FROM user_whitelists;")
            count_result = cursor.fetchone()
            count = count_result['count'] if 'count' in count_result else count_result[0]
            print(f"Total rows in user_whitelists: {count}")
            
            if count > 0:
                print("\nFirst 10 rows:")
                cursor.execute("SELECT * FROM user_whitelists LIMIT 10;")
                rows = cursor.fetchall()
                for i, row in enumerate(rows, 1):
                    print(f"Row {i}: {dict(row)}")
            else:
                print("Table is empty.")
                
        else:
            print("❌ Table 'user_whitelists' does not exist!")
        
        # Check for other whitelist-related tables
        print("\n4. Checking for other whitelist-related tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%whitelist%';
        """)
        whitelist_tables = cursor.fetchall()
        
        if whitelist_tables:
            print("Found whitelist-related tables:")
            for table in whitelist_tables:
                print(f"  - {table['table_name']}")
        else:
            print("No whitelist-related tables found.")
        
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
        print("\n✅ Database investigation completed successfully!")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== Database Whitelist Investigation ===")
    print("This script will connect to the PostgreSQL database and check whitelist table status\n")
    
    success = test_database_connection()
    
    if success:
        print("\n🎉 Investigation completed!")
    else:
        print("\n💥 Investigation failed!")
        sys.exit(1)
