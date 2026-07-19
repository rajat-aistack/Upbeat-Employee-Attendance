"""
Employee App Configuration.
"""
import os
import sys
from pathlib import Path

# Application
APP_NAME = "Upbeat Attendance"
APP_VERSION = "1.0.0"
COMPANY_NAME = "Upbeat Exposition Company"

# Local storage
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).resolve().parent

# Load or generate config.json next to the executable
import json
APP_CONFIG_FILE = APP_DIR / "config.json"
default_config = {
    "API_BASE_URL": "http://127.0.0.1:8000",
    "API_KEY": "upbeat-attendance-api-key-2024-secure",
    "GITHUB_REPO": ""
}

if APP_CONFIG_FILE.exists():
    try:
        with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        API_BASE_URL = user_config.get("API_BASE_URL", default_config["API_BASE_URL"])
        API_KEY = user_config.get("API_KEY", default_config["API_KEY"])
        GITHUB_REPO = user_config.get("GITHUB_REPO", default_config["GITHUB_REPO"])
    except Exception:
        API_BASE_URL = default_config["API_BASE_URL"]
        API_KEY = default_config["API_KEY"]
        GITHUB_REPO = default_config["GITHUB_REPO"]
else:
    try:
        with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
    except Exception:
        pass
    API_BASE_URL = default_config["API_BASE_URL"]
    API_KEY = default_config["API_KEY"]
    GITHUB_REPO = default_config["GITHUB_REPO"]

DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

LOCAL_DB_PATH = DATA_DIR / "offline_attendance.db"
CONFIG_FILE = DATA_DIR / "device_config.json"
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Sync
SYNC_INTERVAL_SECONDS = 300  # 5 minutes default, overridden by server settings

# Auto-update
CHECK_UPDATE_INTERVAL_HOURS = 6

# UI
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 680
