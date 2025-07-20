from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib import messages
from django.conf import settings
from .models import GameContent, ConnectedDevice, GameSession
import qrcode
import io
import base64
import socket
import uuid
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import platform
import subprocess
import re
import os


def get_device_hotspot_settings():
    """Get actual device hotspot settings (SSID and password)"""
    system = platform.system().lower()
    
    hotspot_ssid = None
    hotspot_password = None
    source = None
    
    if system == "linux":
        # Check if it's Raspberry Pi
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'raspberry pi' in cpuinfo.lower() or 'bcm2' in cpuinfo.lower():
                    # Raspberry Pi - check hostapd config
                    if os.path.exists("/etc/hostapd/hostapd.conf"):
                        try:
                            with open("/etc/hostapd/hostapd.conf", 'r') as f:
                                config = f.read()
                                for line in config.split('\n'):
                                    if line.startswith('ssid='):
                                        hotspot_ssid = line.split('=', 1)[1].strip()
                                    elif line.startswith('wpa_passphrase='):
                                        hotspot_password = line.split('=', 1)[1].strip()
                                if hotspot_ssid and hotspot_password:
                                    source = "hostapd config"
                                    return hotspot_ssid, hotspot_password, source
                        except:
                            pass
        except:
            pass
        
        # Check NetworkManager for Linux
        try:
            result = subprocess.run(['nmcli', '-t', '-f', 'NAME,TYPE', 'con', 'show'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '802-11-wireless' in line:
                        connection_name = line.split(':')[0]
                        # Get SSID
                        ssid_result = subprocess.run(['nmcli', '-t', '-f', '802-11-wireless.ssid', 'con', 'show', connection_name], 
                                                   capture_output=True, text=True, timeout=5)
                        if ssid_result.returncode == 0:
                            hotspot_ssid = ssid_result.stdout.strip().split(':')[-1]
                        
                        # Get password
                        pwd_result = subprocess.run(['nmcli', '-s', '-t', '-f', '802-11-wireless-security.psk', 'con', 'show', connection_name], 
                                                  capture_output=True, text=True, timeout=5)
                        if pwd_result.returncode == 0:
                            hotspot_password = pwd_result.stdout.strip().split(':')[-1]
                        
                        if hotspot_ssid and hotspot_password:
                            source = "NetworkManager"
                            return hotspot_ssid, hotspot_password, source
                        break
        except:
            pass
        
        # Fallback to hostname
        try:
            result = subprocess.run(['hostname'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                hotspot_ssid = result.stdout.strip()
                hotspot_password = "raspberry"  # Common default
                source = "hostname + default"
                return hotspot_ssid, hotspot_password, source
        except:
            pass
    
    elif system == "darwin":
        # macOS - get computer name
        try:
            result = subprocess.run(['scutil', '--get', 'ComputerName'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                hotspot_ssid = result.stdout.strip()
                
                # Method 1: Try to get Internet Sharing password from keychain
                try:
                    # Look for Internet Sharing passwords
                    keychain_queries = [
                        ['security', 'find-generic-password', '-w', '-s', 'AirPort network password'],
                        ['security', 'find-generic-password', '-w', '-s', 'Internet Sharing'],
                        ['security', 'find-generic-password', '-w', '-a', 'AirPort'],
                        ['security', 'find-internet-password', '-w', '-s', hotspot_ssid]
                    ]
                    
                    for query in keychain_queries:
                        try:
                            pwd_result = subprocess.run(query, capture_output=True, text=True, timeout=5)
                            if pwd_result.returncode == 0 and pwd_result.stdout.strip():
                                hotspot_password = pwd_result.stdout.strip()
                                if len(hotspot_password) >= 8:  # Valid WiFi password length
                                    source = "macOS keychain"
                                    return hotspot_ssid, hotspot_password, source
                        except:
                            continue
                except:
                    pass
                
                # Method 2: Try to read from system configuration
                try:
                    # Check Internet Sharing plist
                    plist_paths = [
                        '/Library/Preferences/SystemConfiguration/com.apple.nat.plist',
                        '/Library/Preferences/SystemConfiguration/preferences.plist'
                    ]
                    
                    for plist_path in plist_paths:
                        if os.path.exists(plist_path):
                            try:
                                result = subprocess.run(['plutil', '-extract', 'SharingNetworkPassword', 'raw', plist_path], 
                                                      capture_output=True, text=True, timeout=5)
                                if result.returncode == 0 and result.stdout.strip():
                                    hotspot_password = result.stdout.strip()
                                    source = "macOS system preferences"
                                    return hotspot_ssid, hotspot_password, source
                            except:
                                continue
                except:
                    pass
                
                # Method 3: Check if user has Internet Sharing enabled and try to extract password
                try:
                    sharing_result = subprocess.run(['sudo', '-n', 'cat', '/Library/Preferences/SystemConfiguration/com.apple.nat.plist'], 
                                                  capture_output=True, text=True, timeout=5)
                    if sharing_result.returncode == 0:
                        # Try to extract password from the plist output
                        import re
                        password_match = re.search(r'<key>SharingNetworkPassword</key>\s*<string>(.*?)</string>', sharing_result.stdout)
                        if password_match:
                            hotspot_password = password_match.group(1)
                            source = "macOS Internet Sharing config"
                            return hotspot_ssid, hotspot_password, source
                except:
                    pass
                
                # If we found SSID but no password, return with None password to trigger user prompt
                source = "device name (password needed)"
                return hotspot_ssid, None, source
        except:
            pass
    
    elif system == "windows":
        # Windows - get computer name
        try:
            result = subprocess.run(['hostname'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                hotspot_ssid = result.stdout.strip()
                
                # Method 1: Try to get Mobile Hotspot password from various profiles
                try:
                    # Common Mobile Hotspot profile names
                    profile_names = [
                        "Local Area Connection* 12",
                        "Local Area Connection* 2", 
                        "Local Area Connection* 3",
                        "Microsoft Wi-Fi Direct Virtual Adapter",
                        hotspot_ssid
                    ]
                    
                    for profile_name in profile_names:
                        try:
                            hotspot_result = subprocess.run(['netsh.exe', 'wlan', 'show', 'profile', f'name={profile_name}', 'key=clear'], 
                                                          capture_output=True, text=True, timeout=5)
                            if hotspot_result.returncode == 0:
                                for line in hotspot_result.stdout.split('\n'):
                                    if 'Key Content' in line or 'Network key' in line:
                                        password_part = line.split(':')[-1].strip()
                                        if password_part and len(password_part) >= 8:
                                            hotspot_password = password_part
                                            source = "Windows Mobile Hotspot profile"
                                            return hotspot_ssid, hotspot_password, source
                        except:
                            continue
                except:
                    pass
                
                # Method 2: Try to get from registry (requires admin)
                try:
                    reg_result = subprocess.run(['reg', 'query', 'HKLM\\SOFTWARE\\Microsoft\\WlanSvc\\AnqpCache'], 
                                              capture_output=True, text=True, timeout=5)
                    # This would need more complex parsing, skipping for now
                except:
                    pass
                
                # Method 3: Try PowerShell to get hotspot info
                try:
                    ps_cmd = 'Get-NetConnectionProfile | Where-Object {$_.NetworkCategory -eq "Public"} | Select-Object Name'
                    ps_result = subprocess.run(['powershell.exe', '-Command', ps_cmd], 
                                             capture_output=True, text=True, timeout=5)
                    # This would give us network info but not password
                except:
                    pass
                
                # If we found SSID but no password, return with None password to trigger user prompt
                source = "computer name (password needed)"
                return hotspot_ssid, None, source
        except:
            pass
    
    # Ultimate fallback
    try:
        import socket
        hotspot_ssid = socket.gethostname()
        hotspot_password = "gamehub123"
        source = "hostname fallback"
        return hotspot_ssid, hotspot_password, source
    except:
        pass
    
    # Final fallback to original defaults
    return "GameHub-Direct", "gamehub123", "default"


def get_local_ip():
    """Get the local IP address - works across all operating systems"""
    
    # Detect operating system
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Check if it's Raspberry Pi
    is_raspberry_pi = False
    if system == "linux":
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'raspberry pi' in cpuinfo.lower() or 'bcm2' in cpuinfo.lower():
                    is_raspberry_pi = True
        except:
            pass
    
    # Method 1: OS-specific IP detection
    try:
        found_ips = []
        
        if system == "linux":
            # Linux/Raspberry Pi - use ip command
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'inet ' in line:
                        ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match:
                            ip = ip_match.group(1)
                            if not ip.startswith('127.') and not ip.startswith('169.254.'):
                                found_ips.append(ip)
        
        elif system == "darwin":
            # macOS - use ifconfig
            result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'inet ' in line:
                        ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match:
                            ip = ip_match.group(1)
                            if not ip.startswith('127.') and not ip.startswith('169.254.'):
                                found_ips.append(ip)
        
        elif system == "windows":
            # Windows - use ipconfig
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=3, shell=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'IPv4' in line:
                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match:
                            ip = ip_match.group(1)
                            if not ip.startswith('127.') and not ip.startswith('169.254.'):
                                found_ips.append(ip)
        
        # Prioritize IPs based on OS and setup
        if found_ips:
            if is_raspberry_pi:
                # Raspberry Pi - prioritize hotspot IPs
                hotspot_prefixes = ['192.168.4.', '192.168.2.', '192.168.42.', '10.0.']
            elif system == "darwin":
                # macOS - prioritize Internet Sharing IPs
                hotspot_prefixes = ['192.168.2.', '192.168.42.', '10.0.', '192.168.4.']
            elif system == "windows":
                # Windows - prioritize Mobile Hotspot IPs
                hotspot_prefixes = ['192.168.137.', '192.168.2.', '192.168.4.', '10.0.']
            else:
                # Generic Linux
                hotspot_prefixes = ['192.168.4.', '192.168.2.', '192.168.42.', '10.0.']
            
            # First try to find hotspot IPs
            for ip in found_ips:
                for prefix in hotspot_prefixes:
                    if ip.startswith(prefix):
                        return ip
            
            # If no hotspot IP, return first available IP
            return found_ips[0]
                
    except Exception:
        pass
    
    # Method 2: Cross-platform fallback using ifconfig
    try:
        result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            found_ips = []
            for line in result.stdout.split('\n'):
                if 'inet ' in line:
                    ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        ip = ip_match.group(1)
                        if not ip.startswith('127.') and not ip.startswith('169.254.'):
                            found_ips.append(ip)
            
            if found_ips:
                return found_ips[0]
    except Exception:
        pass
    
    # Method 3: Use hostname command (Linux/macOS)
    try:
        if system in ["linux", "darwin"]:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                for ip in ips:
                    if not ip.startswith('127.') and not ip.startswith('169.254.'):
                        return ip
    except Exception:
        pass
    
    # Method 4: Socket method (offline-friendly)
    try:
        # Try to connect to a local network IP to get our interface IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        # Use a local network IP instead of internet IP
        s.connect(("192.168.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith('127.'):
            return ip
    except Exception:
        pass
    
    # Method 5: Alternative local network socket test
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("10.0.0.1", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith('127.'):
            return ip
    except Exception:
        pass
    
    # Method 6: OS-specific default fallback
    if is_raspberry_pi:
        return "192.168.4.1"  # Raspberry Pi hotspot default
    elif system == "darwin":
        return "192.168.2.1"  # macOS Internet Sharing default
    elif system == "windows":
        return "192.168.137.1"  # Windows Mobile Hotspot default
    else:
        return "192.168.4.1"  # Generic Linux default


def generate_wifi_qr_code(ssid, password, url, size=10):
    """Generate WiFi QR code that auto-connects to hotspot and shows URL"""
    # WiFi QR code format: WIFI:T:WPA;S:network_name;P:password;H:false;;
    # We'll embed the URL in a way that shows it after connection
    wifi_data = f"WIFI:T:WPA;S:{ssid};P:{password};H:false;;"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )
    qr.add_data(wifi_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def generate_qr_code(data, size=10):
    """Generate regular QR code as base64 image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def get_device_id(request):
    """Get or create device ID for tracking"""
    device_id = request.session.get('device_id')
    if not device_id:
        device_id = str(uuid.uuid4())
        request.session['device_id'] = device_id
    return device_id


class PiDisplayView(TemplateView):
    """Main display view for the Raspberry Pi monitor"""
    template_name = 'gamehub/pi_display.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current IP and URLs
        current_ip = get_local_ip()
        mobile_url = f"http://{current_ip}:8000/mobile/"
        
        # Get actual device hotspot credentials
        hotspot_name, hotspot_password, hotspot_source = get_device_hotspot_settings()
        
        # Handle missing password
        password_warning = None
        if hotspot_password is None:
            password_warning = "⚠️ Could not detect hotspot password. Please check your system settings."
            hotspot_password = "❌ PASSWORD NEEDED"
            wifi_qr_code = None  # Don't generate QR code with wrong password
        else:
            # Generate WiFi QR code for auto-connection
            wifi_qr_code = generate_wifi_qr_code(hotspot_name, hotspot_password, mobile_url)
        
        # Generate regular URL QR code as backup
        url_qr_code = generate_qr_code(mobile_url)
        
        # Get active content
        active_content = GameContent.objects.filter(is_active=True).first()
        
        # Get device stats
        total_devices = ConnectedDevice.objects.count()
        active_devices = ConnectedDevice.objects.filter(is_active=True).count()
        
        context.update({
            'current_ip': current_ip,
            'mobile_url': mobile_url,
            'hotspot_name': hotspot_name,
            'hotspot_password': hotspot_password,
            'hotspot_source': hotspot_source,
            'password_warning': password_warning,
            'wifi_qr_code': wifi_qr_code,
            'url_qr_code': url_qr_code,
            'active_content': active_content,
            'total_devices': total_devices,
            'active_devices': active_devices,
        })
        
        return context


class MobileDisplayView(TemplateView):
    """Mobile browser display view"""
    template_name = 'gamehub/mobile_display.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the current active content
        active_content = GameContent.objects.filter(is_active=True).first()
        
        # Track this device
        session_id = self.request.session.session_key
        if not session_id:
            self.request.session.create()
            session_id = self.request.session.session_key
        
        # Get client IP
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        
        # Update or create device record
        device, created = ConnectedDevice.objects.get_or_create(
            session_id=session_id,
            defaults={
                'ip_address': ip,
                'user_agent': self.request.META.get('HTTP_USER_AGENT', ''),
                'is_active': True
            }
        )
        
        if not created:
            device.is_active = True
            device.save()
        
        # Update QR scan count if this is a new device
        if created:
            active_session = GameSession.objects.filter(is_active=True).first()
            if active_session:
                active_session.qr_code_scans += 1
                active_session.save()
        
        context.update({
            'active_content': active_content,
            'device': device,
        })
        
        return context


class ContentManagementView(TemplateView):
    """Content management interface"""
    template_name = 'gamehub/content_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'contents': GameContent.objects.all(),
            'active_content': GameContent.objects.filter(is_active=True).first(),
        })
        return context


@csrf_exempt
def api_update_content(request):
    """API endpoint to update content"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content_id = data.get('content_id')
            
            if content_id:
                content = get_object_or_404(GameContent, id=content_id)
                content.is_active = True
                content.save()
                
                # Notify all connected clients via WebSocket
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'content_updates',
                    {
                        'type': 'content_update',
                        'content': {
                            'id': str(content.id),
                            'title': content.title,
                            'content_type': content.content_type,
                            'text_content': content.text_content,
                            'image_url': content.image.url if content.image else None,
                            'background_color': content.background_color,
                            'text_color': content.text_color,
                            'font_size': content.font_size,
                        }
                    }
                )
                
                return JsonResponse({'success': True, 'message': 'Content updated'})
            else:
                return JsonResponse({'success': False, 'message': 'Content ID required'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'POST required'})


@csrf_exempt
def api_create_content(request):
    """API endpoint to create new content"""
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            content_type = request.POST.get('content_type', 'text')
            text_content = request.POST.get('text_content', '')
            background_color = request.POST.get('background_color', '#ffffff')
            text_color = request.POST.get('text_color', '#000000')
            font_size = int(request.POST.get('font_size', 24))
            image = request.FILES.get('image')
            
            content = GameContent.objects.create(
                title=title,
                content_type=content_type,
                text_content=text_content,
                background_color=background_color,
                text_color=text_color,
                font_size=font_size,
                image=image
            )
            
            return JsonResponse({
                'success': True, 
                'message': 'Content created',
                'content_id': str(content.id)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'POST required'})


def api_get_active_content(request):
    """API endpoint to get current active content"""
    active_content = GameContent.objects.filter(is_active=True).first()
    
    if active_content:
        return JsonResponse({
            'success': True,
            'content': {
                'id': str(active_content.id),
                'title': active_content.title,
                'content_type': active_content.content_type,
                'text_content': active_content.text_content,
                'image_url': active_content.image.url if active_content.image else None,
                'background_color': active_content.background_color,
                'text_color': active_content.text_color,
                'font_size': active_content.font_size,
            }
        })
    else:
        return JsonResponse({'success': False, 'message': 'No active content'})


def api_device_stats(request):
    """API endpoint to get device statistics"""
    total_devices = ConnectedDevice.objects.count()
    active_devices = ConnectedDevice.objects.filter(is_active=True).count()
    
    return JsonResponse({
        'total_devices': total_devices,
        'active_devices': active_devices,
        'server_ip': get_local_ip(),
        'hotspot_name': 'GameHub-Direct',
    })
