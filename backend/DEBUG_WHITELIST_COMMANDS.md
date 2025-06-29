# NetPilot Debug Commands - Device Whitelist Issue

## 🔍 **MANUAL COMMANDS TO CHECK WHITELIST STATE**

### **1. Check Current Whitelist Chain Rules**
```bash
# Show the NETPILOT_WHITELIST chain with line numbers
iptables -t mangle -L NETPILOT_WHITELIST -n --line-numbers

# Show with more details (counters, etc.)
iptables -t mangle -L NETPILOT_WHITELIST -n -v --line-numbers
```

### **2. Check Which Chain is Active**
```bash
# Check if whitelist chain is being called
iptables -t mangle -L FORWARD -n --line-numbers | grep -i netpilot

# Check all chains for NetPilot jumps
iptables -t mangle -L -n | grep -A5 -B5 -i netpilot
```

### **3. Check TC (Traffic Control) Setup**
```bash
# Check TC setup on main interfaces
for interface in br-lan wlan0 eth0; do
    echo "=== Interface: $interface ==="
    tc qdisc show dev $interface
    tc class show dev $interface
    tc filter show dev $interface
    echo
done
```

### **4. Check State File Content**
```bash
# Show current state file
cat /etc/config/netpilot_state.json | python3 -m json.tool

# Check whitelist section specifically
cat /etc/config/netpilot_state.json | grep -A20 "whitelist"
```

### **5. Test Device MAC/IP Matching**
```bash
# Find device MAC and IP (replace with actual device)
# For phone/computer you want to whitelist:
ip neigh show | grep "192.168.1.XXX"  # Replace with device IP
arp -a | grep "192.168.1.XXX"
```

### **6. Check Packet Marking in Real-Time**
```bash
# Monitor iptables counters to see rule hits
watch -n 1 'iptables -t mangle -L NETPILOT_WHITELIST -n -v --line-numbers'

# Check TC statistics
watch -n 1 'tc -s class show dev br-lan'
```

### **7. Debug Specific Device Traffic**
```bash
# Replace AA:BB:CC:DD:EE:FF with actual device MAC
# Replace 192.168.1.XXX with actual device IP

# Check if device MAC is in whitelist rules
iptables -t mangle -L NETPILOT_WHITELIST -n | grep -i "AA:BB:CC:DD:EE:FF"

# Check if device IP is in whitelist rules  
iptables -t mangle -L NETPILOT_WHITELIST -n | grep "192.168.1.XXX"
```

## 🐛 **LIKELY ISSUES TO CHECK**

### **Issue 1: Wrong MAC Address Format**
```bash
# Check if MAC is in uppercase vs lowercase
ip neigh show | grep -i "aa:bb:cc:dd:ee:ff"
# vs
ip neigh show | grep -i "AA:BB:CC:DD:EE:FF"
```

### **Issue 2: Rule Order Problem**
```bash
# Default limiting rule should be LAST
iptables -t mangle -L NETPILOT_WHITELIST -n --line-numbers | tail -5
# Should show: "MARK set 0x62" (mark 98) as the last rule
```

### **Issue 3: Chain Not Active**
```bash
# Chain exists but not being called
iptables -t mangle -L FORWARD -n | grep -i netpilot || echo "Chain not active!"
```

### **Issue 4: TC Mark Mismatch**
```bash
# Check if TC filters match the marks (1 for unlimited, 98 for limited)
for interface in br-lan wlan0 eth0; do
    echo "=== $interface TC filters ==="
    tc filter show dev $interface | grep -E "handle (1|98)"
done
```

## 🔧 **QUICK FIXES TO TRY**

### **Fix 1: Manual Device Addition (for testing)**
```bash
# Add device manually to active whitelist (replace MAC/IP)
MAC="aa:bb:cc:dd:ee:ff"
IP="192.168.1.122"

iptables -t mangle -I NETPILOT_WHITELIST 1 -m mac --mac-source $MAC -j MARK --set-mark 1
iptables -t mangle -I NETPILOT_WHITELIST 2 -m mac --mac-source $MAC -j RETURN
iptables -t mangle -I NETPILOT_WHITELIST 3 -d $IP -j MARK --set-mark 1
iptables -t mangle -I NETPILOT_WHITELIST 4 -d $IP -j RETURN
```

### **Fix 2: Verify Rule Order**
```bash
# Make sure default limiting rule is LAST
iptables -t mangle -L NETPILOT_WHITELIST -n --line-numbers
# If not, delete and re-add:
# iptables -t mangle -D NETPILOT_WHITELIST -j MARK --set-mark 98
# iptables -t mangle -A NETPILOT_WHITELIST -j MARK --set-mark 98
```
