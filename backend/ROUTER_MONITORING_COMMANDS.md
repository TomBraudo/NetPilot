# Router Monitoring Commands Guide

This guide provides essential OpenWRT router commands for monitoring and data collection that can be used for NetPilot's monitoring features.

## 🌐 Bandwidth Monitoring (nlbwmon)

### Basic Data Retrieval
```bash
# Get current bandwidth data (human readable)
nlbw -c show

# Get bandwidth data in JSON format (best for API integration)
nl## 🗂️ Storage Monitoring

### Filesystem Structure Verification
```bash
# Check which filesystem each directory is on
df -h /tmp
df -h /etc
df -h /overlay

# Show all mount points and filesystem types
mount | grep -E "(tmp|etc|overlay)"

# Verify filesystem types and sizes
cat /proc/mounts | grep -E "(tmp|etc|overlay)"

# Show detailed filesystem info
findmnt /tmp
findmnt /etc
```

### Storage Space Analysis
```bash
# Compare storage usage across filesystems
echo "=== Filesystem Usage Comparison ==="
echo "/tmp space:"
df -h /tmp | awk 'NR==2{print "  Used: "$3" / "$2" ("$5")"}'
echo "/etc space (overlay):"  
df -h /overlay | awk 'NR==2{print "  Used: "$3" / "$2" ("$5")"}'
echo "/root space:"
df -h /root | awk 'NR==2{print "  Used: "$3" / "$2" ("$5")"}'

# Check if directories are on same filesystem
stat -f /tmp | grep "Type:"
stat -f /etc | grep "Type:"
```

### Database Location Verification
```bash
# Verify nlbwmon database configuration
echo "=== nlbwmon Database Configuration ==="
echo "Configured directory: $(uci get nlbwmon.@nlbwmon[0].database_directory)"
echo "Backup directory: /etc/nlbwmon_backup"

# Check actual database files exist
echo "=== Database Files Found ==="
ls -la /tmp/nlbwmon/ 2>/dev/null || echo "No database directory found"
echo "File count: $(ls /tmp/nlbwmon/*.db* 2>/dev/null | wc -l)"
echo "Total size: $(du -sh /tmp/nlbwmon/ 2>/dev/null || echo "0")"

# Verify file types and compression
echo "=== Database File Details ==="
file /tmp/nlbwmon/*.db* 2>/dev/null | head -3
ls -lh /tmp/nlbwmon/ | head -5
``` bandwidth data in CSV format
nlbw -c csv

# Commit pending data to database (ensures latest data)
nlbw -c commit

# Get CSV data grouped by MAC address, ordered by download traffic
nlbw -c csv -g mac -o -rx

# Get CSV data grouped by MAC address, ordered by upload traffic  
nlbw -c csv -g mac -o -tx

# Get CSV data with quiet output (no headers)
nlbw -c csv -g mac -o -tx -q
```

### Historical Data Access
```bash
# List available database files (chronological order)
ls -t /tmp/nlbwmon/*.db

# Query specific database file
nlbw -d /tmp/nlbwmon/20250731.db.gz -c json

# Get data from specific database in CSV format
nlbw -d /tmp/nlbwmon/20250731.db.gz -c csv -g mac -o -tx

# Get summary data from specific database (reduced data for performance)
nlbw -d /tmp/nlbwmon/20250731.db.gz -c csv -g mac -s
```

### Service Management
```bash
# Check nlbwmon service status
/etc/init.d/nlbwmon status

# Start/stop/restart nlbwmon service
/etc/init.d/nlbwmon start
/etc/init.d/nlbwmon stop
/etc/init.d/nlbwmon restart

# Check if nlbwmon process is running
ps | grep nlbwmon | grep -v grep

# Check Unix socket existence
ls -la /var/run/nlbwmon.sock
```

## 📊 System Resource Monitoring

### Memory Usage
```bash
# Memory usage (human readable)
free -h

# Memory usage (bytes)
free -b

# Memory usage (specific format)
free | grep Mem | awk '{print $3"/"$2}'  # Used/Total

# Get memory percentage
free | grep Mem | awk '{printf "%.1f%%\n", ($3/$2)*100}'
```

### Storage Usage
```bash
# Disk usage (human readable)
df -h

# Disk usage (bytes)
df -B1

# Check specific filesystem
df -h /overlay

# Check storage usage as percentage
df | grep overlay | awk '{print $5}'
```

### CPU and Load
```bash
# System uptime and load average
uptime

# CPU information
cat /proc/cpuinfo

# Current processes (top consumers)
top -n 1 -b

# Load average only
uptime | awk '{print $8,$9,$10}'
```

## 🔌 Network Interface Monitoring

### Interface Status
```bash
# List all network interfaces
ip link show

# Get interface statistics
cat /proc/net/dev

# Specific interface info
ip addr show br-lan
ip addr show eth0

# Interface traffic counters
cat /sys/class/net/br-lan/statistics/rx_bytes
cat /sys/class/net/br-lan/statistics/tx_bytes
```

### WiFi Monitoring
```bash
# WiFi status
uci show wireless

# Check if WiFi is enabled
uci get wireless.@wifi-device[0].disabled

# WiFi interface details
iwinfo

# Connected clients (if available)
iw dev wlan0 station dump
```

## 📡 Connected Devices Discovery

### ARP Table (Device Discovery)
```bash
# View ARP table (connected devices)
arp -a

# ARP table in different format
cat /proc/net/arp

# Get specific device MAC
arp 192.168.1.100

# ARP table with IP and MAC only
arp -a | awk '{print $2, $4}' | sed 's/[()]//g'
```

### DHCP Leases
```bash
# Current DHCP leases
cat /var/dhcp.leases

# DHCP leases formatted
cat /var/dhcp.leases | awk '{print $2, $3, $4}'  # MAC, IP, Hostname
```

### Network Scan
```bash
# Ping sweep of local network (192.168.1.x)
for i in {1..254}; do ping -c 1 -W 1 192.168.1.$i >/dev/null && echo "192.168.1.$i is up"; done

# Nmap-style scan (if nmap available)
nmap -sn 192.168.1.0/24
```

## 🔥 Firewall and Security Monitoring

### Connection Tracking
```bash
# Active connections
cat /proc/net/nf_conntrack

# Connection count
cat /proc/net/nf_conntrack | wc -l

# Connections by protocol
cat /proc/net/nf_conntrack | awk '{print $3}' | sort | uniq -c
```

### Firewall Rules
```bash
# List iptables rules
iptables -L -n -v

# NAT table rules
iptables -t nat -L -n -v

# Mangle table rules
iptables -t mangle -L -n -v
```

## ⚙️ Configuration Monitoring

### UCI Configuration
```bash
# Show all network configuration
uci show network

# Show firewall configuration
uci show firewall

# Show system configuration
uci show system

# Show wireless configuration
uci show wireless

# Show nlbwmon configuration
uci show nlbwmon
```

### System Information
```bash
# Router hostname
uci get system.@system[0].hostname

# LAN IP address
uci get network.lan.ipaddr

# System version
cat /etc/openwrt_release

# Kernel version
uname -r

# Hardware model
cat /proc/cpuinfo | grep "model name"
```

## 📈 Performance Monitoring

### Network Performance
```bash
# Interface packet counts
cat /sys/class/net/br-lan/statistics/rx_packets
cat /sys/class/net/br-lan/statistics/tx_packets

# Interface error counts
cat /sys/class/net/br-lan/statistics/rx_errors
cat /sys/class/net/br-lan/statistics/tx_errors

# Interface dropped packets
cat /sys/class/net/br-lan/statistics/rx_dropped
cat /sys/class/net/br-lan/statistics/tx_dropped
```

### Kernel Buffer Settings
```bash
# Check kernel network buffers
sysctl net.core.rmem_max
sysctl net.core.rmem_default
sysctl net.core.netdev_max_backlog

# All network-related kernel parameters
sysctl -a | grep net.core
```

## 🔧 Service Status Monitoring

### System Services
```bash
# Check if service is enabled
/etc/init.d/dropbear enabled && echo "enabled" || echo "disabled"

# Check multiple services
for service in network firewall dnsmasq nlbwmon; do
    echo -n "$service: "
    /etc/init.d/$service enabled && echo "enabled" || echo "disabled"
done

# List all available services
ls /etc/init.d/
```

### Process Monitoring
```bash
# All running processes
ps aux

# Specific service processes
ps | grep dropbear
ps | grep dnsmasq
ps | grep nlbwmon

# Process tree
ps -ef --forest
```

## 📝 Log Monitoring

### System Logs
```bash
# System log (recent entries)
logread

# Continuous log monitoring
logread -f

# Kernel messages
dmesg

# Last 20 log entries
logread | tail -20
```

## 🎯 API-Ready Commands for NetPilot Integration

### Bandwidth Data (JSON Format)
```bash
# Today's data (JSON - best for APIs)
nlbw -c commit && nlbw -c json

# Historical data from specific day
nlbw -d /tmp/nlbwmon/$(date -d '7 days ago' +%Y%m%d).db.gz -c json

# CSV data for processing
nlbw -c csv -g mac -o -tx -q | head -10
```

### System Status (Structured Output)
```bash
# Memory as percentage
free | awk 'NR==2{printf "%.2f%%\n", $3*100/$2}'

# Storage as percentage  
df /overlay | awk 'NR==2{print $5}'

# Uptime in seconds
cat /proc/uptime | awk '{print $1}'

# Connected devices count
cat /proc/net/arp | grep -v "IP address" | wc -l
```

### Device Information (Structured)
```bash
# Device list with MAC and IP
cat /proc/net/arp | grep -v "IP address" | awk '{print $1","$4","$6}'

# DHCP clients with hostnames
cat /var/dhcp.leases | awk '{print $3","$2","$4}'  # IP,MAC,Hostname
```

## 🚀 Advanced Monitoring Scripts

### Comprehensive Status Check
```bash
#!/bin/sh
echo "=== System Status ==="
echo "Uptime: $(uptime | awk '{print $3,$4}' | sed 's/,//')"
echo "Memory: $(free | awk 'NR==2{printf "%.1f%%\n", ($3/$2)*100}')"
echo "Storage: $(df /overlay | awk 'NR==2{print $5}')"
echo "Load: $(uptime | awk '{print $10}')"

echo "=== Network Status ==="
echo "Connected devices: $(cat /proc/net/arp | grep -v "IP address" | wc -l)"
echo "nlbwmon status: $(/etc/init.d/nlbwmon status)"

echo "=== Top Bandwidth Users ==="
nlbw -c show | head -5
```

### Bandwidth Summary
```bash
#!/bin/sh
echo "=== Today's Bandwidth Usage ==="
nlbw -c commit >/dev/null 2>&1
nlbw -c csv -g mac -o -tx -q | head -10 | while IFS=',' read mac ip host dl ul total; do
    echo "$host ($ip): Down=${dl}B Up=${ul}B Total=${total}B"
done
```

---

## �️ Storage Monitoring

### Filesystem Structure Verification
```bash
# Check which filesystem each directory is on
df -h /tmp
df -h /etc
df -h /overlay

# Show all mount points and filesystem types
mount | grep -E "(tmp|etc|overlay)"

# Verify filesystem types and sizes
cat /proc/mounts | grep -E "(tmp|etc|overlay)"

# Show detailed filesystem info
findmnt /tmp
findmnt /etc
```

### Database Storage Usage
```bash
# Check nlbwmon database storage usage
du -sh /tmp/nlbwmon/
ls -lah /tmp/nlbwmon/ | wc -l  # Count database files

# Verify database files are in correct location
ls -la /tmp/nlbwmon/
file /tmp/nlbwmon/*.db* 2>/dev/null | head -5 || echo "file command not available"

# Alternative verification without 'file' command
ls -lh /tmp/nlbwmon/*.db* 2>/dev/null
hexdump -C /tmp/nlbwmon/*.db.gz 2>/dev/null | head -2  # Check gzip header

# Check nlbwmon configuration directory
uci get nlbwmon.@nlbwmon[0].database_directory
ls -la /etc/nlbwmon_backup/ 2>/dev/null || echo "Backup directory not found"

# Monitor storage growth over time
df -h /tmp && du -sh /tmp/nlbwmon/

# Calculate days of data stored
ls /tmp/nlbwmon/*.db* | wc -l
```

### Storage Cleanup (if needed)
```bash
# Remove oldest database files (keep last 20 days)
cd /tmp/nlbwmon && ls -t *.db* | tail -n +21 | xargs rm -f

# Check storage after cleanup
du -sh /tmp/nlbwmon/
```

## �💡 Usage Notes

1. **Data Freshness**: Always run `nlbw -c commit` before querying bandwidth data to ensure latest information
2. **JSON vs CSV**: Use JSON for API integration, CSV for data processing
3. **Historical Data**: Database files are named by date (YYYYMMDD.db.gz)
4. **Performance**: Use summary commands (`-s` flag) for large datasets
5. **Error Handling**: Check command exit codes and handle "Bad file descriptor" errors gracefully
6. **Network Range**: Adjust IP ranges (192.168.1.x) to match your network configuration
7. **Storage Monitoring**: Monitor `/tmp/nlbwmon/` storage usage regularly (target: <25 MiB for safety)

This guide provides the foundation for implementing comprehensive monitoring features in your NetPilot application!
