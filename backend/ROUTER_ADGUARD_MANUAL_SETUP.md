# AdGuard Home on OpenWrt: API On, UI Not Exposed (Safe, Minimal, Automatic)

This guide configures AdGuard Home (AGH) on OpenWrt (e.g., ASUS RT-AX53U) so that:

- API is fully available on loopback for automation.
- Web UI is not exposed on the LAN/WAN (saves RAM and reduces attack surface).
- Per-device DNS filtering works for IPv4 and IPv6.
- Changes are safe and reversible.

---

## 1) Install AdGuard Home Daemon

Run on the router (SSH):

```sh
opkg update
opkg install adguardhome
```

Notes:
- This installs the AGH binary and init script at `/etc/init.d/adguardhome`.
- On OpenWrt via `opkg`, AGH stores config under `/etc/AdGuardHome`, not `/opt`.

---

## 2) Minimal Config: API On (loopback), UI Not Exposed, Logs/Stats Off

Create or overwrite `/etc/AdGuardHome/AdGuardHome.yaml`.

First, capture your LAN IPs (used below):

```sh
LAN4="$(uci -q get network.lan.ipaddr || ip -4 addr show br-lan | awk '/inet /{print $2}' | cut -d/ -f1)"; [ -z "$LAN4" ] && LAN4=192.168.1.1

# Prefer the router's ULA/GUA on br-lan as reported by ubus; fallback to ip(6), else leave empty
LAN6="$(ubus call network.interface.lan status 2>/dev/null | jsonfilter -e '@.ipv6-address[?(@.preferred==true)].address' | head -n1)"
[ -z "$LAN6" ] && LAN6="$(ip -6 addr show br-lan | awk '/inet6 .* scope global/{print $2; exit}' | cut -d/ -f1)"
```

Now write the config:

```sh
mkdir -p /etc/AdGuardHome
cat > /etc/AdGuardHome/AdGuardHome.yaml <<EOF
http:
  # Keep API reachable locally; UI shares this server but is not exposed off-router
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
chmod 600 /etc/AdGuardHome/AdGuardHome.yaml
```

Notes:
- API and UI share the same HTTP listener. Binding to `127.0.0.1` makes both inaccessible from LAN/WAN. Your automations can access the API locally or via SSH tunnel.
- Disabling `querylog` and `statistics` reduces RAM/flash usage.
- Port `5353` avoids conflicts with `dnsmasq` on port 53.
- AGH only binds to loopback; `dnsmasq` forwards queries locally so AGH does not need to bind to LAN IPv4/IPv6.

---

## 3) Enable and Start AdGuard Home

```sh
/etc/init.d/adguardhome enable
/etc/init.d/adguardhome start
/etc/init.d/adguardhome status || true
logread -e adguardhome | tail -n 50
```

Notes:
- If service fails, check the last 200 log lines: `logread -e adguardhome | tail -n 200`.
- Validate the YAML with `uclient-fetch -O- file:///etc/AdGuardHome/AdGuardHome.yaml | sed -n '1,120p'` if needed.

---

## 4) Forward All DNS to AdGuard Home (with Safety Backup)

Backup current DHCP/DNS settings first:

```sh
uci export dhcp > /root/dhcp.backup
```

Forward IPv4 and IPv6 DNS queries from `dnsmasq` to AGH:

```sh
uci set dhcp.@dnsmasq[0].noresolv='1'
uci -q del dhcp.@dnsmasq[0].server
uci add_list dhcp.@dnsmasq[0].server='127.0.0.1#5353'
uci add_list dhcp.@dnsmasq[0].server='[::1]#5353'
uci commit dhcp
/etc/init.d/dnsmasq restart
```

Notes:
- `noresolv=1` makes `dnsmasq` use only the listed upstreams (AGH). Ensure AGH is running before restarting `dnsmasq`.
- The IPv6 entry ensures local IPv6 queries are also sent to AGH.

---

## 5) Advertise Your Router as Sole DNS (DHCPv4 + RA/DHCPv6)

Use your detected IPs:

```sh
uci -q del dhcp.lan.dhcp_option
uci add_list dhcp.lan.dhcp_option="6,${LAN4}"
uci -q del dhcp.lan.dns
[ -n "$LAN6" ] && uci add_list dhcp.lan.dns="${LAN6}"
uci commit dhcp
/etc/init.d/dnsmasq restart
/etc/init.d/odhcpd restart
```

Notes:
- DHCP option 6 distributes the router’s IPv4 as DNS to clients.
- `odhcpd` advertises the IPv6 DNS via RA/DHCPv6 using the router’s actual ULA/GUA (for example, `fd1f:c83e:bacb::1`). If no IPv6 ULA/GUA is detected, IPv6 DNS advertisement is skipped.

---

## 6) Restore Backup If Needed (In Case of Issues)

```sh
uci import dhcp < /root/dhcp.backup
uci commit dhcp
/etc/init.d/dnsmasq restart
```

Notes:
- This reverts `dnsmasq` to its prior state if you lose connectivity or DNS resolution.

---

## 7) Verify DNS and API

DNS resolution via AGH from the router:

```sh
nslookup openwrt.org 127.0.0.1
nslookup openwrt.org ::1
```

API locally on the router (loopback):

```sh
curl -s http://127.0.0.1:3000/control/status
```

Remote API access (from your PC) via SSH tunnel:

```sh
ssh -L 3000:127.0.0.1:3000 root@<router_ip>
# Then use: http://127.0.0.1:3000
```

Notes:
- Expect HTTP 200 JSON from `/control/status`. If connection refused, ensure the service is running and bound to `127.0.0.1:3000`.
- Prefer SSH tunneling instead of exposing the API on LAN/WAN.

---

## 8) Use the AdGuard Home API (Full Control, No UI)

Examples (run on the router or through an SSH tunnel):

- List clients

```sh
curl -s http://127.0.0.1:3000/api/v1/clients
```

- Add a blocklist filter

```sh
curl -s -X POST http://127.0.0.1:3000/api/v1/filters \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "OISD Basic",
    "url": "https://abp.oisd.nl/basic"
  }'
```

- Assign per-device settings (replace DEVICE_ID)

```sh
curl -s -X PATCH http://127.0.0.1:3000/api/v1/clients/DEVICE_ID \
  -H 'Content-Type: application/json' \
  -d '{
    "filtering_enabled": true,
    "safesearch_enabled": false,
    "adult_block_enabled": false
  }'
```

Notes:
- If you configure users in YAML, add auth with `-u user:password`.
- Keeping the listener on loopback allows operating without auth safely; still prefer SSH tunnels for remote automation.

---

## 9) What to Avoid for Safety

- Avoid manual edits to `/etc/config/network` for DNS unless you know the implications.
- Avoid adding firewall DNAT/redirect rules for DNS until the forwarding works reliably.
- Avoid exposing the AGH HTTP port on LAN/WAN.

---

## Summary

This API-focused, minimal setup provides:

- Full IPv4/IPv6 DNS filtering via AdGuard Home with low resource usage.
- API available on loopback; UI not exposed on the network.
- Safe, reversible configuration with backups.
- Programmatic, per-device control using the REST API.

Ideal for automation-first deployments and remote management on devices like the ASUS RT-AX53U.

---
