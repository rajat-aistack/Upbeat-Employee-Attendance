"""
WiFi and network validation service.
Verifies the employee is connected to the authorized office network.
"""
import logging
import platform
import re
import subprocess
import socket
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NetworkInfo:
    """Current network connection information."""
    wifi_ssid: Optional[str] = None
    wifi_bssid: Optional[str] = None
    gateway_ip: Optional[str] = None
    gateway_mac: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    is_connected: bool = False


def _run_command(cmd: list, timeout: int = 10) -> str:
    """Run a command and return stdout."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
        )
        return result.stdout
    except Exception as e:
        logger.warning(f"Command failed {' '.join(cmd)}: {e}")
        return ""


def get_wifi_info() -> Tuple[Optional[str], Optional[str]]:
    """Get current WiFi SSID and BSSID using netsh on Windows."""
    output = _run_command(["netsh", "wlan", "show", "interfaces"])
    
    ssid = None
    bssid = None
    
    for line in output.split("\n"):
        line = line.strip()
        # Match SSID (but not BSSID)
        if line.startswith("SSID") and "BSSID" not in line:
            match = re.search(r"SSID\s*:\s*(.+)", line)
            if match:
                ssid = match.group(1).strip()
        # Match BSSID
        elif "BSSID" in line:
            match = re.search(r"BSSID\s*:\s*(.+)", line)
            if match:
                bssid = match.group(1).strip().lower()
    
    return ssid, bssid


def get_gateway_info() -> Tuple[Optional[str], Optional[str]]:
    """Get default gateway IP and MAC address."""
    gateway_ip = None
    gateway_mac = None
    
    # Get gateway IP from ipconfig
    output = _run_command(["ipconfig"])
    for line in output.split("\n"):
        if "Default Gateway" in line:
            match = re.search(r":\s*([\d.]+)", line)
            if match:
                ip = match.group(1).strip()
                if ip:
                    gateway_ip = ip
                    break
    
    if not gateway_ip:
        return None, None
    
    # Get gateway MAC from ARP table
    arp_output = _run_command(["arp", "-a"])
    for line in arp_output.split("\n"):
        if gateway_ip in line:
            match = re.search(r"([\da-f]{2}[-:][\da-f]{2}[-:][\da-f]{2}[-:][\da-f]{2}[-:][\da-f]{2}[-:][\da-f]{2})", line, re.IGNORECASE)
            if match:
                gateway_mac = match.group(1).strip().lower().replace("-", ":")
                break
    
    return gateway_ip, gateway_mac


def get_local_ip() -> Optional[str]:
    """Get local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def get_mac_address() -> Optional[str]:
    """Get the MAC address of the primary network interface."""
    try:
        mac = ':'.join(
            f'{(uuid.getnode() >> i) & 0xff:02x}'
            for i in range(0, 48, 8)
        )[::-1]
        # Properly format
        import uuid as uuid_mod
        mac_int = uuid_mod.getnode()
        mac = ':'.join(f'{(mac_int >> (8 * i)) & 0xff:02x}' for i in reversed(range(6)))
        return mac
    except Exception:
        return None


def get_network_info() -> NetworkInfo:
    """Collect all current network information."""
    info = NetworkInfo()
    
    try:
        # WiFi info
        info.wifi_ssid, info.wifi_bssid = get_wifi_info()
        
        # Gateway info
        info.gateway_ip, info.gateway_mac = get_gateway_info()
        
        # Local network info
        info.ip_address = get_local_ip()
        info.mac_address = get_mac_address()
        
        # Determine if connected
        info.is_connected = bool(info.ip_address and (info.gateway_ip or info.wifi_ssid))
        
    except Exception as e:
        logger.error(f"Failed to get network info: {e}")
    
    return info


def check_internet_connectivity() -> bool:
    """Check if internet is available by attempting a socket connection."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except (socket.timeout, OSError):
        return False


def validate_office_network(
    network_info: NetworkInfo,
    required_bssid: Optional[str] = None,
    required_gateway_mac: Optional[str] = None,
    required_ssid: Optional[str] = None,
    required_gateway_ip: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Validate that the current network matches office network configuration.
    
    Primary validation: BSSID + Gateway MAC (most reliable)
    Secondary: SSID + Gateway IP
    
    Returns (is_valid, message).
    """
    if not network_info.is_connected:
        return False, "No network connection detected"
    
    # If no office WiFi is configured, allow all networks
    if not required_bssid and not required_gateway_mac and not required_ssid:
        return True, "Office network not configured — allowing all connections"
    
    # Check if we are on a wired LAN interface matching office configuration
    is_wired_lan = bool(network_info.ip_address and not network_info.wifi_bssid)
    
    # Gateway MAC check variables
    matches_mac = False
    if required_gateway_mac and network_info.gateway_mac:
        matches_mac = (network_info.gateway_mac.lower() == required_gateway_mac.lower())
        
    # Gateway IP check variables
    matches_ip = False
    if required_gateway_ip and network_info.gateway_ip:
        matches_ip = (network_info.gateway_ip == required_gateway_ip)
        
    on_office_lan = is_wired_lan and (matches_mac or matches_ip)
    
    validation_passed = True
    failures = []
    
    # Primary: BSSID check (most reliable)
    if required_bssid:
        if on_office_lan:
            # Bypass WiFi BSSID check since they are verified on the office LAN
            pass
        elif not network_info.wifi_bssid:
            failures.append("WiFi not connected (required for office verification)")
            validation_passed = False
        elif network_info.wifi_bssid.lower() != required_bssid.lower():
            failures.append("Connected to unauthorized WiFi network")
            validation_passed = False
    
    # Primary: Gateway MAC check
    if required_gateway_mac and not on_office_lan:
        if not network_info.gateway_mac:
            failures.append("Cannot determine gateway")
            validation_passed = False
        elif not matches_mac:
            failures.append("Gateway does not match office network")
            validation_passed = False
    
    # Secondary: SSID check
    if required_ssid and validation_passed and not on_office_lan:
        if network_info.wifi_ssid and network_info.wifi_ssid != required_ssid:
            failures.append("WiFi network name does not match")
            validation_passed = False
    
    # Secondary: Gateway IP check
    if required_gateway_ip and validation_passed and not on_office_lan:
        if network_info.gateway_ip and not matches_ip:
            failures.append("Gateway IP does not match office network")
            validation_passed = False
    
    if validation_passed:
        if on_office_lan:
            return True, "Connected to authorized office network (LAN)"
        return True, "Connected to authorized office network"
    else:
        return False, "; ".join(failures)


# Fix the import issue in get_mac_address
import uuid as _uuid_mod
def get_mac_address() -> Optional[str]:
    """Get the MAC address of the primary network interface."""
    try:
        mac_int = _uuid_mod.getnode()
        mac = ':'.join(f'{(mac_int >> (8 * i)) & 0xff:02x}' for i in reversed(range(6)))
        return mac
    except Exception:
        return None
