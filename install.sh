#!/bin/bash
# DreamPi Portal Installer - Raspbian Stretch Compatible

set -e
echo "🎮 Installing DreamPi Server Switcher Portal (Stretch Edition)..."

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

# Fix repositories for Stretch
echo "🔧 Fixing repositories for Raspbian Stretch..."
cp /etc/apt/sources.list /etc/apt/sources.list.backup
cat > /etc/apt/sources.list << 'EOF'
deb http://legacy.raspbian.org/raspbian/ stretch main contrib non-free rpi
EOF

# Update with legacy repos
echo "📦 Installing dependencies..."
apt-get update || true  # Continue even if some repos fail
apt-get install -y python3 python3-pip python3-venv || {
    # If that fails, try without venv
    echo "⚠️  Trying alternative installation..."
    apt-get install -y python3 python3-pip
}

# Create installation directory
PORTAL_DIR="/opt/dreampi-portal"
mkdir -p $PORTAL_DIR/templates

# Try to use venv, fall back to direct pip if it fails
if command -v python3 -m venv >/dev/null 2>&1; then
    echo "📦 Creating virtual environment..."
    python3 -m venv /opt/dreampi-portal-venv
    source /opt/dreampi-portal-venv/bin/activate
    pip install flask
    PYTHON_PATH="/opt/dreampi-portal-venv/bin/python"
else
    echo "📦 Installing Flask directly..."
    pip3 install flask
    PYTHON_PATH="/usr/bin/python3"
fi

# Download files
echo "📥 Downloading portal files..."
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/src/dreampi_portal.py > $PORTAL_DIR/dreampi_portal.py
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/src/templates/index.html > $PORTAL_DIR/templates/index.html
chmod +x $PORTAL_DIR/dreampi_portal.py

# Create systemd service
echo "🔧 Setting up service..."
cat > /etc/systemd/system/dreampi-portal.service << EOF
[Unit]
Description=DreamPi Server Switcher Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/dreampi-portal
ExecStart=$PYTHON_PATH /opt/dreampi-portal/dreampi_portal.py
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

# Restore original sources.list
cp /etc/apt/sources.list.backup /etc/apt/sources.list

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
