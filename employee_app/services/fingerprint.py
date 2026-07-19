"""
Device fingerprint generation using Windows hardware identifiers.
Creates a unique SHA256 hash from multiple hardware signatures.
"""
import hashlib
import logging
import platform
import subprocess
import uuid

logger = logging.getLogger(__name__)


def _run_wmic(wmic_class: str, field: str) -> str:
    """Run a WMIC command and return the result."""
    try:
        result = subprocess.run(
            ["wmic", wmic_class, "get", field],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
        )
        lines = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        if len(lines) > 1:
            return lines[1]  # First line is header, second is value
    except Exception as e:
        logger.warning(f"WMIC query failed for {wmic_class}.{field}: {e}")
    return ""


def _get_machine_guid() -> str:
    """Get Windows Machine GUID from registry."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        )
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return str(value)
    except Exception as e:
        logger.warning(f"Failed to read Machine GUID: {e}")
        return ""


def _get_bios_uuid() -> str:
    """Get BIOS UUID via WMIC."""
    return _run_wmic("csproduct", "UUID")


def _get_cpu_id() -> str:
    """Get CPU Processor ID via WMIC."""
    return _run_wmic("cpu", "ProcessorId")


def _get_motherboard_uuid() -> str:
    """Get Motherboard serial number via WMIC."""
    return _run_wmic("baseboard", "SerialNumber")


def _get_disk_serial() -> str:
    """Get primary disk serial number via WMIC."""
    return _run_wmic("diskdrive", "SerialNumber")


def get_hostname() -> str:
    """Get computer hostname."""
    return platform.node()


def get_system_username() -> str:
    """Get current logged-in system username."""
    import getpass
    return getpass.getuser()


def get_system_details() -> dict:
    """Collect all system details for registration."""
    return {
        "hostname": get_hostname(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "username": get_system_username(),
    }


def generate_fingerprint() -> str:
    """
    Generate a unique SHA256 device fingerprint from multiple hardware identifiers.
    
    Combines:
    - Windows Machine GUID
    - BIOS UUID
    - CPU ID
    - Motherboard UUID
    - Disk Serial
    - Hostname
    
    Returns a 64-character hex SHA256 hash.
    """
    identifiers = []

    # Collect all identifiers
    machine_guid = _get_machine_guid()
    if machine_guid:
        identifiers.append(f"GUID:{machine_guid}")

    bios_uuid = _get_bios_uuid()
    if bios_uuid:
        identifiers.append(f"BIOS:{bios_uuid}")

    cpu_id = _get_cpu_id()
    if cpu_id:
        identifiers.append(f"CPU:{cpu_id}")

    mb_uuid = _get_motherboard_uuid()
    if mb_uuid:
        identifiers.append(f"MB:{mb_uuid}")

    disk_serial = _get_disk_serial()
    if disk_serial:
        identifiers.append(f"DISK:{disk_serial}")

    hostname = get_hostname()
    identifiers.append(f"HOST:{hostname}")

    # Combine and hash
    combined = "|".join(sorted(identifiers))
    fingerprint = hashlib.sha256(combined.encode("utf-8")).hexdigest()

    logger.info(f"Generated fingerprint from {len(identifiers)} identifiers")
    return fingerprint


def get_machine_guid() -> str:
    """Public accessor for Machine GUID."""
    return _get_machine_guid()
