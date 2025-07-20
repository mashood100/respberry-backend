# Raspberry Pi Game Hub Setup Guide

This guide shows how to set up the Game Hub on a Raspberry Pi to create a **standalone hotspot** for mobile gaming without any internet connection.

## 🥧 What This Does

Your Raspberry Pi will:

- Create its own WiFi hotspot named `GameHub-Direct`
- Serve the game interface on `http://192.168.4.1:8000/`
- Allow mobile devices to connect directly to the Pi
- Work completely offline - no internet required

## 📋 Requirements

- Raspberry Pi 3B+ or newer (with built-in WiFi)
- Raspberry Pi OS (Raspbian) installed
- MicroSD card (16GB+ recommended)
- Power supply for Pi
- Monitor/TV for Pi display (optional)

## 🛠️ Installation Steps

### Step 1: Prepare Raspberry Pi

1. **Flash Raspberry Pi OS** to your SD card
2. **Enable SSH** (optional): Create empty `ssh` file on boot partition
3. **Boot the Pi** and connect to keyboard/monitor or SSH

### Step 2: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv git hostapd dnsmasq redis-server

# Enable Redis service
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### Step 3: Setup the Game Hub

```bash
# Clone or copy the project files to Pi
cd /home/pi
# (Copy your project files here)

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python3 manage.py migrate

# Create sample data
python3 manage.py create_sample_data
```

### Step 4: Test the Setup

```bash
# Test Pi environment
python3 test_pi_hotspot.py
```

### Step 5: Start the Game Hub

```bash
# Make script executable
chmod +x start_game_hub.sh

# Start the complete system
./start_game_hub.sh
```

## 🔧 How It Works

### Hotspot Configuration

- **SSID**: `GameHub-Direct`
- **Password**: `gamehub123`
- **Pi IP**: `192.168.4.1`
- **DHCP Range**: `192.168.4.2` to `192.168.4.20`

### Network Setup

The script automatically:

1. Installs `hostapd` (WiFi hotspot daemon)
2. Installs `dnsmasq` (DHCP/DNS server)
3. Configures WiFi interface (`wlan0`)
4. Creates hotspot with the above settings
5. Starts Django server on `192.168.4.1:8000`

### Mobile Connection Process

1. **Connect to WiFi**: Find `GameHub-Direct` in WiFi settings
2. **Enter Password**: `gamehub123`
3. **Access Game**: Go to `http://192.168.4.1:8000/mobile/`
4. **Or Scan QR Code**: Displayed on Pi screen

## 📱 Usage

### For Pi Display

- Connect Pi to monitor/TV
- Open browser: `http://192.168.4.1:8000/`
- Display shows QR codes and game content

### For Mobile Devices

1. Connect to `GameHub-Direct` WiFi
2. Open browser: `http://192.168.4.1:8000/mobile/`
3. Real-time sync with Pi display

### Admin Panel

- URL: `http://192.168.4.1:8000/admin-panel/`
- Create and manage game content
- Monitor connected devices

## 🚀 Auto-Start on Boot (Optional)

To start the Game Hub automatically when Pi boots:

```bash
# Edit crontab
crontab -e

# Add this line:
@reboot cd /home/pi/raspberry && ./start_game_hub.sh
```

## 🛠️ Troubleshooting

### Common Issues

1. **Hotspot won't start**

   ```bash
   # Check WiFi interface
   ip link show wlan0

   # Unblock WiFi
   sudo rfkill unblock wifi

   # Check for conflicting services
   sudo systemctl stop wpa_supplicant
   ```

2. **Can't connect to hotspot**

   ```bash
   # Check hostapd status
   sudo systemctl status hostapd

   # Check dnsmasq status
   sudo systemctl status dnsmasq

   # Restart services
   sudo systemctl restart hostapd
   sudo systemctl restart dnsmasq
   ```

3. **Pi not accessible**

   ```bash
   # Check Pi IP
   ip addr show wlan0

   # Should show: 192.168.4.1
   ```

### Log Files

- Hostapd: `sudo journalctl -u hostapd`
- Dnsmasq: `sudo journalctl -u dnsmasq`
- Django: Check terminal output

## 🔒 Security Notes

- Default password is `gamehub123` - change in `start_game_hub.sh`
- Hotspot is isolated from internet (by design)
- Only local network access to Pi services

## 📊 Performance Tips

- Use Class 10 SD card for better performance
- Raspberry Pi 4 recommended for more users
- Monitor Pi temperature during extended use

## 🎮 Game Development

The system supports:

- Real-time content updates
- WebSocket communication
- Image and text content
- Multiple connected devices
- Session management

## 🔄 Updates

To update the system:

1. Stop the server (Ctrl+C)
2. Update code files
3. Restart: `./start_game_hub.sh`

## 📞 Support

If you encounter issues:

1. Run `python3 test_pi_hotspot.py` to diagnose
2. Check log files for errors
3. Ensure all dependencies are installed
4. Verify Pi model supports hotspot mode

---

**Ready to create your portable gaming hub! 🎮**
