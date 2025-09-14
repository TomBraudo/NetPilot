#!/usr/bin/env python3
"""
Debug script to check and set 2FA status for a user
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from database.connection import db
from models.user import User, User2FASettings
from utils.logging_config import get_logger

logger = get_logger('debug_2fa')

def check_user_2fa_status(email=None):
    """Check 2FA status for a user"""
    
    db_session = db.get_session()
    try:
        print("🔍 Checking user 2FA status...")
        print("=" * 50)
        
        if email:
            user = db_session.query(User).filter_by(email=email).first()
            if not user:
                print(f"❌ User not found with email: {email}")
                return None
        else:
            # Get the most recent user
            user = db_session.query(User).order_by(User.created_at.desc()).first()
            if not user:
                print("❌ No users found in database")
                return None
        
        print(f"✅ User found: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Google ID: {user.google_id}")
        print(f"   Active: {user.is_active}")
        print(f"   Last Login: {user.last_login}")
        
        # Check 2FA settings
        print(f"\n🔐 2FA Status:")
        print(f"   requires_2fa: {user.requires_2fa}")
        print(f"   twofa_enforced_at: {user.twofa_enforced_at}")
        
        # Check if user has 2FA settings record
        user_2fa = db_session.query(User2FASettings).filter_by(user_id=str(user.id)).first()
        if user_2fa:
            print(f"   2FA Settings Found:")
            print(f"     is_enabled: {user_2fa.is_enabled}")
            print(f"     has_totp_secret: {bool(user_2fa.totp_secret)}")
            print(f"     backup_codes_count: {len(user_2fa.backup_codes) if user_2fa.backup_codes else 0}")
            print(f"     failed_attempts: {user_2fa.failed_attempts}")
            print(f"     locked_until: {user_2fa.locked_until}")
        else:
            print(f"   2FA Settings: None")
        
        return user
        
    except Exception as e:
        print(f"❌ Error checking user status: {e}")
        return None
    finally:
        db_session.close()

def enable_2fa_for_user(email):
    """Enable 2FA requirement for a user"""
    
    db_session = db.get_session()
    try:
        user = db_session.query(User).filter_by(email=email).first()
        if not user:
            print(f"❌ User not found with email: {email}")
            return False
        
        print(f"🔧 Enabling 2FA requirement for: {user.email}")
        user.requires_2fa = True
        db_session.commit()
        
        print(f"✅ 2FA requirement enabled for {user.email}")
        print(f"   User must now set up 2FA on next login")
        
        return True
        
    except Exception as e:
        print(f"❌ Error enabling 2FA: {e}")
        db_session.rollback()
        return False
    finally:
        db_session.close()

def enable_2fa_for_all_users():
    """Enable 2FA requirement for ALL users"""
    
    db_session = db.get_session()
    try:
        users = db_session.query(User).all()
        
        if not users:
            print("❌ No users found in database")
            return False
        
        print(f"🔧 Enabling 2FA requirement for ALL {len(users)} users...")
        print("=" * 50)
        
        updated_count = 0
        for user in users:
            if not user.requires_2fa:
                print(f"  📧 {user.email} - Enabling 2FA requirement")
                user.requires_2fa = True
                user.twofa_enforced_at = datetime.utcnow()
                updated_count += 1
            else:
                print(f"  ✅ {user.email} - Already has 2FA requirement")
        
        db_session.commit()
        
        print("=" * 50)
        print(f"✅ 2FA requirement enabled for {updated_count} users")
        print(f"📋 Total users requiring 2FA: {len(users)}")
        print(f"⚠️  All users must set up 2FA on their next login")
        
        return True
        
    except Exception as e:
        print(f"❌ Error enabling 2FA for all users: {e}")
        db_session.rollback()
        return False
    finally:
        db_session.close()

def list_all_users():
    """List all users in the database"""
    
    db_session = db.get_session()
    try:
        users = db_session.query(User).all()
        print(f"📋 Found {len(users)} users:")
        print("=" * 50)
        
        for i, user in enumerate(users, 1):
            print(f"{i}. {user.email}")
            print(f"   ID: {user.id}")
            print(f"   requires_2fa: {user.requires_2fa}")
            print(f"   Last Login: {user.last_login}")
            print()
        
        return users
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return []
    finally:
        db_session.close()

def main():
    print("🚀 NetPilot 2FA User Debug Tool")
    print("=" * 60)
    
    print("\n1. Listing all users...")
    users = list_all_users()
    
    if not users:
        print("No users found. Please log in through OAuth first.")
        return
    
    print("\n2. Checking most recent user's 2FA status...")
    recent_user = check_user_2fa_status()
    
    if recent_user and len(users) > 0:
        print(f"\n3. Choose an option:")
        print(f"   A. Enable 2FA for just {recent_user.email}")
        print(f"   B. Enable 2FA for ALL {len(users)} users (recommended)")
        print(f"   C. Do nothing")
        
        choice = input(f"\nSelect option (A/B/C): ").strip().upper()
        
        if choice == 'A':
            if enable_2fa_for_user(recent_user.email):
                print(f"\n✅ Done! {recent_user.email} must set up 2FA on next login.")
        elif choice == 'B':
            confirm = input(f"\n⚠️  This will require 2FA for ALL {len(users)} users. Continue? (y/N): ").strip().lower()
            if confirm == 'y':
                if enable_2fa_for_all_users():
                    print(f"\n🎉 Success! All users now require 2FA.")
                    print(f"📋 Next steps:")
                    print(f"   1. Logout from the app")
                    print(f"   2. Login again to test 2FA setup flow")
                    print(f"   3. All users will see 2FA setup on their next login")
            else:
                print("Operation cancelled.")
        else:
            print("2FA requirement not changed.")

if __name__ == "__main__":
    main()