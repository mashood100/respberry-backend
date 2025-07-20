#!/usr/bin/env python3
"""
Hotspot Setup Helper for Game Hub
Helps configure macOS Internet Sharing for direct device connections
"""

import subprocess
import time
import os
import sys

def check_internet_sharing_status():
    """Check if Internet Sharing is currently active"""
    try:
        result = subprocess.run(['sudo', '/usr/bin/killall', '-0', 'bootpd'], 
                              capture_output=True, check=False)
        return result.returncode == 0
    except:
        return False

def get_wifi_interface():
    """Get the WiFi interface name"""
    try:
        result = subprocess.run(['networksetup', '-listallhardwareports'], 
                              capture_output=True, text=True, check=True)
        lines = result.stdout.split('\n')
        
        for i, line in enumerate(lines):
            if 'Wi-Fi' in line and i + 1 < len(lines):
                device_line = lines[i + 1]
                if device_line.startswith('Device:'):
                    return device_line.split(':')[1].strip()
    except:
        pass
    return 'en0'  # Default fallback

def setup_sharing_preferences():
    """Configure Internet Sharing preferences"""
    print("🔧 Configuring Internet Sharing...")
    
    try:
        # Enable Internet Sharing via system preferences
        sharing_plist = "/Library/Preferences/SystemConfiguration/com.apple.nat.plist"
        
        # Create NAT configuration
        nat_config = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NAT</key>
    <dict>
        <key>AirPort</key>
        <dict>
            <key>Enabled</key>
            <integer>1</integer>
        </dict>
        <key>Enabled</key>
        <integer>1</integer>
        <key>PrimaryInterface</key>
        <dict>
            <key>Device</key>
            <string>en0</string>
        </dict>
    </dict>
</dict>
</plist>'''
        
        # Write configuration with sudo
        with open('/tmp/nat_config.plist', 'w') as f:
            f.write(nat_config)
        
        subprocess.run(['sudo', 'cp', '/tmp/nat_config.plist', sharing_plist], check=True)
        subprocess.run(['sudo', 'chown', 'root:wheel', sharing_plist], check=True)
        subprocess.run(['sudo', 'chmod', '644', sharing_plist], check=True)
        
        print("✅ Internet Sharing configuration updated")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to configure Internet Sharing: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def provide_manual_instructions():
    """Provide clear manual setup instructions"""
    print("\n📋 MANUAL HOTSPOT SETUP INSTRUCTIONS:")
    print("=====================================")
    print("1. Open System Preferences")
    print("2. Click on 'Sharing'")
    print("3. Select 'Internet Sharing' from the left panel")
    print("4. Configure the following:")
    print("   • Share your connection from: Wi-Fi (or Ethernet if available)")
    print("   • To computers using: Wi-Fi")
    print("5. Click 'Wi-Fi Options...' button and set:")
    print("   • Network Name: GameHub-Direct")
    print("   • Security: WPA2 Personal")
    print("   • Password: gamehub123")
    print("   • Click 'OK'")
    print("6. Check the 'Internet Sharing' checkbox")
    print("7. Click 'Start' when prompted")
    print("\n✅ Once active, you'll see 'Internet Sharing: On' in the Sharing panel")

def wait_for_hotspot():
    """Wait for the hotspot to become active"""
    print("\n⏳ Waiting for hotspot to become active...")
    
    for i in range(30):  # Wait up to 30 seconds
        if check_internet_sharing_status():
            print("✅ Hotspot is now active!")
            return True
        
        if i % 5 == 0:  # Print status every 5 seconds
            print(f"   Still waiting... ({i}/30 seconds)")
        
        time.sleep(1)
    
    print("⚠️  Hotspot not detected automatically")
    return False

def get_hotspot_ip():
    """Get the IP address assigned to the hotspot interface"""
    try:
        # Common hotspot interfaces on macOS
        interfaces = ['bridge0', 'en0', 'en1']
        
        for interface in interfaces:
            try:
                result = subprocess.run(['ifconfig', interface], 
                                      capture_output=True, text=True, check=True)
                
                # Look for inet address
                import re
                ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                if ip_match:
                    ip = ip_match.group(1)
                    # Check if it's a valid hotspot IP range
                    if ip.startswith(('192.168.2.', '192.168.42.', '10.0.')):
                        return ip
            except:
                continue
                
    except Exception:
        pass
    
    return None

def main():
    print("🎮 Game Hub - Hotspot Setup Helper")
    print("==================================")
    
    # Check if already running
    if check_internet_sharing_status():
        print("✅ Internet Sharing is already active!")
        
        hotspot_ip = get_hotspot_ip()
        if hotspot_ip:
            print(f"🌐 Hotspot IP detected: {hotspot_ip}")
        
        print("\n📱 Your hotspot should be available as:")
        print("   Network Name: GameHub-Direct")
        print("   Password: gamehub123")
        return True
    
    print("📡 Internet Sharing is not currently active")
    print("\n🔧 Setting up hotspot for direct device connections...")
    
    # Try automatic configuration
    if setup_sharing_preferences():
        print("✅ Configuration files updated")
        print("\n🔄 You may need to manually enable Internet Sharing in System Preferences")
    
    # Provide manual instructions
    provide_manual_instructions()
    
    # Wait for user confirmation
    input("\n⏳ Press ENTER after you've enabled Internet Sharing...")
    
    # Wait for hotspot to become active
    if wait_for_hotspot():
        hotspot_ip = get_hotspot_ip()
        if hotspot_ip:
            print(f"🌐 Hotspot IP: {hotspot_ip}")
        
        print("\n🎯 Hotspot setup complete!")
        print("📱 Devices can now connect to: GameHub-Direct")
        return True
    else:
        print("\n⚠️  Could not detect active hotspot")
        print("   Please verify the setup in System Preferences → Sharing")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 