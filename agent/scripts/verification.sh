#!/bin/sh
set -e

FLAG_DIR="/etc/netpilot/flags/agh_install"
mkdir -p "$FLAG_DIR"

AGH_UI_PORT=3000

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

detect_service_name() {
  if [ -x /etc/init.d/AdGuardHome ]; then echo /etc/init.d/AdGuardHome; return 0; fi
  if [ -x /etc/init.d/adguardhome ]; then echo /etc/init.d/adguardhome; return 0; fi
  echo ""; return 1
}

port_listen_check() {
  port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -lntu | grep -E ":${port}[[:space:]]" >/dev/null 2>&1
  else
    netstat -lntu 2>/dev/null | grep -E ":${port}[[:space:]]" >/dev/null 2>&1
  fi
}

verify_service_running() {
  flag_file="$FLAG_DIR/verify_service_done"
  [ -f "$flag_file" ] && { echo "[verify] Already done, skipping."; return 0; }

  echo "[verify] Checking AdGuard Home service status..."
  svc="$(detect_service_name || true)"
  [ -n "$svc" ] || { echo "[verify] Init script not found." >&2; exit 1; }
  retry 3 3 sh -c "'$svc' status | grep -qi running"
  echo "[verify] Service is running."

  echo "[verify] Checking listeners and API..."
  retry 5 2 port_listen_check 53
  retry 5 2 sh -c "curl -sf http://127.0.0.1:$AGH_UI_PORT/control/status >/dev/null"

  echo "[verify] Performing a DNS test via loopback..."
  if command -v nslookup >/dev/null 2>&1; then
    retry 3 2 nslookup openwrt.org 127.0.0.1 >/dev/null 2>&1 || echo "[verify] nslookup test failed (non-fatal)"
  fi

  echo "[verify] Verification complete."
  touch "$flag_file"
}

main() {
  verify_service_running || { echo "[main] Verification failed"; exit 1; }
  echo "[main] Verification successful."
}

main
