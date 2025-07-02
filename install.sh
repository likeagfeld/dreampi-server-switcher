#!/bin/bash
# DreamPi Portal Installer

set -e
echo "?? Installing DreamPi Server Switcher Portal..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "? This script must be run as root (use sudo)"
    exit 1
fi

# Validate DreamPi
if [ ! -f "/home/pi/dreampi/dreampi.py" ]; then
    echo "? DreamPi not found. Please install DreamPi first."
    exit 1
fi

echo "? DreamPi found"

# Install dependencies
echo "?? Installing dependencies..."
apt update -q
apt install -y python3 python3-pip python3-venv

# Create installation
PORTAL_DIR="/opt/dreampi-portal"
mkdir -p $PORTAL_DIR/templates

# Create virtual environment
python3 -m venv /opt/dreampi-portal-venv
source /opt/dreampi-portal-venv/bin/activate
pip install flask

# Download files
echo "??  Downloading portal files..."curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/main/src/dreampi_portal.py > $PORTAL_DIR/dreampi_portal.pycurl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/main/src/templates/index.html > $PORTAL_DIR/templates/index.html
chmod +x $PORTAL_DIR/dreampi_portal.py

# Create systemd service
echo "??  Setting up service..."
cat > /etc/systemd/system/dreampi-portal.service << 'EOF'
[Unit]
Description=DreamPi Server Switcher Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/dreampi-portal
Environment=PATH=/opt/dreampi-portal-venv/bin
ExecStart=/opt/dreampi-portal-venv/bin/python /opt/dreampi-portal/dreampi_portal.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create management command
cat > /usr/local/bin/dreampi-portal << 'CMDEOF'
#!/bin/bash
case "$1" in
    start) sudo systemctl start dreampi-portal ;;
    stop) sudo systemctl stop dreampi-portal ;;
    restart) sudo systemctl restart dreampi-portal ;;
    status) systemctl status dreampi-portal ;;
    logs) journalctl -u dreampi-portal -f ;;
    url) echo "http://$(hostname -I | awk '{print $1}'):8080" ;;
    *) echo "Usage: $0 {start|stop|restart|status|logs|url}" ;;
esac
CMDEOF

chmod +x /usr/local/bin/dreampi-portal

# Start service
systemctl daemon-reload
systemctl enable dreampi-portal
systemctl start dreampi-portal

# Show results
PI_IP=$(hostname -I | awk '{print $1}')
echo
echo "? Installation completed!"
echo "?? Portal URL: http://$PI_IP:8080"
echo "?? Access from any device on your network"
echo
echo "Management commands:"
echo "  dreampi-portal start/stop/restart/status/logs"
echo
echo "?? Ready to use!"
