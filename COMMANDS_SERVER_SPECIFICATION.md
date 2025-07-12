# NetPilot Commands Server Specification

## Overview

The **NetPilot Commands Server** is a critical middleware component that sits on the cloud VM (IP: `34.38.207.87`) and acts as a bridge between the cloud-deployed backend and routers connected via reverse SSH tunnels. It serves as the execution engine for all NetPilot router operations in the cloud architecture.

## Architecture Position

```
Cloud Backend (Flask) → Commands Server (VM:3000) → Port Manager (VM:8080) → SSH Tunnels (ports 2200-2299) → Routers
```

The Commands Server operates as a **router command execution proxy** that:
1. Receives NetPilot operation requests from the cloud backend
2. Resolves router connectivity through the Port Manager
3. Executes SSH commands via established reverse tunnels
4. Returns structured responses back to the cloud backend

## Core Purpose

The Commands Server transforms the NetPilot backend from a **direct SSH client** to a **cloud-native service** by:

- **Decoupling Router Access**: Separating cloud backend from direct router SSH connections
- **Tunnel Management**: Leveraging the existing agent-to-VM tunnel infrastructure
- **Multi-Tenant Support**: Enabling multiple cloud users to access their respective routers
- **Centralized Execution**: Providing a single point for all router command execution
- **Security Isolation**: Maintaining router credential security within the VM environment

## Service Configuration

### Server Details
- **Host**: `34.38.207.87` (Cloud VM)
- **Port**: `3000`
- **Protocol**: HTTP REST API
- **Environment**: Node.js/Express

### Dependencies
- **Port Manager**: `http://34.38.207.87:8080` (tunnel management)
- **SSH Tunnels**: Reverse tunnels on ports `2200-2299`
- **Router Credentials**: Stored in Port Manager database

## API Specification

### Base URL
```
http://34.38.207.87:3000/api
```

### Authentication
The Commands Server operates within the trusted VM environment and uses:
- **Router ID validation** through Port Manager
- **Session-based routing** for multi-tenant support
- **Tunnel ownership verification** for security

### Core Endpoints

#### Router Command Execution
```http
POST /api/router/execute
Content-Type: application/json

{
  "routerId": "sha256-hash-of-router-mac",
  "command": "uci show network.lan.ipaddr",
  "timeout": 30
}
```

#### NetPilot Operations
```http
# Network scanning
GET /api/network/scan?routerId=<router-id>

# Device management
POST /api/network/block
POST /api/network/unblock
GET /api/network/blocked

# Whitelist operations
GET /api/whitelist?routerId=<router-id>
POST /api/whitelist/add
POST /api/whitelist/remove
POST /api/whitelist/mode/activate

# Blacklist operations  
GET /api/blacklist?routerId=<router-id>
POST /api/blacklist/add
POST /api/blacklist/remove
POST /api/blacklist/mode/activate

# WiFi management
GET /api/wifi/status?routerId=<router-id>
POST /api/wifi/password
POST /api/wifi/ssid
```

## Integration with Port Manager

The Commands Server depends on the Port Manager (`34.38.207.87:8080`) for:

### Router Resolution
```javascript
// Get router's tunnel port and credentials
const allocation = await portManager.getAllocation(routerId);
// Returns: { port: 2251, routerUsername: "root", routerPassword: "password123" }
```

### Tunnel Verification
```javascript
// Verify tunnel is active and owned by correct router
const verification = await portManager.verifyPortOwnership(port, routerId);
// Returns: { valid: true, routerId: "abc123...", lastHeartbeat: "2025-01-01T..." }
```

### Router Credentials
```javascript
// Get SSH credentials for authenticated tunnel access
const credentials = await portManager.getRouterCredentialsByPort(port);
// Returns: { username: "root", password: "password123" }
```

## Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    "command": "uci show network.lan.ipaddr",
    "output": "network.lan.ipaddr='192.168.1.1'",
    "stderr": "",
    "executionTime": 1.234,
    "routerId": "abc123...",
    "tunnelPort": 2251
  },
  "metadata": {
    "timestamp": "2025-01-01T12:00:00.000Z",
    "commandsServer": "34.38.207.87:3000",
    "version": "1.0.0"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "TUNNEL_UNAVAILABLE",
    "message": "Router tunnel not available on port 2251",
    "details": "SSH connection failed: Connection refused"
  },
  "metadata": {
    "timestamp": "2025-01-01T12:00:00.000Z",
    "routerId": "abc123...",
    "tunnelPort": 2251,
    "commandsServer": "34.38.207.87:3000"
  }
}
```

## Architecture Assumptions

### About the Agent Layer
The Commands Server assumes:
- **Agents establish reverse SSH tunnels** to the VM on ports 2200-2299
- **Agents register with Port Manager** providing router credentials
- **Agents send periodic heartbeats** to maintain tunnel allocations
- **Agents generate deterministic router IDs** from MAC addresses
- **Tunnels remain active** throughout the router's operational period

### About the Port Manager Layer
The Commands Server expects:
- **Port Manager maintains tunnel registry** with router credentials
- **Active tunnel monitoring** with heartbeat tracking
- **Port ownership verification** to prevent unauthorized access
- **Credential security** within the VM environment
- **Tunnel connectivity testing** capabilities

### About the Cloud Backend Layer
The Commands Server provides:
- **Router command execution** via HTTP API
- **Session-based routing** for multi-tenant support
- **Standardized response format** matching Flask backend expectations
- **Error handling** for tunnel connectivity issues
- **Timeout management** for long-running operations

## Example Usage Scenarios

### Scenario 1: Network Device Scanning
```javascript
// Cloud Backend Request
POST http://34.38.207.87:3000/api/network/scan
{
  "routerId": "a1b2c3d4e5f6...",
  "sessionId": "user-session-123"
}

// Commands Server Process:
// 1. Resolve router tunnel: port 2251 from Port Manager
// 2. Execute: cat /proc/net/arp && cat /tmp/dhcp.leases
// 3. Parse device list with IP, MAC, hostname, vendor
// 4. Return structured device array
```

### Scenario 2: Device Blocking
```javascript
// Cloud Backend Request
POST http://34.38.207.87:3000/api/network/block
{
  "routerId": "a1b2c3d4e5f6...",
  "ip": "192.168.1.100"
}

// Commands Server Process:
// 1. Resolve router tunnel: port 2251
// 2. Execute: iptables -I FORWARD -s 192.168.1.100 -j DROP
// 3. Verify rule addition
// 4. Return success confirmation
```

### Scenario 3: WiFi Management
```javascript
// Cloud Backend Request
POST http://34.38.207.87:3000/api/wifi/password
{
  "routerId": "a1b2c3d4e5f6...",
  "password": "NewSecurePassword123"
}

// Commands Server Process:
// 1. Resolve router tunnel: port 2251
// 2. Execute: uci set wireless.@wifi-iface[0].key='NewSecurePassword123'
// 3. Execute: uci commit wireless
// 4. Execute: wifi reload
// 5. Return configuration success
```

## Security Considerations

### Tunnel Security
- **SSH key-based authentication** for enhanced security
- **Connection timeout management** to prevent hanging connections
- **Router credential isolation** within VM environment
- **Port ownership verification** to prevent cross-router access

### Multi-Tenant Isolation
- **Router ID validation** ensures user can only access their routers
- **Session-based routing** prevents cross-user command execution
- **Audit logging** for all router operations
- **Credential encryption** in Port Manager database

## Error Handling

### Tunnel Connectivity Issues
- **Connection timeouts**: 30-second default with configurable limits
- **Tunnel unavailable**: Graceful fallback with retry mechanisms
- **Router offline**: Clear error messages with diagnostic information
- **SSH authentication failures**: Secure error reporting without credential exposure

### Command Execution Failures
- **Invalid commands**: Validation and sanitization
- **Permission errors**: Proper error categorization
- **Network timeouts**: Appropriate timeout handling
- **Router configuration errors**: Detailed diagnostic information

## Performance Considerations

### Connection Pooling
- **Persistent SSH connections** for frequently accessed routers
- **Connection lifecycle management** with idle timeout cleanup
- **Concurrent request handling** for multiple router operations
- **Resource optimization** for high-traffic scenarios

### Response Optimization
- **Command result caching** for frequently requested data
- **Batch operation support** for multiple commands
- **Streaming responses** for long-running operations
- **Compression** for large command outputs

## Monitoring and Logging

### Operational Metrics
- **Tunnel connectivity status** per router
- **Command execution latency** and success rates
- **Error frequency** and categorization
- **Resource utilization** (CPU, memory, connections)

### Audit Trail
- **All router commands** executed with timestamp and user context
- **Authentication attempts** and failures
- **Tunnel establishment** and termination events
- **Configuration changes** and their impacts

## Deployment Requirements

### System Dependencies
- **Node.js 18+** for modern JavaScript features
- **SSH client tools** for tunnel connectivity testing
- **Network connectivity** to Port Manager (port 8080)
- **Firewall configuration** allowing inbound connections on port 3000

### Environment Configuration
```bash
# Port Manager integration
PORT_MANAGER_URL=http://localhost:8080
PORT_MANAGER_API_BASE=/api

# SSH configuration
SSH_CONNECT_TIMEOUT=10
SSH_COMMAND_TIMEOUT=30
SSH_KEEP_ALIVE=5

# Server configuration
COMMANDS_SERVER_PORT=3000
COMMANDS_SERVER_HOST=0.0.0.0
LOG_LEVEL=INFO
```

## Integration with Cloud Backend

The Commands Server seamlessly integrates with the existing NetPilot Flask backend by:

### API Compatibility
- **Matching response formats** with existing backend structure
- **Preserving error codes** and status indicators
- **Maintaining operation semantics** for all NetPilot features
- **Supporting existing session management** patterns

### RouterConnectionManager Integration
```python
# Backend modification for Commands Server integration
class RouterConnectionManager:
    def __init__(self):
        self.commands_server_url = "http://34.38.207.87:3000"
        self.session = requests.Session()
    
    def execute(self, command: str, timeout: int = 30) -> Tuple[str, str]:
        response = self.session.post(
            f"{self.commands_server_url}/api/router/execute",
            json={
                "routerId": g.router_id,
                "command": command,
                "timeout": timeout
            }
        )
        
        if response.json()["success"]:
            data = response.json()["data"]
            return data["output"], data["stderr"]
        else:
            error = response.json()["error"]
            raise RuntimeError(error["message"])
```

This Commands Server design ensures a seamless transition from localhost to cloud deployment while maintaining full compatibility with the existing NetPilot functionality and providing the scalability needed for multi-tenant cloud operations.
