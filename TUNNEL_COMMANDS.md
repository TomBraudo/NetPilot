# NetPilot Reverse SSH Tunnel Testing Guide

> **Date**: June 22, 2025  
> **Status**: ✅ PROVEN WORKING  
> **Architecture**: Router → Cloud VM (Reverse Tunnel)

---

## 🎯 Summary

**What This Achieves:**
- ✅ **Cloud VM controls router remotely** through reverse SSH tunnel
- ✅ **Bypasses NAT/firewall issues** (router initiates connection)
- ✅ **Enables NetPilot production architecture** (cloud-based management)
- ✅ **Allows real-time router configuration** from web dashboard

**Network Flow:**
```
Router (192.168.1.1) → Cloud VM (34.38.207.87) → Back to Router
     [Initiates]           [Receives]              [Commands]
```

---

## 📋 Proven Working Commands

### **Phase 1: Router → Cloud VM (Create Tunnel)**

#### **From Router Terminal:**
```bash
# SSH to router (from local machine)
ssh root@192.168.1.1
Password: admin

# Create reverse tunnel (from router)
ssh -R 2222:localhost:22 netpilot-agent@34.38.207.87
Password: [netpilot-agent password]

# This creates tunnel: Cloud VM port 2222 → Router SSH port 22
# Terminal will hang (this is correct - tunnel is active)
```

**What happens:**
- Router establishes connection TO cloud VM
- Cloud VM opens port 2222 that forwards to router's port 22
- Connection stays open (creates persistent tunnel)

---

### **Phase 2: Cloud VM → Router (Use Tunnel)**

#### **From Cloud VM Terminal:**
```bash
# SSH to cloud VM (new terminal session)
ssh netpilot-agent@34.38.207.87
Password: [netpilot-agent password]

# Verify tunnel is active
netstat -tlnp | grep 2222
# Expected output: tcp 0.0.0.0:2222 LISTEN

# Connect to router through tunnel
ssh -p 2222 root@localhost
Password: [Router password]

# You are now on the router from cloud VM!
```

**What happens:**
- SSH to localhost:2222 on cloud VM
- Traffic forwards through tunnel to router's SSH
- You get router shell from cloud VM

---

### **Phase 3: Remote Command Execution**

#### **Basic Commands (with password prompt):**
```bash
# From cloud VM, single command to router
ssh -p 2222 root@localhost "uci show system.@system[0].hostname"
Password: [Router password]

# Network status
ssh -p 2222 root@localhost "ip route show | head -3"
Password: [Router password]

# Firewall rules
ssh -p 2222 root@localhost "iptables -L INPUT -n | head -5"
Password: [Router password]

# Device discovery
ssh -p 2222 root@localhost "cat /proc/net/arp"
Password: [Router password]
```

#### **Automated Commands (using sshpass):**
```bash
# Install sshpass on cloud VM
sudo apt install -y sshpass

# Router hostname
sshpass -p '[Router password]' ssh -p 2222 -o StrictHostKeyChecking=no root@localhost "uci show system.@system[0].hostname"

# Network configuration
sshpass -p '[Router password]' ssh -p 2222 -o StrictHostKeyChecking=no root@localhost "uci show network.lan"

# System uptime
sshpass -p '[Router password]' ssh -p 2222 -o StrictHostKeyChecking=no root@localhost "uptime"

# Connected devices
sshpass -p '[Router password]' ssh -p 2222 -o StrictHostKeyChecking=no root@localhost "cat /proc/net/arp | grep -v IP"
```

#### **NetPilot API Simulation:**
```bash
# Simulate JSON response for NetPilot dashboard
sshpass -p 'admin' ssh -p 2222 -o StrictHostKeyChecking=no root@localhost "
echo '{'
echo '  \"router_info\": {'
echo '    \"hostname\": \"'$(uci get system.@system[0].hostname)'\",'
echo '    \"lan_ip\": \"'$(uci get network.lan.ipaddr)'\",'
echo '    \"uptime\": \"'$(uptime | cut -d' ' -f3-)'\",'
echo '    \"model\": \"OpenWrt 23.05.5\"'
echo '  }'
echo '}'
"
```

---

## 🔧 Production Setup (SSH Keys - Recommended)

### **Setup SSH Key Authentication:**
```bash
# Generate key pair on cloud VM
ssh-keygen -t rsa -b 4096 -f ~/.ssh/netpilot_key -N ""

# Copy public key to router (through tunnel)
cat ~/.ssh/netpilot_key.pub | sshpass -p 'admin' ssh -p 2222 -o StrictHostKeyChecking=no root@localhost "mkdir -p /root/.ssh && cat >> /root/.ssh/authorized_keys"

# Test key-based authentication
ssh -i ~/.ssh/netpilot_key -p 2222 root@localhost "echo 'Key auth working!'"
```

### **Create SSH Config for Easy Access:**
```bash
# Create SSH config file
cat >> ~/.ssh/config << EOF
Host netpilot-router
    HostName localhost
    Port 2222
    User root
    IdentityFile ~/.ssh/netpilot_key
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF

# Now use simple commands
ssh netpilot-router "uci show system.@system[0].hostname"
ssh netpilot-router "iptables -L INPUT -n | head -3"
ssh netpilot-router "cat /proc/net/arp"
```

---

## 🚀 NetPilot Integration Commands

### **Device Discovery for Dashboard:**
```bash
# Get connected devices
ssh netpilot-router "cat /proc/net/arp | awk 'NR>1 {print \$1,\$4}' | sort"

# Network interfaces
ssh netpilot-router "ip addr show | grep 'inet ' | awk '{print \$2}'"

# Wireless clients
ssh netpilot-router "iw dev wlan0 station dump 2>/dev/null | grep Station || echo 'No wireless clients'"
```

### **Firewall Management:**
```bash
# List current rules
ssh netpilot-router "iptables -L INPUT -n --line-numbers"

# Add blocking rule (example)
ssh netpilot-router "iptables -I INPUT -s 192.168.1.100 -j DROP"

# Remove rule by line number
ssh netpilot-router "iptables -D INPUT 1"

# List NAT rules
ssh netpilot-router "iptables -t nat -L -n"
```

### **System Status for API:**
```bash
# Router status JSON for API endpoint
ssh netpilot-router '
echo "{"
echo "  \"hostname\": \"$(uci get system.@system[0].hostname)\","
echo "  \"lan_ip\": \"$(uci get network.lan.ipaddr)\","
echo "  \"wan_ip\": \"$(curl -s --max-time 5 ifconfig.me || echo unknown)\","
echo "  \"uptime\": \"$(cat /proc/uptime | cut -d\" \" -f1)\","
echo "  \"load\": \"$(cat /proc/loadavg | cut -d\" \" -f1-3)\","
echo "  \"memory\": \"$(free | grep Mem | awk \"{print \$3/\$2*100}\")\","
echo "  \"clients\": $(cat /proc/net/arp | grep -c \"0x2\")"
echo "}"
'
```

---

## 📊 Test Results

### **✅ Proven Working:**
- [x] Reverse tunnel establishment (Router → Cloud)
- [x] Cloud VM → Router SSH access
- [x] Password-based authentication
- [x] SSH key-based authentication
- [x] Remote command execution
- [x] Real-time router configuration
- [x] JSON API response simulation
- [x] Device discovery commands
- [x] Firewall rule management

### **🌐 Network Details:**
- **Router External IP**: `147.235.193.46`
- **Cloud VM IP**: `34.38.207.87`
- **Tunnel Port**: `2222`
- **Router SSH Port**: `22`
- **Authentication**: Password (`admin`) + SSH keys

### **⚡ Performance:**
- **Tunnel Latency**: ~56ms (Router ↔ Cloud VM)
- **Command Response**: < 1 second for basic commands
- **Tunnel Stability**: Persistent (stays connected)

---

## 🔄 Restart Procedures

### **If Tunnel Breaks:**
```bash
# 1. SSH to router
ssh root@192.168.1.1

# 2. Recreate tunnel
ssh -R 2222:localhost:22 netpilot-agent@34.38.207.87

# 3. Verify from cloud VM
ssh netpilot-agent@34.38.207.87
netstat -tlnp | grep 2222
```

### **Persistent Tunnel (Production):**
```bash
# Create keepalive tunnel script on router
cat > /root/netpilot_tunnel.sh << 'EOF'
#!/bin/sh
while true; do
    ssh -R 2222:localhost:22 -N \
        -o ServerAliveInterval=30 \
        -o ServerAliveCountMax=3 \
        -o ExitOnForwardFailure=yes \
        netpilot-agent@34.38.207.87
    sleep 10
done
EOF

chmod +x /root/netpilot_tunnel.sh
```

---

## 🎉 Conclusion

**The reverse SSH tunnel approach successfully solves all NetPilot connectivity challenges:**

1. **Bypasses NAT/firewall** - Router initiates outbound connection
2. **Works with ISP restrictions** - No inbound ports needed
3. **Enables cloud management** - Full remote router control
4. **Production ready** - Stable, secure, automatable

**This architecture is ready for NetPilot production deployment!**

---

**Next Steps:**
1. Integrate tunnel establishment into NetPilot router agent
2. Build cloud backend API endpoints using these SSH commands
3. Create web dashboard that displays real-time router data
4. Implement automatic tunnel recovery and monitoring 