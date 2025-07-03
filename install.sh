#!/bin/bash
# DreamPi Portal Installer - With Auto-Update Scripts

echo "🎮 DreamPi Server Switcher Portal Installer"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run with sudo: sudo bash install.sh"
    exit 1
fi

# Check DreamPi exists
if [ ! -f "/home/pi/dreampi/dreampi.py" ]; then
    echo "❌ DreamPi not found at /home/pi/dreampi/dreampi.py"
    exit 1
fi

echo "✅ DreamPi found"

# Install git if not present
if ! command -v git &> /dev/null; then
    echo "📦 Installing git..."
    apt-get update -qq
    apt-get install -y git
fi

# Get or update custom scripts
echo "📥 Getting latest DreamPi custom scripts..."
cd /home/pi

if [ -d "dreampi_custom_scripts" ]; then
    echo "📥 Updating existing scripts..."
    cd dreampi_custom_scripts
    # Reset any local changes and pull latest
    git reset --hard HEAD
    git pull origin main || git pull origin master
    cd ..
else
    echo "📥 Downloading scripts..."
    git clone https://github.com/scrivanidc/dreampi_custom_scripts.git
fi

# Set permissions
chown -R pi:pi dreampi_custom_scripts
chmod +x dreampi_custom_scripts/*.sh

echo "✅ Scripts ready"

# Install Flask using pip that's already on the system
echo "📦 Installing Flask..."
pip3 install flask==1.1.4 || python3 -m pip install flask==1.1.4 || {
    # If pip3 not found, try to get it
    apt-get install -y python3-pip
    pip3 install flask==1.1.4
}

# Create portal directory
PORTAL_DIR="/opt/dreampi-portal"
mkdir -p $PORTAL_DIR/templates

# Download portal files
echo "📥 Installing portal files..."
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/src/dreampi_portal.py > $PORTAL_DIR/dreampi_portal.py
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/src/templates/index.html > $PORTAL_DIR/templates/index.html
chmod +x $PORTAL_DIR/dreampi_portal.py

# Create systemd service
echo "🔧 Creating service..."
cat > /etc/systemd/system/dreampi-portal.service << 'EOF'
[Unit]
Description=DreamPi Server Switcher Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/dreampi-portal
ExecStart=/usr/bin/python3 /opt/dreampi-portal/dreampi_portal.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create update script
echo "📝 Creating update script..."
cat > /usr/local/bin/dreampi-portal-update << 'EOF'
#!/bin/bash
echo "🔄 Updating DreamPi Portal..."

# Update portal files
echo "📥 Updating portal..."
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/src/dreampi_portal.py > /opt/dreampi-portal/dreampi_portal.py
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/src/templates/index.html > /opt/dreampi-portal/templates/index.html

# Update custom scripts
echo "📥 Updating scripts..."
cd /home/pi/dreampi_custom_scripts
git pull

# Restart portal
echo "🔄 Restarting portal..."
systemctl restart dreampi-portal

echo "✅ Update complete!"
EOF

chmod +x /usr/local/bin/dreampi-portal-update

# Enable and start service
systemctl daemon-reload
systemctl enable dreampi-portal
systemctl start dreampi-portal

# Wait a moment
sleep 3

# Show status
PI_IP=$(hostname -I | awk '{print $1}')
if systemctl is-active --quiet dreampi-portal; then
    echo ""
    echo "✅ Installation complete!"
    echo "🌐 Portal URL: http://$PI_IP:8080"
    echo ""
    echo "📝 Commands:"
    echo "  sudo systemctl status dreampi-portal     # Check status"
    echo "  sudo journalctl -u dreampi-portal -f     # View logs"
    echo "  sudo dreampi-portal-update               # Update everything"
else
    echo ""
    echo "⚠️  Portal may not be running. Check with:"
    echo "  sudo systemctl status dreampi-portal"
    echo "  sudo journalctl -u dreampi-portal -n 50"
fi
