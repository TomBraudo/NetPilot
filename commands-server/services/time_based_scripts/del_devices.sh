#!/bin/sh

GROUP="$1"
shift
BASE_DIR="/root/netlimit"
GROUP_DIR="${BASE_DIR}/${GROUP}"
DEVICE_FILE="${GROUP_DIR}/devices.txt"
TMP_FILE="${GROUP_DIR}/devices.tmp"

if [ ! -d "$GROUP_DIR" ]; then
  echo "Error: Group ${GROUP} does not exist"
  exit 1
fi

if [ ! -f "$DEVICE_FILE" ]; then
  echo "Error: Device list for ${GROUP} is missing"
  exit 1
fi

cp /dev/null "$TMP_FILE"

for dev in "$@"; do
  # Remove matching lines
  grep -vxF "$dev" "$DEVICE_FILE" > "$TMP_FILE" && mv "$TMP_FILE" "$DEVICE_FILE"
done
