# Postman Testing Guide for NetPilot Backend2 (Production)

## Overview

This guide shows how to test your deployed NetPilot backend2 server using Postman without needing an HTTPS frontend. Since your server is deployed in production mode on Cloud Run, we'll simulate the complete OAuth flow and API testing.

**Deployed Server URL:** `https://netpilot-backend2-1053980213438.europe-west1.run.app`

## Prerequisites

- Postman installed (Desktop version recommended)
- Your deployed backend2 server running on Cloud Run
- Google OAuth credentials configured

## Part 1: Understanding the Authentication Flow

Your backend2 uses Google OAuth with session-based authentication:

1. **OAuth Flow:** User → `/login` → Google → `/authorize` → Session created
2. **Session Storage:** Flask session with `user_id` stored
3. **API Protection:** All API endpoints require `@router_context_required` decorator
4. **Required Parameters:** `user_id` (from session) + `routerId` (from client)

## Part 2: Fix OAuth Configuration First!

**⚠️ IMPORTANT:** Before testing, you need to fix the OAuth redirect URI issue.

### Quick Fix Required

The OAuth redirect is currently hardcoded to localhost. Here's what you need to do:

#### Step 1: Update Google OAuth Settings

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/
   - Navigate to: **APIs & Services** → **Credentials**

2. **Edit OAuth 2.0 Client:**
   - Find your client ID: `1053980213438-p4jvv47k3gmcuce206m5iv8cht0gpqhu.apps.googleusercontent.com`
   - Click **Edit** (pencil icon)

3. **Update Authorized redirect URIs:**
   - **Add:** `https://netpilot-backend2-1053980213438.europe-west1.run.app/authorize`
   - **Keep existing:** `http://localhost:5000/authorize` (for local development)

4. **Update Authorized JavaScript origins:**
   - **Add:** `https://netpilot-backend2-1053980213438.europe-west1.run.app`
   - **Keep existing:** `http://localhost:5000` (for local development)

5. **Save changes**

#### Step 2: Redeploy with Updated Code

The auth.py file has been updated to use dynamic redirect URIs, but you need to redeploy:

```bash
# Option 1: Quick redeploy (if you have gcloud setup)
cd NetPilot/backend2
gcloud run deploy netpilot-backend2 \
    --source . \
    --platform managed \
    --region europe-west1

# Option 2: Trigger GitHub Actions
# Just push any small change to the New-Main branch
git add -A
git commit -m "Fix OAuth redirect URI for production"
git push origin New-Main
```

### Step 3: Test the Fixed Auth Flow

1. **Open Browser** and navigate to:
   ```
   https://netpilot-backend2-1053980213438.europe-west1.run.app/login
   ```

2. **Complete OAuth Flow:**
   - Should now redirect properly to the Cloud Run URL
   - No more localhost errors!

3. **Extract Session Cookie** (as before)

## Part 3: Testing Without Full OAuth (Alternative Method)

If you want to test immediately without waiting for the OAuth fix:

### Step 1: Create a Test Session (TEMPORARY SOLUTION)

I've added a temporary development endpoint to create test sessions:

```
GET https://netpilot-backend2-1053980213438.europe-west1.run.app/dev/create-session/your-test-id
```

**Example:**
```bash
curl "https://netpilot-backend2-1053980213438.europe-west1.run.app/dev/create-session/tom123"
```

This will:
1. Create a test session with user ID `test-tom123`
2. Set session cookies automatically
3. Return instructions for using the session

### Step 2: Extract Session Cookie from Test Endpoint

1. **Open browser** and visit:
   ```
   https://netpilot-backend2-1053980213438.europe-west1.run.app/dev/create-session/tom123
   ```

2. **Session is created automatically**

3. **Extract session cookie:**
   - Open Dev Tools (F12)
   - Go to **Application** → **Cookies**
   - Copy the `session` cookie value

4. **Verify it works:**
   ```bash
   curl -X GET "https://netpilot-backend2-1053980213438.europe-west1.run.app/me" \
        -H "Cookie: session=YOUR_SESSION_COOKIE_HERE"
   ```

   Expected response:
   ```json
   {
     "name": "Testtom123",
     "email": "tom123@test.com", 
     "picture": "https://via.placeholder.com/150"
   }
   ```

**⚠️ Note:** This is a temporary solution for testing. Remove this endpoint before production use.

### Step 1: Create a Test User Session

**Option A: Use the Manual Session Creation Endpoint**

First, let's check if we can create a test endpoint for authentication bypass:

```bash
# Test if server has a dev mode endpoint
curl -X GET "https://netpilot-backend2-1053980213438.europe-west1.run.app/health"
```

**Option B: Extract Session from Browser OAuth Flow**

1. Open browser and go to: `https://netpilot-backend2-1053980213438.europe-west1.run.app/login`
2. Complete Google OAuth flow
3. Open browser dev tools → Application → Cookies
4. Copy the `session` cookie value
5. Use this cookie in Postman

## Part 4: Postman Collection Setup

### Collection Variables

Create a new Postman collection with these variables:

| Variable | Value |
|----------|-------|
| `base_url` | `https://netpilot-backend2-1053980213438.europe-west1.run.app` |
| `router_id` | `test-router-123` (or your actual router ID) |
| `session_cookie` | `(extracted from browser)` |

### Environment Setup

1. **Create New Environment:** "NetPilot Production"
2. **Add Variables:**
   - `base_url`: `https://netpilot-backend2-1053980213438.europe-west1.run.app`
   - `router_id`: `your-router-id-here`
   - `session_cookie`: `your-session-cookie-here`

## Part 4: Postman Requests

### 1. Health Check (No Authentication Required)

```
GET {{base_url}}/health
```

**Headers:** None required

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-01T..."
}
```

### 2. Authentication Test

```
GET {{base_url}}/me
```

**Headers:**
```
Cookie: session={{session_cookie}}
```

**Expected Response:**
```json
{
  "name": "Your Name",
  "email": "your@email.com",
  "picture": "https://..."
}
```

### 3. Whitelist Operations

#### Get Whitelist Devices
```
GET {{base_url}}/api/whitelist/devices?routerId={{router_id}}
```

**Headers:**
```
Cookie: session={{session_cookie}}
Content-Type: application/json
```

#### Add Device to Whitelist
```
POST {{base_url}}/api/whitelist/add?routerId={{router_id}}
```

**Headers:**
```
Cookie: session={{session_cookie}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "ip": "192.168.1.100",
  "name": "Test Device",
  "description": "Testing whitelist functionality"
}
```

#### Remove Device from Whitelist
```
POST {{base_url}}/api/whitelist/remove?routerId={{router_id}}
```

**Headers:**
```
Cookie: session={{session_cookie}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "ip": "192.168.1.100"
}
```

#### Set Whitelist Rate Limit
```
POST {{base_url}}/api/whitelist/limit-rate?routerId={{router_id}}
```

**Headers:**
```
Cookie: session={{session_cookie}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "rate": "50"
}
```

#### Get Whitelist Rate Limit
```
GET {{base_url}}/api/whitelist/limit-rate?routerId={{router_id}}
```

**Headers:**
```
Cookie: session={{session_cookie}}
```

#### Activate Whitelist Mode
```
POST {{base_url}}/api/whitelist/mode?routerId={{router_id}}
```

**Headers:**
```
Cookie: session={{session_cookie}}
Content-Type: application/json
```

#### Deactivate Whitelist Mode
```
DELETE {{base_url}}/api/whitelist/mode?routerId={{router_id}}
```

**Headers:**
```
Cookie: session={{session_cookie}}
```

#### Get Whitelist Mode Status
```
GET {{base_url}}/api/whitelist/mode?routerId={{router_id}}
```

**Headers:**
```
Cookie: session={{session_cookie}}
```

### 4. Blacklist Operations

#### Get Blacklist Devices
```
GET {{base_url}}/api/blacklist/devices?routerId={{router_id}}
```

**Headers:**
```
Cookie: session={{session_cookie}}
```

#### Add Device to Blacklist
```
POST {{base_url}}/api/blacklist/add?routerId={{router_id}}
```

**Headers:**
```
Cookie: session={{session_cookie}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "ip": "192.168.1.200",
  "name": "Blocked Device",
  "description": "Testing blacklist functionality"
}
```

#### Remove Device from Blacklist
```
POST {{base_url}}/api/blacklist/remove?routerId={{router_id}}
```

**Headers:**
```
Cookie: session={{session_cookie}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "ip": "192.168.1.200"
}
```

#### Activate/Deactivate Blacklist Mode
```
POST {{base_url}}/api/blacklist/mode?routerId={{router_id}}
DELETE {{base_url}}/api/blacklist/mode?routerId={{router_id}}
GET {{base_url}}/api/blacklist/mode?routerId={{router_id}}
```

### 5. Network Operations

#### Get Network Devices
```
GET {{base_url}}/api/network/devices?routerId={{router_id}}
```

**Headers:**
```
Cookie: session={{session_cookie}}
```

### 6. Session Management

#### Start Session
```
POST {{base_url}}/api/session/start
```

**Headers:**
```
Cookie: session={{session_cookie}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "routerId": "{{router_id}}"
}
```

#### End Session
```
POST {{base_url}}/api/session/end
```

**Headers:**
```
Cookie: session={{session_cookie}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "routerId": "{{router_id}}"
}
```

## Part 5: Getting Session Cookie from Browser

### Method 1: Browser Authentication Flow

1. **Open Browser** and navigate to:
   ```
   https://netpilot-backend2-1053980213438.europe-west1.run.app/login
   ```

2. **Complete OAuth Flow:**
   - Click "Log in with Google"
   - Authorize the application
   - You'll be redirected (might show an error page, but session is created)

3. **Extract Session Cookie:**
   - Open Developer Tools (F12)
   - Go to **Application** tab → **Cookies**
   - Find `https://netpilot-backend2-1053980213438.europe-west1.run.app`
   - Copy the `session` cookie value

4. **Test Session:**
   ```bash
   curl -X GET "https://netpilot-backend2-1053980213438.europe-west1.run.app/me" \
        -H "Cookie: session=YOUR_SESSION_COOKIE_HERE"
   ```

### Method 2: Using Postman Interceptor

1. **Install Postman Interceptor** browser extension
2. **Enable Interceptor** in Postman
3. **Browse to** your backend URL and complete OAuth
4. **Cookies automatically sync** to Postman

## Part 6: Expected Responses

### Success Response Format
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2025-08-01T...",
  "execution_time": 0.123
}
```

### Error Response Format
```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-08-01T...",
  "execution_time": 0.045
}
```

### Common Error Codes
- `UNAUTHENTICATED` (401): No valid session
- `BAD_REQUEST` (400): Missing routerId or invalid data
- `COMMAND_FAILED` (500): Router command execution failed

## Part 7: Advanced Testing Scenarios

### Test Authentication Edge Cases

1. **No Session Cookie:**
   ```
   GET {{base_url}}/api/whitelist/devices?routerId={{router_id}}
   ```
   Expected: 401 Unauthenticated

2. **Missing Router ID:**
   ```
   GET {{base_url}}/api/whitelist/devices
   ```
   Expected: 400 Bad Request

3. **Invalid Session:**
   ```
   GET {{base_url}}/api/whitelist/devices?routerId={{router_id}}
   Cookie: session=invalid-session-value
   ```
   Expected: 401 Unauthenticated

### Test API Data Validation

1. **Invalid IP Address:**
   ```json
   {
     "ip": "not-an-ip",
     "name": "Test Device"
   }
   ```
   Expected: 400 Bad Request

2. **Missing Required Fields:**
   ```json
   {
     "name": "Test Device"
   }
   ```
   Expected: 400 Bad Request (missing IP)

## Part 8: Troubleshooting

### Common Issues

1. **CORS Errors:**
   - Issue: Browser blocks requests
   - Solution: Use Postman desktop app, not web version

2. **Session Expires:**
   - Issue: 401 errors after some time
   - Solution: Re-authenticate in browser and get new session cookie

3. **Missing HTTPS:**
   - Issue: Mixed content warnings
   - Solution: Always use HTTPS URLs for production

4. **Router ID Confusion:**
   - Issue: Which router ID to use?
   - Solution: Use any valid UUID format for testing, e.g., `test-router-123`

### Debug Commands

**Check Service Status:**
```bash
curl -X GET "https://netpilot-backend2-1053980213438.europe-west1.run.app/health"
```

**Verify Session:**
```bash
curl -X GET "https://netpilot-backend2-1053980213438.europe-west1.run.app/me" \
     -H "Cookie: session=YOUR_SESSION_COOKIE" -v
```

**View Server Logs:**
```bash
gcloud logs tail --follow --format="value(textPayload)" \
  --filter="resource.type=cloud_run_revision AND resource.labels.service_name=netpilot-backend2"
```

## Part 9: Sample Postman Collection JSON

Here's a complete Postman collection you can import:

```json
{
  "info": {
    "name": "NetPilot Backend2 Production Tests",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "https://netpilot-backend2-1053980213438.europe-west1.run.app"
    },
    {
      "key": "router_id",
      "value": "test-router-123"
    },
    {
      "key": "session_cookie",
      "value": "your-session-cookie-here"
    }
  ],
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": "{{base_url}}/health"
      }
    },
    {
      "name": "Get User Info",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Cookie",
            "value": "session={{session_cookie}}"
          }
        ],
        "url": "{{base_url}}/me"
      }
    },
    {
      "name": "Get Whitelist Devices",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Cookie",
            "value": "session={{session_cookie}}"
          }
        ],
        "url": "{{base_url}}/api/whitelist/devices?routerId={{router_id}}"
      }
    },
    {
      "name": "Add to Whitelist",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Cookie",
            "value": "session={{session_cookie}}"
          },
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"ip\": \"192.168.1.100\", \"name\": \"Test Device\", \"description\": \"Postman test\"}"
        },
        "url": "{{base_url}}/api/whitelist/add?routerId={{router_id}}"
      }
    }
  ]
}
```

## Summary

With this guide, you can:

1. ✅ **Test all API endpoints** without needing HTTPS frontend
2. ✅ **Simulate authentication** using browser-extracted session cookies
3. ✅ **Validate all CRUD operations** for whitelist/blacklist
4. ✅ **Debug issues** with detailed error responses
5. ✅ **Verify production deployment** works correctly

The key is using the session cookie from a browser OAuth flow to authenticate your Postman requests against the production Cloud Run deployment.
