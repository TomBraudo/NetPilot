# NetPilot Router Fresh Start Commands

## 🧹 **COMPLETE FRESH START - Remove ALL NetPilot Rules**

### **Step 1: Remove ALL NetPilot iptables rules from ALL chains**
```bash
# Remove jump rules from all possible chains
iptables -t mangle -D FORWARD -j NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -D INPUT -j NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -D OUTPUT -j NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -D PREROUTING -j NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -D POSTROUTING -j NETPILOT_WHITELIST 2>/dev/null || true

iptables -t mangle -D FORWARD -j NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -D INPUT -j NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -D OUTPUT -j NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -D PREROUTING -j NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -D POSTROUTING -j NETPILOT_BLACKLIST 2>/dev/null || true

# Flush and delete NetPilot chains
iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -F NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_BLACKLIST 2>/dev/null || true
```

### **Step 2: Remove ALL TC (Traffic Control) rules from ALL interfaces**
```bash
# Remove TC from all interfaces (except loopback)
for interface in $(ls /sys/class/net/ | grep -v lo); do
    echo "Cleaning TC on interface: $interface"
    tc qdisc del dev $interface root 2>/dev/null || true
    tc qdisc del dev $interface ingress 2>/dev/null || true
done
```

### **Step 3: Verify clean state**
```bash
# Check that no NetPilot chains exist
echo "=== Checking for remaining NetPilot chains ==="
iptables -t mangle -L | grep -i netpilot || echo "No NetPilot chains found ✅"

# Check that no TC rules exist
echo "=== Checking for remaining TC rules ==="
for interface in $(ls /sys/class/net/ | grep -v lo); do
    echo "Interface $interface:"
    tc qdisc show dev $interface | grep -v "qdisc noqueue\|qdisc pfifo_fast" || echo "  Clean ✅"
done

# Check internet connectivity
echo "=== Testing internet connectivity ==="
ping -c 3 8.8.8.8 && echo "Internet working ✅" || echo "Internet issue ❌"
```

## 🔧 **ONE-LINER FOR EMERGENCY CLEANUP**
```bash
# Single command to clean everything
for interface in $(ls /sys/class/net/ | grep -v lo); do tc qdisc del dev $interface root 2>/dev/null || true; done; iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true; iptables -t mangle -F NETPILOT_BLACKLIST 2>/dev/null || true; iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true; iptables -t mangle -X NETPILOT_BLACKLIST 2>/dev/null || true; iptables -t mangle -D FORWARD -j NETPILOT_WHITELIST 2>/dev/null || true; iptables -t mangle -D FORWARD -j NETPILOT_BLACKLIST 2>/dev/null || true; echo "Complete cleanup done ✅"
```

## 📋 **Diagnostic Commands**
```bash
# Show current iptables mangle table
iptables -t mangle -L -n -v

# Show current TC setup on all interfaces
for interface in $(ls /sys/class/net/ | grep -v lo); do
    echo "=== Interface: $interface ==="
    tc qdisc show dev $interface
    tc class show dev $interface
    tc filter show dev $interface
    echo
done

# Show network interfaces
ls /sys/class/net/ | grep -v lo

# Test internet speed (if speedtest-cli is available)
# speedtest-cli --simple
```

## ⚠️ **IMPORTANT: Infrastructure Setup Conflict**

The `setup_router_infrastructure()` function in `router_setup_service.py` creates persistent TC and iptables infrastructure that conflicts with our naive approach.

### **Problem:**
- `setup_router_infrastructure()` creates persistent TC qdiscs and iptables chains
- This happens automatically when the app starts (called from session endpoint)
- Conflicts with our naive "complete teardown and rebuild" approach

### **Solutions:**
#### **Option 1: Skip Infrastructure Setup (Recommended)**
Since we use complete teardown/rebuild, we don't need persistent infrastructure:

```python
# In session.py, comment out or skip the infrastructure setup:
# setup_success, setup_error = setup_router_infrastructure(restart=restart)
setup_success, setup_error = True, None  # Skip persistent infrastructure
```

#### **Option 2: Always Force Clean Start**
Modify the infrastructure setup to not create persistent rules when using naive mode.

### **Manual Override Commands**
If persistent infrastructure was already created, use these commands to remove it:

```bash
# Remove persistent TC infrastructure
for interface in $(ls /sys/class/net/ | grep -v lo); do
    tc qdisc del dev $interface root 2>/dev/null || true
done

# Remove persistent iptables chains  
iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -F NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_BLACKLIST 2>/dev/null || true
```

**The naive approach should handle infrastructure creation itself during activation, not rely on persistent setup.**
