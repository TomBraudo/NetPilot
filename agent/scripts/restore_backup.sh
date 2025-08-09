#!/bin/sh
set -e

FLAG_DIR="/etc/netpilot/flags/agh_install"
mkdir -p "$FLAG_DIR"

BACKUP_DIR="$1"

if [ -z "$BACKUP_DIR" ] || [ ! -d "$BACKUP_DIR" ]; then
  echo "Usage: $0 /path/to/backupdir"
  exit 1
fi

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

restore_configs() {
  echo "[restore] Restoring backup from $BACKUP_DIR..."

  # Restore AdGuard YAML (prefer /opt path)
  if [ -f "$BACKUP_DIR/AdGuardHome.yaml" ]; then
    if [ -d /opt/AdGuardHome ]; then
      retry 3 2 cp "$BACKUP_DIR/AdGuardHome.yaml" /opt/AdGuardHome/AdGuardHome.yaml
    else
      mkdir -p /etc/AdGuardHome
      retry 3 2 cp "$BACKUP_DIR/AdGuardHome.yaml" /etc/AdGuardHome/AdGuardHome.yaml
    fi
    echo "[restore] Restored AdGuardHome.yaml"
  fi

  # Restore init script (either name)
  if [ -f "$BACKUP_DIR/init.d_AdGuardHome" ]; then
    retry 3 2 cp "$BACKUP_DIR/init.d_AdGuardHome" /etc/init.d/AdGuardHome
    chmod +x /etc/init.d/AdGuardHome || true
  elif [ -f "$BACKUP_DIR/init.d_adguardhome" ]; then
    retry 3 2 cp "$BACKUP_DIR/init.d_adguardhome" /etc/init.d/adguardhome
    chmod +x /etc/init.d/adguardhome || true
  fi

  # Restore dnsmasq UCI file or snapshot if present
  if [ -f "$BACKUP_DIR/dhcp_config" ]; then
    retry 3 2 cp "$BACKUP_DIR/dhcp_config" /etc/config/dhcp
    echo "[restore] Restored /etc/config/dhcp"
  fi
  if [ -f "$BACKUP_DIR/dhcp.uci" ]; then
    uci import dhcp < "$BACKUP_DIR/dhcp.uci" || true
    uci commit dhcp || true
  fi

  echo "[restore] Restarting services..."
  retry 3 3 /etc/init.d/dnsmasq restart
  svc="$(detect_service_name || true)"
  [ -n "$svc" ] && retry 3 3 "$svc" restart || true

  echo "[restore] Restoration complete."
}

main() {
  restore_configs || { echo "[main] Restoration failed"; exit 1; }
}

main
