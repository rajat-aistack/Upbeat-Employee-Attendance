"""
Configuration settings for the Upbeat Attendance API.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'attendance.db'}")

# Security
API_KEY = os.getenv("API_KEY", "upbeat-attendance-api-key-2024-secure")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "upbeat-jwt-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 480  # 8 hours

# Default Admin
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

# Request validation
REQUEST_TIMESTAMP_TOLERANCE_SECONDS = 300  # 5 minutes

# CORS
ALLOWED_ORIGINS = ["*"]

# Application
APP_NAME = "Upbeat Attendance API"
APP_VERSION = "1.0.0"
