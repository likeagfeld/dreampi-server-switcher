# 🎮 DreamPi Server Switcher Portal

A beautiful web interface for switching between DCLive and DCNet servers on your DreamPi with one click.

![Dreamcast Logo](https://img.shields.io/badge/SEGA-Dreamcast-FF6600?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.5+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-1.1.4-000000?style=for-the-badge&logo=flask&logoColor=white)

## 🚀 Quick Install

One command installation:

```bash
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/install.sh | sudo bash
```

## ✨ Features

- **🔄 One-Click Server Switching** - Switch between DCLive and DCNet instantly
- **📱 Mobile Friendly** - Beautiful responsive design works on any device
- **🔍 Real-Time Status** - See current server and service status
- **🎨 Dreamcast Themed** - Authentic Dreamcast orange and blue design
- **🚦 Auto-Start** - Runs automatically on boot
- **🔧 No Configuration** - Works out of the box

## 📋 Requirements

- Raspberry Pi with DreamPi installed
- Python 3.5+ (included in Raspbian)
- Network connection
- DreamPi custom scripts (auto-downloaded during install)

## 🖥️ Usage

1. Open your browser and go to: `http://YOUR_PI_IP:8080`
2. Current server status is shown at the top
3. Click the button for the server you want to use
4. Wait ~10 seconds for the switch to complete
5. The page will refresh showing the new server

## 🛠️ Management Commands

```bash
# Check portal status
sudo systemctl status dreampi-portal

# View logs
sudo journalctl -u dreampi-portal -f

# Restart portal
sudo systemctl restart dreampi-portal

# Stop portal
sudo systemctl stop dreampi-portal

# Start portal
sudo systemctl start dreampi-portal
```

## 📁 File Locations

- Portal files: `/opt/dreampi-portal/`
- Custom scripts: `/home/pi/dreampi_custom_scripts/`
- DreamPi files: `/home/pi/dreampi/`
- Service file: `/etc/systemd/system/dreampi-portal.service`

## 🔧 How It Works

The portal works by copying different versions of `dreampi.py`:

- **DCLive Mode**: Uses the standard `dreampi.py`
- **DCNet Mode**: Uses `dreampi_dcnet.py` which includes DCNet/Flycast support

When you click a button, the portal:
1. Stops the DreamPi service
2. Copies the appropriate dreampi.py version
3. Starts the DreamPi service
4. Updates the display

## 🆘 Troubleshooting

### Portal won't start
```bash
# Check Python version (needs 3.5+)
python3 --version

# Check if Flask is installed
python3 -m pip list | grep flask

# Reinstall Flask if needed
sudo python3 -m pip install flask==1.1.4
```

### Can't access the portal
```bash
# Check if it's running
sudo systemctl status dreampi-portal

# Check your Pi's IP
hostname -I

# Check if port 8080 is open
sudo netstat -tlnp | grep 8080
```

### Server won't switch
```bash
# Check if scripts exist
ls -la /home/pi/dreampi_custom_scripts/
ls -la /home/pi/dreampi_custom_scripts/DCNET_V2/

# Check DreamPi service
sudo systemctl status dreampi

# Try manual switch to test
sudo systemctl stop dreampi
sudo cp /home/pi/dreampi_custom_scripts/DCNET_V2/dreampi_dcnet.py /home/pi/dreampi/dreampi.py
sudo systemctl start dreampi
```

## 🗑️ Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/likeagfeld/dreampi-server-switcher/master/uninstall.sh | sudo bash
```

## 🤝 Contributing

Pull requests are welcome! Feel free to:
- Add new features
- Improve the UI
- Fix bugs
- Update documentation

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Credits

- DreamPi Team for the amazing DreamPi software
- [scrivanidc](https://github.com/scrivanidc) for the DCNet custom scripts
- The Dreamcast community for keeping the dream alive!

## 🌟 Support

If you find this useful, please give it a star! ⭐

For issues or questions:
- Open an [issue](https://github.com/likeagfeld/dreampi-server-switcher/issues)
- Join the Dreamcast community forums

---

*Made with ❤️ for the Dreamcast community*
