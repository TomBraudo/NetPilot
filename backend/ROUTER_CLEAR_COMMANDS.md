# NetPilot Router Clear Commands

## 🧹 COMPLETE CLEAN START
```bash
# Remove all NetPilot iptables rules
iptables -t mangle -D FORWARD -j NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -D FORWARD -j NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -F NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_BLACKLIST 2>/dev/null || true

# Remove all TC rules
for interface in $(ls /sys/class/net/ | grep -v lo); do
    tc qdisc del dev $interface root 2>/dev/null || true
done

# Verify clean state
echo "=== VERIFICATION ==="
iptables -t mangle -L | grep -i netpilot || echo "No NetPilot chains ✅"
ping -c 3 8.8.8.8 && echo "Internet working ✅"
```

## 🚀 ONE-LINER EMERGENCY CLEAN
```bash
for i in $(ls /sys/class/net/ | grep -v lo); do tc qdisc del dev $i root 2>/dev/null || true; done; iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true; iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true; iptables -t mangle -D FORWARD -j NETPILOT_WHITELIST 2>/dev/null || true; echo "Clean ✅"
```
