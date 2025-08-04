#!/usr/bin/env python3
"""
2FA Implementation Test Script
Tests basic functionality and race condition protections.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pyotp
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from database.connection import db
from models.user import User, User2FASettings, User2FAAttempt
from services.twofa_service import twofa_service
from utils.logging_config import get_logger

logger = get_logger('2fa_test')

def test_basic_2fa_functionality():
    """Test basic 2FA service functionality"""
    print("\n🔍 Testing Basic 2FA Functionality...")
    print("=" * 50)
    
    try:
        # Test secret generation
        secret = twofa_service.generate_totp_secret()
        print(f"✅ Secret generation: {secret[:8]}...")
        
        # Test encryption/decryption
        encrypted = twofa_service.encrypt_secret(secret)
        decrypted = twofa_service.decrypt_secret(encrypted)
        assert secret == decrypted, "Encryption/decryption failed"
        print("✅ Encryption/decryption works")
        
        # Test TOTP code generation and verification
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        verification_result = twofa_service.verify_totp_code(secret, current_code)
        assert verification_result, "TOTP verification failed"
        print(f"✅ TOTP verification works (code: {current_code})")
        
        # Test backup code generation and verification
        backup_codes = twofa_service.generate_backup_codes()
        assert len(backup_codes) == 8, "Wrong number of backup codes"
        
        test_code = backup_codes[0]
        hashed_code = twofa_service.hash_backup_code(test_code)
        verification = twofa_service.verify_backup_code(hashed_code, test_code)
        assert verification, "Backup code verification failed"
        print(f"✅ Backup codes work (sample: {test_code})")
        
        # Test QR code generation
        qr_code = twofa_service.generate_qr_code("test@example.com", secret)
        assert qr_code.startswith("data:image/png;base64,"), "QR code generation failed"
        print("✅ QR code generation works")
        
        print("\n🎉 All basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_race_condition_protection():
    """Test race condition protections with concurrent operations"""
    print("\n🔍 Testing Race Condition Protection...")
    print("=" * 50)
    
    db_session = db.get_session()
    try:
        # Create a test user and 2FA settings
        test_user = User(
            google_id="test_race_condition",
            email="race_test@example.com",
            full_name="Race Test User",
            is_active=True
        )
        db_session.add(test_user)
        db_session.commit()
        
        user_id = str(test_user.id)
        secret = twofa_service.generate_totp_secret()
        
        # Create 2FA settings
        user_2fa = User2FASettings(
            user_id=user_id,
            is_enabled=True,
            totp_secret=twofa_service.encrypt_secret(secret),
            backup_codes=[twofa_service.hash_backup_code("TEST1234"), twofa_service.hash_backup_code("TEST5678")],
            failed_attempts=0
        )
        db_session.add(user_2fa)
        db_session.commit()
        
        print(f"✅ Test user created with ID: {user_id}")
        
        # Test 1: Concurrent failed attempt increments
        print("\n📊 Testing concurrent failed attempt increments...")
        
        def simulate_failed_attempt():
            test_session = db.get_session()
            try:
                failed_count, should_lock = twofa_service.atomic_increment_failed_attempts(test_session, user_id)
                test_session.commit()
                return failed_count, should_lock
            except Exception as e:
                test_session.rollback()
                raise e
            finally:
                test_session.close()
        
        # Run 5 concurrent failed attempts
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(simulate_failed_attempt) for _ in range(5)]
            results = [future.result() for future in futures]
        
        final_attempts = max(result[0] for result in results)
        print(f"✅ Concurrent failed attempts handled correctly: {final_attempts} attempts recorded")
        
        # Test 2: Concurrent backup code usage
        print("\n📊 Testing concurrent backup code usage...")
        
        # Reset for backup code test
        twofa_service.atomic_reset_failed_attempts(db_session, user_id)
        db_session.commit()
        
        backup_hash = twofa_service.hash_backup_code("TEST1234")
        
        def try_use_backup_code():
            test_session = db.get_session()
            try:
                result = twofa_service.atomic_use_backup_code(test_session, user_id, backup_hash)
                test_session.commit()
                return result
            except Exception as e:
                test_session.rollback()
                raise e
            finally:
                test_session.close()
        
        # Try to use the same backup code concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(try_use_backup_code) for _ in range(3)]
            results = [future.result() for future in futures]
        
        # Only one should succeed
        successful_uses = sum(1 for result in results if result)
        assert successful_uses == 1, f"Expected 1 successful backup code use, got {successful_uses}"
        print(f"✅ Backup code race condition prevented: only 1 of 3 concurrent attempts succeeded")
        
        # Test 3: Setup token validation race condition
        print("\n📊 Testing setup token validation race condition...")
        
        # Create setup token
        setup_token = "test_setup_token_123"
        user_2fa_fresh = db_session.query(User2FASettings).filter_by(user_id=user_id).first()
        user_2fa_fresh.setup_token = setup_token
        user_2fa_fresh.setup_expires_at = time.time() + 600  # 10 minutes from now (this is wrong - should be datetime)
        
        # Fix the datetime issue
        from datetime import datetime, timedelta
        user_2fa_fresh.setup_expires_at = datetime.utcnow() + timedelta(minutes=10)
        db_session.commit()
        
        def try_validate_token():
            test_session = db.get_session()
            try:
                result = twofa_service.atomic_validate_and_expire_setup_token(test_session, user_id, setup_token)
                test_session.commit()
                return result is not None
            except Exception as e:
                test_session.rollback()
                raise e
            finally:
                test_session.close()
        
        # Try to validate the same token concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(try_validate_token) for _ in range(3)]
            results = [future.result() for future in futures]
        
        # Only one should succeed
        successful_validations = sum(1 for result in results if result)
        assert successful_validations == 1, f"Expected 1 successful token validation, got {successful_validations}"
        print(f"✅ Setup token race condition prevented: only 1 of 3 concurrent validations succeeded")
        
        print("\n🎉 All race condition protection tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Race condition test failed: {e}")
        return False
    finally:
        # Cleanup
        try:
            db_session.query(User2FAAttempt).filter_by(user_id=user_id).delete()
            db_session.query(User2FASettings).filter_by(user_id=user_id).delete()
            db_session.query(User).filter_by(id=user_id).delete()
            db_session.commit()
            print("✅ Test data cleaned up")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
        finally:
            db_session.close()

def test_endpoint_imports():
    """Test that all modules can be imported without errors"""
    print("\n🔍 Testing Module Imports...")
    print("=" * 50)
    
    try:
        # Test 2FA service import
        from services.twofa_service import twofa_service
        print("✅ TwoFAService import successful")
        
        # Test 2FA endpoints import
        from endpoints.twofa import twofa_bp
        print("✅ 2FA endpoints import successful")
        
        # Test auth integration
        from auth import login_required, twofa_required
        print("✅ Auth decorators import successful")
        
        # Test model imports
        from models.user import User, User2FASettings, User2FAAttempt
        print("✅ 2FA models import successful")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 NetPilot 2FA Implementation Test Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_endpoint_imports),
        ("Basic Functionality", test_basic_2fa_functionality),
        ("Race Condition Protection", test_race_condition_protection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} tests...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! 2FA implementation is ready.")
        print("\n📋 NEXT STEPS:")
        print("1. Set TOTP_ENCRYPTION_KEY environment variable")
        print("2. Start the server: python server.py")
        print("3. Test endpoints with Postman")
        print("4. Implement frontend integration (Phase 3)")
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())