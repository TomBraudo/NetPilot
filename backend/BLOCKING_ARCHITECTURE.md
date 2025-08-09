# Automated Per-Device, Per-Category Domain Blocking Architecture with AdGuard Home on OpenWrt

This document describes a **complete, automated architecture setup** with scripts to achieve per-device, per-category domain blocking on OpenWrt using AdGuard Home. Devices are assigned categories programmatically for dynamic and easy control.

---

## Overview

- **One-time infrastructure setup** installs and configures AdGuard Home, DHCP tagging, DNS forwarding.
- **Domain categories** (e.g., social, adult, games) each correspond to a blocklist loaded in AdGuard Home.
- Devices are identified by MAC, assigned to 0 or more categories via AdGuard Home client configuration.
- Scripts allow easy programmatic **marking/unmarking** of devices for categories via AdGuard Home API.
- Everything is fully automated for easy integration into your application.

---

## 1. One-Time Infrastructure Setup Script

(s)```
#!/bin/sh

# Install AdGuard Home and dependencies
opkg update
opkg install adguardhome luci-app-adguardhome curl jq

# Start and enable AdGuard Home service
/etc/init.d/adguardhome enable
/etc/init.d/adguardhome start

# Wait for AdGuard Home to bootstrap
sleep 10

# Define categories and blocklist URLs (empty placeholder files)
/etc/adguardhome-blocklists
mkdir -p /etc/adguardhome-blocklists
categories="social adult games entertainment"
for cat in $categories; do
  echo "# Blocklist for $cat" > "/etc/adguardhome-blocklists/${cat}.txt"
done

ADGUARD_API="http://127.0.0.1:3000"
ADMIN_TOKEN=""
while [ -z "$ADMIN_TOKEN" ]; do
  ADMIN_TOKEN=$(curl -s "$ADGUARD_API/control/token" | jq -r '.token')
  sleep 1
done

add_blocklist() {
  name=$1
  url=$2
  curl -s -X POST "$ADGUARD_API/control/dns_blocklists" \
    -H "Content-Type: application/json" \
    -H "X-Admin-Token: $ADMIN_TOKEN" \
    -d "{\"name\":\"$name\",\"urls\":[\"$url\"],\"enabled\":true}" > /dev/null
}

for cat in $categories; do
  add_blocklist "$cat" "file:///etc/adguardhome-blocklists/$cat.txt"
done

# Force clients to use AdGuard Home DNS
uci set dhcp.lan.dhcp_option='6,127.0.0.1#3000'
uci commit dhcp
/etc/init.d/dnsmasq restart

echo "One-time infrastructure setup completed."

#!/bin/sh

ADGUARD_API="http://127.0.0.1:3000"
ADMIN_TOKEN=$(curl -s "$ADGUARD_API/control/token" | jq -r '.token') || exit 1

api_get_clients() {
  curl -s -H "X-Admin-Token: $ADMIN_TOKEN" "$ADGUARD_API/control/clients"
}

api_update_client() {
  local id="$1"
  local config_json="$2"
  curl -s -X POST -H "Content-Type: application/json" -H "X-Admin-Token: $ADMIN_TOKEN" -d "$config_json" "$ADGUARD_API/control/clients/update?id=$id" > /dev/null
}

get_client_id_by_mac() {
  local mac="$1"
  api_get_clients | jq -r --arg MAC "$mac" '.clients[] | select(.mac==$MAC) | .id'
}

get_client_config_by_id() {
  local id="$1"
  api_get_clients | jq -r --arg ID "$id" '.clients[] | select(.id==$ID)'
}

add_category() {
  local mac="$1"
  local category="$2"
  local id=$(get_client_id_by_mac "$mac")
  if [ -z "$id" ]; then
    # Add new client with MAC and category
    config=$(jq -n --arg mac "$mac" --argjson tags "[\"$category\"]" '{mac: $mac, filtering_enabled: true, tags: $tags}')
    curl -s -X POST -H "Content-Type: application/json" -H "X-Admin-Token: $ADMIN_TOKEN" -d "$config" "$ADGUARD_API/control/clients" > /dev/null
    echo "Created client $mac and assigned to category $category"
  else
    # Update existing client categories
    config_json=$(get_client_config_by_id "$id")
    current_tags=$(echo $config_json | jq -r '.tags')
    new_tags=$(echo $current_tags | jq --arg cat "$category" 'if index($cat) == null then . + [$cat] else . end')
    update_json=$(echo $config_json | jq --argjson tags "$new_tags" '.tags = $tags | .filtering_enabled = true')
    api_update_client "$id" "$update_json"
    echo "Added category $category to client $mac"
  fi
}

remove_category() {
  local mac="$1"
  local category="$2"
  local id=$(get_client_id_by_mac "$mac")
  if [ -z "$id" ]; then
    echo "Client with MAC $mac not found"
    return
  fi
  config_json=$(get_client_config_by_id "$id")
  current_tags=$(echo $config_json | jq -r '.tags')
  new_tags=$(echo $current_tags | jq --arg cat "$category" 'del(.[] | select(. == $cat))')
  update_json=$(echo $config_json | jq --argjson tags "$new_tags" '.tags = $tags')
  api_update_client "$id" "$update_json"
  echo "Removed category $category from client $mac"
}

list_categories() {
  local mac="$1"
  local id=$(get_client_id_by_mac "$mac")
  if [ -z "$id" ]; then
    echo "Client with MAC $mac not found"
    return
  fi
  config_json=$(get_client_config_by_id "$id")
  echo "Categories for $mac:"
  echo $config_json | jq -r '.tags[]'
}

case "$1" in
  add) add_category "$2" "$3" ;;
  remove) remove_category "$2" "$3" ;;
  list) list_categories "$2" ;;
  *) echo "Usage: $0 {add|remove|list} <MAC> [category]" ;;
esac

To save and prepare the script:

cat > /usr/local/bin/device_category_manager.sh << 'EOF'
<PASTE THE SCRIPT CONTENT ABOVE HERE>
EOF

chmod +x /usr/local/bin/device_category_manager.sh

This script will allow you to add, remove, and list category tags for devices identified by MAC address using the AdGuard Home API.



---

## Usage Examples

Mark a device as blocking "social" and "games":

./device_category_manager.sh add D8:BB:C1:47:3A:43 social
./device_category_manager.sh add D8:BB:C1:47:3A:43 games


Remove "games" category from a device:
./device_category_manager.sh remove D8:BB:C1:47:3A:43 games


List categories assigned to a device:
./device_category_manager.sh list D8:BB:C1:47:3A:43


---

## Conclusion

- The **`setup_adguard.sh`** script performs a fully automated one-time setup of AdGuard Home with categorized blocklists and network DNS integration.
- The **`device_category_manager.sh`** script provides a programmatic, API-driven interface for marking/unmarking devices by MAC into any number of blocking categories.
- This architecture ensures **flexible, scalable, maintainable, and fully automated** per-device, per-category domain blocking on OpenWrt.

---

**This setup enables your application to control client internet access dynamically and granularly with minimal manual intervention.**