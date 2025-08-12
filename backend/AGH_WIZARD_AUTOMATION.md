## AdGuard Home Full Headless Setup (No GUI Wizard) — OpenWrt 23.05

This guide is the canonical source for building an installer that configures AdGuard Home (AGH) behind the scenes for a general user: frees port 53, downloads the correct official binary for the router’s architecture, seeds a minimal, valid YAML, patches the init script to use it, starts the service, and verifies that DNS is listening on :53 and API on 127.0.0.1:3000.

Run all commands on the router (SSH). Copy/paste blocks are safe for BusyBox/ash.

### 0) Prerequisites and variables

```sh
set -e
AGH_DIR=/opt/AdGuardHome
ARCHIVE=/tmp/AdGuardHome.tar.gz

# Optional: install SSL-capable downloader and certs if needed for HTTPS
opkg update || true
opkg install ca-bundle ca-certificates uclient-fetch 2>/dev/null || true

# Helper: robust downloader selection
dl() {
  url="$1"; out="$2"
  if command -v uclient-fetch >/dev/null 2>&1; then uclient-fetch -q -O "$out" "$url"; return $?; fi
  if command -v wget >/dev/null 2>&1; then wget -q -O "$out" "$url"; return $?; fi
  if command -v curl >/dev/null 2>&1; then curl -sSL -o "$out" "$url"; return $?; fi
  echo "No downloader available" >&2; return 1
}

# Helper: detect correct AdGuard Home binary URL
detect_agh_url() {
  # Allow override via env AGH_BIN_URL
  [ -n "$AGH_BIN_URL" ] && { echo "$AGH_BIN_URL"; return; }

  arch=$(uname -m 2>/dev/null || echo unknown)
  pkg=""
  if command -v opkg >/dev/null 2>&1 && opkg print-architecture 2>/dev/null | grep -q mipsel; then
    pkg=AdGuardHome_linux_mipsle_softfloat
  fi
  if [ -z "$pkg" ]; then
    case "$arch" in
      aarch64|arm64) pkg=AdGuardHome_linux_arm64 ;;
      armv7l|armv8l) pkg=AdGuardHome_linux_armv7 ;;
      mipsel*|mips*) pkg=AdGuardHome_linux_mipsle_softfloat ;;
      x86_64)        pkg=AdGuardHome_linux_amd64 ;;
      i686|i386)     pkg=AdGuardHome_linux_386 ;;
      *) echo "Unsupported arch: $arch (set AGH_BIN_URL manually)" >&2; exit 1 ;;
    esac
  fi
  echo "https://github.com/AdguardTeam/AdGuardHome/releases/latest/download/${pkg}.tar.gz"
}
```

### 1) Cleanup previous state (init, process, YAML, listeners)

```sh
# Stop/disable/remove existing init service
if [ -x /etc/init.d/AdGuardHome ]; then
  /etc/init.d/AdGuardHome disable || true
  /etc/init.d/AdGuardHome stop || true
  rm -f /etc/init.d/AdGuardHome
  rm -f /etc/rc.d/*AdGuardHome* 2>/dev/null || true
fi

# Kill stray process and stale pidfile
killall -q AdGuardHome || true
rm -f /var/run/AdGuardHome.pid 2>/dev/null || true

# Remove previous YAML (force clean start)
rm -f "$AGH_DIR/AdGuardHome.yaml" 2>/dev/null || true
mkdir -p "$AGH_DIR"
```

### 2) Download and install the official AdGuard Home binary (dynamic arch)

```sh
AGH_BIN_URL=$(detect_agh_url)
echo "Downloading: $AGH_BIN_URL"
dl "$AGH_BIN_URL" "$ARCHIVE"
[ -s "$ARCHIVE" ]
tar -xzf "$ARCHIVE" -C /opt
[ -x "$AGH_DIR/AdGuardHome" ]

cd "$AGH_DIR"
./AdGuardHome -s install  # creates /etc/init.d/AdGuardHome
```

### 3) Free port 53 (dnsmasq DNS off; DHCP stays on)

```sh
uci export dhcp > /root/dhcp.before-agh  # backup
uci set dhcp.@dnsmasq[0].port='0'
uci commit dhcp
/etc/init.d/dnsmasq restart
(netstat -ltnu 2>/dev/null | grep ':53') || echo 'port 53 free'
```

### 4) Force init to use explicit config/workdir (robustness)

```sh
SVC=/etc/init.d/AdGuardHome
if [ -x "$SVC" ]; then
  if grep -q '^cmd=' "$SVC"; then
    sed -i 's#^cmd=.*#cmd="/opt/AdGuardHome/AdGuardHome -c /opt/AdGuardHome/AdGuardHome.yaml -w /opt/AdGuardHome -s run"#' "$SVC"
  else
    printf '\ncmd="/opt/AdGuardHome/AdGuardHome -c /opt/AdGuardHome/AdGuardHome.yaml -w /opt/AdGuardHome -s run"\n' >> "$SVC"
  fi
  chmod +x "$SVC"
fi
```

### 5) Write minimal YAML (skip wizard) and secure permissions

```sh
cat > "$AGH_DIR/AdGuardHome.yaml" <<'EOF'
http:
  address: 127.0.0.1:3000

querylog:
  enabled: false

statistics:
  enabled: false

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
EOF
tr -d '\r' < "$AGH_DIR/AdGuardHome.yaml" > "$AGH_DIR/AdGuardHome.yaml.tmp" && mv "$AGH_DIR/AdGuardHome.yaml.tmp" "$AGH_DIR/AdGuardHome.yaml"
chmod 600 "$AGH_DIR/AdGuardHome.yaml"
chmod 700 "$AGH_DIR" 2>/dev/null || true
```

### 6) Start service and verify API and DNS

```sh
/etc/init.d/AdGuardHome restart
curl -sf http://127.0.0.1:3000/control/status
pgrep -fa AdGuardHome
netstat -lntu 2>/dev/null | grep -E ':(53|3000)[[:space:]]'
```

### 7) Disable logging and statistics (mandatory for lower RAM)

```sh
CFG=/opt/AdGuardHome/AdGuardHome.yaml
sed -i '/^querylog:/,/^[^ ]/ s/^\([[:space:]]*enabled:\).*/\1 false/' "$CFG"
sed -i '/^querylog:/,/^[^ ]/ s/^\([[:space:]]*file_enabled:\).*/\1 false/' "$CFG"
sed -i '/^statistics:/,/^[^ ]/ s/^\([[:space:]]*enabled:\).*/\1 false/' "$CFG"
/etc/init.d/AdGuardHome restart
```

Verify:
```sh
sed -n '/^querylog:/,/^[^ ]/p' /opt/AdGuardHome/AdGuardHome.yaml
sed -n '/^statistics:/,/^[^ ]/p' /opt/AdGuardHome/AdGuardHome.yaml
```

### 8) Rollback (if needed)

```sh
uci import dhcp < /root/dhcp.before-agh
uci commit dhcp
/etc/init.d/dnsmasq restart
```

### Troubleshooting

```sh
logread -e AdGuardHome | tail -n 200
sed -n '1,200p' "$AGH_DIR/AdGuardHome.yaml"
/opt/AdGuardHome/AdGuardHome -c "$AGH_DIR/AdGuardHome.yaml" -w "$AGH_DIR" --no-check-update --verbose 2>&1 | tail -n +1
```


