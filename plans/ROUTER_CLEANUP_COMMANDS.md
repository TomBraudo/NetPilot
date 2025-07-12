# Router Storage Cleanup Commands

> **Critical**: Run these commands on your router to free up space before reinstalling packages.

## 🚨 **Emergency Space Cleanup**

### **SSH to Router First:**
```bash
ssh root@192.168.1.1
# Password: admin (or your router password)
```

### **1. Remove Failed Package Installations:**
```bash
# Clean up failed package installations and debris
opkg clean

# Remove broken package files
rm -rf /usr/lib/opkg/info/*openssh-client*
rm -rf /usr/lib/opkg/info/*autossh*
rm -rf /usr/lib/opkg/info/*ca-certificates*
rm -rf /usr/lib/opkg/info/*cron*

# Fix opkg status file if corrupted
cp /usr/lib/opkg/status /usr/lib/opkg/status.backup || true
echo "" > /usr/lib/opkg/status
```

### **2. Remove Unnecessary Pre-installed Packages:**
```bash
# Remove large optional packages that may be pre-installed
opkg remove --force-removal-of-dependent-packages luci-ssl
opkg remove --force-removal-of-dependent-packages luci-app-* 2>/dev/null || true
opkg remove --force-removal-of-dependent-packages luci-theme-* 2>/dev/null || true
opkg remove --force-removal-of-dependent-packages luci-proto-* 2>/dev/null || true

# Remove development/debugging tools if present
opkg remove --force-removal-of-dependent-packages gdb 2>/dev/null || true
opkg remove --force-removal-of-dependent-packages strace 2>/dev/null || true
opkg remove --force-removal-of-dependent-packages tcpdump-mini 2>/dev/null || true
```

### **3. Clear Temporary Files and Caches:**
```bash
# Clear all temporary files
rm -rf /tmp/*

# Clear package cache
rm -rf /var/opkg-lists/*

# Clear log files
rm -rf /var/log/*

# Clear any leftover kernel modules
rm -rf /lib/modules/*/kernel/drivers/usb/storage/ 2>/dev/null || true
rm -rf /lib/modules/*/kernel/drivers/scsi/ 2>/dev/null || true
```

### **4. Check Available Space:**
```bash
# Check current space usage
df -h

# Check overlay specifically
df -h /overlay

# List largest files/directories
du -sh /* 2>/dev/null | sort -h
```

### **5. Remove Non-Essential Network Packages:**
```bash
# Remove IPv6 packages if not needed
opkg remove --force-removal-of-dependent-packages odhcpd 2>/dev/null || true
opkg remove --force-removal-of-dependent-packages ip6tables 2>/dev/null || true

# Remove PPP if not using PPPoE
opkg remove --force-removal-of-dependent-packages ppp* 2>/dev/null || true

# Remove wireless drivers for unused radios
opkg remove --force-removal-of-dependent-packages kmod-ath* 2>/dev/null || true
```

### **6. Remove ALL Non-Essential Packages (Nuclear Package Cleanup):**
```bash
# ⚠️ WARNING: This removes ALL packages except core firmware packages
# This is the most aggressive cleanup - only use if desperate for space

# One-liner to remove ALL non-essential packages
opkg list-installed | awk '{print $1}' | grep -v -E '^(base-files|busybox|ca-bundle|dnsmasq|dropbear|firewall|fstools|fwtool|getrandom|ip6tables|iptables|iwinfo|jshn|jsonfilter|kernel|kmod-|libc|libgcc|libpthread|libubox|libubus|libuci|libuclient|libiwinfo|logd|mtd|netifd|nftables|odhcp6c|odhcpd-ipv6only|openwrt-keyring|opkg|ppp|procd|swconfig|ubox|ubus|ubusd|uci|uclient-fetch|urandom-seed|urngd|usign|wifi-scripts|wireless-regdb|wpad-basic)' | xargs -r opkg remove --force-removal-of-dependent-packages

# Alternative safer approach (removes packages one by one with confirmation)
echo "Packages that will be removed:"
opkg list-installed | awk '{print $1}' | grep -v -E '^(base-files|busybox|ca-bundle|dnsmasq|dropbear|firewall|fstools|fwtool|getrandom|ip6tables|iptables|iwinfo|jshn|jsonfilter|kernel|kmod-|libc|libgcc|libpthread|libubox|libubus|libuci|libuclient|libiwinfo|logd|mtd|netifd|nftables|odhcp6c|odhcpd-ipv6only|openwrt-keyring|opkg|ppp|procd|swconfig|ubox|ubus|ubusd|uci|uclient-fetch|urandom-seed|urngd|usign|wifi-scripts|wireless-regdb|wpad-basic)'
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read
opkg list-installed | awk '{print $1}' | grep -v -E '^(base-files|busybox|ca-bundle|dnsmasq|dropbear|firewall|fstools|fwtool|getrandom|ip6tables|iptables|iwinfo|jshn|jsonfilter|kernel|kmod-|libc|libgcc|libpthread|libubox|libubus|libuci|libuclient|libiwinfo|logd|mtd|netifd|nftables|odhcp6c|odhcpd-ipv6only|openwrt-keyring|opkg|ppp|procd|swconfig|ubox|ubus|ubusd|uci|uclient-fetch|urandom-seed|urngd|usign|wifi-scripts|wireless-regdb|wpad-basic)' | xargs -r opkg remove --force-removal-of-dependent-packages
```

### **7. Force Clean Package Database:**
```bash
# Recreate package database
opkg update --force-overwrite

# Remove orphaned dependencies
opkg list-installed | awk '{print $1}' > /tmp/installed.txt
for pkg in $(cat /tmp/installed.txt); do
    opkg whatdepends $pkg >/dev/null 2>&1 || echo "Orphaned: $pkg"
done
```

## 📊 **Check Results:**
```bash
# Final space check
echo "=== STORAGE STATUS ==="
df -h /overlay
echo ""
echo "=== LARGEST DIRECTORIES ==="
du -sh /overlay/* 2>/dev/null | sort -h | tail -10
echo ""
echo "=== AVAILABLE SPACE ==="
AVAILABLE=$(df /overlay | tail -1 | awk '{print $4}')
echo "Available: ${AVAILABLE}KB"
if [ "$AVAILABLE" -gt 500 ]; then
    echo "✅ Space cleanup successful! Ready for package installation."
else
    echo "⚠️  Still low on space. Consider firmware with more storage."
fi
```

## 🔄 **Complete Reset (Nuclear Option):**
```bash
# ⚠️ WARNING: This will reset router to factory defaults
# Only use if above steps don't free enough space

# Reset to factory defaults and reboot
firstboot -y && reboot
```

## 📝 **Notes:**
- Run commands one section at a time
- Check available space after each section
- Some packages may not exist on your router (errors are normal)
- Aim for at least 500KB free space before reinstalling NetPilot packages
- The cleanup should free up 1-3MB typically

## 🚀 **After Cleanup:**
1. **Reboot router**: `reboot`
2. **Wait 2 minutes** for router to fully restart
3. **Run NetPilot Agent** with optimized package list (only 9 packages now)
4. **Success!** Should install without storage issues 