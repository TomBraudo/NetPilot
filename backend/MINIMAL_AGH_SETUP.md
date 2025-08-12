## Minimal, Invisible AdGuard Home on OpenWrt (Working Setup)

Goal: Run AdGuard Home (AGH) on the router with minimal RAM, UI/API bound to loopback only, and forward all router DNS (dnsmasq) to AGH on port 5353. Includes verification and rollback.

### 1) Install

```sh
opkg update
opkg install adguardhome
```

### 2) Configure AGH (loopback UI, low-RAM, local DNS on 5353)

Write `/etc/adguardhome.yaml`:

```sh
cat > /etc/adguardhome.yaml <<'EOF'
http:
  address: 127.0.0.1:3000

querylog:
  enabled: false

statistics:
  enabled: false

filters: []

dns:
  bind_hosts:
    - 127.0.0.1
    - ::1
  port: 5353
  cache_size: 4096
  protection_enabled: true
  upstream_dns:
    - tls://dns.adguard.com
EOF
chmod 600 /etc/adguardhome.yaml
```

Enable and start:

```sh
/etc/init.d/adguardhome enable
/etc/init.d/adguardhome start
```

Verify AGH is up (listeners + API):

```sh
pgrep -fa AdGuardHome
(if command -v ss >/dev/null 2>&1; then ss -lntu; else netstat -lntu 2>/dev/null; fi) \
  | grep -E '127\.0\.0\.1:(3000|5353)|\[::1\]:5353' || echo 'AGH listeners missing'

# Install curl if needed: opkg install curl
curl -s http://127.0.0.1:3000/control/status | sed -n '1,80p'
```

Direct DNS test against AGH (BusyBox nslookup cannot set port; use dig):

```sh
opkg install bind-dig
dig @127.0.0.1 -p 5353 openwrt.org +short
dig @127.0.0.1 -p 5353 AAAA openwrt.org +short
dig @::1       -p 5353 openwrt.org +short
dig @::1       -p 5353 AAAA openwrt.org +short
```

### 3) Forward dnsmasq to AGH (with backup and safe apply)

Backup and forward only to AGH on loopback:

```sh
uci export dhcp > /root/dhcp.before-agh2
uci set dhcp.@dnsmasq[0].noresolv='1'
uci -q del dhcp.@dnsmasq[0].server
uci add_list dhcp.@dnsmasq[0].server='127.0.0.1#5353'
uci commit dhcp
/etc/init.d/dnsmasq restart
```

Verify dnsmasq config and runtime:

```sh
uci -q show dhcp.@dnsmasq[0] | grep -E 'noresolv|server'
sed -n '1,200p' /var/etc/dnsmasq.conf.cfg* | grep -E '^(server=|no-resolv)'

dig openwrt.org +short
dig AAAA openwrt.org +short
```

Packet-level proof (optional):

```sh
opkg install tcpdump-mini
tcpdump -ni lo port 5353 -vv -c 4 &
sleep 1
dig openwrt.org +short; dig AAAA openwrt.org +short
wait
```

### 4) Rollback (restore previous dnsmasq state)

```sh
uci import dhcp < /root/dhcp.before-agh2
uci commit dhcp
/etc/init.d/dnsmasq restart
```

### Notes

- UI/API are bound to 127.0.0.1:3000 only (not exposed on LAN/WAN).
- Logging and statistics are disabled to save RAM.
- The kernel message `udhcpc: no lease, failing` during dnsmasq restarts is normal for WAN DHCP and does not affect LAN DNS.
- If you prefer `nslookup` with port selection, install the full tool: `opkg install bind-nslookup` and use `nslookup -port=5353 name 127.0.0.1`.


