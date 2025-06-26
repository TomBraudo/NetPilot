# NetPilot Commands Server Transformation Plan

## Executive Summary

This plan details the transformation of the existing Flask backend from a localhost application to a **Commands Server** that runs on the VM (34.38.207.87) and routes SSH commands to routers via established tunnels using session-based connection management with routerId lookup through the port-manager.

## Current Architecture Analysis

### ✅ What We Have
- **Flask Backend**: Complete API endpoints for NetPilot operations
- **Service Layer**: All NetPilot functionality (blocking, scanning, wifi management, etc.)
- **SSH Execution**: Uses `ssh_manager.execute_command()` with paramiko for direct connections
- **Port Manager**: Running on VM with router credential storage and port allocation
- **Agent Tunnel System**: Establishes reverse SSH tunnels with unique routerIds

### 🎯 Transformation Goal
Transform the backend into a **Commands Server** where:
- API calls include `sessionId` and `routerId` parameters
- Server maintains session-based connection pools for multi-user support
- Each user session can manage multiple router connections simultaneously
- Automatic connection lifecycle management with configurable timeouts
- Server queries port-manager to get tunnel port and credentials for each routerId
- SSH commands are executed via persistent paramiko connections through tunnel ports
- All existing business logic and service structure remains unchanged

## Architecture Changes

### Before (Current)
```
API Call → Endpoint → Service → ssh_manager (paramiko) → Direct Router SSH
```

### After (Session-Based Commands Server)
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

## Transformation Plan

## Phase 1: Core Infrastructure Setup (Week 1)

### Step 1.1: Project Setup on VM
- [ ] **Create Commands Server Directory Structure on VM**
  - Copy existing backend structure to `/opt/netpilot-commands-server`
  - Set up Python virtual environment and dependencies
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
  - Maintain backward compatibility with existing service calls
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
  - Maintain existing endpoint behavior and response formats

- [ ] **Update Endpoint Categories**
  - Network operations: block, unblock, scan, speedtest, reset
  - WiFi management: status, enable, disable, password, SSID changes
  - Whitelist/Blacklist: add, remove, list operations
  - Configuration: router settings and status queries

### Step 2.3: Remove Database Dependencies
- [ ] **Disable Database Initialization**
  - Comment out TinyDB initialization and cleanup
  - Update server startup and shutdown procedures
  - Remove database connection management

- [ ] **Create Mock Database Services**
  - Implement lightweight device lookup functions
  - Generate consistent device information for blocking operations
  - Maintain service layer compatibility without database overhead

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

## Phase 4: Testing & Validation (Week 2-3)

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

## Phase 5: Deployment & Service Management (Week 3)

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

### ✅ Phase 1 Complete
- [ ] Commands server runs on VM port 3000 with session management
- [ ] RouterConnectionManager successfully manages multi-user connection pools
- [ ] Port-manager integration works for credential and port lookup
- [ ] Paramiko connections established successfully via tunnel ports

### ✅ Phase 2 Complete  
- [ ] All endpoints accept and validate sessionId and routerId parameters
- [ ] Session management endpoints functional for start/end/refresh operations
- [ ] Database dependencies removed and mock services implemented
- [ ] Error handling implemented for missing or invalid session/router parameters

### ✅ Phase 3 Complete
- [ ] All NetPilot services work with session-aware connection routing
- [ ] Command execution latency acceptable with connection reuse
- [ ] Session isolation verified for multi-user concurrent access
- [ ] Connection cleanup and timeout behavior working correctly

### ✅ Integration Success
- [ ] End-to-end test: User Login → Session Start → Router Commands → Session End
- [ ] Multiple concurrent users with different routers operate independently
- [ ] Real NetPilot operations (scan, block, wifi) function properly with session context
- [ ] Performance meets requirements under expected user load

## Estimated Timeline

- **Week 1**: Phase 1-2 (Core infrastructure + API modifications)
- **Week 2**: Phase 3-4 (Service updates + comprehensive testing)  
- **Week 3**: Phase 5 (Deployment + production validation)

**Total**: 3 weeks for complete transformation

## Success Criteria

1. **Functional**: All existing NetPilot operations work via session-based commands server
2. **Performance**: Command execution <2s for 90% of operations with connection reuse
3. **Scalable**: Multiple users can manage multiple routers simultaneously without interference
4. **Reliable**: Commands server handles tunnel disconnections and session timeouts gracefully  
5. **Resource Efficient**: Automatic connection cleanup prevents memory leaks and resource exhaustion
6. **Maintainable**: Minimal changes to existing business logic with clear session management layer

This transformation creates a robust, session-aware commands server that leverages your existing tunnel infrastructure while providing the multi-user, multi-router support required for the web application architecture. The session-based design ensures efficient resource usage while maintaining the high-performance SSH execution that NetPilot operations require. 