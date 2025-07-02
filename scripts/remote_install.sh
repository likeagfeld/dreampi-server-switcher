#!/bin/bash
# Remote installer for DreamPi Portal

echo "?? DreamPi Portal Remote Installer"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <pi_ip_address> [username]"
    echo "Example: $0 192.168.1.100"
    exit 1
fi

PI_IP="$1"
PI_USER="${2:-pi}"

echo "?? Installing on $PI_USER@$PI_IP..."
echo "?? Default password is usually: raspberry"

# Execute installer on Piif ssh "$PI_USER@$PI_IP" "curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/main/install.sh | sudo bash"; then
    echo
    echo "?? SUCCESS!"
    echo "?? Portal: http://$PI_IP:8080"
else
    echo "? Installation failed"
fi
