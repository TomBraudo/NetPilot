# NetPilot Agent Tunnel Robustness - Improvement Plan

## Current State Analysis

The tunnel system is working with basic functionality, but has significant gaps in client-side robustness that need to be addressed for production readiness.

### Current Flow
1. User clicks "Connect Tunnel" button
2. Agent allocates port from cloud VM
3. Router creates 2 autossh processes connecting VM port to router port 22
4. Processes run indefinitely until manually stopped
5. **PROBLEM**: When agent app stops, tunnel processes continue running on router
6. **PROBLEM**: When agent app restarts, no knowledge of existing tunnels

### Key Issues Identified

1. **Critical Bug**: `main.js:508` calls non-existent `tunnelManager.disconnect()` instead of `cleanup()`
2. **State Loss**: No persistence of tunnel state across app restarts
3. **Orphaned Processes**: Tunnel processes continue running on router after app closure  
4. **No Auto-recovery**: No mechanism to restore tunnels when app restarts
5. **Memory-only State**: Both `PortAllocator` and `TunnelManager` store state in memory only
6. **Incomplete Cleanup**: Cleanup only works when `isConnected` is true (memory state)

---

## IMPROVEMENT PLAN

### PHASE 1: Critical Fixes (Immediate Implementation)

#### 1.1 Fix Cleanup Method Call
- **File**: `agent/src/main.js` line 508
- **Current**: `await this.tunnelManager.disconnect();`
- **Fix**: `await this.tunnelManager.cleanup();`
- **Impact**: Ensures tunnels are properly terminated when app closes


#### 1.2 Add Persistent State Storage
- **Create**: New `StateManager` module for persistent storage
- **Location**: Use Electron's `userData` directory (`~/.netpilot/` or equivalent)
- **Files**:
  - `tunnel-state.json` - Active tunnel information
  - `port-allocations.json` - Current port allocations
  - `router-connections.json` - Router connection history
- **Format**: JSON files for easy debugging and manual intervention

```json
// tunnel-state.json example
{
  "activeTunnel": {
    "port": 2250,
    "routerId": "router_192_168_1_1_1234567890",
    "routerCredentials": {
      "host": "192.168.1.1",
      "username": "root",
      "port": 22
    },
    "cloudVmIp": "cloud.example.com",
    "established": "2024-01-15T10:30:00Z",
    "lastHeartbeat": "2024-01-15T11:45:00Z"
  },
  "lastConnection": {
    "timestamp": "2024-01-15T10:30:00Z",
    "success": true
  }
}
```

#### 1.3 Enhanced Cleanup Logic
- **Modify**: `TunnelManager.cleanup()` to work regardless of `isConnected` state
- **Add**: Force cleanup mode that kills processes by port number pattern
- **Implement**: Robust SSH reconnection for cleanup operations

```javascript
async forceCleanup(tunnelState) {
  // Reconnect to router for cleanup even if not currently connected
  // Kill processes by pattern matching tunnel port
  // Clean up state files
}
```

### PHASE 2: Enhanced Robustness

#### 2.1 Auto-reconnect on Startup
- **Add**: `autoRestore()` method to `TunnelManager`
- **Implementation**:
  1. Check for existing `tunnel-state.json` on app startup
  2. Verify router connectivity and existing processes
  3. Restore tunnel connection and monitoring
  4. Update UI to reflect current status

```javascript
async autoRestore() {
  const savedState = this.stateManager.getTunnelState();
  if (savedState && savedState.activeTunnel) {
    // Attempt to restore tunnel connection
    await this.restoreFromState(savedState.activeTunnel);
  }
}
```

#### 2.2 Graceful Process Termination
- **Implement**: Cleanup tokens for better process identification
- **Add**: Multi-stage process termination (SIGTERM → SIGKILL)
- **Create**: Cleanup verification and retry logic

```bash
# Enhanced tunnel script with cleanup token
CLEANUP_TOKEN="netpilot_${ROUTER_ID}_${TIMESTAMP}"
autossh -M 0 -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" \
  -R ${REMOTE_PORT}:localhost:22 \
  ${CLOUD_USER}@${CLOUD_VM} \
  "echo '${CLEANUP_TOKEN}' > /tmp/netpilot_cleanup_${REMOTE_PORT}.token"
```

#### 2.3 State Synchronization
- **Add**: IPC events for tunnel state changes
- **Sync**: Main process and renderer state automatically
- **Update**: UI to reflect current tunnel status on startup

```javascript
// New IPC events
ipcMain.handle('tunnel-state-changed', async (event, state) => {
  this.stateManager.saveTunnelState(state);
  // Broadcast to all renderer processes
});
```

### PHASE 3: Advanced Features

#### 3.1 Tunnel Health Monitoring
- **Enhance**: Current monitoring to detect connection drops
- **Add**: Automatic tunnel recovery on failure
- **Implement**: Connection quality metrics and reporting

#### 3.2 Smart Reconnection
- **Add**: Exponential backoff for failed connections
- **Implement**: Network change detection and adaptation
- **Create**: Fallback port allocation strategies

---

## Implementation Files

### New Files to Create
1. `agent/src/modules/StateManager.js` - Persistent state management
2. `agent/src/utils/TunnelStateValidator.js` - State validation and recovery
3. `agent/src/modules/AutoRestore.js` - Startup tunnel restoration logic

### Files to Modify
1. `agent/src/main.js` - Fix cleanup call, add auto-restore
2. `agent/src/modules/TunnelManager.js` - Add state persistence, enhanced cleanup
3. `agent/src/modules/PortAllocator.js` - Add state persistence
4. `agent/src/preload.js` - Add new IPC methods
5. `agent/src/renderer/scripts/main.js` - Handle auto-restored tunnels

---

## Implementation Priority

### High Priority (User Requirements)
1. ✅ **App Exit Cleanup**: Fix tunnel termination when agent stops
2. ✅ **Auto-connect on Boot**: Restore tunnels when agent starts

### Medium Priority (Robustness)  
3. State persistence and synchronization
4. Enhanced cleanup mechanisms

### Low Priority (Nice-to-have)
5. Advanced monitoring and health checks
6. Smart reconnection strategies

---

## Expected Benefits

- **Immediate**: Proper tunnel cleanup on app exit
- **User Experience**: Seamless tunnel restoration on app restart  
- **Reliability**: Reduced orphaned processes on router
- **Maintainability**: Better state management and debugging capabilities
- **Robustness**: Automatic recovery from connection failures

---

## Testing Strategy

### Unit Tests
- State persistence and restoration
- Cleanup logic under various conditions
- Auto-reconnection scenarios

### Integration Tests
- Full app lifecycle (start → connect → exit → restart)
- Network interruption recovery
- Multiple tunnel scenarios

### Manual Testing
- Router process verification
- State file integrity
- UI synchronization

---

## Risk Assessment

### Low Risk
- State file corruption (JSON validation handles this)
- UI desynchronization (IPC events maintain sync)

### Medium Risk
- Router connectivity issues during cleanup (retry logic mitigates)
- Process identification on router (enhanced pattern matching)

### High Risk
- None identified with proposed implementation

---

## Timeline Estimate

- **Phase 1**: 2-3 days (critical fixes)
- **Phase 2**: 3-4 days (robustness features)
- **Phase 3**: 2-3 days (advanced features)

**Total**: ~1-2 weeks for complete implementation

---

*This plan addresses the specific user requirements while laying the foundation for a more robust and professional tunnel management system.* 