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

### **Step 2: Remove NetPilot TC (Traffic Control) rules from ALL interfaces**
```bash
# Remove NetPilot TC rules from all interfaces (except loopback)
for interface in $(ls /sys/class/net/ | grep -v lo); do
    echo "Cleaning TC on interface: $interface"
    # Only remove HTB qdiscs (used by NetPilot) to preserve router defaults
    if tc qdisc show dev $interface | grep -q "htb"; then
        echo "  Found NetPilot HTB qdisc - removing"
        tc qdisc del dev $interface root 2>/dev/null || true
    else
        echo "  No NetPilot HTB qdisc found - preserving default config"
    fi
done
```

### **Step 3: Verify clean state**
```bash
# Check that no NetPilot chains exist
echo "=== Checking for remaining NetPilot chains ==="
iptables -t mangle -L | grep -i netpilot || echo "No NetPilot chains found ✅"

# Check that no NetPilot HTB TC rules exist
echo "=== Checking for remaining NetPilot TC rules ==="
for interface in $(ls /sys/class/net/ | grep -v lo); do
    echo "Interface $interface:"
    # Only check for HTB qdiscs (used by NetPilot)
    if tc qdisc show dev $interface | grep -q "htb"; then
        tc qdisc show dev $interface | grep "htb"
        echo "  ❌ NetPilot HTB qdisc still present!"
    else
        echo "  Clean ✅ (No NetPilot HTB qdisc)"
    fi
done

# Check internet connectivity
echo "=== Testing internet connectivity ==="
ping -c 3 8.8.8.8 && echo "Internet working ✅" || echo "Internet issue ❌"
```

## 🔧 **ONE-LINER FOR EMERGENCY CLEANUP**
```bash
# Single command to clean only NetPilot-specific rules
for interface in $(ls /sys/class/net/ | grep -v lo); do if tc qdisc show dev $interface | grep -q "htb"; then tc qdisc del dev $interface root 2>/dev/null || true; fi; done; iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true; iptables -t mangle -F NETPILOT_BLACKLIST 2>/dev/null || true; iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true; iptables -t mangle -X NETPILOT_BLACKLIST 2>/dev/null || true; iptables -t mangle -D FORWARD -j NETPILOT_WHITELIST 2>/dev/null || true; iptables -t mangle -D FORWARD -j NETPILOT_BLACKLIST 2>/dev/null || true; iptables -t mangle -D INPUT -j NETPILOT_WHITELIST 2>/dev/null || true; iptables -t mangle -D INPUT -j NETPILOT_BLACKLIST 2>/dev/null || true; iptables -t mangle -D OUTPUT -j NETPILOT_WHITELIST 2>/dev/null || true; iptables -t mangle -D OUTPUT -j NETPILOT_BLACKLIST 2>/dev/null || true; iptables -t mangle -D PREROUTING -j NETPILOT_WHITELIST 2>/dev/null || true; iptables -t mangle -D PREROUTING -j NETPILOT_BLACKLIST 2>/dev/null || true; iptables -t mangle -D POSTROUTING -j NETPILOT_WHITELIST 2>/dev/null || true; iptables -t mangle -D POSTROUTING -j NETPILOT_BLACKLIST 2>/dev/null || true; echo "Complete cleanup done ✅"
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
# Remove persistent NetPilot TC infrastructure (only HTB qdiscs)
for interface in $(ls /sys/class/net/ | grep -v lo); do
    # Only remove HTB qdiscs (used by NetPilot)
    if tc qdisc show dev $interface | grep -q "htb"; then
        echo "Removing NetPilot HTB qdisc from $interface"
        tc qdisc del dev $interface root 2>/dev/null || true
    fi
done

# Remove persistent iptables chains  
iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -F NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_BLACKLIST 2>/dev/null || true
```

**The naive approach should handle infrastructure creation itself during activation, not rely on persistent setup.**
