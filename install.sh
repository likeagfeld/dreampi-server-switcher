#!/bin/bash
# DreamPi Portal Installer - No Repository Update Version

set -e
echo "🎮 Installing DreamPi Server Switcher Portal..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Validate DreamPi
if [ ! -f "/home/pi/dreampi/dreampi.py" ]; then
    echo "❌ DreamPi not found. Please install DreamPi first."
    exit 1
fi

echo "✅ DreamPi found"

# Check if Python3 and pip are already installed (they should be on DreamPi)
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. This is required for the portal."
    exit 1
fi

echo "✅ Python3 found"

# Try to install Flask without updating repositories
echo "📦 Installing Flask..."
if command -v pip3 &> /dev/null; then
    pip3 install flask || python3 -m pip install flask || {
        echo "⚠️  pip3 not found, trying alternative method..."
        # Try to install pip without apt
        curl -s https://bootstrap.pypa.io/get-pip.py | python3
        python3 -m pip install flask
    }
else
    echo "⚠️  pip3 not found, downloading..."
    curl -s https://bootstrap.pypa.io/get-pip.py | python3
    python3 -m pip install flask
fi

# Create installation directory
PORTAL_DIR="/opt/dreampi-portal"
mkdir -p $PORTAL_DIR/templates

# Download files
echo "📥 Downloading portal files..."
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/src/dreampi_portal.py > $PORTAL_DIR/dreampi_portal.py
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/src/templates/index.html > $PORTAL_DIR/templates/index.html
chmod +x $PORTAL_DIR/dreampi_portal.py

# Create systemd service
echo "🔧 Setting up service..."
cat > /etc/systemd/system/dreampi-portal.service << 'EOF'
[Unit]
Description=DreamPi Server Switcher Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/dreampi-portal
ExecStart=/usr/bin/python3 /opt/dreampi-portal/dreampi_portal.py
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
echo "✅ Installation completed!"
echo "🌐 Portal URL: http://$PI_IP:8080"
echo "📱 Access from any device on your network"
echo
echo "Management commands:"
echo "  dreampi-portal start/stop/restart/status/logs"
echo
echo "🎮 Ready to use!"
