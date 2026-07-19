"""
REST API client for the Admin Application.
Includes JWT authentication for admin endpoints.
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import date

import requests

from admin_app.config import API_BASE_URL, API_KEY, TOKEN_FILE

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15


class AdminAPIClient:
    """HTTP client for admin operations with JWT auth."""

    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = (base_url or API_BASE_URL).rstrip("/")
        self.api_key = api_key or API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        })
        self._token: Optional[str] = None
        self._username: Optional[str] = None
        self._load_saved_token()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            data = {"detail": response.text}
        if response.status_code >= 400:
            detail = data.get("detail", "Unknown error")
            raise APIError(response.status_code, detail)
        return data

    def _auth_headers(self) -> dict:
        """Get authorization headers."""
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _save_token(self):
        """Persist token to file."""
        try:
            TOKEN_FILE.write_text(json.dumps({
                "token": self._token,
                "username": self._username,
            }))
        except Exception as e:
            logger.warning(f"Could not save token: {e}")

    def _load_saved_token(self):
        """Load saved token from file."""
        try:
            if TOKEN_FILE.exists():
                data = json.loads(TOKEN_FILE.read_text())
                self._token = data.get("token")
                self._username = data.get("username")
        except Exception as e:
            logger.warning(f"Could not load saved token: {e}")

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    @property
    def username(self) -> Optional[str]:
        return self._username

    # ─────────────── Auth ───────────────

    def login(self, username: str, password: str) -> Dict[str, Any]:
        response = self.session.post(
            self._url("/api/auth/login"),
            json={"username": username, "password": password},
            timeout=REQUEST_TIMEOUT,
        )
        data = self._handle_response(response)
        self._token = data.get("access_token")
        self._username = data.get("username")
        self._save_token()
        return data

    def logout(self):
        self._token = None
        self._username = None
        try:
            TOKEN_FILE.unlink(missing_ok=True)
        except Exception:
            pass

    def check_health(self) -> bool:
        try:
            r = self.session.get(self._url("/health"), timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    # ─────────────── Dashboard ───────────────

    def get_dashboard_stats(self) -> Dict[str, Any]:
        r = self.session.get(
            self._url("/api/dashboard/stats"),
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    # ─────────────── Employees ───────────────

    def list_employees(self, search=None, department=None, status=None, skip=0, limit=100) -> Dict:
        params = {"skip": skip, "limit": limit}
        if search: params["search"] = search
        if department: params["department"] = department
        if status: params["status"] = status
        r = self.session.get(
            self._url("/api/employees"),
            params=params,
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    def get_employee(self, employee_id: int) -> Dict:
        r = self.session.get(
            self._url(f"/api/employees/{employee_id}"),
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    def create_employee(self, data: dict) -> Dict:
        r = self.session.post(
            self._url("/api/employees"),
            json=data,
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    def update_employee(self, employee_id: int, data: dict) -> Dict:
        r = self.session.put(
            self._url(f"/api/employees/{employee_id}"),
            json=data,
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    def update_employee_status(self, employee_id: int, status: str) -> Dict:
        r = self.session.patch(
            self._url(f"/api/employees/{employee_id}/status"),
            json={"status": status},
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    def delete_employee(self, employee_id: int) -> Dict:
        r = self.session.delete(
            self._url(f"/api/employees/{employee_id}"),
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    def list_departments(self) -> List[str]:
        r = self.session.get(
            self._url("/api/employees/departments"),
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    # ─────────────── Devices ───────────────

    def list_devices(self, status=None) -> Dict:
        params = {}
        if status: params["status"] = status
        r = self.session.get(
            self._url("/api/devices"),
            params=params,
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    def list_pending_devices(self) -> Dict:
        r = self.session.get(
            self._url("/api/devices/pending"),
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    def register_device(self, registration_code: str, employee_id: int) -> Dict:
        r = self.session.post(
            self._url("/api/devices/register"),
            json={"registration_code": registration_code, "employee_id": employee_id},
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    def replace_device(self, device_id: int, new_code: str, employee_id: int) -> Dict:
        r = self.session.put(
            self._url(f"/api/devices/{device_id}/replace"),
            json={"new_registration_code": new_code, "employee_id": employee_id},
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    def update_device_status(self, device_id: int, status: str) -> Dict:
        r = self.session.patch(
            self._url(f"/api/devices/{device_id}/status"),
            json={"status": status},
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    # ─────────────── Reports ───────────────

    def get_attendance_report(self, start_date: str, end_date: str,
                              employee_id=None, department=None, status=None) -> Dict:
        params = {"start_date": start_date, "end_date": end_date}
        if employee_id: params["employee_id"] = employee_id
        if department: params["department"] = department
        if status: params["status"] = status
        r = self.session.get(
            self._url("/api/reports/attendance"),
            params=params,
            headers=self._auth_headers(),
            timeout=30,
        )
        return self._handle_response(r)

    def get_report_summary(self, start_date: str, end_date: str,
                           employee_id=None, department=None) -> Dict:
        params = {"start_date": start_date, "end_date": end_date}
        if employee_id: params["employee_id"] = employee_id
        if department: params["department"] = department
        r = self.session.get(
            self._url("/api/reports/summary"),
            params=params,
            headers=self._auth_headers(),
            timeout=30,
        )
        return self._handle_response(r)

    # ─────────────── Settings ───────────────

    def get_settings(self) -> Dict:
        r = self.session.get(
            self._url("/api/settings"),
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)

    def update_settings(self, data: dict) -> Dict:
        r = self.session.put(
            self._url("/api/settings"),
            json=data,
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        return self._handle_response(r)


class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")
