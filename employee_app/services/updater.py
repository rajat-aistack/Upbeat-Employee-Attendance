"""
Auto-updater service.
Checks GitHub Releases for new versions and prompts user to update.
"""
import logging
import os
import sys
import subprocess
import tempfile
from typing import Optional, Tuple

import requests

from employee_app.config import APP_VERSION, GITHUB_REPO

logger = logging.getLogger(__name__)


def check_for_update() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check GitHub Releases for a newer version.
    
    Returns:
        (update_available, latest_version, download_url)
    """
    if not GITHUB_REPO:
        return False, None, None

    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return False, None, None

        data = response.json()
        latest_version = data.get("tag_name", "").lstrip("v")

        if not latest_version:
            return False, None, None

        # Simple version comparison
        if _compare_versions(latest_version, APP_VERSION) > 0:
            # Find .exe asset
            download_url = None
            for asset in data.get("assets", []):
                if asset["name"].endswith(".exe"):
                    download_url = asset["browser_download_url"]
                    break

            return True, latest_version, download_url

        return False, latest_version, None

    except Exception as e:
        logger.warning(f"Update check failed: {e}")
        return False, None, None


def _compare_versions(v1: str, v2: str) -> int:
    """Compare two version strings. Returns positive if v1 > v2."""
    try:
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]

        # Pad with zeros
        max_len = max(len(parts1), len(parts2))
        parts1.extend([0] * (max_len - len(parts1)))
        parts2.extend([0] * (max_len - len(parts2)))

        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return 0
    except ValueError:
        return 0


def download_update(download_url: str, progress_callback=None) -> Optional[str]:
    """
    Download the update file.
    
    Returns path to downloaded file, or None on failure.
    """
    try:
        response = requests.get(download_url, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        # Save to temp file
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "Attendance_Update.exe")

        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total_size > 0:
                    progress_callback(downloaded / total_size)

        logger.info(f"Update downloaded to {temp_path}")
        return temp_path

    except Exception as e:
        logger.error(f"Download failed: {e}")
        return None


def apply_update(downloaded_path: str):
    """Replace current executable with the downloaded update."""
    if not getattr(sys, 'frozen', False):
        logger.info("Not running as frozen executable, skipping update")
        return

    current_exe = sys.executable

    # Create a batch script to replace the exe after it closes
    batch_content = f"""@echo off
timeout /t 2 /nobreak >nul
copy /y "{downloaded_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
    batch_path = os.path.join(os.path.dirname(current_exe), "_update.bat")

    with open(batch_path, "w") as f:
        f.write(batch_content)

    # Run the batch script and exit
    subprocess.Popen(
        ["cmd", "/c", batch_path],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    sys.exit(0)
