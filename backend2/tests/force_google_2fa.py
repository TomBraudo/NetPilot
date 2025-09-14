#!/usr/bin/env python3
"""
Force Google 2FA Detection
Multiple approaches to force Google to require and report 2FA
"""

import sys
import os
import jwt
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def solution_1_decode_id_token():
    """
    Solution 1: Decode the ID token JWT to see if 2FA info is hidden there
    """
    
    modification = '''
# Add this function to backend2/auth.py:

import jwt
import json

def decode_google_id_token(token):
    """
    Decode Google ID token to extract 2FA claims
    """
    id_token = token.get('id_token')
    if not id_token:
        return {}
    
    try:
        # Decode without verification (Google's signature verification is complex)
        # In production, you should verify the signature
        decoded = jwt.decode(id_token, options={"verify_signature": False})
        
        logger.info(f"ID Token Claims: {json.dumps(decoded, indent=2)}")
        
        return decoded
    except Exception as e:
        logger.error(f"Failed to decode ID token: {e}")
        return {}

# Update the authorize() function:
@auth_bp.route('/authorize')
def authorize():
    # ... existing code until token analysis ...
    
    # === ENHANCED 2FA DETECTION ===
    logger.info("=== ENHANCED GOOGLE 2FA ANALYSIS ===")
    
    # Decode ID token for additional claims
    id_token_claims = decode_google_id_token(token)
    
    # Check for 2FA in ID token claims
    if 'amr' in id_token_claims:
        logger.info(f"ID Token AMR: {id_token_claims['amr']}")
    if 'acr' in id_token_claims:
        logger.info(f"ID Token ACR: {id_token_claims['acr']}")
    if 'auth_time' in id_token_claims:
        auth_time = datetime.fromtimestamp(id_token_claims['auth_time'])
        logger.info(f"ID Token auth_time: {auth_time}")
    
    # Update detect_google_2fa to use ID token claims
    google_2fa_used, google_method, confidence = detect_google_2fa(token, id_token_claims)
    
    logger.info("=== END ENHANCED ANALYSIS ===")
    # ... rest of existing code ...

# Update detect_google_2fa function:
def detect_google_2fa(token, id_token_claims=None):
    """
    Enhanced 2FA detection using both token and ID token claims
    """
    
    # ... existing detection logic ...
    
    # ADDITION: Check ID token claims
    if not used_2fa and id_token_claims:
        # Check AMR in ID token
        id_amr = id_token_claims.get('amr', [])
        for amr_method in id_amr:
            if amr_method.lower() in strong_methods:
                used_2fa = True
                method = f"id_token_{amr_method}"
                confidence = "high"
                break
        
        # Check ACR in ID token
        if not used_2fa:
            id_acr = id_token_claims.get('acr')
            if id_acr in ['2', 'mfa', 'https://schemas.openid.net/pape/policies/2007/06/multi-factor']:
                used_2fa = True
                method = f"id_token_acr:{id_acr}"
                confidence = "high"
    
    return used_2fa, method, confidence
'''
    
    print("🔧 SOLUTION 1: DECODE ID TOKEN")
    print("=" * 50)
    print(modification)

def solution_2_force_fresh_auth():
    """
    Solution 2: Force Google to require fresh authentication
    """
    
    modification = '''
# Update backend2/auth.py OAuth configuration:

google = oauth.register(
    "NetPilot",
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'login consent',  # Force fresh login
        'max_age': 0,  # Force re-authentication
        'hd': None,  # Remove hosted domain restriction
        # Optionally force 2FA (might be too aggressive):
        # 'acr_values': 'http://schemas.openid.net/pape/policies/2007/06/multi-factor',
    },
)

# Alternative: Force logout before login
@auth_bp.route('/login')
def login():
    """Initiate Google OAuth login with forced fresh auth"""
    
    # Clear any existing session first
    session.clear()
    
    # Force Google logout first (optional)
    # google_logout_url = "https://accounts.google.com/logout"
    
    # Use request host to determine correct redirect URI
    from flask import request
    host = request.host
    scheme = 'https' if request.is_secure else 'http'
    redirect_uri = f"{scheme}://{host}/authorize"
    
    # Force fresh authentication
    return google.authorize_redirect(
        redirect_uri,
        prompt='select_account login',  # Force account selection and login
        max_age=0  # Force re-authentication
    )
'''
    
    print("🔧 SOLUTION 2: FORCE FRESH AUTHENTICATION")
    print("=" * 50)
    print(modification)

def solution_3_accept_reality():
    """
    Solution 3: Accept that Google might not expose 2FA details
    """
    
    alternative = '''
# Alternative approach: Focus on what we CAN detect

def detect_google_security_level(token, id_token_claims=None):
    """
    Detect overall Google account security level instead of specific 2FA
    """
    
    security_score = 0
    indicators = []
    
    # Check email verification
    userinfo = token.get('userinfo', {})
    if userinfo.get('email_verified'):
        security_score += 20
        indicators.append("email_verified")
    
    # Check fresh authentication
    if id_token_claims and 'auth_time' in id_token_claims:
        auth_time = datetime.fromtimestamp(id_token_claims['auth_time'])
        time_diff = datetime.utcnow() - auth_time
        
        if time_diff < timedelta(minutes=5):
            security_score += 30
            indicators.append("fresh_auth")
        elif time_diff < timedelta(hours=1):
            security_score += 15
            indicators.append("recent_auth")
    
    # Check if user had to go through OAuth consent
    if 'consent' in token.get('scope', ''):
        security_score += 10
        indicators.append("explicit_consent")
    
    # Determine security level
    if security_score >= 50:
        level = "high"
        message = "Strong Google authentication detected"
    elif security_score >= 30:
        level = "medium" 
        message = "Moderate Google authentication"
    else:
        level = "low"
        message = "Basic Google authentication"
    
    return level, security_score, indicators, message

# Then in authorize():
security_level, score, indicators, message = detect_google_security_level(token, id_token_claims)

logger.info(f"Google Security Assessment for {user.email}:")
logger.info(f"  Level: {security_level}")
logger.info(f"  Score: {score}/100")
logger.info(f"  Indicators: {indicators}")
logger.info(f"  Message: {message}")

# Accept high or medium security as "good enough"
if security_level in ['high', 'medium']:
    session['2fa_verified'] = True
    session['2fa_method'] = f"google_security_{security_level}"
    return redirect(f"{frontend_url}?login=success&security_level={security_level}")
else:
    # Suggest user enable Google 2FA
    return redirect(f"{frontend_url}?login=success&security_level=low&recommend_2fa=true")
'''
    
    print("🔧 SOLUTION 3: SECURITY LEVEL DETECTION")
    print("=" * 50)
    print(alternative)

def main():
    print("🔍 Google 2FA Detection: Next Steps")
    print("=" * 50)
    
    print("📋 From your logs, Google is NOT sending 2FA indicators in the standard fields.")
    print("📋 This is actually common - Google doesn't always expose this info.")
    
    print("\n🚀 Three approaches to try:")
    print("   A. Decode ID token JWT (might find hidden 2FA info)")
    print("   B. Force fresh Google authentication")
    print("   C. Use security level detection instead of strict 2FA")
    print("   D. Show all solutions")
    
    choice = input(f"\nSelect option (A/B/C/D): ").strip().upper()
    
    if choice == 'A':
        solution_1_decode_id_token()
        print(f"\n💡 This will decode the JWT token from line 334 in your logs")
        print(f"📋 Install required: pip install PyJWT")
        
    elif choice == 'B':
        solution_2_force_fresh_auth()
        print(f"\n💡 This forces Google to require fresh login every time")
        print(f"📋 Users will need to enter password + 2FA on each login")
        
    elif choice == 'C':
        solution_3_accept_reality()
        print(f"\n💡 This accepts that strict 2FA detection might not work")
        print(f"📋 Instead focuses on overall account security level")
        
    else:
        print("\n" + "="*60)
        solution_1_decode_id_token()
        print("\n" + "="*60)
        solution_2_force_fresh_auth()  
        print("\n" + "="*60)
        solution_3_accept_reality()
        
        print(f"\n🎯 RECOMMENDED ORDER:")
        print(f"1. Try Solution A first (decode ID token)")
        print(f"2. If that doesn't work, try Solution B (force fresh auth)")
        print(f"3. If still no luck, use Solution C (security level)")

if __name__ == "__main__":
    main()