"""
Admin App Configuration.
"""
import os
import sys
from pathlib import Path

# Application
APP_NAME = "Upbeat Attendance Admin"
APP_VERSION = "1.0.0"
COMPANY_NAME = "Upbeat Exposition Company"

# Local storage
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).resolve().parent

# Load or generate config.json next to the executable
import json
APP_CONFIG_FILE = APP_DIR / "config.json"
default_config = {
    "API_BASE_URL": "http://127.0.0.1:8000",
    "API_KEY": "upbeat-attendance-api-key-2024-secure"
}

if APP_CONFIG_FILE.exists():
    try:
        with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        API_BASE_URL = user_config.get("API_BASE_URL", default_config["API_BASE_URL"])
        API_KEY = user_config.get("API_KEY", default_config["API_KEY"])
    except Exception:
        API_BASE_URL = default_config["API_BASE_URL"]
        API_KEY = default_config["API_KEY"]
else:
    try:
        with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
    except Exception:
        pass
    API_BASE_URL = default_config["API_BASE_URL"]
    API_KEY = default_config["API_KEY"]

DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

TOKEN_FILE = DATA_DIR / "auth_token.json"
EXPORTS_DIR = DATA_DIR / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)

# UI
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
SIDEBAR_WIDTH = 220
