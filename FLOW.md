# Scan API Call Flow in Backend2

This document describes the complete flow for the scan API call in the backend2 system, from the API endpoint to the commands server black box.

## Overview

The scan API call follows a layered architecture through backend2, with clear separation of concerns at each level. The commands server at `http://34.38.207.87:5000` serves as the black box cutoff point.

## Complete Flow

### 0. **Application Setup** (Runs for ALL requests)
- **File**: `backend2/server.py`
- **Hook**: `@app.before_request`
- **Actions**:
  - Creates database session: `g.db_session = db.get_session()`
  - Sets user context: `g.user_id = flask_session.get('user_id')`
- **Purpose**: Provides database access and user authentication for all API calls
- **Context Available**: `g.db_session`, `g.user_id`

### 1. **API Endpoint Entry Point**
- **File**: `backend2/endpoints/api.py`
- **Route**: `GET /api/network/scan`
- **Function**: `scan_router()`
- **Decorator**: `@router_context_required`
- **Context Available**: `g.db_session`, `g.user_id` (from step 0)
- **Action**: Calls `scan_network_via_router(g.router_id)`

### 2. **Middleware Processing**
- **File**: `backend2/utils/middleware.py`
- **Function**: `router_context_required`
- **Actions**:
  - Extracts `sessionId` and `routerId` from query params or JSON body
  - Stores them in Flask's `g` object (`g.session_id`, `g.router_id`)
  - Validates both parameters are present
  - Returns error if missing
- **Context Available**: `g.db_session`, `g.user_id`, `g.session_id`, `g.router_id`

### 3. **Service Layer - Business Logic**
- **File**: `backend2/services/network_service.py`
- **Function**: `scan_network_via_router(router_id)`
- **Actions**:
  - Calls `commands_server_manager.execute_router_command()`
  - Parameters:
    - `router_id`: from function parameter
    - `session_id`: "dummy-session-id" (hardcoded - could be enhanced to use `g.user_id`)
    - `endpoint`: "/network/scan"
    - `method`: "GET"

### 4. **Manager Layer - Connection Management**
- **File**: `backend2/managers/commands_server_manager.py`
- **Function**: `CommandsServerManager.execute_router_command()`
- **Actions**:
  - Validates `router_id` and `session_id` are provided
  - Checks commands server connectivity via `is_connected()`
  - Performs health checks with 30-second caching
  - Calls `send_direct_command()` with endpoint details

### 5. **Manager Layer - Direct Command**
- **File**: `backend2/managers/commands_server_manager.py`
- **Function**: `CommandsServerManager.send_direct_command()`
- **Actions**:
  - Validates commands server is connected
  - Calls `service._make_request()` with method, endpoint, payload, params

### 6. **Service Layer - HTTP Communication**
- **File**: `backend2/services/commands_server_service.py`
- **Function**: `CommandsServerService._make_request()`
- **Actions**:
  - Constructs full URL: `http://34.38.207.87:5000{endpoint}`
  - Makes HTTP request using requests.Session
  - Handles connection errors, timeouts, HTTP errors (status >= 400)
  - Calls `unpack_commands_server_response()` to process response
  - Returns tuple of (response_data, error_message)

### 7. **Commands Server (Black Box)**
- **URL**: `http://34.38.207.87:5000`
- **Endpoint**: `/network/scan`
- **Method**: GET
- **Status**: Working black box (cutoff point as requested)
- **Purpose**: Performs actual router network scanning operations

### 8. **Response Processing**
- **File**: `backend2/utils/response_unpack.py`
- **Function**: `unpack_commands_server_response()`
- **Actions**:
  - Expects standardized response format with 'success', 'data', 'error', 'metadata'
  - On success: extracts and returns the 'data' field
  - On failure: extracts error message and code from 'error' field
  - Returns tuple of (data, error_message)

### 9. **Response Building**
- **File**: `backend2/utils/response_helpers.py`
- **Functions**: `build_success_response()` or `build_error_response()`
- **Actions**:
  - Creates standardized JSON response format
  - Includes metadata: sessionId, routerId, timestamp, executionTime
  - Returns Flask jsonify object with appropriate status code

### 10. **Final API Response**
- Returns to frontend/client with standardized response format
- Includes success/error status, data, and metadata

### 11. **Application Cleanup** (Runs for ALL requests)
- **File**: `backend2/server.py`
- **Hook**: `@app.teardown_request`
- **Actions**:
  - Rolls back database session if there's an exception
  - Closes database session: `g.db_session.close()`
- **Purpose**: Ensures proper database session cleanup

## Key Configuration

- **Commands Server URL**: `http://34.38.207.87:5000`
- **Health Check Interval**: 30 seconds
- **Request Timeout**: 30 seconds (configurable)
- **Session Management**: Currently using "dummy-session-id" (TODO: implement real session management)

## Context Flow

```
Request → Application Setup → API Endpoint → Middleware → Service → Manager → HTTP → Commands Server → Response Processing → Response Building → Final Response → Application Cleanup
```

## Key Relationships

1. **Database Session**: Available as `g.db_session` for all API calls (though scan API doesn't directly use it, other endpoints in the same file do)

2. **User Context**: Available as `g.user_id` for authentication/authorization (could enhance scan API to use real session management instead of "dummy-session-id")

3. **Session Management**: The scan API could be enhanced to use the user context for proper session management instead of the hardcoded "dummy-session-id"

4. **Error Handling**: If any step fails, the teardown hook ensures database sessions are properly cleaned up

## Architecture Benefits

- **Clear Separation**: Each layer has a specific responsibility
- **Error Handling**: Comprehensive error handling at each level
- **Session Management**: Application-level hooks ensure proper resource management
- **Extensibility**: Easy to add new endpoints following the same pattern
- **Black Box Integration**: Commands server is treated as a working external service

## Future Enhancements

1. **Real Session Management**: Replace "dummy-session-id" with proper session management using `g.user_id`
2. **Database Integration**: Use `g.db_session` for logging scan results or user preferences
3. **Authentication**: Leverage `g.user_id` for proper user authentication and authorization
4. **Caching**: Add caching layer for frequently scanned networks
5. **Monitoring**: Add metrics and monitoring at each layer 