# NetPilot backend2 ↔ Command Server Integration Plan

## Overview
This document outlines the step-by-step plan to connect `backend2` (with Google authentication and Postgres DB) to the NetPilot Command Server (running on Google Cloud, port 5000). All authentication, authorization, and validation will be performed in `backend2` before proxying requests to the Command Server.

---

## 1. Define Integration Points
- [ ] List all backend2 endpoints that require command execution on routers (e.g., network scan, block/unblock device, whitelist/blacklist, WiFi management).
- [ ] For each, specify required parameters (e.g., `routerId`, `command`, user/session info).

## 2. Security & Validation in backend2
- [ ] Ensure all requests are authenticated via Google OAuth.
- [ ] Check that the authenticated user is authorized to operate on the specified `routerId` (DB ownership check).
- [ ] Validate all incoming parameters (e.g., command strings, router IDs, device IPs).
- [ ] Ensure session or user context is included and validated.

## 3. Prepare Command Server Integration Logic
- [ ] Set Command Server URL: `http://<GCP-VM-IP>:5000/api` (replace `<GCP-VM-IP>` with actual IP).
- [ ] After all checks, use the commands_server_manager to send requests to the Command Server using the appropriate endpoint and method.
- [ ] Set reasonable timeouts for requests to the Command Server.
- [ ] Handle errors gracefully and relay meaningful messages to the frontend.

## 4. Implement Command Server Manager Functions in backend2
- [ ] For each relevant endpoint:
    - [ ] After validation, construct the request payload for the Command Server.
    - [ ] Use the commands_server_manager to POST/GET to the Command Server.
    - [ ] Parse the Command Server’s response and return it to the frontend in backend2’s standard format.

## 5. Logging & Auditing
- [ ] Log all forwarded requests and responses (user, routerId, command, timestamp).
- [ ] Log errors and failed validations for audit and debugging.

## 6. Testing
- [ ] Unit tests for validation and proxy logic.
- [ ] Integration tests with mocked Command Server responses.
- [ ] Manual tests with the real Command Server running on GCP.

## 7. Configuration
- [ ] Store the Command Server URL and port in backend2’s config/environment variables.
- [ ] Allow easy switching between local/dev/staging/prod Command Server endpoints.

## 8. Documentation
- [ ] Document which backend2 endpoints proxy to the Command Server.
- [ ] Document required request/response formats and error codes.

---

## Example Flow

1. **Frontend** sends a request (e.g., block device) to `backend2`.
2. **backend2**:
    - Authenticates user (Google OAuth).
    - Checks user owns the router (`routerId`).
    - Validates input (e.g., device IP).
    - If valid, forwards request to `http://<GCP-VM-IP>:5000/api/network/block` with required payload.
    - Receives response from Command Server.
    - Returns response to frontend.

---

## Next Steps
- [ ] Complete the checklist above, step by step, as you implement the integration. 

---

## How to Debug

### 1. **Check Command Server API Spec**
According to your `COMMANDS_SERVER_SPECIFICATION.md`, the `/api/network/scan` endpoint expects:
- `routerId` as a query parameter (which you are sending)
- Possibly also a `sessionId` (you are sending it, but the spec does not require it)

### 2. **Check Command Server Error Response**
The Command Server should return a JSON error body with a message.  
**Check the backend2 logs or add a print statement to log the full response body from the Command Server.**

### 3. **Possible Causes**
- The `routerId` is not recognized or not registered in the Port Manager.
- The Command Server expects additional parameters or a different format.
- The tunnel for the router is not active.

---

### A. **Print the Full Error Response**
Update error handling in the commands_server_manager or commands_server_service to log the error response body for debugging.

### B. **Check Command Server Logs**
If you have access to the Command Server logs, check them for more details about why the request was rejected.

### C. **Verify routerId**
- Make sure the `routerId` you are using is valid and registered with the Command Server/Port Manager.
- If you have a dashboard or API for the Port Manager, check if the router is online.

---

**Summary:**  
You are very close! The integration is working, but the Command Server is rejecting the request.  
Print/log the full error response from the Command Server to see the exact reason, and check the router/tunnel status.

Would you like help editing the proxy utility to print the error response, or do you want to check the Command Server/Port Manager status first? 

---

### 1. **Print More Details in the Manager/Service**
Let’s make sure we print everything possible from the error, including the response text and status code if available, in the commands_server_manager or commands_server_service error handling.

---

### 2. **Restart backend2 and Test Again**
- Stop and restart your backend2 server after making the change.
- Trigger the scan from the frontend.
- Check the backend2 terminal for any new output.

---

### 3. **If You Still Don’t See a JSON Error**
- The Command Server may not be returning a JSON error body, or the error is happening before a response is generated.
- In that case, you’ll need to check the Command Server logs directly (see previous instructions for SSH and log file access).

---

**Please update the error handling, restart, and try again. Paste any new output you see here!**  
This will help us get the exact reason for the 400 

---

You now have a new backend2 endpoint at:

```
GET /api/command-server/health
```

This endpoint proxies directly to the Command Server's `/health` endpoint and will let you verify basic connectivity and integration.

---

**How to test:**

1. Make sure your backend2 server is running.
2. In your browser or with curl, visit:
   ```
   http://localhost:5000/api/command-server/health
   ```
3. You should see a response like:
   ```json
   {
     "success": true,
     "data": {
       "message": "Server is healthy"
     },
     ...
   }
   ```
   or an error message if the Command Server is not reachable.

---

**Try this and let me know what response you get!**  
If this works, we can proceed to proxy the other simple endpoints (infrastructure, device-chains, etc.) in the same way. 

---

That’s a very useful discovery! If your friend was able to get a successful response from the Command Server by passing `sessionId=null` (or omitting it), it means the Command Server may accept `null` or missing values for `sessionId` (and possibly `routerId`) for the `/health` endpoint.

---

## What to Try Next

### 1. **Test With sessionId and routerId as null**

Try this URL in your browser:
```
http://34.38.207.87:5000/api/health?routerId=null&sessionId=null
```
or, if you’re using your backend2 proxy:
- Update your health check proxy to send `"routerId": None, "sessionId": None` (Python `None` will be converted to `null` in JSON/query params).

### 2. **Or, Omit the Parameters Entirely**
Try:
```
http://34.38.207.87:5000/api/health
```
and see if it works.

---

## How to Update Your Integration

Use the commands_server_manager's health_check or is_connected methods to check the Command Server health, and update error handling as needed.

---

## Next Steps

1. Update your backend2 health check proxy to use `None` for both parameters.
2. Restart backend2.
3. Test the health endpoint again from your browser:
   ```
   http://localhost:5000/api/network/command-server/health
   ```
4. Let me know if you get a successful response!

---

Would you like me to make the code change for you? 