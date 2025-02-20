#!/bin/bash

ROUTER_IP="192.168.1.1"
ROUTER_USER="root"
REQUIREMENTS_FILE="pkg_requirements.txt"

# Disable SSH host key verification
export SSH_OPTIONS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

echo "[INFO] Fixing SSH known hosts issue..."
ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$ROUTER_IP"

echo "[INFO] Ensuring SSH key-based login works..."
ssh $SSH_OPTIONS "$ROUTER_USER@$ROUTER_IP" "echo 'Connected successfully!'"

echo "[INFO] Transferring package list to OpenWrt..."
scp $SSH_OPTIONS "$REQUIREMENTS_FILE" "$ROUTER_USER@$ROUTER_IP:/tmp/$REQUIREMENTS_FILE"

echo "[INFO] Installing required packages on OpenWrt..."
ssh $SSH_OPTIONS "$ROUTER_USER@$ROUTER_IP" <<EOF
    opkg update
    opkg install \$(cat /tmp/$REQUIREMENTS_FILE)
EOF

echo "[INFO] Restarting OpenWrt services..."
ssh $SSH_OPTIONS "$ROUTER_USER@$ROUTER_IP" <<EOF
    /etc/init.d/network restart
    /etc/init.d/firewall restart
    wifi reload
EOF

echo "[INFO] Verifying installed packages..."
ssh $SSH_OPTIONS "$ROUTER_USER@$ROUTER_IP" "opkg list-installed | grep -f /tmp/$REQUIREMENTS_FILE"

echo "[SUCCESS] OpenWrt setup is complete!"
