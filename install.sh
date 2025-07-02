#!/bin/bash
# DreamPi Portal Installer - Safe Version (No System Changes)

echo "🎮 DreamPi Server Switcher Portal - Safe Installer"
echo "✅ This installer will NOT modify any system packages or repositories"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Validate DreamPi exists
if [ ! -f "/home/pi/dreampi/dreampi.py" ]; then
    echo "❌ DreamPi not found at /home/pi/dreampi/dreampi.py"
    exit 1
fi

echo "✅ DreamPi found"

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION found"

# Create portal directory
PORTAL_DIR="/opt/dreampi-portal"
mkdir -p $PORTAL_DIR/templates

# Check if pip exists, if not install it locally
if python3 -m pip --version &> /dev/null; then
    echo "✅ pip is already available"
else
    echo "📦 Installing pip locally (no system changes)..."
    cd /tmp
    curl -s https://bootstrap.pypa.io/pip/3.5/get-pip.py -o get-pip.py
    python3 get-pip.py --user
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install Flask in portal directory only (isolated installation)
echo "📦 Installing Flask (isolated from system)..."
cd $PORTAL_DIR
python3 -m pip install --target=$PORTAL_DIR --ignore-installed flask==2.0.3 werkzeug==2.0.3 Jinja2==3.0.3 click==8.0.4 itsdangerous==2.0.1 MarkupSafe==2.0.1

# Download portal files
echo "📥 Downloading portal files..."
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/src/dreampi_portal.py > $PORTAL_DIR/dreampi_portal.py
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/src/templates/index.html > $PORTAL_DIR/templates/index.html

# Make portal executable
chmod +x $PORTAL_DIR/dreampi_portal.py

# Create a wrapper script that sets up the environment
cat > $PORTAL_DIR/run_portal.sh << 'EOF'
#!/bin/bash
export PYTHONPATH="/opt/dreampi-portal:$PYTHONPATH"
cd /opt/dreampi-portal
exec /usr/bin/python3 /opt/dreampi-portal/dreampi_portal.py
EOF
chmod +x $PORTAL_DIR/run_portal.sh

# Create systemd service
echo "🔧 Creating service..."
cat > /etc/systemd/system/dreampi-portal.service << 'EOF'
[Unit]
Description=DreamPi Server Switcher Portal
After=network.target

[Service]
Type=simple
User=root
ExecStart=/opt/dreampi-portal/run_portal.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create management script
cat > /usr/local/bin/dreampi-portal << 'EOF'
#!/bin/bash
case "$1" in
    start)
        sudo systemctl start dreampi-portal
        echo "Portal started"
        ;;
    stop)
        sudo systemctl stop dreampi-portal
        echo "Portal stopped"
        ;;
    restart)
        sudo systemctl restart dreampi-portal
        echo "Portal restarted"
        ;;
    status)
        systemctl status dreampi-portal
        ;;
    logs)
        journalctl -u dreampi-portal -f
        ;;
    test)
        cd /opt/dreampi-portal
        export PYTHONPATH="/opt/dreampi-portal:$PYTHONPATH"
        python3 dreampi_portal.py
        ;;
    *)
        echo "Usage: dreampi-portal {start|stop|restart|status|logs|test}"
        ;;
esac
EOF
chmod +x /usr/local/bin/dreampi-portal

# Enable and start service
systemctl daemon-reload
systemctl enable dreampi-portal
systemctl start dreampi-portal

# Wait for service to start
sleep 3

# Check if service is running
if systemctl is-active --quiet dreampi-portal; then
    PI_IP=$(hostname -I | awk '{print $1}')
    echo ""
    echo "✅ Installation completed successfully!"
    echo "🌐 Portal URL: http://$PI_IP:8080"
    echo ""
    echo "Commands:"
    echo "  dreampi-portal status  - Check if running"
    echo "  dreampi-portal logs    - View logs"
    echo "  dreampi-portal restart - Restart portal"
else
    echo ""
    echo "⚠️  Service may not have started. Check with:"
    echo "  dreampi-portal status"
    echo "  dreampi-portal logs"
fi
