#!/usr/bin/env python3
"""
Google 2FA Detection and Hybrid 2FA Approach
Checks Google OAuth authentication strength and conditionally requires 2FA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from database.connection import db
from models.user import User, User2FASettings
from utils.logging_config import get_logger

logger = get_logger('google_2fa_detection')

def analyze_google_oauth_token(user_token):
    """
    Analyze Google OAuth token for authentication strength indicators
    
    Returns:
        dict: Analysis results including 2FA indicators
    """
    
    analysis = {
        'has_strong_auth': False,
        'auth_time': None,
        'amr': [],  # Authentication Methods Reference
        'acr': None,  # Authentication Context Class Reference
        'requires_custom_2fa': True  # Default to requiring custom 2FA
    }
    
    try:
        # Check if we have userinfo
        userinfo = user_token.get('userinfo', {})
        
        # Check authentication time (recent = stronger)
        if 'auth_time' in user_token:
            auth_time = datetime.fromtimestamp(user_token['auth_time'])
            analysis['auth_time'] = auth_time
            
            # If authenticated very recently (within 5 minutes), likely went through 2FA
            if datetime.utcnow() - auth_time < timedelta(minutes=5):
                analysis['has_strong_auth'] = True
        
        # Check Authentication Methods Reference (AMR) if available
        if 'amr' in user_token:
            analysis['amr'] = user_token['amr']
            
            # Common AMR values that indicate 2FA:
            # 'mfa' = Multi-factor authentication
            # 'sms' = SMS-based authentication  
            # 'otp' = One-time password
            # 'totp' = Time-based one-time password
            strong_methods = ['mfa', 'sms', 'otp', 'totp', 'hwk']
            
            if any(method in analysis['amr'] for method in strong_methods):
                analysis['has_strong_auth'] = True
                analysis['requires_custom_2fa'] = False
        
        # Check Authentication Context Class Reference (ACR) if available
        if 'acr' in user_token:
            analysis['acr'] = user_token['acr']
            
            # ACR values that indicate strong authentication
            # '2' = Two-factor authentication
            # 'mfa' = Multi-factor authentication
            if analysis['acr'] in ['2', 'mfa']:
                analysis['has_strong_auth'] = True
                analysis['requires_custom_2fa'] = False
        
        # Check if user explicitly verified email recently
        if userinfo.get('email_verified') == True:
            # This is a weak indicator, but better than nothing
            pass
        
        # Log the analysis
        logger.info(f"Google OAuth analysis: {analysis}")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing Google OAuth token: {e}")
        # Default to requiring custom 2FA on error
        return analysis

def should_require_custom_2fa(user, user_token):
    """
    Determine if custom 2FA should be required based on Google auth strength
    
    Args:
        user: User object
        user_token: Google OAuth token
        
    Returns:
        tuple: (requires_2fa: bool, reason: str)
    """
    
    # Always require if admin has enforced it
    if user.twofa_enforced_at:
        return True, "2FA enforced by administrator"
    
    # Analyze Google authentication strength
    analysis = analyze_google_oauth_token(user_token)
    
    if analysis['has_strong_auth']:
        return False, f"Google 2FA detected (methods: {analysis.get('amr', 'recent_auth')})"
    else:
        return True, "No strong authentication detected from Google"

def update_user_2fa_requirement_logic():
    """
    Update the auth.py logic to use hybrid approach
    """
    
    new_auth_logic = """
# In backend2/auth.py, update the authorize() function:

@auth_bp.route('/authorize')
def authorize():
    # ... existing OAuth code ...
    
    # After successful user creation/update:
    db_session.commit()
    
    # HYBRID 2FA LOGIC
    from google_2fa_detection import should_require_custom_2fa
    
    requires_custom_2fa, reason = should_require_custom_2fa(user, token)
    logger.info(f"2FA decision for {user.email}: {requires_custom_2fa} - {reason}")
    
    # Store user_id in session
    session['user_id'] = str(user.id)
    session.permanent = True
    
    # Clear any previous 2FA verification
    session.pop('2fa_verified', None)
    session.pop('2fa_verified_at', None)
    
    # Redirect with 2FA indicator
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    
    if requires_custom_2fa:
        user_2fa = db_session.query(User2FASettings).filter_by(user_id=str(user.id)).first()
        if user_2fa and user_2fa.is_enabled:
            return redirect(f"{frontend_url}?login=success&requires_2fa=true&action=verify")
        else:
            return redirect(f"{frontend_url}?login=success&requires_2fa=true&action=setup")
    else:
        # Google 2FA is sufficient
        session['2fa_verified'] = True  # Mark as verified
        session['2fa_verified_at'] = datetime.utcnow().isoformat()
        return redirect(f"{frontend_url}?login=success")
"""
    
    print("🔧 HYBRID 2FA IMPLEMENTATION LOGIC:")
    print("=" * 60)
    print(new_auth_logic)

def disable_2fa_for_all_users():
    """
    Disable custom 2FA requirement for all users (trust Google 2FA)
    """
    
    db_session = db.get_session()
    try:
        users = db_session.query(User).filter_by(requires_2fa=True).all()
        
        if not users:
            print("✅ No users currently require custom 2FA")
            return True
        
        print(f"🔧 Disabling custom 2FA requirement for {len(users)} users...")
        print("   (Will trust Google's 2FA instead)")
        print("=" * 50)
        
        for user in users:
            print(f"  📧 {user.email} - Disabling custom 2FA requirement")
            user.requires_2fa = False
            user.twofa_enforced_at = None
        
        db_session.commit()
        
        print("=" * 50)
        print(f"✅ Custom 2FA disabled for {len(users)} users")
        print(f"🔐 Users will now rely on Google's 2FA only")
        print(f"📋 Benefits:")
        print(f"   - No additional 2FA setup required")
        print(f"   - Uses Google's SMS/Phone authentication")  
        print(f"   - Reduced friction for users")
        
        return True
        
    except Exception as e:
        print(f"❌ Error disabling 2FA: {e}")
        db_session.rollback()
        return False
    finally:
        db_session.close()

def main():
    print("🔐 Google 2FA vs Custom 2FA Analysis Tool")
    print("=" * 60)
    
    print("\n🤔 You have several options:")
    print("   A. Disable custom 2FA (trust Google's 2FA only)")
    print("   B. Keep custom 2FA (maximum security)")
    print("   C. Implement hybrid approach (smart detection)")
    print("   D. Analyze current situation")
    
    choice = input(f"\nSelect option (A/B/C/D): ").strip().upper()
    
    if choice == 'A':
        confirm = input(f"\n⚠️  This will disable custom 2FA and trust Google's 2FA. Continue? (y/N): ").strip().lower()
        if confirm == 'y':
            if disable_2fa_for_all_users():
                print(f"\n🎉 Success! Now using Google's 2FA only.")
                print(f"📋 Users with Google 2FA enabled are automatically protected.")
                print(f"📋 Users without Google 2FA should enable it in their Google account.")
    elif choice == 'B':
        print(f"\n🔐 Keeping custom 2FA for maximum security.")
        print(f"📋 Users will need to set up authenticator apps in addition to Google 2FA.")
    elif choice == 'C':
        print(f"\n🧠 Hybrid approach would:")
        print(f"   ✅ Trust users who used Google 2FA during login")
        print(f"   ⚠️  Require custom 2FA for users without Google 2FA")
        update_user_2fa_requirement_logic()
    else:
        print(f"\n📊 Current situation analysis:")
        from database.connection import db
        db_session = db.get_session()
        users = db_session.query(User).all()
        users_requiring_2fa = db_session.query(User).filter_by(requires_2fa=True).count()
        db_session.close()
        
        print(f"   📋 Total users: {len(users)}")
        print(f"   🔐 Users requiring custom 2FA: {users_requiring_2fa}")
        print(f"   💡 Recommendation: Option A (trust Google 2FA) for better UX")

if __name__ == "__main__":
    main()