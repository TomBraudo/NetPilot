# OAuth Fix Guide for Cloud Run Deployment

## Problem

Your OAuth flow is failing because the redirect URI is hardcoded to `localhost:5000`, but your server is running on Cloud Run at `https://netpilot-backend2-1053980213438.europe-west1.run.app`.

**Error you saw:**
```
http://localhost:5000/authorize?state=...&code=...
```

## Solution

### Step 1: Update Google Cloud Console OAuth Settings

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/
   - Navigate to: **APIs & Services** → **Credentials**

2. **Find your OAuth 2.0 Client:**
   - Client ID: `1053980213438-p4jvv47k3gmcuce206m5iv8cht0gpqhu.apps.googleusercontent.com`
   - Click the **Edit** (pencil) icon

3. **Update Authorized redirect URIs:**
   - **Current:** `http://localhost:5000/authorize`
   - **Add new:** `https://netpilot-backend2-1053980213438.europe-west1.run.app/authorize`
   - **Keep both** (for local dev and production)

4. **Update Authorized JavaScript origins:**
   - **Current:** `http://localhost:5000`
   - **Add new:** `https://netpilot-backend2-1053980213438.europe-west1.run.app`
   - **Keep both**

5. **Save Changes**

### Step 2: Redeploy Backend2 with Fix

The `auth.py` file has been updated to use dynamic redirect URIs. Redeploy:

#### Option A: Quick Redeploy (if you have gcloud CLI)

```bash
cd /path/to/NetPilot/backend2
gcloud run deploy netpilot-backend2 \
    --source . \
    --platform managed \
    --region europe-west1
```

#### Option B: GitHub Actions Deployment

```bash
# Make any small change and push
cd /path/to/NetPilot
echo "# OAuth fix deployed" >> backend2/README.md
git add -A
git commit -m "Fix OAuth redirect URI for Cloud Run"
git push origin New-Main
```

### Step 3: Update Cloud Run Environment (Important!)

You also need to update the CORS origins to allow your production URL:

```bash
gcloud run services update netpilot-backend2 \
    --region europe-west1 \
    --set-env-vars="CORS_ORIGINS=https://netpilot-backend2-1053980213438.europe-west1.run.app,http://localhost:5173,http://localhost:3000"
```

## Testing the Fix

### 1. Test OAuth Flow

1. **Open browser:** `https://netpilot-backend2-1053980213438.europe-west1.run.app/login`
2. **Should redirect to Google OAuth**
3. **After authorization, should redirect back to:** `https://netpilot-backend2-1053980213438.europe-west1.run.app/authorize`
4. **No more localhost errors!**

### 2. Extract Session Cookie

1. **Complete OAuth flow**
2. **Open Dev Tools (F12)**
3. **Go to Application → Cookies**
4. **Copy the `session` cookie value**

### 3. Test API with Postman

Use the session cookie in Postman requests as described in the Postman guide.

## Alternative: Temporary Test Endpoint (Quick Testing)

If you want to test the APIs immediately without fixing OAuth, we can create a temporary development endpoint:

### Add Temporary Test User Endpoint

Add this to your `auth.py` file (DEVELOPMENT ONLY):

```python
@auth_bp.route('/dev/login/<user_email>')
def dev_login(user_email):
    """DEVELOPMENT ONLY: Create test session"""
    from flask import current_app
    
    # Only allow in development or for testing
    if not current_app.config.get('FLASK_ENV') == 'development':
        return "Not available in production", 403
    
    # Create fake session
    session['user_id'] = f"test-user-{user_email.replace('@', '-').replace('.', '-')}"
    session['user'] = {
        'userinfo': {
            'email': user_email,
            'name': f"Test User ({user_email})",
            'picture': 'https://via.placeholder.com/150',
            'sub': session['user_id']
        }
    }
    session.permanent = True
    
    return f"Test session created for {user_email}. Session ID: {session['user_id']}"
```

### Use the Test Endpoint

1. **Create test session:**
   ```
   GET https://netpilot-backend2-1053980213438.europe-west1.run.app/dev/login/test@example.com
   ```

2. **Extract session cookie from browser dev tools**

3. **Use in Postman requests**

## Verification Commands

### Check OAuth Configuration
```bash
# Test login endpoint
curl -I "https://netpilot-backend2-1053980213438.europe-west1.run.app/login"

# Should return 302 redirect to Google OAuth
```

### Check Service Configuration
```bash
# View current environment variables
gcloud run services describe netpilot-backend2 \
    --region europe-west1 \
    --format="export" | grep -E "(CORS_ORIGINS|GOOGLE_CLIENT_ID)"
```

### Test Session After Fix
```bash
# After getting session cookie from browser
curl -X GET "https://netpilot-backend2-1053980213438.europe-west1.run.app/me" \
     -H "Cookie: session=YOUR_SESSION_COOKIE_HERE" \
     -v
```

## Summary

1. ✅ **Update Google OAuth settings** to include Cloud Run URL
2. ✅ **Redeploy backend2** with the fixed auth.py
3. ✅ **Update CORS_ORIGINS** environment variable
4. ✅ **Test OAuth flow** in browser
5. ✅ **Extract session cookie** for Postman testing

After these fixes, your OAuth flow will work correctly with the production Cloud Run deployment!
