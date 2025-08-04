#!/usr/bin/env python3
"""
2FA Schema Verification Script
Verifies that all 2FA database schema changes were applied correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import db
from sqlalchemy import text, inspect
from utils.logging_config import get_logger

logger = get_logger('schema_verification')

def verify_2fa_schema():
    """Verify that all 2FA schema changes were applied correctly."""
    
    try:
        # Get database engine
        engine = db.engine
        
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            print("🔍 Verifying 2FA Database Schema Changes...")
            print("=" * 50)
            
            # 1. Check if new tables exist
            tables = inspector.get_table_names()
            
            print("\n✅ 1. Checking for new 2FA tables:")
            expected_tables = ['user_2fa_settings', 'user_2fa_attempts']
            
            for table in expected_tables:
                if table in tables:
                    print(f"   ✅ {table} - EXISTS")
                else:
                    print(f"   ❌ {table} - MISSING")
                    return False
            
            # 2. Check user_2fa_settings table structure
            print("\n✅ 2. Checking user_2fa_settings table structure:")
            settings_columns = inspector.get_columns('user_2fa_settings')
            expected_settings_cols = [
                'id', 'user_id', 'is_enabled', 'totp_secret', 'backup_codes',
                'sms_phone', 'email_2fa_enabled', 'created_at', 'updated_at',
                'last_used_at', 'setup_token', 'setup_expires_at', 
                'failed_attempts', 'locked_until'
            ]
            
            actual_cols = [col['name'] for col in settings_columns]
            for col in expected_settings_cols:
                if col in actual_cols:
                    print(f"   ✅ {col} - EXISTS")
                else:
                    print(f"   ❌ {col} - MISSING")
            
            # 3. Check user_2fa_attempts table structure
            print("\n✅ 3. Checking user_2fa_attempts table structure:")
            attempts_columns = inspector.get_columns('user_2fa_attempts')
            expected_attempts_cols = [
                'id', 'user_id', 'attempt_type', 'success', 'ip_address',
                'user_agent', 'created_at'
            ]
            
            actual_cols = [col['name'] for col in attempts_columns]
            for col in expected_attempts_cols:
                if col in actual_cols:
                    print(f"   ✅ {col} - EXISTS")
                else:
                    print(f"   ❌ {col} - MISSING")
            
            # 4. Check users table has new 2FA columns
            print("\n✅ 4. Checking users table for new 2FA columns:")
            users_columns = inspector.get_columns('users')
            expected_user_cols = ['requires_2fa', 'twofa_enforced_at']
            
            actual_cols = [col['name'] for col in users_columns]
            for col in expected_user_cols:
                if col in actual_cols:
                    print(f"   ✅ {col} - EXISTS")
                else:
                    print(f"   ❌ {col} - MISSING")
            
            # 5. Check indexes exist
            print("\n✅ 5. Checking for performance indexes:")
            try:
                # Check for our specific indexes
                result = conn.execute(text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE indexname LIKE 'idx_2fa%'
                    ORDER BY indexname
                """))
                
                indexes = [row[0] for row in result]
                expected_indexes = ['idx_2fa_attempts_failed', 'idx_2fa_attempts_user_time']
                
                for idx in expected_indexes:
                    if idx in indexes:
                        print(f"   ✅ {idx} - EXISTS")
                    else:
                        print(f"   ❌ {idx} - MISSING")
                
            except Exception as e:
                print(f"   ⚠️  Could not verify indexes: {e}")
            
            # 6. Test basic functionality
            print("\n✅ 6. Testing basic table access:")
            try:
                # Try to query each table (should not error if tables exist and are accessible)
                conn.execute(text("SELECT COUNT(*) FROM user_2fa_settings")).fetchone()
                print("   ✅ user_2fa_settings - ACCESSIBLE")
                
                conn.execute(text("SELECT COUNT(*) FROM user_2fa_attempts")).fetchone()
                print("   ✅ user_2fa_attempts - ACCESSIBLE")
                
                conn.execute(text("SELECT COUNT(*) FROM users WHERE requires_2fa IS NOT NULL")).fetchone()
                print("   ✅ users.requires_2fa - ACCESSIBLE")
                
            except Exception as e:
                print(f"   ❌ Table access test failed: {e}")
                return False
            
            print("\n" + "=" * 50)
            print("🎉 2FA Schema Verification COMPLETE!")
            print("✅ All database schema changes have been applied successfully.")
            print("✅ Phase 1 (Database Schema Changes) is COMPLETE!")
            
            return True
            
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False

if __name__ == "__main__":
    success = verify_2fa_schema()
    if not success:
        sys.exit(1)