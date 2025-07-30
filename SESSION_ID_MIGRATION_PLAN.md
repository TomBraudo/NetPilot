# Session ID Migration Plan: From Dummy to User-Based Sessions

## Executive Summary

This document outlines the plan to migrate backend2's session management from using a hardcoded "dummy-session-id" to using authenticated user IDs (`g.user_id`) as the session identifier for commands server communication.

## ⚠️ Plan Corrections Applied

**Critical dependency issues were identified and corrected**:

1. **Phase Order Fixed**: Moved middleware enhancement to Phase 1 (was Phase 2) because all other phases depend on middleware setting correct authentication and session context.

2. **Architectural Consistency**: Services now use `g.session_id` (set by middleware) instead of directly accessing `g.user_id` for better separation of concerns.

3. **Dependency Chain**: Established clear critical path: Middleware → Services → Endpoints → Frontend.

**Result**: Migration now follows proper dependency order and reduces risk of breaking changes during transition.

## Current State Analysis

### Current Session Architecture

Backend2 currently has **two separate session concepts**:

1. **User Authentication Session**: Managed by Flask session, stores `user_id` from Google OAuth
2. **Router Command Session**: Used for commands server communication, currently hardcoded as "dummy-session-id"

### Current Flow Issues

1. **Hardcoded Session ID**: `network_service.py` uses `"dummy-session-id"` instead of real user context
2. **Disconnected Sessions**: User authentication session is separate from router command session
3. **No User Context in Commands**: Commands server doesn't know which user is making requests
4. **Inconsistent Session Management**: Middleware extracts `sessionId` from client but service layer ignores it

### Files Currently Using session_id

| File | Usage | Current Behavior |
|------|-------|------------------|
| `services/network_service.py` | Hardcoded "dummy-session-id" | **NEEDS CHANGE** |
| `utils/middleware.py` | Extracts sessionId from request | Keep but modify validation |
| `managers/commands_server_manager.py` | Validates session_id parameter | Keep validation |
| `utils/response_helpers.py` | Includes session_id in metadata | Keep but ensure correct value |
| `endpoints/api.py` | Session management endpoints | **NEEDS CHANGE** |
| `services/session_service.py` | Session start/end operations | **NEEDS CHANGE** |

## Migration Strategy

### Phase 1: Middleware Enhancement (FOUNDATION)

**Priority**: CRITICAL - Must be done first as all other phases depend on this
**Rationale**: Middleware sets up authentication validation and session context that services depend on

#### 1.1 Enhanced Router Context Middleware
**File**: `backend2/utils/middleware.py`
**Current Issues**:
- Requires `sessionId` from client but doesn't validate it against user context
- No authentication validation

**New Approach**:
```python
def router_context_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        # 1. Validate user authentication first
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return build_error_response("User authentication required", 401, "UNAUTHENTICATED", start_time)
        
        # 2. Extract routerId (still required from client)
        router_id = request.args.get('routerId') or (request.json or {}).get('routerId')
        if not router_id:
            return build_error_response("routerId is required", 400, "BAD_REQUEST", start_time)
        
        # 3. Use user_id as session_id (no longer extract from client)
        g.session_id = str(user_id)  # User ID becomes session ID
        g.router_id = router_id
        
        # 4. Optional: Validate router belongs to user (future enhancement)
        # validate_user_router_access(user_id, router_id)
        
        return f(*args, **kwargs)
    return decorated_function
```

### Phase 2: Core Service Changes

**Priority**: HIGH - Depends on Phase 1 middleware setting correct session context
**Rationale**: Services use `g.session_id` which middleware now populates with user ID

#### 2.1 Update Network Service
**File**: `backend2/services/network_service.py`
**Current Code**:
```python
response, error = commands_server_manager.execute_router_command(
    router_id=router_id,
    session_id="dummy-session-id",  # TODO: Replace with real session management
    endpoint="/network/scan",
    method="GET"
)
```

**New Code**:
```python
from flask import g

response, error = commands_server_manager.execute_router_command(
    router_id=router_id,
    session_id=g.session_id,  # Now contains authenticated user ID (set by middleware)
    endpoint="/network/scan",
    method="GET"
)
```

#### 2.2 Update Session Service
**File**: `backend2/services/session_service.py`
**Changes**:
- Modify `start_session()` to use `g.session_id` (which contains user_id)
- Remove UUID generation for session_id
- Use user_id as the session identifier

### Phase 3: Session Management Endpoints

**Priority**: MEDIUM - Depends on Phase 1-2 for middleware and service updates
**Rationale**: Session endpoints need authentication validation and consistent session handling

#### 3.1 Update Session Endpoints
**File**: `backend2/endpoints/api.py`
**Changes Required**:

1. **Session Start Endpoint**:
```python
@network_bp.route("/session/start", methods=["POST"])
@login_required  # Add authentication requirement
def start_session():
    # Note: g.user_id set by before_request, g.session_id set by middleware if needed
    user_id = g.user_id  # Get from authenticated user
    data = request.get_json()
    router_id = data.get("routerId")
    restart = data.get("restart", False)
    
    # Use user_id as session_id (consistent with middleware approach)
    payload = {
        "sessionId": str(user_id),
        "routerId": router_id,
        "restart": restart
    }
    # ... rest of implementation
```

2. **Session End/Refresh Endpoints**: Similar pattern - use `str(g.user_id)` for sessionId

### Phase 4: Frontend Changes

**Priority**: LOW - Should be done after all backend changes are complete and tested
**Rationale**: Frontend changes depend on stable backend implementation

#### 4.1 Frontend Changes Required
**Current**: Frontend sends `sessionId` and `routerId`
**New**: Frontend only sends `routerId` (user authentication provides session context)

**API Call Changes**:
```javascript
// OLD
const response = await fetch('/api/network/scan?sessionId=abc123&routerId=router456');

// NEW  
const response = await fetch('/api/network/scan?routerId=router456');
// sessionId automatically derived from authenticated user
```

**Transition Strategy**: Backend should handle both approaches during migration period for safety.

### Phase 5: Response and Metadata

**Priority**: NONE - No changes needed
**Rationale**: Current implementation already uses `g.get("session_id")` correctly

#### 5.1 Response Helpers
**File**: `backend2/utils/response_helpers.py`
**Current**: Already correctly uses `g.get("session_id")`
**Result**: No changes needed, will automatically use new user-based session_id

## Implementation Details

### Authentication Flow Integration

```
1. User authenticates via Google OAuth → user_id in Flask session
2. Flask before_request sets g.user_id from session
3. Router context middleware uses g.user_id as session_id
4. Commands server receives user_id as session identifier
5. All subsequent commands use user_id for session tracking
```

### Database Considerations

**Current**: No session tracking in database
**Future Enhancement**: Could add session logging with user_id for audit trails

### Error Handling

#### New Error Scenarios:
1. **Unauthenticated User**: Return 401 with clear message
2. **Invalid User ID**: Handle cases where user_id is malformed
3. **User-Router Access**: Future validation of router ownership

#### Error Response Examples:
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHENTICATED",
    "message": "User authentication required for router operations"
  },
  "metadata": {
    "sessionId": null,
    "routerId": "router123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Benefits

### 1. Security Improvements
- Real user context in commands server
- Prevents session hijacking (sessions tied to authenticated users)
- Audit trail capability (commands linked to specific users)

### 2. Simplified Architecture
- Single session concept (user-based)
- No more dummy sessions
- Consistent session management

### 3. Future Enhancements Enabled
- User-specific router access control
- Per-user session logging
- Multi-tenant router management

## Migration Timeline

| Phase | Tasks | Priority | Estimated Effort | Dependencies |
|-------|-------|----------|------------------|--------------|
| 1 | **Middleware enhancement** | CRITICAL | 2-3 hours | None (Foundation) |
| 2 | **Core service changes** | HIGH | 2-3 hours | Phase 1 |
| 3 | **Session endpoints** | MEDIUM | 2-3 hours | Phase 1-2 |
| 4 | **Frontend updates** | LOW | 1-2 hours | Phase 1-3 (backend stable) |
| 5 | **Testing & documentation** | HIGH | 2-3 hours | All phases |

**Total Estimated Effort**: 9-14 hours

**Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4

## Testing Strategy

### 1. Unit Tests
- Test middleware with authenticated/unauthenticated users
- Test service layer with real user_ids
- Test session management endpoints

### 2. Integration Tests
- Full flow: authentication → router operation → commands server
- Error scenarios (unauthenticated, invalid router, etc.)

### 3. Manual Testing
- Login with Google OAuth
- Perform network scan with authenticated user
- Verify commands server receives correct user_id as session_id

## Rollback Plan

### Quick Rollback
If issues arise, can temporarily revert `network_service.py` to hardcoded session:
```python
session_id = "dummy-session-id"  # Temporary rollback
```

### Full Rollback
- Revert all middleware changes
- Restore original session endpoint implementations
- Update frontend to send sessionId again

## Future Enhancements

### 1. User-Router Access Control
```python
def validate_user_router_access(user_id: str, router_id: str) -> bool:
    """Validate that user has access to the specified router"""
    session = g.db_session
    user_router = session.query(UserRouter).filter_by(
        user_id=user_id, 
        router_id=router_id, 
        is_active=True
    ).first()
    return user_router is not None
```

### 2. Session Audit Logging
```python
class SessionLog(Base):
    __tablename__ = 'session_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    router_id = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
```

### 3. Session Timeout Management
- Implement user-specific session timeouts
- Automatic session cleanup based on user activity

## Conclusion

This migration will transform backend2 from using dummy sessions to a proper user-authenticated session management system. The changes are mostly contained within the service layer and middleware, with minimal impact on the commands server (black box) and manageable frontend changes.

The new architecture provides better security, clearer audit trails, and enables future multi-tenant capabilities while maintaining compatibility with the existing commands server interface. 
