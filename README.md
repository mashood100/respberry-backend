# Universal Game Hub

A cross-platform Django application that creates a local game hub where mobile devices can connect via QR code to see synchronized content in real-time. **Works on Raspberry Pi, macOS, Windows, and Linux** with automatic OS detection and appropriate hotspot setup.

## 🌟 Features

- **🔄 Universal OS Support**: Automatically detects and configures for Raspberry Pi OS, macOS, Windows, and Linux
- **📱 QR Code Connection**: WiFi QR codes for automatic hotspot connection + URL QR codes for easy access
- **⚡ Real-time Sync**: Content updates instantly across all connected devices via WebSockets
- **📊 Progress Feedback**: Visual progress indicators during dependency installation
- **🎮 Dynamic Content**: Support for text, images, and mixed content with customizable styling
- **🏠 Offline Operation**: Works completely offline - no internet required
- **📡 Smart Hotspot**: Creates appropriate hotspot for each operating system
- **👥 Device Tracking**: Monitor connected devices and session statistics

## 🖥️ Operating System Support

| OS                  | Hotspot Method        | Default IP      | Status             |
| ------------------- | --------------------- | --------------- | ------------------ |
| **Raspberry Pi OS** | `hostapd` + `dnsmasq` | `192.168.4.1`   | ✅ Fully Automated |
| **Linux**           | `hostapd` + `dnsmasq` | `192.168.4.1`   | ✅ Fully Automated |
| **macOS**           | Internet Sharing      | `192.168.2.1`   | 🔧 Semi-Automated  |
| **Windows**         | Mobile Hotspot        | `192.168.137.1` | 🔧 Semi-Automated  |

## 📋 Requirements

### Universal Requirements

- Python 3.8+
- Modern web browsers on mobile devices

### OS-Specific Requirements

#### Raspberry Pi / Linux

- `hostapd` and `dnsmasq` (auto-installed)
- `redis-server` (auto-installed)
- WiFi capability

#### macOS

- Homebrew (auto-installed if missing)
- Redis via Homebrew
- WiFi capability

#### Windows

- Python from python.org
- Redis (or Windows Subsystem for Linux)
- WiFi capability

## 🚀 Quick Start

### Option 1: Universal One-Command Setup (Recommended)

```bash
./start_game_hub.sh
```

**New: Smart Hotspot Detection!** 🔍

- Automatically detects existing hotspot settings on your device
- Uses your device name as hotspot SSID when available
- Prompts only for missing information (like passwords)
- Falls back to default settings only when necessary

**Detection Sources:**

- **Raspberry Pi/Linux**: Checks `hostapd.conf` and NetworkManager profiles
- **macOS**: Uses device name and Internet Sharing preferences
- **Windows**: Detects Mobile Hotspot settings and computer name
- **Fallback**: Uses "GameHub-Direct" with password "gamehub123"

This universal script will:

1. 🔍 Detect your operating system
2. 📡 Find existing hotspot settings or prompt for custom ones
3. 📦 Install required dependencies with progress indicators
4. 🔧 Set up OS-appropriate hotspot (hostapd/Internet Sharing/Mobile Hotspot)
5. 🚀 Start the Game Hub server with real-time sync

### 2. Start the Game Hub

```bash
# Make executable and run
chmod +x start_game_hub.sh
./start_game_hub.sh
```

### 3. Connect Mobile Devices

The script will automatically:

1. **Detect your OS** (Raspberry Pi, macOS, Windows, Linux)
2. **Install dependencies** with progress feedback
3. **Create appropriate hotspot** for your system
4. **Start the game server**
5. **Display connection instructions**

## 🔧 How It Works

### Automatic OS Detection

```bash
🔍 Detecting operating system...
🥧 Detected: Raspberry Pi OS    # or macOS, Windows, Linux
   IP will be: 192.168.4.1
   Interface: wlan0
```

### Progress Feedback

```bash
📦 Installing dependencies for raspberry_pi...
🔄 Updating package list...
Updating repositories [✅]
   📥 Installing python3-pip...
Installing python3-pip [✅]
   📥 Installing hostapd...
Installing hostapd [✅]
```

### Smart Hotspot Creation

The system automatically configures the appropriate hotspot method:

- **Raspberry Pi/Linux**: Uses `hostapd` and `dnsmasq`
- **macOS**: Configures Internet Sharing (with manual assistance)
- **Windows**: Sets up Mobile Hotspot (with manual assistance)

## 📱 Connection Process

### For Phones/Tablets

1. **Scan WiFi QR Code** → Auto-connect to hotspot
2. **Scan URL QR Code** → Open game interface
3. **Start Playing** → Real-time sync with main display

### Hotspot Details

- **SSID**: `GameHub-Direct`
- **Password**: `gamehub123`
- **URLs**:
  - Main Display: `http://[IP]:8000/`
  - Mobile View: `http://[IP]:8000/mobile/`
  - Admin Panel: `http://[IP]:8000/admin-panel/`

## 🎮 Usage Examples

### Raspberry Pi Setup

```bash
# On Raspberry Pi
./start_game_hub.sh

# Creates standalone hotspot at 192.168.4.1
# Phones connect directly to Pi
# Complete offline operation
```

### macOS Setup

```bash
# On Mac
./start_game_hub.sh

# Guides through Internet Sharing setup
# Creates hotspot at 192.168.2.1
# Phones connect to Mac's hotspot
```

### Windows Setup

```bash
# On Windows (with WSL or Git Bash)
./start_game_hub.sh

# Guides through Mobile Hotspot setup
# Creates hotspot at 192.168.137.1
# Phones connect to Windows hotspot
```

## 🛠️ Advanced Configuration

### Custom Hotspot Settings

Edit `start_game_hub.sh`:

```bash
HOTSPOT_SSID="MyGameHub"
HOTSPOT_PASSWORD="mypassword123"
SERVER_PORT="8000"
```

### OS-Specific Customization

The script automatically handles:

- **IP Detection**: Prioritizes hotspot IPs for each OS
- **Command Selection**: Uses appropriate tools (`ip` vs `ifconfig` vs `ipconfig`)
- **Service Management**: `systemctl` vs `brew services` vs Windows services

## 📊 Admin Interface

Access the admin panel at `http://[IP]:8000/admin-panel/` to:

- **Create Content**: Text, images, mixed content
- **Manage Sessions**: Track connected devices
- **Real-time Control**: Activate/deactivate content instantly
- **Monitor Stats**: View connection statistics

## 🔧 Troubleshooting

### Run Diagnostics

```bash
python3 test_universal.py
```

### Common Issues

#### Raspberry Pi/Linux

```bash
# WiFi blocked
sudo rfkill unblock wifi

# Missing packages
sudo apt install hostapd dnsmasq

# Service conflicts
sudo systemctl stop wpa_supplicant
```

#### macOS

```bash
# Homebrew issues
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Internet Sharing
# Go to System Preferences → Sharing → Internet Sharing
```

#### Windows

```bash
# Use WSL for Linux commands
wsl --install

# Or install Windows dependencies manually
# Python, Redis, enable Mobile Hotspot
```

## 🔒 Security & Performance

### Security Features

- **Isolated Network**: Hotspot is separate from main internet
- **Local Only**: No external connections required
- **Configurable**: Change default passwords and SSIDs

### Performance Tips

- **Raspberry Pi 4** recommended for 10+ devices
- **Class 10 SD Card** for better Pi performance
- **5GHz WiFi** for better bandwidth (if supported)

## 📁 File Structure

```
raspberry/
├── start_game_hub.sh           # Universal startup script
├── test_universal.py           # OS detection & testing
├── gamehub/                    # Django app
│   ├── views.py               # Universal IP detection
│   ├── models.py              # Game content & sessions
│   └── consumers.py           # WebSocket handlers
├── templates/gamehub/          # Responsive templates
├── RASPBERRY_PI_SETUP.md      # Pi-specific guide
└── requirements.txt           # Python dependencies
```

## 🎯 Use Cases

- **🏫 Classroom Games**: Teacher's device as hub, students connect
- **🎉 Party Games**: Host creates hub, guests join via QR
- **🏢 Corporate Events**: Interactive presentations and polls
- **🏠 Family Gaming**: Living room hub for mobile games
- **🚌 Travel Entertainment**: Portable gaming on the go

## 🔄 Updates & Development

### Update the System

```bash
# Stop server (Ctrl+C)
# Update code files
./start_game_hub.sh  # Restart
```

### Add New OS Support

1. Update `detect_os()` in `start_game_hub.sh`
2. Add OS-specific setup function
3. Update IP detection in `gamehub/views.py`
4. Test with `test_universal.py`

## 🤝 Contributing

1. **Test on your OS**: Run `test_universal.py`
2. **Report Issues**: Include OS detection output
3. **Add Features**: Follow the universal detection pattern
4. **Submit PRs**: Include cross-platform testing

## 📞 Support

For issues:

1. **Run diagnostics**: `python3 test_universal.py`
2. **Check logs**: Terminal output during startup
3. **Verify OS support**: Ensure your OS is in the compatibility list
4. **Manual setup**: Follow OS-specific guides if auto-setup fails

---

**🎮 Ready to create your universal gaming hub across any platform!**
