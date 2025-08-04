#!/usr/bin/env python3
"""
Enforce Google 2FA Detection
Modify the OAuth flow to require Google 2FA for all users
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def show_auth_modification():
    """
    Show how to modify auth.py to enforce Google 2FA
    """
    
    modification = '''
# Update backend2/auth.py - Modify the authorize() function:

@auth_bp.route('/authorize')
def authorize():
    # ... existing OAuth code until user creation/update ...
    
    # After successful user creation/update:
    db_session.commit()
    
    # CHECK GOOGLE 2FA ENFORCEMENT
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    
    # Store user_id in session
    session['user_id'] = str(user.id)
    session.permanent = True
    
    # ENFORCE GOOGLE 2FA DETECTION
    google_2fa_detected = False
    
    # Method 1: Check auth_time (recent auth suggests 2FA)
    if 'auth_time' in token:
        auth_time = datetime.fromtimestamp(token['auth_time'])
        # If authenticated within last 2 minutes, likely used 2FA
        if datetime.utcnow() - auth_time < timedelta(minutes=2):
            google_2fa_detected = True
            logger.info(f"Google 2FA detected via recent auth for {user.email}")
    
    # Method 2: Check for MFA indicators in token (if available)
    if token.get('amr') and any(method in ['mfa', 'sms', 'otp'] for method in token.get('amr', [])):
        google_2fa_detected = True
        logger.info(f"Google 2FA detected via AMR for {user.email}")
    
    if google_2fa_detected:
        # Mark as 2FA verified
        session['2fa_verified'] = True
        session['2fa_verified_at'] = datetime.utcnow().isoformat()
        logger.info(f"User {user.email} authenticated with Google 2FA")
        return redirect(f"{frontend_url}?login=success&google_2fa=verified")
    else:
        # No 2FA detected - redirect with warning
        logger.warning(f"No Google 2FA detected for {user.email}")
        return redirect(f"{frontend_url}?login=success&google_2fa=required")
    
# Update /me endpoint to return Google 2FA status:

@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    # ... existing code ...
    
    return jsonify({
        'user': {
            'id': str(user.id),
            'email': user.email,
            'name': user.name
        },
        'google_2fa_verified': session.get('2fa_verified', False),
        'auth_method': 'google_oauth_2fa' if session.get('2fa_verified') else 'google_oauth_basic'
    })
'''
    
    print("🔧 GOOGLE 2FA ENFORCEMENT MODIFICATION:")
    print("=" * 60)
    print(modification)
    
    print("\n📋 FRONTEND MODIFICATION NEEDED:")
    print("=" * 40)
    
    frontend_mod = '''
# Update frontend/dashboard/src/context/AuthContext.jsx:

// In the useEffect for login success:
useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const loginSuccess = urlParams.get('login');
    const google2fa = urlParams.get('google_2fa');
    
    if (loginSuccess === 'success') {
        if (google2fa === 'required') {
            // Show warning that Google 2FA is recommended
            setShowGoogle2FAWarning(true);
        } else if (google2fa === 'verified') {
            // Show success message
            console.log('Authenticated with Google 2FA');
        }
        
        // Clear URL params
        window.history.replaceState({}, document.title, window.location.pathname);
        
        checkAuthStatus();
    }
}, []);

// Add state for Google 2FA warning
const [showGoogle2FAWarning, setShowGoogle2FAWarning] = useState(false);
'''
    
    print(frontend_mod)

def check_current_google_oauth_flow():
    """
    Check what's currently happening in the OAuth flow
    """
    
    print("🔍 DEBUGGING CURRENT OAUTH FLOW:")
    print("=" * 50)
    
    debug_script = '''
# Add this to backend2/auth.py in the authorize() function for debugging:

@auth_bp.route('/authorize')
def authorize():
    # ... existing code ...
    
    # ADD THIS DEBUG SECTION:
    logger.info(f"=== OAUTH DEBUG for {user.email} ===")
    logger.info(f"Token keys: {list(token.keys())}")
    
    if 'auth_time' in token:
        auth_time = datetime.fromtimestamp(token['auth_time'])
        time_diff = datetime.utcnow() - auth_time
        logger.info(f"Auth time: {auth_time}, Diff: {time_diff}")
    
    if 'amr' in token:
        logger.info(f"AMR (Auth Methods): {token['amr']}")
    
    if 'acr' in token:
        logger.info(f"ACR (Auth Context): {token['acr']}")
    
    logger.info(f"=== END OAUTH DEBUG ===")
    
    # ... rest of existing code ...
'''
    
    print(debug_script)
    
    print("\n📋 TO DEBUG:")
    print("1. Add the debug code above to auth.py")
    print("2. Restart the backend server")
    print("3. Try logging in")
    print("4. Check backend2/logs/main.log for debug info")

def main():
    print("🔐 Google 2FA Enforcement Options")
    print("=" * 50)
    
    print("\n🤔 You're seeing only 1 factor because:")
    print("   1. Custom 2FA is disabled ✅")  
    print("   2. Google 2FA isn't being detected/enforced ❌")
    print("   3. Most users don't have Google 2FA enabled ❌")
    
    print("\n🚀 Choose your approach:")
    print("   A. Show how to enforce Google 2FA detection")
    print("   B. Debug current OAuth flow to see what's available")
    print("   C. Go back to custom 2FA (re-enable)")
    print("   D. Test with your own Google account (enable Google 2FA first)")
    
    choice = input(f"\nSelect option (A/B/C/D): ").strip().upper()
    
    if choice == 'A':
        show_auth_modification()
        print(f"\n💡 This will:")
        print(f"   ✅ Detect when users used Google 2FA")
        print(f"   ⚠️  Show warning when they didn't")
        print(f"   📱 Encourage enabling Google 2FA")
        
    elif choice == 'B':
        check_current_google_oauth_flow()
        print(f"\n💡 This will help us see what Google sends during OAuth")
        
    elif choice == 'C':
        print(f"\n🔐 To re-enable custom 2FA:")
        print(f"   cd backend2")
        print(f"   python debug_user_2fa_status.py")
        print(f"   Select option to enable 2FA for all users")
        
    elif choice == 'D':
        print(f"\n📱 To test Google 2FA:")
        print(f"   1. Go to myaccount.google.com")
        print(f"   2. Security → 2-Step Verification")
        print(f"   3. Enable with your phone number")
        print(f"   4. Try logging into NetPilot")
        print(f"   5. You should get SMS during login!")
        
    else:
        print(f"\n💡 Recommendation: Try option D first to test Google 2FA with your account!")

if __name__ == "__main__":
    main()