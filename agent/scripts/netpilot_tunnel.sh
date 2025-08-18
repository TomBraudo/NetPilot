#!/bin/sh

# NetPilot Tunnel Script (standalone)
# Usage (set env vars first):
#   export CLOUD_VM="<vm_ip>"
#   export CLOUD_USER="<user>"
#   export CLOUD_PASSWORD="<password>"
#   export CLOUD_PORT="22"            # optional, default 22
#   export REMOTE_PORT="2220"         # required: reverse port on cloud VM
#   /root/netpilot_tunnel.sh
#
# Notes:
# - Requires: sshpass, autossh, ssh, nohup
# - Creates logs: /tmp/netpilot_tunnel.log, /tmp/autossh.log
# - PID file: /var/run/netpilot_tunnel_${REMOTE_PORT}.pid

CLOUD_VM="${CLOUD_VM}"
CLOUD_USER="${CLOUD_USER}"
CLOUD_PASSWORD="${CLOUD_PASSWORD}"
CLOUD_PORT="${CLOUD_PORT:-22}"
LOCAL_PORT="22"
REMOTE_PORT="${REMOTE_PORT}"
PID_FILE="/var/run/netpilot_tunnel_${REMOTE_PORT}.pid"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> /tmp/netpilot_tunnel.log
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Validate required inputs
if [ -z "$CLOUD_VM" ] || [ -z "$CLOUD_USER" ] || [ -z "$CLOUD_PASSWORD" ] || [ -z "$REMOTE_PORT" ]; then
    echo "Usage: set CLOUD_VM, CLOUD_USER, CLOUD_PASSWORD, REMOTE_PORT (and optional CLOUD_PORT) as environment variables" >&2
    exit 2
fi

log_message "Starting NetPilot tunnel to ${CLOUD_VM}:${REMOTE_PORT}"

# Check tooling availability
for cmd in sshpass autossh ssh nohup; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log_message "ERROR: Required command '$cmd' not found"
    exit 1
  fi
done

# Cleanup existing processes for this port only (BusyBox compatible)
log_message "Cleaning up existing tunnel processes for port ${REMOTE_PORT}..."
ps | grep "autossh.*-R ${REMOTE_PORT}:localhost:${LOCAL_PORT}" | grep -v grep | awk '{print $1}' | xargs -r kill 2>/dev/null || true
ps | grep "sshpass.*autossh.*${REMOTE_PORT}" | grep -v grep | awk '{print $1}' | xargs -r kill 2>/dev/null || true
sleep 2

# Remove stale PID file
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
  if [ -n "$OLD_PID" ]; then
    log_message "Found stale PID file with PID $OLD_PID, attempting to kill it"
    kill -9 "$OLD_PID" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
fi

# Ensure SSHD is running on router
if ! pgrep dropbear >/dev/null 2>&1 && ! pgrep sshd >/dev/null 2>&1; then
  log_message "ERROR: SSHD is not running on router"
  exit 1
fi

# Cloud connectivity check
log_message "Pinging cloud VM..."
if ! ping -c 3 -W 5 "$CLOUD_VM" >/dev/null 2>&1; then
  log_message "ERROR: Cannot reach cloud VM $CLOUD_VM"
  exit 1
fi

# SSH connectivity test
log_message "Testing SSH connectivity to cloud VM..."
if ! sshpass -p "$CLOUD_PASSWORD" ssh -p "$CLOUD_PORT" \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o PasswordAuthentication=yes \
    -o PubkeyAuthentication=no \
    "$CLOUD_USER@$CLOUD_VM" "echo 'SSH test successful'" 2>/tmp/ssh_test.log; then
  log_message "ERROR: SSH connectivity test failed"
  log_message "SSH error details: $(cat /tmp/ssh_test.log 2>/dev/null)"
  exit 1
fi

log_message "SSH connectivity verified"

# Start autossh with enhanced logging
export AUTOSSH_LOGFILE="/tmp/autossh.log"
export AUTOSSH_LOGLEVEL=7
export AUTOSSH_DEBUG=1
export AUTOSSH_PIDFILE="$PID_FILE"
export SSHPASS="$CLOUD_PASSWORD"

log_message "Starting autossh tunnel..."
(
  cd /
  umask 0
  exec nohup sshpass -e autossh -M 0 -N \
    -p "$CLOUD_PORT" \
    -R "${REMOTE_PORT}:localhost:${LOCAL_PORT}" \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o ConnectTimeout=10 \
    -o LogLevel=VERBOSE \
    -o PasswordAuthentication=yes \
    -o PubkeyAuthentication=no \
    "$CLOUD_USER@$CLOUD_VM" \
    < /dev/null > /tmp/nohup_autossh.out 2>&1 &
) &

sleep 3

# Verify autossh is running and stable
attempt=1
while [ "$attempt" -le 5 ]; do
  if ps | grep -v grep | grep "autossh.*${REMOTE_PORT}:localhost:${LOCAL_PORT}" >/dev/null; then
    PID=$(ps | grep -v grep | grep "autossh.*${REMOTE_PORT}:localhost:${LOCAL_PORT}" | awk '{print $1}')
    echo "$PID" > "$PID_FILE"
    log_message "Autossh running with PID $PID (attempt $attempt)"
    sleep 2
    if ps | grep -v grep | grep "autossh.*${REMOTE_PORT}:localhost:${LOCAL_PORT}" >/dev/null; then
      log_message "Autossh stable; tunnel should be functional"
      exit 0
    else
      log_message "Autossh died during stability check (attempt $attempt)"
      log_message "Autossh logs: $(tail -10 /tmp/autossh.log 2>/dev/null)"
    fi
  else
    log_message "Autossh not found (attempt $attempt)"
    log_message "SSH procs: $(ps | grep -i ssh | grep -v grep)"
    log_message "Recent autossh logs: $(tail -5 /tmp/autossh.log 2>/dev/null)"
  fi
  attempt=$((attempt + 1))
  sleep 2
done

log_message "ERROR: Autossh failed to start or died within 15 seconds"
log_message "Final autossh logs: $(cat /tmp/autossh.log 2>/dev/null)"
log_message "Final SSH test logs: $(cat /tmp/ssh_test.log 2>/dev/null)"
exit 1


