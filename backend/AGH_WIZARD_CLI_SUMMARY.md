## AdGuard Home Wizard Replication via CLI — Summary

### Current router state (after minimal AGH setup)
- dnsmasq: DNS forwarding to AGH on loopback (router advertises itself as DNS; DHCP/RA normal).
- AGH: UI/API on `127.0.0.1:3000`, DNS on `127.0.0.1/::1:5353`; verified A/AAAA; tcpdump on `lo:5353` shows dnsmasq → AGH queries.
- Custom blocklist: subscription via `add_url` works; rules can use `$client=IP` (effective only when AGH can see real client IPs).
- Not in use currently: AGH on `:53` (direct) — attempts failed due to YAML/schema issues; rolled back to stable 5353+forwarding.

### Goal
- Replicate the GUI wizard in CLI: UI on `127.0.0.1:3000`, DNS on `:53`, AGH auto‑learns clients (no manual adds), minimal but useful logs/stats, and apply a custom blocklist per device.

### What we tried
- AGH on loopback 3000 + DNS on `127.0.0.1/::1:5353` with dnsmasq forwarding → verified A/AAAA resolution and path via tcpdump on `lo:5353`.
- Custom blocklist subscription via `add_url` + `refresh`; used `$client` in rules; avoided `add_rules` (404) and used `set_rules/add_url` instead.
- Switched dnsmasq DNS off and attempted to bind AGH directly to `:53` (wizard‑style) with minimal YAML.

### What worked
- DNS on `5353` with dnsmasq forwarding to AGH (IPv4/IPv6). Verified with `dig` and `tcpdump`.
- Custom list subscription (`/control/filtering/add_url`) and refresh pipeline.
- Clean diagnostics and rollback for dnsmasq/odhcpd and UCI.

### What didn’t
- `$client=IP` rules while dnsmasq forwarded to loopback: AGH saw source as `127.0.0.1`, so per‑client rules didn’t match.
- Moving AGH to `:53`: AGH often failed to start due to YAML schema/migration errors and config path confusion; service did not bind `:53`.
- Did not test “manual client add” path: a 404 occurred when trying a rule tied to a non‑existent client entry. This path is intentionally not desired; the feature must work without manually adding every client.

### Root causes & gotchas
- **Service config path mismatch**:
  - OpenWrt `adguardhome` procd service reads its config via UCI in `/etc/config/adguardhome`. If `config_file`/`work_dir` aren’t set to your YAML/work dir, the service may use a different path (logs indicated `/tmp/adguardhome` in some runs).
  - Set and verify:
    - `uci set adguardhome.@adguardhome[0].config_file='/etc/adguardhome.yaml'`
    - `uci set adguardhome.@adguardhome[0].work_dir='/var/adguardhome'`
    - `uci commit adguardhome && mkdir -p /var/adguardhome`
- **YAML pitfalls that crash AGH**:
  - Unquoted IPv6 bind host: use `"::"` not `::`.
  - `bootstrap_dns` must be a flat list (avoid nested arrays).
  - Avoid adding a top‑level `clients:` map manually (triggered migration errors like “unexpected type of clients”).
  - Errors seen: `cannot unmarshal !!seq into string`, `dns.bind_hosts … not a valid ip address`.
  - AGH rewrites YAML on successful starts (adds normalized sections), so the file content may change after a run.
- **“Internet works with :53 free”**:
  - Likely due to client/OS DNS cache, DoH, or IPv6 RDNSS; not proof that the router serves DNS.

### Verification checklist (next attempt)
- Confirm service uses your YAML:
  - `uci -q show adguardhome`
  - `sed -n '1,200p' /etc/init.d/adguardhome`
  - One foreground run to surface parse/migration errors:
    - `/usr/bin/AdGuardHome -c /etc/adguardhome.yaml -w /var/adguardhome --no-check-update --verbose | tail -n 80`
- Free `:53` from dnsmasq DNS (DHCP stays): `uci set dhcp.@dnsmasq[0].port='0'` → restart dnsmasq → verify `:53` free.
- Start AGH and verify listeners:
  - `pgrep -fa AdGuardHome`
  - `ss -lntu | grep -E ':(53|3000)[[:space:]]'`
  - `curl -s http://127.0.0.1:3000/control/status`
  - `dig @127.0.0.1 openwrt.org +short` and `dig @::1 openwrt.org +short`
- Force clients to use router DNS:
  - DHCPv4 option 6 → router IPv4; RA/DHCPv6 → router IPv6; restart dnsmasq/odhcpd; renew client leases.

### “Wizard‑like” YAML notes (v0.107.46)
- Keep YAML minimal; let AGH generate `clients`/other sections on first start.
- Quote `"::"` in `dns.bind_hosts`.
- `bootstrap_dns` must be a simple list of IPs.
- Prefer numeric upstreams initially; switch to DoT/DoH later.

Example minimal YAML skeleton (tested pattern)

```yaml
http:
  address: 127.0.0.1:3000

querylog:
  enabled: true
  file_enabled: false
  interval: 24h
  size_memory: 1000

statistics:
  enabled: true
  interval: 24h

filters: []

dns:
  bind_hosts:
    - 0.0.0.0
    - "::"
  port: 53
  cache_size: 4096
  protection_enabled: true
  upstream_dns:
    - 94.140.14.14
    - 94.140.15.15
  bootstrap_dns:
    - 9.9.9.9
    - 1.1.1.1
```

Start once in foreground to validate, then manage via init service.

### Applying a per‑device custom blocklist (no manual client adds)
- With AGH on `:53`, AGH sees the real client IPs, so blocklist rules with `$client=IP` apply to that device only.
- Host a tiny list (e.g., `/www/agh-custom/pc-netflix.txt` with `||netflix.com^$client=192.168.1.122`) and subscribe via `add_url` + `refresh`.
- For grouping later, use the `ctag` rule modifier (docs):
  - https://github.com/AdguardTeam/AdGuardHome/wiki/Hosts-Blocklists#ctag

### What to research/confirm on your box
- OpenWrt `adguardhome` init: which UCI keys are honored (`config_file`, `work_dir`) and when.
- AGH API for DNS config (switching port/binds) to avoid direct YAML edits.
- AGH YAML schema expectations for v0.107.46 (fields allowed; quoting rules).
- Client DoH usage and IPv6 RDNSS behavior when validating router‑served DNS.


