#!/bin/sh

GROUP="$1"
shift
BASE_DIR="/root/netlimit"
GROUP_DIR="${BASE_DIR}/${GROUP}"
DEVICE_FILE="${GROUP_DIR}/devices.txt"

# Create group directory if missing
if [ ! -d "$GROUP_DIR" ]; then
  mkdir -p "$GROUP_DIR"
  chmod 700 "$GROUP_DIR"
fi

# Create device file if missing
touch "$DEVICE_FILE"
chmod 600 "$DEVICE_FILE"

# Add devices avoiding duplicates
for dev in "$@"; do
  grep -qxF "$dev" "$DEVICE_FILE" 2>/dev/null || echo "$dev" >> "$DEVICE_FILE"
done
