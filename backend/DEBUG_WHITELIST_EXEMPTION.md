# Debug Whitelist Device Exemption Issues

This guide provides comprehensive manual commands to debug why whitelisted devices may not be getting unlimited internet access.

## 1. Quick Status Check Commands

### Check Active Mode
```bash
# Check which NetPilot mode is currently active
iptables -t mangle -L FORWARD -n | grep NETPILOT
iptables -t mangle -L PREROUTING -n | grep NETPILOT
iptables -t mangle -L POSTROUTING -n | grep NETPILOT

# Expected for whitelist mode: NETPILOT_WHITELIST in FORWARD chain
```

### Check Whitelist Chain Contents
```bash
# List all rules in the whitelist chain with line numbers
iptables -t mangle -L NETPILOT_WHITELIST -n --line-numbers -v

# Look for:
# - Your device's MAC in --mac-source rules
# - Your device's IP in -d rules
# - MARK --set-mark 1 (unlimited mark)
# - RETURN rules after MARK rules
# - Default MARK --set-mark 98 rule at the end
```

### Check TC Classes and Filters
```bash
# Check TC setup on all interfaces
for iface in $(ls /sys/class/net/ | grep -v lo); do
    echo "=== Interface: $iface ==="
    tc qdisc show dev $iface
    tc class show dev $iface
    tc filter show dev $iface
    echo ""
done

# Look for:
# - htb qdisc with handle 1:
# - class 1:1 (unlimited) and 1:10 (limited) 
# - filter handle 1 fw flowid 1:1 (unlimited traffic)
# - filter handle 98 fw flowid 1:10 (limited traffic)
```

## 2. Test Device Exemption Step-by-Step

### Step 1: Find Your Device
```bash
# Get your device's MAC and IP from router
cat /proc/net/arp | grep -v "00:00:00:00:00:00"

# Or check DHCP leases
cat /tmp/dhcp.leases

# Or scan current connections
ip neigh show
```

### Step 2: Check if Device is in Whitelist State
```bash
# Check NetPilot state file
cat /etc/config/netpilot_state.json | grep -A 10 -B 10 "whitelist"

# Look for your device MAC in the whitelist array
```

### Step 3: Test Packet Marking
```bash
# Monitor packet marking in real-time (run this while device is browsing)
watch -n 1 "iptables -t mangle -L NETPILOT_WHITELIST -n -v"

# Look for packet counters increasing on your device's rules
# The MARK --set-mark 1 rule should show packets
# The RETURN rule should also show packets
```

### Step 4: Check TC Traffic Shaping
```bash
# Monitor TC classes in real-time (run while device is browsing)
for iface in $(ls /sys/class/net/ | grep -v lo); do
    echo "=== $iface ==="
    tc -s class show dev $iface
done

# Look for:
# - class 1:1 (unlimited) should show traffic from your device
# - class 1:10 (limited) should NOT show traffic from your device
```

## 3. Manual Test Commands

### Test 1: Add Device Manually
```bash
# Replace with your device's MAC and IP
DEVICE_MAC="aa:bb:cc:dd:ee:ff"
DEVICE_IP="192.168.1.100"

# Add manual whitelist rules
iptables -t mangle -I NETPILOT_WHITELIST 1 -m mac --mac-source $DEVICE_MAC -j MARK --set-mark 1
iptables -t mangle -I NETPILOT_WHITELIST 2 -m mac --mac-source $DEVICE_MAC -j RETURN
iptables -t mangle -I NETPILOT_WHITELIST 3 -d $DEVICE_IP -j MARK --set-mark 1  
iptables -t mangle -I NETPILOT_WHITELIST 4 -d $DEVICE_IP -j RETURN

# Test if device now has unlimited access
```

### Test 2: Check Rule Order
```bash
# Rule order is CRITICAL - exemption rules must come BEFORE the default limiting rule
iptables -t mangle -L NETPILOT_WHITELIST -n --line-numbers

# Correct order should be:
# 1-N: Device exemption rules (MARK 1 + RETURN pairs)
# Last: Default limiting rule (MARK 98)
```

### Test 3: Verify Packet Flow
```bash
# Enable iptables logging temporarily to trace packets
iptables -t mangle -I NETPILOT_WHITELIST 1 -m mac --mac-source $DEVICE_MAC -j LOG --log-prefix "WHITELIST_MAC: "
iptables -t mangle -I NETPILOT_WHITELIST 1 -d $DEVICE_IP -j LOG --log-prefix "WHITELIST_IP: "

# Check system logs
logread | grep WHITELIST

# Remove logging rules after testing
iptables -t mangle -D NETPILOT_WHITELIST -m mac --mac-source $DEVICE_MAC -j LOG --log-prefix "WHITELIST_MAC: "
iptables -t mangle -D NETPILOT_WHITELIST -d $DEVICE_IP -j LOG --log-prefix "WHITELIST_IP: "
```

## 4. Common Issues and Fixes

### Issue 1: Device Not in State File
```bash
# Check if device is actually in the state file
cat /etc/config/netpilot_state.json | jq '.devices.whitelist'

# If missing, add manually to state file or via API
```

### Issue 2: Wrong Chain Active
```bash
# Whitelist mode should use FORWARD chain
iptables -t mangle -L FORWARD -n | grep NETPILOT_WHITELIST

# If missing, add manually:
iptables -t mangle -A FORWARD -j NETPILOT_WHITELIST
```

### Issue 3: TC Not Set Up
```bash
# Check if TC is properly configured
tc qdisc show | grep htb

# If missing, rebuild TC infrastructure:
# (Use the rebuild command from mode_activation_service.py)
```

### Issue 4: Wrong Mark Numbers
```bash
# Exempted devices should use mark 1, limited devices mark 98
iptables -t mangle -L NETPILOT_WHITELIST -n -v | grep "MARK set 1"
iptables -t mangle -L NETPILOT_WHITELIST -n -v | grep "MARK set 98"

# TC filters should match these marks
tc filter show dev br-lan | grep "handle 1"
tc filter show dev br-lan | grep "handle 98"
```

### Issue 5: Missing RETURN Rules
```bash
# Each MARK rule should be followed by a RETURN rule
iptables -t mangle -L NETPILOT_WHITELIST -n --line-numbers | grep -A 1 "MARK"

# Look for RETURN rules immediately after MARK rules
# If missing, exempted devices will hit the default limiting rule
```

## 5. Performance Test Commands

### Speed Test Your Device
```bash
# Test download speed
wget -O /dev/null http://speedtest.wdc01.softlayer.com/downloads/test100.zip

# Test upload speed 
curl -F "file=@/dev/urandom" http://httpbin.org/post >/dev/null

# Compare speeds before/after whitelist exemption
```

### Monitor Real-Time Traffic
```bash
# Monitor interface traffic
iftop -i br-lan

# Monitor per-device bandwidth
tc -s class show dev br-lan | grep -A 3 "class htb"
```

## 6. Clean Slate Test

### Complete Reset and Rebuild
```bash
# 1. Complete teardown
iptables -t mangle -D FORWARD -j NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true

for iface in $(ls /sys/class/net/ | grep -v lo); do
    tc qdisc del dev $iface root 2>/dev/null || true
done

# 2. Rebuild TC infrastructure
for iface in $(ls /sys/class/net/ | grep -v lo); do
    tc qdisc add dev $iface root handle 1: htb default 1
    tc class add dev $iface parent 1: classid 1:1 htb rate 1000mbit
    tc class add dev $iface parent 1: classid 1:10 htb rate 50mbit
    tc filter add dev $iface parent 1: protocol ip prio 1 handle 1 fw flowid 1:1
    tc filter add dev $iface parent 1: protocol ip prio 2 handle 98 fw flowid 1:10
done

# 3. Create and populate whitelist chain
iptables -t mangle -N NETPILOT_WHITELIST

# Add your device (replace with actual MAC/IP)
iptables -t mangle -A NETPILOT_WHITELIST -m mac --mac-source aa:bb:cc:dd:ee:ff -j MARK --set-mark 1
iptables -t mangle -A NETPILOT_WHITELIST -m mac --mac-source aa:bb:cc:dd:ee:ff -j RETURN
iptables -t mangle -A NETPILOT_WHITELIST -d 192.168.1.100 -j MARK --set-mark 1
iptables -t mangle -A NETPILOT_WHITELIST -d 192.168.1.100 -j RETURN

# Add default limiting rule LAST
iptables -t mangle -A NETPILOT_WHITELIST -j MARK --set-mark 98

# 4. Activate whitelist mode
iptables -t mangle -A FORWARD -j NETPILOT_WHITELIST

# 5. Test device speed - should be unlimited
```

## 7. Troubleshooting Checklist

- [ ] Device MAC/IP found in router ARP table
- [ ] Device MAC present in `/etc/config/netpilot_state.json` whitelist array
- [ ] NETPILOT_WHITELIST chain exists and contains device rules
- [ ] Device rules use correct mark (1 for unlimited)
- [ ] Device rules include both MARK and RETURN for MAC and IP
- [ ] RETURN rules prevent hitting default limiting rule
- [ ] TC classes and filters are properly configured on all interfaces
- [ ] FORWARD chain has jump to NETPILOT_WHITELIST
- [ ] Packet counters increase when device browses internet
- [ ] TC class 1:1 (unlimited) shows traffic from device
- [ ] No conflicting iptables rules or old NetPilot rules

Use these commands to systematically debug why a whitelisted device might not be getting unlimited access.
