# NetPilot Whitelist/Blacklist Implementation Plan

## Current Working Implementation Analysis

### ✅ **What Works (DO NOT CHANGE)**

1. **Traffic Control Structure**
   ```bash
   tc qdisc add dev {interface} root handle 1: htb default 1
   tc class add dev {interface} parent 1: classid 1:1 htb rate 1000mbit  # Unlimited
   tc class add dev {interface} parent 1: classid 1:10 htb rate 50mbit   # Limited
   tc filter add dev {interface} parent 1: protocol ip handle 99 fw flowid 1:10
   ```

2. **Packet Marking Logic**
   - **Whitelist Mode**: Mark ALL traffic with 98 → limited, then mark whitelisted IPs with 1 → unlimited
   - **Blacklist Mode**: Only mark blacklisted IPs with 98 → limited, others stay unmarked → unlimited

3. **Multi-Interface Application**
   - Apply to ALL network interfaces (br-lan, eth0, lan1-4, phy0-ap0, etc.)
   - Use bidirectional rules (PREROUTING + POSTROUTING)

### ❌ **Performance Issues**

1. **Heavy Rule Reconstruction**: Every mode activation rebuilds ALL rules on ALL interfaces
2. **Complete Teardown**: Deactivation removes ALL traffic control completely
3. **No Rule Persistence**: No way to keep rules "ready but disabled"

## 🚀 **Current Implementation: Naive Full Teardown/Rebuild**

### **Core Concept: Complete Teardown and Rebuild**

For reliability and simplicity, we use a **complete teardown and rebuild** approach on every mode activation/deactivation.

### **Phase 1: Complete Teardown**

Remove ALL NetPilot rules and TC infrastructure:

```bash
# 1. Remove all NetPilot iptables rules
iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -D FORWARD -j NETPILOT_WHITELIST 2>/dev/null || true

# 2. Remove TC infrastructure on ALL interfaces
for interface in $(ls /sys/class/net/ | grep -v lo); do
    tc qdisc del dev $interface root 2>/dev/null || true
done
```

### **Phase 2: Rebuild TC Infrastructure**

Set up TC on all interfaces with proven working structure:

```bash
for interface in $(ls /sys/class/net/ | grep -v lo); do
    tc qdisc add dev $interface root handle 1: htb default 1
    tc class add dev $interface parent 1: classid 1:1 htb rate 1000mbit  # Unlimited (mark 1)
    tc class add dev $interface parent 1: classid 1:10 htb rate 50mbit   # Limited (mark 98)
    tc filter add dev $interface parent 1: protocol ip prio 1 handle 1 fw flowid 1:1    # Unlimited
    tc filter add dev $interface parent 1: protocol ip prio 2 handle 98 fw flowid 1:10  # Limited
done
```

### **Phase 3: Rebuild Whitelist Chain**

Create whitelist chain with MAC+IP+RETURN logic:

```bash
# Create and populate whitelist chain
iptables -t mangle -N NETPILOT_WHITELIST

# For each whitelisted device (MAC+IP combination)
iptables -t mangle -A NETPILOT_WHITELIST -m mac --mac-source AA:BB:CC:DD:EE:FF -s 192.168.1.122 -j MARK --set-mark 1
iptables -t mangle -A NETPILOT_WHITELIST -m mac --mac-source AA:BB:CC:DD:EE:FF -s 192.168.1.122 -j RETURN

# Default rule: limit all other traffic
iptables -t mangle -A NETPILOT_WHITELIST -j MARK --set-mark 98

# Activate in FORWARD chain (proven to work)
iptables -t mangle -A FORWARD -j NETPILOT_WHITELIST
```

### **Phase 4: Mode Deactivation**

Complete teardown (same as Phase 1):

```bash
# Remove all NetPilot rules and TC infrastructure
# This restores full internet connectivity
```

## 📋 **Implementation Phases**

### **Phase 1: Infrastructure Service**

Create `infrastructure_service.py`:

```python
def setup_persistent_infrastructure():
    """Set up TC and iptables infrastructure once during router initialization"""
    # 1. Set up TC on all interfaces
    # 2. Create iptables chains
    # 3. Set default rates from config
    
def update_infrastructure_rates(whitelist_limited, whitelist_full, blacklist_limited):
    """Update rates without rebuilding entire infrastructure"""
    # Update TC class rates on all interfaces
    
def reset_infrastructure():
    """Complete teardown for troubleshooting"""
    # Remove all TC and iptables rules
```

### **Phase 2: Device Management Service**

Create `device_rule_service.py`:

```python
def add_device_to_whitelist_rules(ip_or_mac):
    """Add device rule to NETPILOT_WHITELIST chain (doesn't activate mode)"""
    
def remove_device_from_whitelist_rules(ip_or_mac):
    """Remove device rule from NETPILOT_WHITELIST chain"""
    
def rebuild_whitelist_chain():
    """Rebuild whitelist chain from database (when multiple changes)"""
    
def add_device_to_blacklist_rules(ip_or_mac):
    """Add device rule to NETPILOT_BLACKLIST chain"""
```

### **Phase 3: Mode Activation Service**

Update `whitelist_service.py` and `blacklist_service.py`:

```python
def activate_whitelist_mode():
    """Fast activation - single iptables jump command"""
    # iptables -A PREROUTING -j NETPILOT_WHITELIST
    # iptables -A POSTROUTING -j NETPILOT_WHITELIST
    
def deactivate_whitelist_mode():
    """Fast deactivation - remove jump commands"""  
    # iptables -D PREROUTING -j NETPILOT_WHITELIST
    # iptables -D POSTROUTING -j NETPILOT_WHITELIST
    
def add_device_to_whitelist(ip):
    """Add device and update rules if mode is active"""
    add_to_whitelist_db(ip)
    add_device_to_whitelist_rules(ip)
    # No mode reactivation needed!
```

### **Phase 4: Router Setup Integration**

Update `router_setup_service.py`:

```python
def setup_router_infrastructure():
    """Include persistent infrastructure setup"""
    # 1. NFT setup (if needed)
    # 2. Persistent TC setup
    # 3. Persistent iptables chains
    # 4. State file initialization
```

## 🎯 **Performance Benefits**

### **Before (Current)**
- **Mode Activation**: ~5-10 seconds (rebuild all rules on all interfaces)
- **Device Add/Remove**: ~3-5 seconds (rebuild mode rules)  
- **Mode Switch**: ~10-15 seconds (teardown + rebuild)

### **After (Improved)**  
- **Mode Activation**: ~0.1 seconds (single iptables command)
- **Device Add/Remove**: ~0.1 seconds (single rule addition)
- **Mode Switch**: ~0.2 seconds (disable + enable)

## 🔧 **Implementation Strategy**

### **Step 1: Create Infrastructure Service**
- Implement persistent TC and iptables setup
- Test with current working logic to ensure compatibility

### **Step 2: Update Device Management**  
- Modify add/remove device functions to update chains instead of rebuilding
- Maintain compatibility with existing database structure

### **Step 3: Fast Mode Activation**
- Replace mode activation with gateway toggle
- Ensure deactivation properly disables without destroying infrastructure

### **Step 4: Integration Testing**
- Test all combinations: add devices → activate mode → remove devices → deactivate
- Verify performance improvements
- Ensure no regression in functionality

## 🚨 **Risk Mitigation**

### **Backwards Compatibility**
- Keep current `setup_traffic_rules()` as fallback
- Add feature flag to enable new implementation
- Support both approaches during transition

### **Failure Recovery**
- Infrastructure validation checks
- Automatic rebuild if chains become corrupted
- Graceful fallback to current implementation

### **Testing Strategy**  
- Unit tests for each service component
- Integration tests for full workflow
- Performance benchmarks before/after
- Multi-device stress testing

## 📊 **Success Metrics**

1. **Mode activation time < 500ms**
2. **Device add/remove time < 200ms**  
3. **No functional regression**
4. **Memory usage reduction (fewer rule rebuilds)**
5. **CPU usage reduction during operations**

## 🏁 **Rollout Plan**

1. **Week 1**: Implement infrastructure service
2. **Week 2**: Implement device management service  
3. **Week 3**: Implement fast mode activation
4. **Week 4**: Integration testing and performance validation
5. **Week 5**: Production deployment with fallback option

This improved implementation maintains the **proven working logic** while dramatically improving performance through **persistent rule infrastructure** and **gateway-based activation**.

---

## 📊 **CURRENT STATUS: IMPLEMENTATION COMPLETE**

### **🟢 PROVEN WORKING APPROACH IMPLEMENTED**
- **Complete Teardown**: Removes all NetPilot rules and TC infrastructure ✅
- **TC Infrastructure**: Sets up proven working structure on all interfaces ✅
- **Whitelist Chain**: MAC+IP+RETURN logic with default limiting ✅
- **Speed Limiting**: Tested and confirmed working (unlimited vs 50mbps) ✅
- **Chain Activation**: Uses FORWARD chain (proven reliable) ✅
- **Code Implementation**: Automated in `mode_activation_service.py` ✅

### **🚀 READY FOR PRODUCTION**
- Manual approach proven to work reliably
- Automated implementation uses same exact steps
- Simple, maintainable, robust solution
- Emergency recovery commands documented

### **🔄 EMERGENCY RECOVERY COMMANDS**

If whitelist mode gets stuck or needs immediate deactivation:

```bash
# EMERGENCY: Complete teardown (restore full internet)
iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -D FORWARD -j NETPILOT_WHITELIST 2>/dev/null || true

for interface in $(ls /sys/class/net/ | grep -v lo); do
    tc qdisc del dev $interface root 2>/dev/null || true
done
```

### **🎯 FUTURE OPTIMIZATIONS**

If performance becomes an issue, we can implement:
1. **Persistent Infrastructure**: Keep TC setup, only toggle chains
2. **Rule Caching**: Store and reuse device rules
3. **Incremental Updates**: Add/remove individual devices without full rebuild

But the current **naive approach** is:
- **Simple**: Easy to understand and debug
- **Reliable**: Complete teardown prevents rule conflicts
- **Maintainable**: No complex state management
- **Proven**: Based on manual testing that works 100%

---

**IMPLEMENTATION DECISION: We've chosen the naive full teardown/rebuild approach because it's proven to work reliably and is much simpler to maintain. The complex persistent infrastructure approach described above is not currently implemented.**
