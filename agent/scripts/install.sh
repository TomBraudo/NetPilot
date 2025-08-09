#!/bin/sh
set -e

#============ Configuration =============#
FLAG_DIR="/etc/netpilot/flags/agh_install"
mkdir -p "$FLAG_DIR"

AGH_BASE_DIR="/opt"
AGH_WORKDIR="$AGH_BASE_DIR/AdGuardHome"

# REST API port (bind localhost only)
AGH_API_PORT=3000

DNSMASQ_CONF="/etc/config/dhcp"
#=======================================#

# ash/POSIX-safe retry helper
retry() {
  max_attempts="$1"; shift
  sleep_secs="$1"; shift
  attempt_num=1
  while :; do
    "$@" && return 0
    if [ "$attempt_num" -ge "$max_attempts" ]; then
      echo "[retry] Attempt $attempt_num failed! No more retries left."
      return 1
    fi
    echo "[retry] Attempt $attempt_num failed! Retrying in $sleep_secs seconds..."
    sleep "$sleep_secs"
    attempt_num=$((attempt_num + 1))
  done
}

# Prefer ss; fallback to netstat
port_listen_check() {
  port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -lntu | grep -E ":${port}[[:space:]]" >/dev/null 2>&1
  else
    netstat -lntu 2>/dev/null | grep -E ":${port}[[:space:]]" >/dev/null 2>&1
  fi
}

detect_arch() {
  # Allow override via env AGH_PACKAGE or AGH_BINARY_URL
  if [ -n "$AGH_BINARY_URL" ]; then
    echo "$AGH_BINARY_URL"
    return 0
  fi

  arch="$(uname -m 2>/dev/null || echo unknown)"
  if command -v opkg >/dev/null 2>&1; then
    if opkg print-architecture 2>/dev/null | grep -q mipsel; then
      pkg="AdGuardHome_linux_mipsle_softfloat"
    fi
  fi
  if [ -z "$pkg" ]; then
    case "$arch" in
      aarch64|arm64) pkg="AdGuardHome_linux_arm64" ;;
      armv7l|armv8l) pkg="AdGuardHome_linux_armv7" ;;
      mipsel*|mips*) pkg="AdGuardHome_linux_mipsle_softfloat" ;;
      x86_64)        pkg="AdGuardHome_linux_amd64" ;;
      *) echo "[detect_arch] Unsupported arch '$arch'. Set AGH_BINARY_URL to override." >&2; return 1 ;;
    esac
  fi
  echo "https://github.com/AdguardTeam/AdGuardHome/releases/latest/download/${pkg}.tar.gz"
}

download_binary() {
  flag_file="$FLAG_DIR/download_done"
  [ -f "$flag_file" ] && { echo "[download_binary] Already done, skipping."; return 0; }

  echo "[download_binary] Determining download URL..."
  AGH_BINARY_URL_RESOLVED="$(detect_arch)" || return 1
  ARCHIVE="/tmp/AdGuardHome.tar.gz"
  echo "[download_binary] Downloading: $AGH_BINARY_URL_RESOLVED"

  downloader=""
  if command -v wget >/dev/null 2>&1; then downloader="wget -q -O"; fi
  if [ -z "$downloader" ] && command -v uclient-fetch >/dev/null 2>&1; then downloader="uclient-fetch -q -O"; fi
  if [ -z "$downloader" ] && command -v curl >/dev/null 2>&1; then downloader="curl -sSL -o"; fi
  [ -z "$downloader" ] && { echo "[download_binary] No downloader found (wget/uclient-fetch/curl)." >&2; return 1; }

  retry 3 3 sh -c "$downloader '$ARCHIVE' '$AGH_BINARY_URL_RESOLVED'"
  [ -s "$ARCHIVE" ] || { echo "[download_binary] Error: Downloaded archive is empty." >&2; return 1; }
  echo "[download_binary] Download complete."
  touch "$flag_file"
}

extract_binary() {
  flag_file="$FLAG_DIR/extract_done"
  [ -f "$flag_file" ] && { echo "[extract_binary] Already done, skipping."; return 0; }

  echo "[extract_binary] Extracting archive to $AGH_BASE_DIR ..."
  mkdir -p "$AGH_BASE_DIR"
  retry 3 3 tar -xzf /tmp/AdGuardHome.tar.gz -C "$AGH_BASE_DIR"
  if [ ! -x "$AGH_WORKDIR/AdGuardHome" ]; then
    echo "[extract_binary] Error: $AGH_WORKDIR/AdGuardHome not found after extraction." >&2
    return 1
  fi
  echo "[extract_binary] Extraction complete."
  touch "$flag_file"
}

snapshot_dnsmasq() {
  flag_file="$FLAG_DIR/snapshot_done"
  [ -f "$flag_file" ] && return 0
  echo "[snapshot_dnsmasq] Saving current dnsmasq UCI to /root/dhcp.before-agh"
  uci export dhcp > /root/dhcp.before-agh || true
  touch "$flag_file"
}

disable_dnsmasq_dns() {
  flag_file="$FLAG_DIR/disable_dnsmasq_done"
  [ -f "$flag_file" ] && { echo "[disable_dnsmasq_dns] Already done, skipping."; return 0; }
  echo "[disable_dnsmasq_dns] Disabling dnsmasq DNS (port=0) to free port 53..."
  uci set dhcp.@dnsmasq[0].port='0'
  uci commit dhcp
  retry 3 3 /etc/init.d/dnsmasq restart
  # Verify that port 53 is free
  if port_listen_check 53; then
    echo "[disable_dnsmasq_dns] Port 53 still in use after dnsmasq change." >&2
    return 1
  fi
  echo "[disable_dnsmasq_dns] Port 53 is free."
  touch "$flag_file"
}

disable_logs_stats() {
  echo "[logs] Disabling querylog and statistics (RAM saving)"
  CFG="$AGH_WORKDIR/AdGuardHome.yaml"
  if [ ! -f "$CFG" ]; then
    echo "[logs] Config not found at $CFG" >&2
    return 1
  fi
  sed -i '/^querylog:/,/^[^ ]/ s/^\([[:space:]]*enabled:\).*/\1 false/' "$CFG"
  sed -i '/^querylog:/,/^[^ ]/ s/^\([[:space:]]*file_enabled:\).*/\1 false/' "$CFG"
  sed -i '/^statistics:/,/^[^ ]/ s/^\([[:space:]]*enabled:\).*/\1 false/' "$CFG"
}

create_minimal_config() {
  # Pre-seed a valid YAML to bypass the wizard
  AGH_CONFIG="$AGH_WORKDIR/AdGuardHome.yaml"
  echo "[config] Writing wizard-less YAML at $AGH_CONFIG"
  cat > "$AGH_CONFIG" <<'EOF'
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
  [ -s "$AGH_CONFIG" ] || { echo "[config] Failed to create YAML" >&2; return 1; }
  # Normalize line endings and permissions
  tr -d '\r' < "$AGH_CONFIG" > "$AGH_CONFIG.tmp" && mv "$AGH_CONFIG.tmp" "$AGH_CONFIG"
  chmod 600 "$AGH_CONFIG" || true
  chmod 700 "$AGH_WORKDIR" 2>/dev/null || true
}

detect_service_name() {
  if [ -x /etc/init.d/AdGuardHome ]; then echo /etc/init.d/AdGuardHome; return 0; fi
  if [ -x /etc/init.d/adguardhome ]; then echo /etc/init.d/adguardhome; return 0; fi
  echo ""; return 1
}

install_service() {
  flag_file="$FLAG_DIR/install_done"
  [ -f "$flag_file" ] && { echo "[install_service] Already done, skipping."; return 0; }
  echo "[install_service] Installing AdGuard Home service..."
  ( cd "$AGH_WORKDIR" && ./AdGuardHome -s install )
  svc="$(detect_service_name || true)"
  [ -n "$svc" ] || { echo "[install_service] Could not detect init script after install." >&2; return 1; }
  chmod +x "$svc" || true
  "$svc" enable
  echo "[install_service] Service installed and enabled ($svc)."
  touch "$flag_file"
}

patch_init_script() {
  svc="$(detect_service_name || true)"
  [ -n "$svc" ] || { echo "[patch_init] Init script not found" >&2; return 1; }
  echo "[patch_init] Forcing init cmd to use -c and -w paths"
  if grep -q '^cmd=' "$svc"; then
    sed -i 's#^cmd=.*#cmd="/opt/AdGuardHome/AdGuardHome -c /opt/AdGuardHome/AdGuardHome.yaml -w /opt/AdGuardHome -s run"#' "$svc"
  else
    printf '\ncmd="/opt/AdGuardHome/AdGuardHome -c /opt/AdGuardHome/AdGuardHome.yaml -w /opt/AdGuardHome -s run"\n' >> "$svc"
  fi
  chmod +x "$svc" || true
}

start_service() {
  flag_file="$FLAG_DIR/start_done"
  [ -f "$flag_file" ] && { echo "[start_service] Already done, skipping."; return 0; }
  svc="$(detect_service_name || true)"
  [ -n "$svc" ] || { echo "[start_service] Init script not found." >&2; return 1; }
  echo "[start_service] Starting AdGuard Home service..."
  retry 3 3 "$svc" start
  retry 3 3 sh -c "'$svc' status | grep -qi running"
  echo "[start_service] Service running."
  touch "$flag_file"
}

verify() {
  flag_file="$FLAG_DIR/verify_done"
  [ -f "$flag_file" ] && { echo "[verify] Already done, skipping."; return 0; }
  echo "[verify] Verifying AdGuard Home service..."
  svc="$(detect_service_name || true)"
  [ -n "$svc" ] || { echo "[verify] Init script not found." >&2; return 1; }
  retry 3 3 sh -c "'$svc' status | grep -qi running" || { echo "[verify] Service not running" >&2; return 1; }
  retry 5 2 sh -c 'pgrep -fa AdGuardHome >/dev/null' || { echo "[verify] No AdGuardHome process" >&2; return 1; }
  retry 5 2 port_listen_check 53 || { echo "[verify] Port 53 not listening" >&2; return 1; }
  retry 5 2 sh -c "curl -sf http://127.0.0.1:$AGH_API_PORT/control/status >/dev/null" || { echo "[verify] API not responsive" >&2; return 1; }
  # Basic DNS test from router
  if command -v nslookup >/dev/null 2>&1; then
    retry 3 2 nslookup openwrt.org 127.0.0.1 >/dev/null 2>&1 || echo "[verify] nslookup test failed (non-fatal)"
  fi
  echo "[verify] All checks passed."
  touch "$flag_file"
}

rollback_dnsmasq() {
  if [ -f /root/dhcp.before-agh ]; then
    echo "[rollback] Restoring dnsmasq UCI snapshot..."
    uci import dhcp < /root/dhcp.before-agh || true
    uci commit dhcp || true
    /etc/init.d/dnsmasq restart || true
  fi
}

stop_existing() {
  echo "[pre] Stopping any running AdGuardHome and freeing port 53..."
  svc="$(detect_service_name || true)"
  if [ -n "$svc" ]; then
    "$svc" disable || true
    "$svc" stop || true
  fi
  killall -q AdGuardHome || true
  # ensure pidfile cleaned
  rm -f /var/run/AdGuardHome.pid 2>/dev/null || true
}

cleanup_existing_service() {
  # Remove any existing init scripts to avoid "Init already exists"
  svc="$(detect_service_name || true)"
  if [ -n "$svc" ]; then
    echo "[pre] Removing existing init script $svc"
    "$svc" disable || true
    rm -f "$svc" || true
    # remove rc.d symlinks if present
    rm -f /etc/rc.d/*AdGuardHome* 2>/dev/null || true
  fi
}

main() {
  # Allow FORCE=1 to reset flags for a clean run
  if [ "${FORCE:-0}" = "1" ]; then
    echo "[init] FORCE=1 → clearing flags in $FLAG_DIR"
    rm -f "$FLAG_DIR"/* 2>/dev/null || true
    cleanup_existing_service || true
    # Ensure dnsmasq is restored to a known state (port 53) before downloads
    echo "[init] FORCE=1 → restoring dnsmasq DNS to port 53 for connectivity"
    uci set dhcp.@dnsmasq[0].port='53' 2>/dev/null || true
    uci commit dhcp 2>/dev/null || true
    /etc/init.d/dnsmasq restart || true
    # Remove existing YAML to force clean regeneration
    if [ -f "$AGH_WORKDIR/AdGuardHome.yaml" ]; then
      echo "[init] FORCE=1 → deleting old YAML at $AGH_WORKDIR/AdGuardHome.yaml"
      rm -f "$AGH_WORKDIR/AdGuardHome.yaml" 2>/dev/null || true
    fi
    echo "[init] FORCE=1 → removing $AGH_WORKDIR"
    rm -rf "$AGH_WORKDIR" 2>/dev/null || true
  fi

  stop_existing || true

  # Download and install before DNS changes to keep connectivity
  if ! download_binary; then echo "[main] Download failed" >&2; exit 1; fi
  if ! extract_binary; then echo "[main] Extract failed" >&2; exit 1; fi
  if ! install_service; then echo "[main] Service install failed" >&2; exit 1; fi
  patch_init_script || true

  # Free port 53 and configure
  snapshot_dnsmasq || true
  if ! disable_dnsmasq_dns; then rollback_dnsmasq; echo "[main] dnsmasq reconfigure failed" >&2; exit 1; fi
  if ! create_minimal_config; then rollback_dnsmasq; echo "[main] Config creation failed" >&2; exit 1; fi

  # Restart cleanly and verify base health
  stop_existing || true
  if ! start_service; then rollback_dnsmasq; echo "[main] Service start failed" >&2; exit 1; fi
  if ! verify; then rollback_dnsmasq; echo "[main] Verification failed" >&2; exit 1; fi

  # Enforce RAM savings
  if ! disable_logs_stats; then echo "[main] Failed to disable logs/stats" >&2; exit 1; fi
  svc="$(detect_service_name || true)"; [ -n "$svc" ] && "$svc" restart || true
  retry 5 2 sh -c "curl -sf http://127.0.0.1:$AGH_API_PORT/control/status >/dev/null"

  echo "[main] AdGuard Home successfully installed and running with low RAM config."
}

main
