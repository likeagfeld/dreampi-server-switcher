#!/bin/bash
# DreamPi Portal Uninstaller

echo "🧹 Uninstalling DreamPi Portal..."

# Stop and disable service
echo "Stopping service..."
systemctl stop dreampi-portal 2>/dev/null
systemctl disable dreampi-portal 2>/dev/null

# Remove service file
rm -f /etc/systemd/system/dreampi-portal.service
systemctl daemon-reload

# Remove portal directory
echo "Removing portal files..."
rm -rf /opt/dreampi-portal
rm -f /usr/local/bin/dreampi-portal

# Clean up any dreampi backups that might have wrong Python version
if [ -f "/home/pi/dreampi/dreampi.py" ]; then
    echo "Checking DreamPi script..."
    if grep -q "python3" /home/pi/dreampi/dreampi.py; then
        echo "⚠️  DreamPi script may be using Python 3. Checking for original backup..."
        if [ -f "/home/pi/dreampi/dreampi_original.py" ]; then
            echo "Restoring original DreamPi script..."
            cp /home/pi/dreampi/dreampi_original.py /home/pi/dreampi/dreampi.py
            systemctl restart dreampi
        fi
    fi
fi

# Remove backup files created by portal
rm -f /home/pi/dreampi/dreampi_original.py
rm -f /home/pi/dreampi/dreampi_dcnet.py

echo "✅ Portal uninstalled"
echo ""
echo "Note: DreamPi custom scripts were kept in /home/pi/dreampi_custom_scripts"
echo "Remove manually if not needed: rm -rf /home/pi/dreampi_custom_scripts"
