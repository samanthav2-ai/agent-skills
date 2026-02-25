#!/bin/bash
# Quick installer for watchdog on any Clawdbot instance

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${CLAWDBOT_WORKSPACE:-/home/ubuntu/clawd}/scripts"
SERVICE_DIR="/etc/systemd/system"

echo "Installing watchdog to $INSTALL_DIR..."

# Create install directory if needed
mkdir -p "$INSTALL_DIR"

# Copy watchdog script
cp "$SCRIPT_DIR/watchdog.sh" "$INSTALL_DIR/clawdbot-watchdog.sh"
chmod +x "$INSTALL_DIR/clawdbot-watchdog.sh"

echo "Watchdog script installed to $INSTALL_DIR/clawdbot-watchdog.sh"

# Optionally install systemd service
if [ "$1" == "--systemd" ]; then
    echo "Installing systemd service..."
    sudo cp "$SCRIPT_DIR/clawdbot-watchdog.service" "$SERVICE_DIR/"
    sudo systemctl daemon-reload
    sudo systemctl enable clawdbot-watchdog
    sudo systemctl start clawdbot-watchdog
    echo "Systemd service installed and started"
fi

echo "Done! Edit the script to set your CLAWDBOT_SOS_TARGET."
