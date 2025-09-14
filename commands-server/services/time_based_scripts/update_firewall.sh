#!/bin/sh

GROUP="$1"
ACTION="$2"
BASE_DIR="/root/netlimit"
DEVICE_FILE="${BASE_DIR}/${GROUP}/devices.txt"
RULE_PREFIX="netlimit_block_${GROUP}"

if [ -z "$GROUP" ] || [ -z "$ACTION" ]; then
  echo "Usage: $0 group_name [block|unblock|refresh]"
  exit 1
fi

if [ ! -d "${BASE_DIR}/${GROUP}" ]; then
  echo "Error: Group directory ${GROUP} does not exist"
  exit 1
fi

if [ ! -f "$DEVICE_FILE" ]; then
  echo "Warning: Device list file missing. No devices to block."
fi

remove_rules() {
  # Delete only rules whose name starts with the exact RULE_PREFIX, in reverse index order
  # BusyBox-safe: extract indices from lines containing .name='<RULE_PREFIX>_...'
  IDX_LIST=$(uci show firewall | grep "\.name='${RULE_PREFIX}_" | sed -n "s/.*\[\([0-9]\+\)\].*/\1/p" | sort -rn)
  for idx in $IDX_LIST; do
    uci delete firewall.@rule[$idx]
  done
}

add_rules() {
  [ ! -f "$DEVICE_FILE" ] && return
  while IFS= read -r dev; do
    [ -z "$dev" ] && continue
    uci add firewall rule
    uci set firewall.@rule[-1].name="${RULE_PREFIX}_${dev}"
    uci set firewall.@rule[-1].src="lan"
    uci set firewall.@rule[-1].target="DROP"
    uci set firewall.@rule[-1].proto="all"
    uci set firewall.@rule[-1].mac="$dev"
    uci set firewall.@rule[-1].enabled="1"
  done < "$DEVICE_FILE"
}

case "$ACTION" in
  unblock)
    remove_rules
    uci commit firewall
    /etc/init.d/firewall reload
    ;;
  block)
    remove_rules
    add_rules
    uci commit firewall
    /etc/init.d/firewall reload
    ;;
  refresh)
    remove_rules
    add_rules
    uci commit firewall
    /etc/init.d/firewall reload
    ;;
  *)
    echo "Invalid action: $ACTION"
    echo "Usage: $0 group_name [block|unblock|refresh]"
    exit 1
    ;;
esac
