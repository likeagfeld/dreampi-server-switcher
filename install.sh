#!/bin/bash
# DreamPi Portal - Python 3.5 Compatible Installer

echo "🎮 Installing DreamPi Server Switcher Portal..."

# Must run as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Run with sudo: sudo bash install.sh"
    exit 1
fi

# Check DreamPi exists
if [ ! -f "/home/pi/dreampi/dreampi.py" ]; then
    echo "❌ DreamPi not found"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Found Python $PYTHON_VERSION"

# Install git if needed
if ! command -v git &> /dev/null; then
    echo "📦 Installing git..."
    apt-get update -qq
    apt-get install -y git
fi

# Install pip for Python 3.5 if needed
if ! python3 -m pip --version &> /dev/null; then
    echo "📦 Installing pip for Python 3.5..."
    cd /tmp
    curl -s https://bootstrap.pypa.io/pip/3.5/get-pip.py -o get-pip.py
    python3 get-pip.py
fi

# Install Flask 1.1.4 (Python 3.5 compatible)
echo "📦 Installing Flask..."
python3 -m pip install flask==1.1.4 werkzeug==1.0.1

# Get custom scripts
echo "📥 Getting custom scripts..."
cd /home/pi
if [ ! -d "dreampi_custom_scripts" ]; then
    git clone https://github.com/scrivanidc/dreampi_custom_scripts.git
fi
chown -R pi:pi dreampi_custom_scripts
chmod +x dreampi_custom_scripts/*.sh

# Create portal
echo "📥 Installing portal..."
mkdir -p /opt/dreampi-portal/templates

# Download files
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/src/dreampi_portal.py > /opt/dreampi-portal/dreampi_portal.py
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/src/templates/index.html > /opt/dreampi-portal/templates/index.html
chmod +x /opt/dreampi-portal/dreampi_portal.py

# Create service
cat > /etc/systemd/system/dreampi-portal.service << EOF
[Unit]
Description=DreamPi Portal
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /opt/dreampi-portal/dreampi_portal.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
systemctl daemon-reload
systemctl enable dreampi-portal
systemctl start dreampi-portal

# Wait a moment
sleep 3

# Done
IP=$(hostname -I | awk '{print $1}')
if systemctl is-active --quiet dreampi-portal; then
    echo ""
    echo "✅ Installation complete!"
    echo "🌐 Access portal at: http://$IP:8080"
    echo ""
    echo "Commands:"
    echo "  sudo systemctl status dreampi-portal"
    echo "  sudo journalctl -u dreampi-portal -f"
else
    echo ""
    echo "⚠️ Portal may not have started. Check:"
    echo "  sudo systemctl status dreampi-portal"
    echo "  sudo journalctl -u dreampi-portal -n 50"
fi
