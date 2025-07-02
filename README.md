# DreamPi Server Switcher Portal

Beautiful web interface for switching between DCLive and DCNet servers on your DreamPi with one click.

## Quick Install

### One-Command Install
``bash
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/main/install.sh | sudo bash
``

### Remote Install (from your PC)
``bash
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/main/scripts/remote_install.sh | bash -s 192.168.1.100
``

## Features

- **One-click server switching** between DCLive and DCNet
- **Mobile-friendly** web interface
- **Real-time monitoring** of DreamPi service
- **Authentic Dreamcast styling**
- **Auto-start on boot**

## Usage

1. Open `http://YOUR_PI_IP:8080` in browser
2. Click server buttons to switch
3. Monitor service status in real-time

## Requirements

- Raspberry Pi with DreamPi installed
- SSH enabled on Pi
- Network connection

## Management

``bash
dreampi-portal start      # Start portal
dreampi-portal stop       # Stop portal  
dreampi-portal restart    # Restart portal
dreampi-portal status     # Check status
dreampi-portal logs       # View logs
``

## License

MIT License - see LICENSE file.

---

*Made for the Dreamcast community* ??
