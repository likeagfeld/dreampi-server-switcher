#!/bin/bash
# DreamPi Portal Uninstaller

echo "🧹 Uninstalling DreamPi Portal..."

# Stop service
systemctl stop dreampi-portal 2>/dev/null
systemctl disable dreampi-portal 2>/dev/null
rm -f /etc/systemd/system/dreampi-portal.service
systemctl daemon-reload

# Remove portal
rm -rf /opt/dreampi-portal

echo "✅ Portal uninstalled"
echo ""
echo "Note: Custom scripts kept in /home/pi/dreampi_custom_scripts"
