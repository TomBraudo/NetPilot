# NetPilot Commands Server Transformation Plan

## Executive Summary

This plan details the transformation of the existing Flask backend from a localhost application to a **Commands Server** that runs on the VM (34.38.207.87) and routes SSH commands to routers via established tunnels using session-based connection management with routerId lookup through the port-manager.

## Current Architecture Analysis

### ✅ What We Have (After Cleanup)
- **Cleaned Flask Backend**: ✅ Database dependencies removed, local-only services eliminated
- **SSH-Focused Service Layer**: ✅ Only SSH-based NetPilot functionality remains (blocking, scanning, wifi management, etc.)
- **Simplified SSH Execution**: ✅ Uses streamlined `ssh_manager.execute_command()` with minimal validation
- **Port Manager**: Running on VM with router credential storage and port allocation
- **Agent Tunnel System**: Establishes reverse SSH tunnels with unique routerIds
- **Lean Dependencies**: ✅ 50% fewer dependencies, only Flask, paramiko, requests for SSH operations
- **In-Memory Storage**: ✅ All services use in-memory dictionaries instead of database storage

### 🎯 Transformation Goal
Transform the cleaned backend into a **Commands Server** where:
- API calls include `sessionId` and `routerId` parameters
- Server maintains session-based connection pools for multi-user support
- Each user session can manage multiple router connections simultaneously
- Automatic connection lifecycle management with configurable timeouts
- Server queries port-manager to get tunnel port and credentials for each routerId
- SSH commands are executed via persistent paramiko connections through tunnel ports
- All existing business logic and service structure remains unchanged

### ✅ Completed Cleanup Work

#### Phase 0: Backend Cleanup (COMPLETED ✅)
- ✅ **Database Infrastructure Removal**
  - Removed entire backend/db/ directory
  - Removed database endpoints (db.py)
  - Updated server.py: removed database initialization, imports, cleanup functions, and blueprint registrations

- ✅ **Local-Only Services Removal**
  - Deleted: network_scanner.py, speed_test.py, mode_state_service.py, config_service.py, subnets_manager.py
  - Deleted: endpoints/config.py
  - Kept: SSH-based services and venv/scripts for local testing

- ✅ **SSH Services Database Dependency Cleanup**
  - **block_ip.py**: Replaced database device lookup with router ARP table lookup via SSH
  - **reset_rules.py**: Removed database imports, simplified to focus on SSH rule reset operations
  - **router_scanner.py**: Removed device registration calls
  - **whitelist/blacklist services**: Replaced database storage with in-memory dictionaries
  - **bandwidth_mode.py**: Simplified to use in-memory state management

- ✅ **Development Files Cleanup**
  - Removed: setup_openwrt.py/sh, server.spec, build directory, __pycache__ directories
  - Updated requirements.txt: Removed scapy, netifaces, speedtest-cli, tinydb, pyinstaller dependencies

- ✅ **Validation Simplification** (Based on upstream authorization assumptions)
  - Removed duplicate checking logic from whitelist/blacklist services
  - Removed existence checking and complex error handling
  - Simplified to: add to storage → apply SSH rules → return success
  - Streamlined all services assuming upstream validation

## Architecture Changes

### Before (Original)
```
API Call → Endpoint → Service → Database + SSH → Direct Router SSH
```

### After Cleanup (Current State)
```
API Call → Endpoint → Service → In-Memory Storage + SSH → Direct Router SSH
```

### Target (Session-Based Commands Server)
```
User Login → Session Start → API Call (+ sessionId + routerId) → Endpoint → 
Service → RouterConnectionManager → Session-Aware Connection Pool → 
Port Manager Lookup → Persistent Paramiko via Tunnel → Router SSH (port 22)
```

## Connection Management Architecture

### Session-Based Connection Pool Design

The commands server maintains an **in-memory, session-aware connection pool** that provides:

**Multi-User Isolation**: Each user session gets completely isolated connection management
**Multi-Router Support**: Each session can maintain connections to multiple routers simultaneously  
**Automatic Lifecycle Management**: Connections are created on-demand, reused for performance, and cleaned up automatically

### Connection Pool Structure

**Memory-Based Storage**: No local database required - all connection state maintained in memory with structured cleanup
**Thread-Safe Operations**: Connection pool operations are protected with threading locks for concurrent access
**Hierarchical Organization**: `{session_id: {router_id: connection_data}}`

### Connection Lifecycle Management

**Connection Creation**: 
- Triggered on first command to a router within a session
- Port-manager queried for tunnel port and credentials
- Paramiko connection established to localhost:tunnel_port
- Connection stored in session's router pool

**Connection Reuse**:
- Subsequent commands to same router reuse existing connection
- Connection health validated before each use
- Dead connections automatically detected and recreated

**Automatic Cleanup**:
- Individual router connections: Closed after 5 minutes of inactivity
- Entire sessions: Removed after 30 minutes of total inactivity
- Background cleanup thread runs continuously
- Explicit session termination on user logout

### Storage Requirements

**No Local Database Needed**: 
- All connection state maintained in memory
- Port-manager handles credential storage
- Session data ephemeral by design
- Configuration via environment variables

**Memory Footprint**:
- Each paramiko connection: ~1-2MB memory overhead
- Typical session (3 routers): ~5MB total
- 100 concurrent users: ~500MB memory usage
- Automatic cleanup prevents memory leaks

**High Availability Considerations**:
- Commands server restart clears all sessions (by design)
- Users automatically reconnect on next command
- No persistent state to backup or restore

## Transformation Plan (Updated)

## Phase 1: Core Infrastructure Setup (Week 1) - NEXT PHASE

### Step 1.1: Project Setup on VM
- [ ] **Deploy Cleaned Commands Server to VM**
  - Copy cleaned backend structure to `/opt/netpilot-commands-server`
  - Set up Python virtual environment with simplified dependencies
  - Configure proper file permissions and ownership

- [ ] **Environment Configuration**
  - Configure commands server port (3000)
  - Set port-manager integration URLs and tokens
  - Configure session timeout parameters
  - Set logging levels and file paths

### Step 1.2: RouterConnectionManager Development
- [ ] **Design Session-Based Connection Manager**
  - Implement thread-safe session management
  - Create connection pool with hierarchical structure
  - Add port-manager integration for credential lookup
  - Implement persistent paramiko connections via tunnel ports

- [ ] **Connection Lifecycle Management**
  - Implement automatic connection health monitoring
  - Add idle timeout detection and cleanup
  - Create background cleanup thread for expired sessions
  - Handle connection failures and automatic recreation

### Step 1.3: Update SSH Client Interface
- [ ] **Modify SSH Client for Session Awareness**
  - Update interface to accept sessionId and routerId parameters
  - Integrate with new RouterConnectionManager
  - Preserve existing error handling patterns

## Phase 2: API Layer Modifications (Week 1-2)

### Step 2.1: Add Session Management Endpoints
- [ ] **Create Session Management API**
  - Session start endpoint for user login integration
  - Session end endpoint for explicit logout cleanup
  - Session refresh endpoint for activity-based timeout extension
  - Session status endpoint for debugging and monitoring

### Step 2.2: Update Existing Endpoints
- [ ] **Modify All Existing Endpoints**
  - Add sessionId and routerId parameter validation
  - Update error handling for session-related failures
  - Implement session context setting for service calls
  - **Implement standardized response format** for database layer integration
  - Ensure all responses include complete metadata and structured data

- [ ] **Update Endpoint Categories**
  - Network operations: block, unblock, scan, speedtest, reset
  - WiFi management: status, enable, disable, password, SSID changes
  - Whitelist/Blacklist: add, remove, list operations
  - Configuration: router settings and status queries

### ~~Step 2.3: Remove Database Dependencies~~ ✅ COMPLETED
- ✅ **Database Initialization Disabled**
- ✅ **Mock Database Services Created** (In-memory storage implemented)

## Phase 3: Service Layer Updates (Week 2)

### Step 3.1: Update Service Dependencies
- [ ] **Ensure Session Context Propagation**
  - Verify all services receive proper session and router context
  - Test service operations with session-aware SSH manager
  - Validate that existing business logic remains unchanged

### Step 3.2: Add Router Context Validation
- [ ] **Implement Router Validation Middleware**
  - Add router availability checking before command execution
  - Implement graceful handling of inactive or unreachable routers
  - Create consistent error responses for router connection failures

## Phase 4: Testing & Validation (Week 2)

### Step 4.1: Unit Testing
- [ ] **Test RouterConnectionManager Components**
  - Session creation, management, and cleanup
  - Connection pool operations and thread safety
  - Port-manager integration and credential retrieval
  - Connection health monitoring and recovery

### Step 4.2: Integration Testing
- [ ] **Test Session-Based Operations**
  - Multi-user session isolation
  - Concurrent router operations within sessions
  - Session timeout and cleanup behavior
  - Real tunnel integration with agent connections

### Step 4.3: Performance Testing
- [ ] **Measure Session-Based Performance**
  - Connection reuse performance vs. new connections
  - Memory usage under various user loads
  - Cleanup efficiency and resource management
  - Command execution latency with session overhead

## Phase 5: Deployment & Service Management (Week 2-3)

### Step 5.1: Service Configuration
- [ ] **Create Production Service Configuration**
  - Systemd service definition for auto-start and monitoring
  - Process monitoring and restart policies
  - Log rotation and management configuration
  - Resource limits and security constraints

### Step 5.2: Monitoring & Logging
- [ ] **Implement Session Monitoring**
  - Active session count and router connection metrics
  - Connection pool utilization and cleanup statistics
  - Performance metrics for command execution
  - Error tracking and alerting for connection failures

### Step 5.3: Security Configuration
- [ ] **Configure Access Controls**
  - Firewall rules for commands server port access
  - Internal-only access restrictions
  - Secure credential handling and logging practices

## Session Management Integration

### Frontend Integration Flow
- User authentication creates unique sessionId in auth server
- Frontend calls session start endpoint with sessionId
- All router commands include sessionId and routerId parameters
- Periodic session refresh calls maintain active session status
- User logout triggers explicit session termination

### Backend Integration (Auth + DB Server)
- Login endpoint creates sessionId and starts commands server session
- Logout endpoint terminates commands server session
- Session token validation includes sessionId for commands server context
- User database stores sessionId association for audit and tracking

### Connection Lifecycle
- **Session Start**: User logs in → Backend starts session → Commands server initializes session pool
- **Active Usage**: Commands execute on persistent connections → Connections automatically refreshed on use
- **Idle Detection**: 5 minutes no activity → Individual router connections closed automatically
- **Session Timeout**: 30 minutes total inactivity → Entire session removed with all connections
- **Explicit Logout**: User logs out → All session connections immediately closed

## API Specification

### Session Management Endpoints
```
POST /api/session/start     # Body: {sessionId}
POST /api/session/end       # Body: {sessionId}  
POST /api/session/refresh   # Body: {sessionId}
```

### Commands Server Endpoints

All endpoints require `sessionId` and `routerId` parameters to identify user session and target router.

#### Network Operations
```
GET  /api/blocked?sessionId={uuid}&routerId={uuid}
POST /api/block                    # Body: {sessionId, routerId, ip}
POST /api/unblock                  # Body: {sessionId, routerId, ip}
POST /api/reset                    # Body: {sessionId, routerId}
GET  /api/scan?sessionId={uuid}&routerId={uuid}
GET  /api/scan/router?sessionId={uuid}&routerId={uuid}
GET  /api/speedtest?sessionId={uuid}&routerId={uuid}
```

#### WiFi Operations
```
GET  /api/wifi/status?sessionId={uuid}&routerId={uuid}
POST /api/wifi/enable              # Body: {sessionId, routerId}
POST /api/wifi/disable             # Body: {sessionId, routerId}
POST /api/wifi/password            # Body: {sessionId, routerId, password}
POST /api/wifi/ssid                # Body: {sessionId, routerId, ssid}
```

#### Whitelist/Blacklist Operations
```
GET  /api/whitelist?sessionId={uuid}&routerId={uuid}
POST /api/whitelist/add            # Body: {sessionId, routerId, ip, ...}
POST /api/whitelist/remove         # Body: {sessionId, routerId, ip}
GET  /api/blacklist?sessionId={uuid}&routerId={uuid}
POST /api/blacklist/add            # Body: {sessionId, routerId, ip, ...}
POST /api/blacklist/remove         # Body: {sessionId, routerId, ip}
```

## Key Implementation Details

### Router Identification Flow
1. API call includes sessionId (from auth server) and routerId (from agent)
2. Commands server queries port-manager for router allocation by routerId
3. Port-manager returns tunnel port and stored router credentials
4. Commands server establishes or reuses paramiko connection to localhost:tunnel_port
5. SSH command executed on persistent connection with automatic timeout handling

### Response Format Guidelines

The commands server must return structured, consistent responses that allow the upper database layer to:
- Determine operation success/failure status
- Extract relevant data for database updates
- Handle errors appropriately and maintain data consistency
- Parse results uniformly across all operations

#### Standard Response Structure
```json
{
  "success": boolean,
  "data": object|array|null,
  "error": {
    "code": string,
    "message": string,
    "details": object|null
  },
  "metadata": {
    "sessionId": string,
    "routerId": string,
    "timestamp": string,
    "executionTime": number
  }
}
```

#### Data Structure Requirements
- **Consistent field naming**: Use camelCase throughout all responses
- **Predictable data types**: Arrays for lists, objects for complex data, strings for IDs
- **Complete information**: Include all data needed for database synchronization
- **Error details**: Provide enough context for the upper layer to make decisions
- **Metadata**: Always include session context and timing information

### Error Handling
- **Router Not Found**: 404 if routerId not found in port-manager
- **Session Invalid**: 401 if sessionId not active or expired
- **Tunnel Down**: 503 if SSH connection fails or tunnel unavailable
- **Command Timeout**: 408 if command execution exceeds configured timeout
- **Invalid Parameters**: 400 for malformed requests or missing required fields

### Security Considerations
- Commands server accessible only from localhost and authenticated cloud backend
- No direct router credentials stored in commands server memory
- All credentials retrieved from port-manager on-demand for each new connection
- SSH commands executed with strict timeout limits to prevent resource exhaustion
- Session isolation prevents cross-user access to router connections

## Testing Checklist

### ✅ Phase 0 Complete (Backend Cleanup)
- ✅ Database infrastructure completely removed
- ✅ Local-only services eliminated (network_scanner, speed_test, etc.)
- ✅ SSH services converted to in-memory storage
- ✅ Dependencies reduced by 50% (scapy, tinydb, pyinstaller removed)
- ✅ All validation simplified assuming upstream authorization
- ✅ All services compile without syntax errors

### 🚀 Phase 1 Ready (Next Steps)
- [ ] Commands server runs on VM port 3000 with session management
- [ ] RouterConnectionManager successfully manages multi-user connection pools
- [ ] Port-manager integration works for credential and port lookup
- [ ] Paramiko connections established successfully via tunnel ports

### 🎯 Phase 2-3 Targets  
- [ ] All endpoints accept and validate sessionId and routerId parameters
- [ ] Session management endpoints functional for start/end/refresh operations
- [ ] **Standardized response format implemented** across all endpoints
- [ ] Response data structure validated for database layer integration
- [ ] All NetPilot services work with session-aware connection routing
- [ ] Session isolation verified for multi-user concurrent access

### 🏁 Integration Success
- [ ] End-to-end test: User Login → Session Start → Router Commands → Session End
- [ ] Multiple concurrent users with different routers operate independently
- [ ] Real NetPilot operations (scan, block, wifi) function properly with session context
- [ ] Performance meets requirements under expected user load

## Estimated Timeline (Updated)

- **Week 1**: Phase 1 (Core session infrastructure - RouterConnectionManager)
- **Week 2**: Phase 2-4 (API modifications + testing)  
- **Week 3**: Phase 5 (Deployment + production validation)

**Total**: 3 weeks for session-based transformation (Cleanup phase already completed ✅)

## Success Criteria

1. **✅ Cleanup Complete**: Backend successfully cleaned of database dependencies and local-only services
2. **Functional**: All existing NetPilot operations work via session-based commands server
3. **Performance**: Command execution <2s for 90% of operations with connection reuse
4. **Scalable**: Multiple users can manage multiple routers simultaneously without interference
5. **Reliable**: Commands server handles tunnel disconnections and session timeouts gracefully  
6. **Resource Efficient**: Automatic connection cleanup prevents memory leaks and resource exhaustion
7. **Maintainable**: Minimal changes to existing business logic with clear session management layer

## Current Status Summary

**✅ COMPLETED**: Comprehensive backend cleanup eliminating all database dependencies, local-only services, and complex validation logic. The backend is now lean, SSH-focused, and ready for session-based transformation.

**🚀 NEXT**: Implement RouterConnectionManager for session-based connection pooling and port-manager integration.

**📊 IMPACT**: 50% reduction in dependencies, 100% elimination of database overhead, significant simplification of validation logic assuming upstream authorization, and full preservation of SSH-based NetPilot functionality.

This transformation creates a robust, session-aware commands server that leverages your existing tunnel infrastructure while providing the multi-user, multi-router support required for the web application architecture. The session-based design ensures efficient resource usage while maintaining the high-performance SSH execution that NetPilot operations require. 