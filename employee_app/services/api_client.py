"""
REST API client for the Employee Application.
Handles all HTTP communication with the backend.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import requests

from employee_app.config import API_BASE_URL, API_KEY

logger = logging.getLogger(__name__)

# Default timeout for API requests (seconds)
REQUEST_TIMEOUT = 15


class APIClient:
    """HTTP client for communicating with the Attendance REST API."""

    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = (base_url or API_BASE_URL).rstrip("/")
        self.api_key = api_key or API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        })

    def _url(self, path: str) -> str:
        """Build full URL."""
        return f"{self.base_url}{path}"

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse response and raise on errors."""
        try:
            data = response.json()
        except ValueError:
            data = {"detail": response.text}

        if response.status_code >= 400:
            detail = data.get("detail", "Unknown error")
            logger.error(f"API error {response.status_code}: {detail}")
            raise APIError(response.status_code, detail)

        return data

    # ─────────────────── Health ───────────────────

    def check_health(self) -> bool:
        """Check if the API server is reachable."""
        try:
            response = self.session.get(
                self._url("/health"), timeout=5
            )
            return response.status_code == 200
        except requests.ConnectionError:
            return False
        except Exception:
            return False

    # ─────────────────── Device ───────────────────

    def lookup_device(self, fingerprint: str) -> Dict[str, Any]:
        """Check if this device is registered. Returns device/employee info."""
        response = self.session.get(
            self._url(f"/api/devices/lookup/{fingerprint}"),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(response)

    def request_registration(
        self,
        fingerprint: str,
        hostname: Optional[str] = None,
        machine_guid: Optional[str] = None,
        system_username: Optional[str] = None,
        system_details: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Request device registration (first-time setup)."""
        payload = {
            "fingerprint": fingerprint,
            "hostname": hostname,
            "machine_guid": machine_guid,
            "system_username": system_username,
            "system_details": system_details,
        }
        response = self.session.post(
            self._url("/api/devices/request-registration"),
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(response)

    # ─────────────────── Attendance ───────────────────

    def punch_in(self, data: Dict[str, Any], timeout: float = REQUEST_TIMEOUT) -> Dict[str, Any]:
        """Record punch-in."""
        response = self.session.post(
            self._url("/api/attendance/punch-in"),
            json=data,
            timeout=timeout,
        )
        return self._handle_response(response)

    def punch_out(self, data: Dict[str, Any], timeout: float = REQUEST_TIMEOUT) -> Dict[str, Any]:
        """Record punch-out."""
        response = self.session.post(
            self._url("/api/attendance/punch-out"),
            json=data,
            timeout=timeout,
        )
        return self._handle_response(response)

    def get_attendance_status(self, fingerprint: str) -> Dict[str, Any]:
        """Get today's attendance status."""
        response = self.session.get(
            self._url(f"/api/attendance/status/{fingerprint}"),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(response)

    def sync_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync offline attendance records."""
        response = self.session.post(
            self._url("/api/attendance/sync"),
            json={"records": records},
            timeout=30,  # Longer timeout for bulk sync
        )
        return self._handle_response(response)

    # ─────────────────── Settings ───────────────────

    def get_wifi_settings(self) -> Dict[str, Any]:
        """Get office WiFi validation settings."""
        response = self.session.get(
            self._url("/api/settings/wifi"),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(response)


class APIError(Exception):
    """Exception raised for API errors."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")
