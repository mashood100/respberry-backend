#!/bin/bash

# Universal Game Hub Startup Script
# Automatically detects OS and uses existing hotspot settings when available
# Supports: Raspberry Pi OS, macOS, Windows (WSL), and Linux

echo "🎮 Starting Game Hub - Universal Mode"
echo "===================================="

# Default fallback configuration (only used if no existing settings found)
DEFAULT_HOTSPOT_SSID="GameHub-Direct"
DEFAULT_HOTSPOT_PASSWORD="gamehub123"
SERVER_PORT="8000"

# Variables for detected settings
HOTSPOT_SSID=""
HOTSPOT_PASSWORD=""
HOTSPOT_SOURCE=""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "❌ Please don't run this script as root. We'll ask for sudo when needed."
    exit 1
fi

# Function to show progress spinner
show_spinner() {
    local pid=$1
    local message=$2
    local delay=0.1
    local spinstr='|/-\'
    echo -n "$message "
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf "[%c]" "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b"
    done
    printf "   \b\b\b"
    echo "✅"
}

# Function to detect existing hotspot settings
detect_hotspot_settings() {
    echo "🔍 Detecting existing hotspot settings..."
    
    case $OS_TYPE in
        "raspberry_pi"|"linux")
            # Check existing hostapd configuration
            if [ -f "/etc/hostapd/hostapd.conf" ]; then
                existing_ssid=$(grep "^ssid=" /etc/hostapd/hostapd.conf 2>/dev/null | cut -d'=' -f2)
                existing_password=$(grep "^wpa_passphrase=" /etc/hostapd/hostapd.conf 2>/dev/null | cut -d'=' -f2)
                
                if [ -n "$existing_ssid" ] && [ -n "$existing_password" ]; then
                    HOTSPOT_SSID="$existing_ssid"
                    HOTSPOT_PASSWORD="$existing_password"
                    HOTSPOT_SOURCE="existing hostapd config"
                    echo "✅ Found existing hotspot: $HOTSPOT_SSID"
                    return 0
                fi
            fi
            
            # Check NetworkManager saved connections
            if command -v nmcli &> /dev/null; then
                hotspot_connection=$(nmcli -t -f NAME,TYPE con show | grep ":802-11-wireless" | head -1 | cut -d':' -f1)
                if [ -n "$hotspot_connection" ]; then
                    existing_ssid=$(nmcli -t -f 802-11-wireless.ssid con show "$hotspot_connection" 2>/dev/null | cut -d':' -f2)
                    existing_password=$(nmcli -s -t -f 802-11-wireless-security.psk con show "$hotspot_connection" 2>/dev/null | cut -d':' -f2)
                    
                    if [ -n "$existing_ssid" ] && [ -n "$existing_password" ]; then
                        HOTSPOT_SSID="$existing_ssid"
                        HOTSPOT_PASSWORD="$existing_password"
                        HOTSPOT_SOURCE="NetworkManager profile"
                        echo "✅ Found NetworkManager hotspot: $HOTSPOT_SSID"
                        return 0
                    fi
                fi
            fi
            ;;
            
        "macos")
            # Check macOS Internet Sharing preferences
            if [ -f "/Library/Preferences/SystemConfiguration/preferences.plist" ]; then
                # Try to extract WiFi hotspot settings (requires plutil)
                if command -v plutil &> /dev/null; then
                    existing_ssid=$(plutil -extract "NetworkServices" raw "/Library/Preferences/SystemConfiguration/preferences.plist" 2>/dev/null | grep -i "ssid" | head -1 | cut -d'"' -f4)
                    if [ -n "$existing_ssid" ]; then
                        HOTSPOT_SSID="$existing_ssid"
                        HOTSPOT_PASSWORD="$(security find-generic-password -w -s 'AirPort network password' 2>/dev/null || echo '')"
                        HOTSPOT_SOURCE="macOS Internet Sharing"
                        echo "✅ Found macOS hotspot: $HOTSPOT_SSID"
                        return 0
                    fi
                fi
            fi
            
                         # Check for common macOS hotspot patterns
             device_name=$(scutil --get ComputerName 2>/dev/null)
             if [ -n "$device_name" ]; then
                 HOTSPOT_SSID="$device_name"
                 # Generate a reasonable default password based on device name
                 device_suffix=$(echo "$device_name" | sed 's/[^a-zA-Z0-9]//g' | tr '[:upper:]' '[:lower:]' | tail -c 5)
                 HOTSPOT_PASSWORD="${device_suffix}123"
                 HOTSPOT_SOURCE="device name + generated password"
                 echo "✅ Using device name as hotspot: $HOTSPOT_SSID"
                 echo "✅ Generated password: $HOTSPOT_PASSWORD"
                 return 0
             fi
            ;;
            
        "windows")
            # Check Windows Mobile Hotspot settings
            if command -v netsh.exe &> /dev/null; then
                hotspot_info=$(netsh.exe wlan show profile name="Local Area Connection* 12" key=clear 2>/dev/null)
                if [ -n "$hotspot_info" ]; then
                    existing_ssid=$(echo "$hotspot_info" | grep "SSID name" | cut -d'"' -f2)
                    existing_password=$(echo "$hotspot_info" | grep "Key Content" | cut -d':' -f2 | xargs)
                    
                    if [ -n "$existing_ssid" ]; then
                        HOTSPOT_SSID="$existing_ssid"
                        HOTSPOT_PASSWORD="$existing_password"
                        HOTSPOT_SOURCE="Windows Mobile Hotspot"
                        echo "✅ Found Windows hotspot: $HOTSPOT_SSID"
                        return 0
                    fi
                fi
            fi
            
                         # Fallback to computer name
             computer_name=$(hostname 2>/dev/null)
             if [ -n "$computer_name" ]; then
                 HOTSPOT_SSID="$computer_name"
                 # Generate a reasonable default password based on computer name
                 device_suffix=$(echo "$computer_name" | sed 's/[^a-zA-Z0-9]//g' | tr '[:upper:]' '[:lower:]' | tail -c 5)
                 HOTSPOT_PASSWORD="${device_suffix}123"
                 HOTSPOT_SOURCE="computer name + generated password"
                 echo "✅ Using computer name as hotspot: $HOTSPOT_SSID"
                 echo "✅ Generated password: $HOTSPOT_PASSWORD"
                 return 0
             fi
            ;;
    esac
    
    echo "⚠️  No existing hotspot settings found"
    return 1
}

# Function to prompt user for hotspot settings
prompt_hotspot_settings() {
    echo ""
    echo "🔧 Hotspot Configuration"
    echo "========================"
    
    # Show current settings
    echo "📱 Current settings:"
    echo "   SSID: ${HOTSPOT_SSID:-$DEFAULT_HOTSPOT_SSID}"
    echo "   Password: ${HOTSPOT_PASSWORD:-$DEFAULT_HOTSPOT_PASSWORD}"
    echo "   Source: ${HOTSPOT_SOURCE:-default}"
    echo ""
    echo "Would you like to:"
    echo "   1) Use these settings (Recommended)"
    echo "   2) Enter custom settings"
    echo "   3) Use default GameHub settings"
    echo ""
    read -p "Choice (1-3, default: 1): " choice
    
    case $choice in
        2)
            echo "📱 Enter custom hotspot name:"
            read -p "SSID: " custom_ssid
            echo "🔑 Enter custom password:"
            read -s -p "Password: " custom_password
            echo ""
            if [ -n "$custom_ssid" ] && [ -n "$custom_password" ]; then
                HOTSPOT_SSID="$custom_ssid"
                HOTSPOT_PASSWORD="$custom_password"
                HOTSPOT_SOURCE="user input"
            else
                echo "⚠️  Invalid input, using detected settings"
            fi
            ;;
        3)
            HOTSPOT_SSID="$DEFAULT_HOTSPOT_SSID"
            HOTSPOT_PASSWORD="$DEFAULT_HOTSPOT_PASSWORD"
            HOTSPOT_SOURCE="default"
            ;;
        *)
            echo "✅ Using detected settings"
            ;;
    esac
    
    # Final fallback to defaults
    if [ -z "$HOTSPOT_SSID" ]; then
        HOTSPOT_SSID="$DEFAULT_HOTSPOT_SSID"
        HOTSPOT_PASSWORD="$DEFAULT_HOTSPOT_PASSWORD"
        HOTSPOT_SOURCE="default fallback"
    fi
}

# Function to detect and setup Python
setup_python() {
    echo "🐍 Checking Python installation..."
    
    # Variable to store the Python command to use
    PYTHON_CMD=""
    PYTHON_VERSION=""
    
    # Check for python3 first (preferred)
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        echo "✅ Found Python 3: $PYTHON_VERSION"
        return 0
    fi
    
    # Check for python command
    if command -v python &> /dev/null; then
        # Determine if it's Python 2 or 3
        python_version=$(python --version 2>&1)
        if [[ $python_version == *"Python 3"* ]]; then
            PYTHON_CMD="python"
            PYTHON_VERSION=$(echo "$python_version" | cut -d' ' -f2)
            echo "✅ Found Python 3 (via 'python'): $PYTHON_VERSION"
            return 0
        elif [[ $python_version == *"Python 2"* ]]; then
            echo "⚠️  Found Python 2: $(echo "$python_version" | cut -d' ' -f2)"
            echo "   Python 3 is required but not found as 'python3'"
            
            # Try to install Python 3
            install_python3
            if [ $? -eq 0 ]; then
                return 0
            else
                echo "❌ Failed to install Python 3"
                return 1
            fi
        fi
    fi
    
    # No Python found at all
    echo "❌ No Python installation found"
    install_python3
    return $?
}

# Function to install Python 3
install_python3() {
    echo "📦 Installing Python 3..."
    
    case $OS_TYPE in
        "raspberry_pi"|"linux")
            echo "🔄 Installing Python 3 on Linux..."
            if command -v apt &> /dev/null; then
                sudo apt update -qq &
                show_spinner $! "Updating package lists"
                sudo apt install -y python3 python3-pip python3-venv &
                show_spinner $! "Installing Python 3"
            elif command -v yum &> /dev/null; then
                sudo yum install -y python3 python3-pip &
                show_spinner $! "Installing Python 3"
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y python3 python3-pip &
                show_spinner $! "Installing Python 3"
            elif command -v pacman &> /dev/null; then
                sudo pacman -S --noconfirm python python-pip &
                show_spinner $! "Installing Python 3"
            else
                echo "❌ Unsupported Linux distribution"
                return 1
            fi
            ;;
            
        "macos")
            echo "🔄 Installing Python 3 on macOS..."
            if command -v brew &> /dev/null; then
                brew install python3 &
                show_spinner $! "Installing Python 3 via Homebrew"
            elif command -v port &> /dev/null; then
                sudo port install python39 +universal &
                show_spinner $! "Installing Python 3 via MacPorts"
            else
                echo "❌ Neither Homebrew nor MacPorts found"
                echo "📋 Please install Python 3 manually:"
                echo "   • Install Homebrew: https://brew.sh"
                echo "   • Then run: brew install python3"
                echo "   • Or download from: https://python.org/downloads/"
                return 1
            fi
            ;;
            
        "windows")
            echo "🔄 Installing Python 3 on Windows..."
            if command -v winget &> /dev/null; then
                winget install Python.Python.3 &
                show_spinner $! "Installing Python 3 via winget"
            elif command -v choco &> /dev/null; then
                choco install python3 -y &
                show_spinner $! "Installing Python 3 via Chocolatey"
            else
                echo "❌ Neither winget nor Chocolatey found"
                echo "📋 Please install Python 3 manually:"
                echo "   • Download from: https://python.org/downloads/"
                echo "   • Or install via Microsoft Store"
                return 1
            fi
            ;;
            
        *)
            echo "❌ Unsupported operating system for automatic Python installation"
            echo "📋 Please install Python 3 manually and try again"
            return 1
            ;;
    esac
    
    # Verify installation
    sleep 2
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        echo "✅ Successfully installed Python 3: $PYTHON_VERSION"
        return 0
    elif command -v python &> /dev/null; then
        python_version=$(python --version 2>&1)
        if [[ $python_version == *"Python 3"* ]]; then
            PYTHON_CMD="python"
            PYTHON_VERSION=$(echo "$python_version" | cut -d' ' -f2)
            echo "✅ Successfully installed Python 3 (via 'python'): $PYTHON_VERSION"
            return 0
        fi
    fi
    
    echo "❌ Python 3 installation failed or not detected"
    return 1
}

# Function to detect operating system
detect_os() {
    echo "🔍 Detecting operating system..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Check if it's Raspberry Pi
        if [ -f /proc/cpuinfo ] && grep -q "Raspberry Pi\|BCM2" /proc/cpuinfo 2>/dev/null; then
            echo "🥧 Detected: Raspberry Pi OS"
            OS_TYPE="raspberry_pi"
            HOTSPOT_IP="192.168.4.1"
            WIFI_INTERFACE="wlan0"
        elif command -v systemctl &> /dev/null; then
            echo "🐧 Detected: Linux (systemd)"
            OS_TYPE="linux"
            HOTSPOT_IP="192.168.4.1"
            WIFI_INTERFACE="wlan0"
        else
            echo "🐧 Detected: Linux (generic)"
            OS_TYPE="linux_generic"
            HOTSPOT_IP="192.168.4.1"
            WIFI_INTERFACE="wlan0"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "🍎 Detected: macOS"
        OS_TYPE="macos"
        HOTSPOT_IP="192.168.2.1"
        WIFI_INTERFACE="en0"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || grep -q Microsoft /proc/version 2>/dev/null; then
        echo "🪟 Detected: Windows (WSL/MSYS)"
        OS_TYPE="windows"
        HOTSPOT_IP="192.168.137.1"
        WIFI_INTERFACE="wlan0"
    else
        echo "❓ Detected: Unknown OS ($OSTYPE)"
        OS_TYPE="unknown"
        HOTSPOT_IP="127.0.0.1"
        WIFI_INTERFACE="wlan0"
    fi
    
    echo "   IP will be: $HOTSPOT_IP"
    echo "   Interface: $WIFI_INTERFACE"
}

# Function to install dependencies with progress
install_dependencies_with_progress() {
    echo "📦 Installing dependencies for $OS_TYPE..."
    
    case $OS_TYPE in
        "raspberry_pi"|"linux")
            echo "🔄 Updating package list..."
            sudo apt update -qq &
            show_spinner $! "Updating repositories"
            
            echo "🔄 Installing system packages..."
            packages=("hostapd" "dnsmasq" "redis-server")
            
            # Only install Python packages if we don't already have a working Python 3
            if [ -z "$PYTHON_CMD" ]; then
                packages+=("python3-pip" "python3-venv")
            fi
            
            for package in "${packages[@]}"; do
                echo "   📥 Installing $package..."
                sudo apt install -y "$package" > /dev/null 2>&1 &
                show_spinner $! "Installing $package"
            done
            
            echo "🔄 Enabling services..."
            sudo systemctl enable redis-server > /dev/null 2>&1
            sudo systemctl start redis-server > /dev/null 2>&1
            echo "   ✅ Redis service enabled"
            ;;
            
        "macos")
            if ! command -v brew &> /dev/null; then
                echo "🍺 Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" &
                show_spinner $! "Installing Homebrew"
            fi
            
            echo "🔄 Installing macOS packages..."
            packages=("redis")
            
            # Only install Python if we don't already have a working Python 3
            if [ -z "$PYTHON_CMD" ]; then
                packages+=("python3")
            fi
            
            for package in "${packages[@]}"; do
                echo "   📥 Installing $package..."
                brew install "$package" > /dev/null 2>&1 &
                show_spinner $! "Installing $package"
            done
            
            echo "🔄 Starting services..."
            brew services start redis > /dev/null 2>&1
            echo "   ✅ Redis service started"
            ;;
            
        "windows")
            echo "🔄 Installing Windows (WSL) packages..."
            if command -v apt &> /dev/null; then
                sudo apt update -qq &
                show_spinner $! "Updating repositories"
                
                packages=("redis-server")
                
                # Only install Python packages if we don't already have a working Python 3
                if [ -z "$PYTHON_CMD" ]; then
                    packages+=("python3-pip" "python3-venv")
                fi
                
                for package in "${packages[@]}"; do
                    echo "   📥 Installing $package..."
                    sudo apt install -y "$package" > /dev/null 2>&1 &
                    show_spinner $! "Installing $package"
                done
            fi
            ;;
            
        *)
            echo "⚠️  Unknown OS - attempting generic Linux installation..."
            if command -v apt &> /dev/null; then
                if [ -z "$PYTHON_CMD" ]; then
                    sudo apt update -qq && sudo apt install -y python3-pip python3-venv redis-server
                else
                    sudo apt update -qq && sudo apt install -y redis-server
                fi
            elif command -v yum &> /dev/null; then
                if [ -z "$PYTHON_CMD" ]; then
                    sudo yum install -y python3-pip redis
                else
                    sudo yum install -y redis
                fi
            elif command -v pacman &> /dev/null; then
                if [ -z "$PYTHON_CMD" ]; then
                    sudo pacman -S --noconfirm python-pip redis
                else
                    sudo pacman -S --noconfirm redis
                fi
            fi
            ;;
    esac
}

# Function to install Python dependencies with progress
install_python_dependencies() {
    echo "🐍 Installing Python dependencies..."
    
    # Check if virtual environment exists and activate it
    if [ -d "venv" ]; then
        echo "📦 Activating existing virtual environment..."
        source venv/bin/activate
    else
        echo "📦 Creating virtual environment..."
        $PYTHON_CMD -m venv venv &
        show_spinner $! "Creating virtual environment"
        source venv/bin/activate
    fi
    
    # Install dependencies if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        echo "📥 Installing Python packages..."
        
        # Count total packages for progress
        total_packages=$(grep -c "^[^#]" requirements.txt 2>/dev/null || echo "unknown")
        echo "   Total packages to install: $total_packages"
        
        # Install with verbose output
        echo "🔄 Installing packages (this may take a while)..."
        $PYTHON_CMD -m pip install -r requirements.txt --progress-bar on 2>&1 | while IFS= read -r line; do
            if [[ $line == *"Collecting"* ]]; then
                package=$(echo "$line" | sed 's/Collecting //' | cut -d' ' -f1)
                echo "   📥 Downloading: $package"
            elif [[ $line == *"Installing collected packages"* ]]; then
                echo "   🔧 Installing collected packages..."
            elif [[ $line == *"Successfully installed"* ]]; then
                echo "   ✅ Installation completed"
            fi
        done
        
        echo "✅ Python dependencies installed successfully"
    else
        echo "⚠️  No requirements.txt found"
    fi
}

# Function to setup hotspot based on OS
setup_hotspot_by_os() {
    echo "🔧 Setting up hotspot for $OS_TYPE..."
    
    case $OS_TYPE in
        "raspberry_pi"|"linux")
            setup_linux_hotspot
            ;;
        "macos")
            setup_macos_hotspot
            ;;
        "windows")
            setup_windows_hotspot
            ;;
        *)
            echo "⚠️  Hotspot setup not available for this OS"
            echo "   The app will run in localhost mode"
            return 1
            ;;
    esac
}

# Function to setup Linux/Pi hotspot
setup_linux_hotspot() {
    echo "🐧 Setting up Linux hotspot..."
    
    # Check if hostapd and dnsmasq are available
    if ! command -v hostapd &> /dev/null || ! command -v dnsmasq &> /dev/null; then
        echo "❌ hostapd or dnsmasq not available"
        return 1
    fi
    
    # Create hostapd configuration
    echo "📝 Creating hotspot configuration..."
    sudo tee /etc/hostapd/hostapd.conf > /dev/null << EOF
interface=$WIFI_INTERFACE
driver=nl80211
ssid=$HOTSPOT_SSID
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$HOTSPOT_PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

    # Create dnsmasq configuration
    sudo tee /etc/dnsmasq.conf > /dev/null << EOF
interface=$WIFI_INTERFACE
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=wlan
address=/gw.wlan/$HOTSPOT_IP
EOF

    # Configure interface
    sudo ifconfig $WIFI_INTERFACE $HOTSPOT_IP netmask 255.255.255.0 2>/dev/null
    
    # Start services
    echo "🚀 Starting hotspot services..."
    sudo hostapd /etc/hostapd/hostapd.conf -B &
    show_spinner $! "Starting hostapd"
    
    sudo dnsmasq -C /etc/dnsmasq.conf &
    show_spinner $! "Starting dnsmasq"
    
    if pgrep hostapd > /dev/null && pgrep dnsmasq > /dev/null; then
        echo "✅ Linux hotspot started successfully"
        return 0
    else
        echo "❌ Failed to start Linux hotspot"
        return 1
    fi
}

# Function to setup macOS hotspot
setup_macos_hotspot() {
    echo "🍎 Setting up macOS hotspot..."
    
    # Check if Internet Sharing is available
    if ! pgrep -f "InternetSharing" > /dev/null 2>&1; then
        echo "📋 Manual macOS setup required:"
        echo "   1. Go to System Preferences → Sharing"
        echo "   2. Select 'Internet Sharing'"
        echo "   3. Share from: Wi-Fi, To: Wi-Fi"
        echo "   4. Set WiFi Options:"
        echo "      - Network Name: $HOTSPOT_SSID"
        echo "      - Password: $HOTSPOT_PASSWORD"
        echo "   5. Enable Internet Sharing"
        echo ""
        echo "⏳ Press ENTER when setup is complete..."
        read -p ""
    else
        echo "✅ macOS Internet Sharing already active"
    fi
    
    return 0
}

# Function to setup Windows hotspot
setup_windows_hotspot() {
    echo "🪟 Setting up Windows hotspot..."
    
    if command -v netsh.exe &> /dev/null; then
        echo "🔧 Configuring Windows Mobile Hotspot..."
        netsh.exe wlan set hostednetwork mode=allow ssid="$HOTSPOT_SSID" key="$HOTSPOT_PASSWORD" &
        show_spinner $! "Configuring hotspot"
        
        netsh.exe wlan start hostednetwork &
        show_spinner $! "Starting hotspot"
        
        echo "✅ Windows hotspot configured"
    else
        echo "📋 Manual Windows setup required:"
        echo "   1. Open Settings → Network & Internet → Mobile hotspot"
        echo "   2. Set Network name: $HOTSPOT_SSID"
        echo "   3. Set Network password: $HOTSPOT_PASSWORD"
        echo "   4. Turn on Mobile hotspot"
        echo ""
        echo "⏳ Press ENTER when setup is complete..."
        read -p ""
    fi
    
    return 0
}

# Main execution starts here
echo ""

# Detect OS
detect_os

# Check and setup Python
if ! setup_python; then
    echo "❌ Python 3 is required but could not be installed or detected."
    echo "📋 Please install Python 3 manually and try again."
    exit 1
fi

# Detect existing hotspot settings
if ! detect_hotspot_settings; then
    # Prompt user for hotspot settings if no existing ones found
    prompt_hotspot_settings
fi

# Handle missing passwords (critical for QR code generation)
if [ -n "$HOTSPOT_SSID" ] && [ -z "$HOTSPOT_PASSWORD" ]; then
    echo ""
    echo "🚨 CRITICAL: Hotspot password required for QR code generation!"
    echo "📱 Hotspot Name: $HOTSPOT_SSID"
    echo "🔍 Could not auto-detect password from system settings"
    echo ""
    echo "📋 Please check your system and find the actual hotspot password:"
    
    case $OS_TYPE in
        "macos")
            echo "   1. Go to System Preferences → Sharing → Internet Sharing"
            echo "   2. Click 'Wi-Fi Options...' to see the password"
            echo "   3. Or check Keychain Access for saved WiFi passwords"
            ;;
        "windows")
            echo "   1. Go to Settings → Network & Internet → Mobile hotspot"
            echo "   2. Check the 'Network password' field"
            echo "   3. Or use: netsh wlan show profile name=\"$HOTSPOT_SSID\" key=clear"
            ;;
        "raspberry_pi"|"linux")
            echo "   1. Check /etc/hostapd/hostapd.conf for 'wpa_passphrase'"
            echo "   2. Or check NetworkManager: nmcli connection show"
            ;;
    esac
    
    echo ""
    while [ -z "$HOTSPOT_PASSWORD" ]; do
        read -s -p "🔑 Enter the ACTUAL hotspot password for '$HOTSPOT_SSID': " HOTSPOT_PASSWORD
        echo ""
        
        if [ -z "$HOTSPOT_PASSWORD" ]; then
            echo "❌ Password cannot be empty! QR codes won't work without the correct password."
            echo "   Would you like to:"
            echo "   1) Try again (Recommended)"
            echo "   2) Use default password 'gamehub123' (QR codes may not work)"
            echo "   3) Skip hotspot setup (Local network only)"
            echo ""
            read -p "Choice (1-3): " choice
            
            case $choice in
                2)
                    HOTSPOT_PASSWORD="$DEFAULT_HOTSPOT_PASSWORD"
                    HOTSPOT_SOURCE="$HOTSPOT_SOURCE + fallback default"
                    echo "⚠️  Using default password - QR codes may not work for auto-connection"
                    break
                    ;;
                3)
                    HOTSPOT_PASSWORD="SKIP_HOTSPOT"
                    HOTSPOT_SOURCE="manual setup required"
                    echo "⚠️  Skipping hotspot setup - manual connection required"
                    break
                    ;;
                *)
                    echo "🔄 Please try entering the password again..."
                    ;;
            esac
        else
            # Validate password length
            if [ ${#HOTSPOT_PASSWORD} -lt 8 ]; then
                echo "⚠️  WiFi passwords should be at least 8 characters. Are you sure this is correct?"
                read -p "Continue anyway? (y/N): " confirm
                if [[ ! $confirm =~ ^[Yy]$ ]]; then
                    HOTSPOT_PASSWORD=""
                    continue
                fi
            fi
            
            HOTSPOT_SOURCE="$HOTSPOT_SOURCE + user provided"
            echo "✅ Password accepted"
        fi
    done
fi

# Display final settings
echo ""
echo "📡 Final Hotspot Configuration:"
echo "   SSID: $HOTSPOT_SSID"
echo "   Password: $HOTSPOT_PASSWORD"
echo "   Source: $HOTSPOT_SOURCE"
echo ""

# Install system dependencies
install_dependencies_with_progress

# Install Python dependencies
install_python_dependencies

# Setup hotspot
HOTSPOT_SUCCESS=false
if setup_hotspot_by_os; then
    HOTSPOT_SUCCESS=true
fi

# Run database operations
echo "🗄️ Setting up database..."
$PYTHON_CMD manage.py migrate --run-syncdb > /dev/null 2>&1 &
show_spinner $! "Running migrations"

echo "📝 Creating sample data..."
$PYTHON_CMD manage.py create_sample_data > /dev/null 2>&1 &
show_spinner $! "Creating sample data"

# Detect IP address
echo "🌐 Detecting network configuration..."
DETECTED_IP=""

# Enhanced IP detection
for i in {1..5}; do
    case $OS_TYPE in
        "raspberry_pi"|"linux")
            DETECTED_IP=$(ip addr show $WIFI_INTERFACE 2>/dev/null | grep -o "inet [0-9.]*" | cut -d' ' -f2 | head -1)
            ;;
        "macos")
            DETECTED_IP=$(ifconfig $WIFI_INTERFACE 2>/dev/null | grep "inet " | awk '{print $2}' | head -1)
            ;;
        "windows")
            DETECTED_IP=$(ipconfig.exe | grep -A 1 "Wireless LAN adapter" | grep "IPv4" | awk '{print $NF}' | head -1)
            ;;
    esac
    
    # Fallback to hostname
    if [ -z "$DETECTED_IP" ]; then
        DETECTED_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    
    # Final fallback to OS-specific default
    if [ -z "$DETECTED_IP" ] || [ "$DETECTED_IP" == "127.0.0.1" ]; then
        DETECTED_IP="$HOTSPOT_IP"
    fi
    
    if [ "$DETECTED_IP" != "$HOTSPOT_IP" ] && [ "$DETECTED_IP" != "127.0.0.1" ]; then
        echo "✅ Network interface ready: $DETECTED_IP"
        break
    fi
    
    sleep 1
done

# Display results
echo ""
echo "🎯 ========== GAME HUB READY =========="
echo "🖥️  Operating System: $OS_TYPE"
echo "🐍 Python Version: $PYTHON_VERSION ($PYTHON_CMD)"
echo "🌐 Server IP: $DETECTED_IP"

if [ "$HOTSPOT_SUCCESS" = true ]; then
    echo "📡 Hotspot Mode: ACTIVE"
echo "📱 Hotspot SSID: $HOTSPOT_SSID"
echo "🔑 Hotspot Password: $HOTSPOT_PASSWORD"
echo "🔧 Configuration Source: $HOTSPOT_SOURCE"
else
    echo "📡 Hotspot Mode: DISABLED"
    echo "🌐 Network Mode: Using existing connection"
fi

echo ""
echo "📱 Connection URLs:"
echo "   Main Display: http://$DETECTED_IP:$SERVER_PORT/"
echo "   Mobile View:  http://$DETECTED_IP:$SERVER_PORT/mobile/"
echo "   Admin Panel:  http://$DETECTED_IP:$SERVER_PORT/admin-panel/"
echo ""

if [ "$HOTSPOT_SUCCESS" = true ]; then
    echo "📋 MOBILE CONNECTION STEPS:"
    echo "   1. Connect to WiFi: '$HOTSPOT_SSID'"
    echo "   2. Enter password: '$HOTSPOT_PASSWORD'"
    echo "   3. Scan QR code OR go to: http://$DETECTED_IP:$SERVER_PORT/mobile/"
    echo "   📝 Note: Using $HOTSPOT_SOURCE for hotspot configuration"
else
    echo "📋 NETWORK MODE USAGE:"
    echo "   • Ensure devices are on same network as this computer"
    echo "   • Or manually set up hotspot '$HOTSPOT_SSID' and restart"
fi

echo ""
echo "🚀 Starting Game Hub server..."
echo "💡 Press Ctrl+C to stop"
echo "================================"

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    echo "👋 Game Hub stopped!"
    exit 0
}

# Set up cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start the Django server
$PYTHON_CMD manage.py runserver 0.0.0.0:$SERVER_PORT 