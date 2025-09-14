#!/usr/bin/env python3
"""
Debug Google OAuth Token Contents
This script will help us see what Google actually sends during OAuth
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def show_oauth_debug_modification():
    """
    Show how to add debugging to auth.py to see what Google sends
    """
    
    debug_code = '''
# ADD THIS TO backend2/auth.py in the authorize() function:

@auth_bp.route('/authorize')
def authorize():
    """Handle OAuth callback"""
    token = google.authorize_access_token()
    session['user'] = token

    # === ADD THIS GOOGLE 2FA DEBUG SECTION ===
    logger.info("=== GOOGLE OAUTH TOKEN DEBUG ===")
    logger.info(f"Token keys: {list(token.keys())}")
    
    # Log all token contents (be careful with sensitive data in production)
    for key, value in token.items():
        if key not in ['access_token', 'refresh_token']:  # Don't log sensitive tokens
            logger.info(f"Token[{key}]: {value}")
    
    # Check for 2FA indicators
    userinfo = token.get('userinfo', {})
    id_token_claims = token.get('id_token_claims', {})
    
    logger.info(f"Userinfo keys: {list(userinfo.keys())}")
    logger.info(f"ID token claims keys: {list(id_token_claims.keys()) if id_token_claims else 'None'}")
    
    # Look for authentication method references
    if 'amr' in token:
        logger.info(f"AMR (Auth Methods): {token['amr']}")
    if 'acr' in token:
        logger.info(f"ACR (Auth Context): {token['acr']}")
    if 'auth_time' in token:
        from datetime import datetime
        auth_time = datetime.fromtimestamp(token['auth_time'])
        logger.info(f"Auth time: {auth_time}")
        
    # Check ID token for additional claims
    if id_token_claims:
        if 'amr' in id_token_claims:
            logger.info(f"ID Token AMR: {id_token_claims['amr']}")
        if 'acr' in id_token_claims:
            logger.info(f"ID Token ACR: {id_token_claims['acr']}")
        if 'auth_time' in id_token_claims:
            auth_time = datetime.fromtimestamp(id_token_claims['auth_time'])
            logger.info(f"ID Token auth_time: {auth_time}")
    
    logger.info("=== END GOOGLE OAUTH DEBUG ===")
    # === END DEBUG SECTION ===

    userToken = session.get('user')
    # ... rest of existing code ...
'''
    
    print("🔧 GOOGLE OAUTH DEBUG CODE:")
    print("=" * 60)
    print(debug_code)
    
    print("\n📋 STEPS TO DEBUG:")
    print("1. Add this debug code to backend2/auth.py")
    print("2. Restart the backend server")
    print("3. Login with Google (use your account with 2FA)")
    print("4. Check backend2/logs/main.log for debug output")
    print("5. Look for the '=== GOOGLE OAUTH TOKEN DEBUG ===' section")

def show_google_2fa_implementation():
    """
    Show how to implement Google 2FA detection based on what we find
    """
    
    implementation = '''
# After debugging, here's how to implement Google 2FA detection:

def detect_google_2fa(token):
    """
    Detect if user used Google 2FA during login
    Returns: (used_2fa: bool, method: str, confidence: str)
    """
    
    # Check various 2FA indicators
    used_2fa = False
    method = "unknown"
    confidence = "low"
    
    # Method 1: Check Authentication Methods Reference (AMR)
    amr = token.get('amr', [])
    if not amr:
        # Also check in ID token claims
        id_token_claims = token.get('id_token_claims', {})
        amr = id_token_claims.get('amr', [])
    
    # Known 2FA AMR values:
    # 'mfa' = Multi-factor authentication
    # 'sms' = SMS-based authentication
    # 'otp' = One-time password
    # 'totp' = Time-based one-time password
    # 'hwk' = Hardware key
    strong_methods = ['mfa', 'sms', 'otp', 'totp', 'hwk', 'oath']
    
    for amr_method in amr:
        if amr_method.lower() in strong_methods:
            used_2fa = True
            method = amr_method
            confidence = "high"
            break
    
    # Method 2: Check Authentication Context Class Reference (ACR)
    if not used_2fa:
        acr = token.get('acr')
        if not acr:
            id_token_claims = token.get('id_token_claims', {})
            acr = id_token_claims.get('acr')
        
        # ACR values indicating 2FA
        if acr in ['2', 'mfa', 'https://schemas.openid.net/pape/policies/2007/06/multi-factor']:
            used_2fa = True
            method = f"acr:{acr}"
            confidence = "high"
    
    # Method 3: Check auth_time (recent auth suggests 2FA)
    if not used_2fa:
        auth_time = token.get('auth_time')
        if not auth_time:
            id_token_claims = token.get('id_token_claims', {})
            auth_time = id_token_claims.get('auth_time')
        
        if auth_time:
            from datetime import datetime, timedelta
            auth_datetime = datetime.fromtimestamp(auth_time)
            time_diff = datetime.utcnow() - auth_datetime
            
            # If authenticated very recently (within 2 minutes), possibly 2FA
            if time_diff < timedelta(minutes=2):
                used_2fa = True
                method = "recent_auth"
                confidence = "medium"
    
    return used_2fa, method, confidence

# Then modify the authorize() function:
@auth_bp.route('/authorize')
def authorize():
    # ... existing code until user creation ...
    
    # DETECT GOOGLE 2FA
    google_2fa_used, method, confidence = detect_google_2fa(token)
    
    logger.info(f"Google 2FA detection for {user.email}:")
    logger.info(f"  Used 2FA: {google_2fa_used}")
    logger.info(f"  Method: {method}")
    logger.info(f"  Confidence: {confidence}")
    
    # Store user_id and 2FA status in session
    session['user_id'] = str(user.id)
    session.permanent = True
    
    if google_2fa_used:
        # Mark as 2FA verified since Google handled it
        session['2fa_verified'] = True
        session['2fa_verified_at'] = datetime.utcnow().isoformat()
        session['2fa_method'] = f"google_{method}"
        
        logger.info(f"User {user.email} authenticated with Google 2FA ({method})")
        return redirect(f"{frontend_url}?login=success&google_2fa=verified&method={method}")
    else:
        # No Google 2FA detected
        logger.warning(f"No Google 2FA detected for {user.email}")
        session.pop('2fa_verified', None)
        return redirect(f"{frontend_url}?login=success&google_2fa=not_detected")
'''
    
    print("🔐 GOOGLE 2FA DETECTION IMPLEMENTATION:")
    print("=" * 60)
    print(implementation)

def show_oauth_scope_upgrade():
    """
    Show how to upgrade OAuth scopes to get more 2FA information
    """
    
    scope_upgrade = '''
# UPDATE backend2/auth.py OAuth configuration:

def init_oauth(app):
    """Initialize OAuth with the Flask app"""
    global oauth, google
    oauth = OAuth(app)
    
    google = oauth.register(
        "NetPilot",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'prompt': 'consent',  # Force consent to get fresh auth info
            'max_age': 0,  # Force re-authentication 
        },
    )
    
# Alternative with explicit 2FA request:
# Note: This might be too aggressive and force 2FA even for users who don't have it
    
    google_strict = oauth.register(
        "NetPilot",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'prompt': 'consent',
            'max_age': 0,
            'acr_values': 'http://schemas.openid.net/pape/policies/2007/06/multi-factor',
        },
    )
'''
    
    print("🔧 OAUTH SCOPE UPGRADE:")
    print("=" * 40)
    print(scope_upgrade)

def main():
    print("🔍 Google 2FA Detection Debugging Tool")
    print("=" * 60)
    
    print("🤔 The issue: Your auth.py never checks for Google 2FA indicators!")
    print("📋 Even if you used Google 2FA, NetPilot doesn't detect it.")
    
    print("\n🚀 Choose debugging approach:")
    print("   A. Add debug code to see what Google sends")
    print("   B. Show Google 2FA detection implementation")
    print("   C. Show OAuth scope upgrades")
    print("   D. All of the above")
    
    choice = input(f"\nSelect option (A/B/C/D): ").strip().upper()
    
    if choice == 'A':
        show_oauth_debug_modification()
    elif choice == 'B':
        show_google_2fa_implementation()
    elif choice == 'C':
        show_oauth_scope_upgrade()
    else:  # D or anything else
        print("\n" + "="*60)
        show_oauth_debug_modification()
        print("\n" + "="*60)
        show_google_2fa_implementation()
        print("\n" + "="*60)
        show_oauth_scope_upgrade()
        
        print(f"\n🎯 RECOMMENDED NEXT STEPS:")
        print(f"1. Start with option A - add debug code")
        print(f"2. Login with your Google account (that has 2FA)")
        print(f"3. Check what Google actually sends")
        print(f"4. Then implement option B based on what you find")

if __name__ == "__main__":
    main()