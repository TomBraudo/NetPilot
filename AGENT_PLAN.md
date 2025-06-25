# NetPilot Router Agent - COMPREHENSIVE DEVELOPMENT PLAN

> **Goal**: Create a minimal agent app that automates OpenWrt router setup and establishes persistent reverse SSH tunnels to enable cloud-based NetPilot architecture with multi-user support.

---

## 🎯 Overview

### **Current Situation (from Investigation)**
- ✅ **Manual tunnel working**: Router → Cloud VM (34.38.207.87) via port 2222
- ✅ **Manual SSH commands working**: Cloud VM can control router remotely
- ✅ **Existing router setup**: Manual package installation via `backend/setup_openwrt.sh`
- ❌ **Single port limitation**: Only 1 user can connect at a time
- ❌ **Manual configuration**: Router setup requires manual intervention

### **Agent Requirements**
- **Simple UI**: 2 text boxes (username/password) + Install button
- **Automated Setup**: Download packages, configure ports, establish tunnel
- **Multi-user Support**: Dynamic port allocation for multiple routers
- **Verification**: Check setup correctness and provide status endpoint
- **Persistent Connection**: Maintain tunnel while agent is running

### **Architecture Solution**
```
Agent App → Router Setup → Tunnel (Router → Cloud VM:DYNAMIC_PORT) → Cloud Backend
```

---

## 📋 Development Phases

## Phase 1: Investigation & Requirements Analysis ✅

### 1.1 Documentation Analysis
- [x] **Read TUNNEL_COMMANDS.md**: Understand proven working methods
- [x] **Read ARCHITECTURE.md**: Understand current localhost-based architecture
- [x] **Read IMPLEMENTATION_PLAN.md**: Understand cloud migration approach
- [x] **Read CLOUD_CHECKLIST.md**: Understand cloud infrastructure setup

### 1.2 Codebase Analysis
- [x] **Analyze existing router setup**: `backend/setup_openwrt.sh` and `backend/utils/commands.py`
- [x] **Identify required packages**: From `backend/installed_packages.txt`
- [x] **Understand SSH implementation**: `backend/utils/ssh_client.py`
- [x] **Map NetPilot services**: Understand which router features need to be enabled

### 1.3 Technical Requirements Extraction
- [x] **Required OpenWrt packages**: 
  - `openssh-client`, `autossh` (for tunnel)
  - `firewall4`, `iptables-mod-ipopt`, `tc`, `kmod-sched` (for traffic control)
  - `uci`, `ip-full`, `dnsmasq` (for configuration)
  - `dropbear` (SSH server)
- [x] **Router configuration commands**: Based on existing `setup_openwrt.sh`
- [x] **Tunnel establishment**: From proven TUNNEL_COMMANDS.md methods
- [x] **Multi-user port strategy**: Dynamic port allocation system

---

## Phase 2: Agent Architecture Design

### 2.1 Technology Stack Selection
- [x] **Frontend Framework**: Choose between:
  - Electron (cross-platform desktop app)

### 2.2 Application Components
- [x] **Main Window**: Username/password inputs + Install button
- [x] **Router Communication Module**: SSH connection handling
- [x] **Package Installation Module**: Automated OpenWrt setup
- [x] **Tunnel Management Module**: Establish and maintain reverse SSH tunnel
- [x] **Port Allocation Service**: Request available ports from cloud VM
- [x] **Verification Module**: Check setup status and connectivity
- [ ] **Status API**: HTTP endpoint for frontend verification

### 2.3 Architecture Diagram
- [x] **Create system architecture diagram** showing:
  - Agent → Router connection
  - Router → Cloud VM tunnel
  - Cloud Backend → Router command flow
  - Multi-user port allocation

---

## Phase 3: Cloud VM Port Management System ✅

### 3.1 Port Allocation API (Cloud VM)
- [x] **Design port allocation strategy**:
  - Port range: 2200-2299 (100 concurrent users)
  - Port assignment endpoint: `POST /api/allocate-port`
  - Port release endpoint: `POST /api/release-port/{port}`
  - Port status endpoint: `GET /api/port-status`

### 3.2 Port Management Service
- [x] **Create port allocation database**: Track assigned ports and router IDs
- [x] **Implement port assignment logic**: Find next available port
- [x] **Add port timeout mechanism**: Auto-release inactive ports
- [x] **Create port health checking**: Verify tunnel connectivity

### 3.3 Security Considerations
- [x] **Router authentication**: Each router gets unique tunnel credentials
- [x] **Port access control**: Restrict port access to specific router
- [x] **Connection monitoring**: Track and log tunnel activities

---

## Phase 4: Router Setup Automation ✅

### 4.1 SSH Connection Module
- [x] **Create SSH connection class**: Handle password-based authentication
- [x] **Add connection validation**: Test SSH connectivity before proceeding
- [x] **Implement command execution**: Execute router commands with error handling
- [x] **Add progress reporting**: Report setup progress to UI

### 4.2 Package Installation Automation
- [x] **Create package installer**: Automate `opkg update && opkg install` commands
- [x] **Required packages list**:
  ```bash
  # Optimized package list for minimal storage usage
  openssh-client autossh sshpass  # For tunnel establishment
  uci iptables tc kmod-sched-core # For NetPilot core functionality
  ip-full dropbear               # Network and SSH access
  ```

### 4.3 Router Configuration
- [x] **Enable SSH service**: Ensure dropbear is running and configured
- [x] **Configure firewall**: Open necessary ports for NetPilot functionality
- [x] **Setup UCI configurations**: Prepare router for NetPilot commands
- [x] **Verify installations**: Check all packages installed correctly
- [x] **NetPilot compatibility verification**: Comprehensive setup validation

---

## Phase 5: Reverse SSH Tunnel Implementation

### 5.1 Dynamic Port Allocation
- [x] **Request port from cloud VM**: Call port allocation API
- [x] **Store port assignment**: Save allocated port for tunnel establishment
- [x] **Handle allocation failures**: Retry logic and error reporting

### 5.2 SSH Key Management
- [x] **Generate router SSH keys**: Create unique keypair for each router
- [x] **Upload public key to cloud VM**: Authenticate tunnel user (optional improvement)
- [x] **Configure SSH client**: Setup SSH config for tunnel connection

### 5.3 Tunnel Establishment
- [x] **Create tunnel script**: Generate autossh command with allocated port
- [x] **Install tunnel script on router**: Copy script to `/root/netpilot_tunnel.sh`
- [x] **Create init.d service**: Auto-start tunnel on router boot
- [x] **Start tunnel service**: Establish initial connection

### 5.4 Tunnel Monitoring
- [x] **Implement connection checking**: Verify tunnel is active
- [x] **Add auto-recovery**: Restart tunnel if connection drops
- [x] **Status reporting**: Report tunnel status to agent UI

---

## Phase 6: Agent User Interface

### 6.1 Main Window Design ✅ COMPLETE
- [x] **Create main window layout**:
  - NetPilot logo and branding ✅
  - Router IP input (pre-filled with 192.168.1.1) ✅
  - Username input (pre-filled with "root") ✅  
  - Password input ✅
  - "Install & Connect" button ✅
  - Progress bar and status messages ✅
  - Connection status indicator ✅

### 6.2 Setup Process Flow ✅ COMPLETE
- [x] **Input validation**: Check IP format, non-empty credentials ✅
- [x] **SSH connectivity test**: Verify router access before proceeding ✅
- [x] **Progress tracking**: Show current step (connecting, installing, configuring, tunneling) ✅
- [x] **Error handling**: Display clear error messages with solutions ✅
- [x] **Success confirmation**: Show tunnel status and allocated port ✅

### 6.3 Advanced Features ✅ COMPLETE
- [x] **Settings panel**: Configure cloud VM endpoint, advanced options ✅
- [x] **Log viewer**: Show detailed installation and connection logs ✅
- [x] **Reconnect functionality**: Re-establish tunnel without full reinstall ✅
- [x] **Uninstall option**: Remove NetPilot components from router ✅

---

## Phase 7: Verification & Status API

### 7.1 Router Setup Verification ✅ COMPLETE
- [x] **Package verification**: Check all required packages are installed ✅
- [x] **Service verification**: Verify SSH, firewall, and network services ✅
- [x] **Configuration verification**: Test UCI commands and router responses ✅
- [x] **NetPilot compatibility check**: Run sample NetPilot commands ✅

### 7.2 Tunnel Connectivity Verification ✅ COMPLETE
- [x] **Tunnel status check**: Verify reverse tunnel is active ✅
- [x] **Command execution test**: Test cloud VM → router command flow ✅
- [x] **Latency measurement**: Check tunnel performance ✅
- [x] **Port accessibility**: Verify allocated port is working ✅

### 7.3 Status API Implementation ✅ COMPLETE
- [x] **Create HTTP server**: Simple web server in agent for status queries ✅
- [x] **Status endpoint**: `GET /api/status` returning JSON status ✅
- [x] **Health endpoint**: `GET /api/health` for basic connectivity check ✅
- [x] **Logs endpoint**: `GET /api/logs` for troubleshooting ✅

---

## Phase 8: UI/UX Improvements & Tunnel Management Refinement ⚠️ **NEXT PHASE**

> **Current Status**: Basic tunnel connection working! All 5 steps complete and tunnel established on port 2211.
> **Key Fixes Applied**: 
> - ✅ Port parameter bug fixed (was undefined, now correctly passes port number)
> - ✅ SSH BatchMode bug fixed (was preventing password authentication)
> - ✅ Cloud port manager deployed and working
> - ✅ Package detection optimized (prevents unnecessary reinstalls)

### 8.1 Button State Management ✅
- [x] **Context-aware UI**: Make uninstall and reconnect buttons only visible when tunnel is connected
- [x] **Connection state indicators**: Clear visual feedback for different connection states
- [x] **Button grouping**: Organize actions by connection state (disconnected vs connected)

### 8.2 Separate One-Time Configuration from Multi-Use Operations ✅ COMPLETE
Currently the "Install & Connect" button does everything at once. Split this into:

#### **One-Time Router Configuration (Setup Phase)**
- [x] **"Configure Router" button**: Separate one-time setup operation ✅
  - Package installation (openssh-client, autossh, sshpass, etc.) ✅
  - SSH key generation and setup ✅
  - Router NetPilot configuration (firewall, UCI settings) ✅
  - Init.d service creation for auto-start ✅
  - Verification of router readiness ✅
- [x] **Configuration persistence**: Remember which routers are already configured ✅
- [x] **Configuration status check**: Quick verification if router is NetPilot-ready ✅
- [x] **Separate progress tracking**: Configuration has its own 5-step progress ✅

#### **Multi-Use Tunnel Management (Connection Phase)**
- [x] **"Connect Tunnel" button**: Quick tunnel establishment ✅
  - Port allocation from cloud VM ✅
  - Tunnel script creation with allocated port ✅
  - Tunnel process startup ✅
  - Connection verification ✅
- [x] **"Reconnect" button**: Re-establish tunnel using existing allocated port ✅
  - Skip port allocation if valid port exists ✅
  - Restart tunnel process only ✅
  - No package installation or configuration ✅
- [x] **"Disconnect" button**: Stop tunnel while keeping configuration ✅
  - Stop tunnel process ✅
  - Release allocated port ✅
  - Keep router configuration intact for future connections ✅
- [x] **Separate progress tracking**: Tunnel connection has its own 4-step progress ✅

#### **UI/UX Improvements**
- [x] **Smaller notification popups**: Reduced size and better styling ✅
- [x] **Click-outside-to-close**: Notifications now dismissible by clicking outside ✅
- [x] **Fixed success icon issue**: Proper emoji handling in notifications ✅
- [x] **Fixed tunnel script errors**: Improved password authentication and BatchMode handling ✅

### 8.3 Enhanced Reconnection Logic
- [x] **Smart reconnection**: Try to reuse existing port allocation before requesting new port
- [x] **Port validation**: Check if previously allocated port is still valid/availableavailable
- [x] **Connection history**: Remember successful configurations for quick reconnection

### 8.4 Configuration State Management
- [x] **Router configuration database**: Track which routers have been configured
- [x] **Configuration versioning**: Handle updates to router configuration requirements
- [x] **Configuration cleanup**: Remove NetPilot configuration when requested

### 8.5 User Experience Improvements
- [ ] **Setup wizard**: Guide new users through one-time configuration
- [x] **Quick connect for configured routers**: Fast connection for already-setup routers
- [x] **Status persistence**: Remember connection state across agent restarts

---

## Phase 10: Error Handling & Recovery

### 10.1 Common Error Scenarios
- [ ] **SSH connection failures**: Wrong credentials, network issues
- [ ] **Package installation failures**: Repository issues, disk space
- [ ] **Tunnel establishment failures**: Cloud VM unavailable, firewall blocks
- [ ] **Port allocation failures**: No available ports, API errors

### 10.2 Error Recovery Mechanisms
- [ ] **Automatic retry logic**: Exponential backoff for transient failures
- [ ] **Partial setup recovery**: Resume from failed step
- [ ] **Connection restoration**: Auto-reconnect lost tunnels
- [ ] **Fallback procedures**: Alternative approaches for common issues

### 10.3 User-Friendly Error Messages
- [ ] **Clear error descriptions**: Non-technical language
- [ ] **Solution suggestions**: Actionable steps to resolve issues
- [ ] **Troubleshooting guide**: Common problems and solutions
- [ ] **Support contact information**: How to get help

---

## Phase 11: Documentation & Deployment

### 11.1 User Documentation
- [ ] **Installation guide**: How to download and run agent
- [ ] **Router compatibility list**: Tested OpenWrt versions
- [ ] **Troubleshooting guide**: Common issues and solutions
- [ ] **FAQ section**: Frequently asked questions

### 11.2 Technical Documentation
- [ ] **API documentation**: Cloud VM port allocation endpoints
- [ ] **Architecture documentation**: System design and components
- [ ] **Development setup**: How to build and modify agent
- [ ] **Deployment instructions**: How to package and distribute

### 11.3 Distribution Package
- [ ] **Cross-platform builds**: Windows, macOS, Linux executables
- [ ] **Installer creation**: Easy installation packages
- [ ] **Auto-update mechanism**: Automatic agent updates
- [ ] **Version management**: Release versioning and changelog

---

## 🔧 Technical Implementation Details

### Required Router Packages (Final List)
```bash
# Core tunnel packages
openssh-client autossh

# NetPilot functionality packages  
firewall4 iptables-mod-ipopt iptables ip-full
tc kmod-sched kmod-sched-core
uci dnsmasq odhcpd-ipv6only
curl wget ca-certificates cron

# Usually pre-installed but verify
dropbear
```

### Tunnel Command Template
```bash
# Router side tunnel establishment
autossh -M 0 -N -R {allocated_port}:localhost:22 \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -o ExitOnForwardFailure=yes \
  -o StrictHostKeyChecking=no \
  netpilot-agent@{cloud_vm_ip}
```

### Port Allocation Strategy
```
Port Range: 2200-2299 (100 concurrent users)
Router ID: Generated UUID for each router
Database: {router_id: port_number, timestamp, status}
Timeout: Release ports after 24h of inactivity
```

### Verification Commands
```bash
# Check packages installed
opkg list-installed | grep -E "(openssh-client|autossh|firewall4|tc)"

# Check tunnel active
ps | grep autossh

# Check connectivity
ssh -p {port} root@localhost "echo 'connected'" # (from cloud VM)
```

---

## 📊 Success Criteria

### Phase Completion Metrics
- [x] **Phase 2**: Agent architecture documented and approved
- [x] **Phase 3**: Port allocation API working with 100 concurrent users
- [x] **Phase 4**: Router setup automation 100% successful on test router
- [x] **Phase 5**: Reverse SSH tunnel established and persistent
- [x] **Phase 6**: User interface working and user-friendly
- [x] **Phase 7**: Verification endpoints returning accurate status ✅ COMPLETE
- [ ] **Phase 8**: UI/UX improvements and tunnel management refinement ⚠️ **NEXT PHASE**
- [ ] **Phase 9**: All tests passing with 95%+ success rate
- [ ] **Phase 10**: Error scenarios handled gracefully
- [ ] **Phase 11**: Documentation complete and agent packaged

### Final Success Validation
- [ ] **Multi-user testing**: 10+ routers connected simultaneously
- [ ] **Cloud NetPilot integration**: Web dashboard controlling multiple routers
- [ ] **User experience**: Non-technical users can install in <5 minutes
- [ ] **Reliability**: 99%+ tunnel uptime over 24-hour period
- [ ] **Performance**: <100ms command execution latency

---

## 🚀 Next Steps

### Immediate Actions (This Week)
1. **Choose technology stack** for agent development
2. **Set up development environment** 
3. **Create basic agent UI** with input fields
4. **Test manual SSH connection** from agent to router

### Week 2-3 Goals
1. **Implement router setup automation**
2. **Create port allocation API** on cloud VM
3. **Test tunnel establishment** with dynamic ports

### Month 1 Target
1. **Complete working agent** with all core features
2. **Successful multi-user testing** with 5+ routers
3. **Integration with cloud NetPilot** backend

---

**Legend**: [ ] = Pending | [x] = Complete

This comprehensive plan will transform NetPilot from a localhost-only application to a scalable cloud-based network management platform! 🎯 