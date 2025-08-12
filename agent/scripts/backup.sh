#!/bin/sh
set -e

FLAG_DIR="/etc/netpilot/flags/agh_install"
mkdir -p "$FLAG_DIR"

BACKUP_DIR="/root/adguard_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

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

backup_configs() {
  echo "[backup] Backing up AdGuard Home and dnsmasq configs..."

  # AdGuard YAML
  if [ -f /opt/AdGuardHome/AdGuardHome.yaml ]; then
    retry 3 2 cp /opt/AdGuardHome/AdGuardHome.yaml "$BACKUP_DIR/AdGuardHome.yaml"
  elif [ -f /etc/AdGuardHome/AdGuardHome.yaml ]; then
    retry 3 2 cp /etc/AdGuardHome/AdGuardHome.yaml "$BACKUP_DIR/AdGuardHome.yaml"
  fi

  # Init script (detect name)
  if [ -f /etc/init.d/AdGuardHome ]; then
    retry 3 2 cp /etc/init.d/AdGuardHome "$BACKUP_DIR/init.d_AdGuardHome"
  elif [ -f /etc/init.d/adguardhome ]; then
    retry 3 2 cp /etc/init.d/adguardhome "$BACKUP_DIR/init.d_adguardhome"
  fi

  # dnsmasq UCI file and a snapshot export
  if [ -f /etc/config/dhcp ]; then
    retry 3 2 cp /etc/config/dhcp "$BACKUP_DIR/dhcp_config"
  fi
  uci export dhcp > "$BACKUP_DIR/dhcp.uci" 2>/dev/null || true

  echo "[backup] Backup completed at $BACKUP_DIR"
}

main() {
  backup_configs || { echo "[main] Backup failed"; exit 1; }
}

main
