# NetPilot 2FA Frontend Integration Test Guide

## 🎯 Test Objective
Verify that the complete 2FA implementation works end-to-end from frontend to backend.

## 🔧 Prerequisites Setup

### 1. Set TOTP Encryption Key
```powershell
# In PowerShell, set the encryption key generated during testing
$env:TOTP_ENCRYPTION_KEY = "tOt3uoWcrvYUlAtmWmqVj8lea90KSH4dmijZAl67z7E="

# Verify it's set
echo $env:TOTP_ENCRYPTION_KEY
```

### 2. Start Backend Server
```powershell
cd backend2
python server.py
```
Expected: Server starts on http://localhost:5000

### 3. Start Frontend Server
```powershell
cd frontend/dashboard
npm run dev
```
Expected: Frontend starts on http://localhost:5173

## 🧪 Test Scenarios

### Test 1: Basic Authentication (No 2FA Required)
**Goal**: Verify existing OAuth flow still works

1. Navigate to http://localhost:5173
2. Click "Log in with Google"
3. Complete Google OAuth
4. **Expected**: Redirected to dashboard, no 2FA prompts

### Test 2: 2FA Setup Flow
**Goal**: Test complete 2FA setup process

#### Step 1: Enable 2FA Requirement
```python
# In backend2, run this script to enable 2FA for your user:
from database.connection import db
from models.user import User

db_session = db.get_session()
user = db_session.query(User).filter_by(email="your_email@gmail.com").first()
if user:
    user.requires_2fa = True
    db_session.commit()
    print(f"2FA enabled for {user.email}")
db_session.close()
```

#### Step 2: Test Setup Flow
1. **Logout** and **login again** 
2. **Expected**: After OAuth, 2FA Setup Modal appears
3. Click "Get Started"
4. **Expected**: QR code displayed with secret key
5. **Scan QR code** with authenticator app (Google Authenticator, Authy)
6. Click "Continue"
7. **Enter 6-digit code** from authenticator app
8. Click "Verify"
9. **Expected**: Backup codes displayed
10. Click "Download" to save codes
11. Click "Complete Setup"
12. **Expected**: Modal closes, redirected to dashboard

### Test 3: 2FA Verification Flow
**Goal**: Test 2FA verification during login

1. **Logout** and **login again**
2. **Expected**: After OAuth, 2FA Verification Modal appears
3. **Enter 6-digit code** from authenticator app
4. Click "Verify"
5. **Expected**: Modal closes, redirected to dashboard

### Test 4: Backup Code Usage
**Goal**: Test backup code functionality

1. **Logout** and **login again**
2. **Expected**: 2FA Verification Modal appears
3. Click "Backup Code" tab
4. **Enter one of your backup codes** (format: XXXX-XXXX)
5. Click "Verify"
6. **Expected**: Modal closes, redirected to dashboard
7. **Note**: This backup code is now used and cannot be reused

### Test 5: Error Handling
**Goal**: Test error scenarios

#### Invalid TOTP Code
1. Login and get to 2FA verification
2. Enter invalid code (e.g., "000000")
3. **Expected**: Error message displayed

#### Expired Setup Token
1. Start 2FA setup, get to QR code step
2. Wait 11 minutes (setup token expires in 10 minutes)
3. Try to verify code
4. **Expected**: "Invalid or expired setup token" error

#### Account Lockout
1. Login and get to 2FA verification
2. Enter wrong code 3 times in a row
3. **Expected**: "Account locked" error message

## 🔍 API Endpoint Testing

### Test Backend Endpoints Directly
```powershell
# Test 2FA status endpoint
curl -X GET "http://localhost:5000/api/2fa/status" -H "Cookie: session=your_session_cookie"

# Test setup start
curl -X POST "http://localhost:5000/api/2fa/setup/start" -H "Cookie: session=your_session_cookie"
```

## ✅ Success Criteria

### All tests should pass with:
- ✅ OAuth login flow works normally when 2FA not required
- ✅ 2FA setup modal appears when 2FA required but not enabled
- ✅ QR code generation works and can be scanned
- ✅ TOTP verification works with authenticator apps
- ✅ Backup codes can be downloaded and used
- ✅ 2FA verification modal appears on subsequent logins
- ✅ Both TOTP and backup code methods work
- ✅ Error messages display appropriately
- ✅ Account lockout works after failed attempts
- ✅ UI is responsive and user-friendly

## 🐛 Troubleshooting

### Common Issues:

#### "TOTP_ENCRYPTION_KEY not set" Error
```powershell
# Set the encryption key
$env:TOTP_ENCRYPTION_KEY = "tOt3uoWcrvYUlAtmWmqVj8lea90KSH4dmijZAl67z7E="
```

#### "2FA modals not appearing"
- Check browser console for JavaScript errors
- Verify API endpoints are responding
- Check that user has `requires_2fa = True` in database

#### "QR code not scanning"
- Ensure QR code image is displaying correctly
- Try manual entry with the secret key
- Verify authenticator app compatibility

#### "Session/Authentication issues"
- Clear browser cookies and localStorage
- Restart both frontend and backend servers
- Check that OAuth configuration is correct

## 📊 Test Results Log

Date: ___________
Tester: ___________

- [ ] Test 1: Basic Authentication
- [ ] Test 2: 2FA Setup Flow  
- [ ] Test 3: 2FA Verification Flow
- [ ] Test 4: Backup Code Usage
- [ ] Test 5: Error Handling
- [ ] API Endpoint Testing

**Overall Result**: ✅ PASS / ❌ FAIL

**Notes**: ____________________