"""
Main application window for the Employee Attendance App.
Orchestrates views, services, and background tasks.
"""
import customtkinter as ctk
import logging
import threading
from datetime import datetime
from typing import Optional

from employee_app.config import APP_NAME, APP_VERSION, COMPANY_NAME, WINDOW_WIDTH, WINDOW_HEIGHT
from employee_app.ui.themes import COLORS, FONTS
from employee_app.ui.attendance_view import AttendanceView
from employee_app.ui.registration_view import RegistrationView
from employee_app.ui.components import show_toast, LoadingSpinner
from employee_app.services.api_client import APIClient, APIError
from employee_app.services.fingerprint import generate_fingerprint, get_hostname, get_system_username, get_system_details, get_machine_guid
from employee_app.services.wifi_validator import get_network_info, validate_office_network, check_internet_connectivity
from employee_app.services.offline_store import OfflineStore
from employee_app.services.sync_manager import SyncManager

logger = logging.getLogger(__name__)


class AttendanceApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title(f"{APP_NAME} — {COMPANY_NAME}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(460, 600)
        self.resizable(True, True)

        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (WINDOW_WIDTH // 2)
        y = (self.winfo_screenheight() // 2) - (WINDOW_HEIGHT // 2)
        self.geometry(f"+{x}+{y}")

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Services
        self.api_client = APIClient()
        self.offline_store = OfflineStore()
        self.sync_manager = SyncManager(self.api_client, self.offline_store)
        self.sync_manager.set_sync_callback(self._on_sync_complete)

        # State
        self.fingerprint: Optional[str] = None
        self.employee_name: Optional[str] = None
        self.employee_db_id: Optional[int] = None
        self.wifi_settings: Optional[dict] = None
        self.current_view: Optional[ctk.CTkFrame] = None

        # WiFi check timer
        self._wifi_check_interval = 30000  # 30 seconds

        # Show loading, then initialize
        self._show_loading()
        self.after(500, self._initialize)

    def _show_loading(self, text="Connecting to server..."):
        """Show loading screen while initializing."""
        self._clear_view()

        loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        loading_frame.pack(fill="both", expand=True)

        # Center content
        center = ctk.CTkFrame(loading_frame, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            center,
            text="⚡",
            font=("Segoe UI", 48),
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            center,
            text=COMPANY_NAME,
            font=FONTS["heading_lg"],
            text_color=COLORS["primary_light"],
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            center,
            text=APP_NAME,
            font=FONTS["body"],
            text_color=("#94A3B8", "#64748B"),
        ).pack(pady=(0, 20))

        self.loading_spinner = LoadingSpinner(center, text=text)
        self.loading_spinner.pack()

        self.current_view = loading_frame

    def _initialize(self):
        """Initialize the app in a background thread."""
        thread = threading.Thread(target=self._do_initialize, daemon=True)
        thread.start()

    def _do_initialize(self):
        """Background initialization logic."""
        try:
            # Generate fingerprint
            logger.info("Generating device fingerprint...")
            self.fingerprint = generate_fingerprint()
            logger.info(f"Fingerprint: {self.fingerprint[:16]}...")

            # Try to fetch WiFi settings
            try:
                self.wifi_settings = self.api_client.get_wifi_settings()
                logger.info("WiFi settings loaded from server")
            except Exception as e:
                logger.warning(f"Could not fetch WiFi settings: {e}")
                self.wifi_settings = None

            # Check device registration
            try:
                device_info = self.api_client.lookup_device(self.fingerprint)
                logger.info(f"Device lookup result: {device_info}")

                if device_info.get("registered") and device_info.get("employee_status") == "active":
                    # Device is registered and employee is active
                    self.employee_name = device_info.get("employee_name", "Employee")
                    self.employee_db_id = device_info.get("employee_db_id")
                    self.after(0, self._show_attendance_view)
                else:
                    # Not registered — request registration
                    self._request_registration()

            except APIError as e:
                logger.error(f"API error during lookup: {e}")
                self._request_registration()

            except Exception as e:
                logger.error(f"Connection error: {e}")
                # Show offline message
                self.after(0, lambda: self._show_error(
                    "Cannot connect to server",
                    "Please check your internet connection and try again.",
                ))

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            self.after(0, lambda: self._show_error(
                "Initialization Error",
                str(e),
            ))

    def _request_registration(self):
        """Request device registration from the API."""
        try:
            hostname = get_hostname()
            machine_guid = get_machine_guid()
            system_username = get_system_username()
            system_details = get_system_details()

            result = self.api_client.request_registration(
                fingerprint=self.fingerprint,
                hostname=hostname,
                machine_guid=machine_guid,
                system_username=system_username,
                system_details=system_details,
            )

            code = result.get("registration_code", "---")
            message = result.get("message", "")

            self.after(0, lambda: self._show_registration_view(
                code, hostname, system_username, message
            ))

        except Exception as e:
            logger.error(f"Registration request failed: {e}")
            self.after(0, lambda: self._show_error(
                "Connection Error",
                "Could not connect to the server to register this device.",
            ))

    def _show_registration_view(self, code: str, hostname: str, device_name: str, message: str):
        """Show the registration screen."""
        self._clear_view()

        view = RegistrationView(
            self,
            registration_code=code,
            hostname=hostname,
            device_name=device_name,
            message=message,
            on_retry=self._retry_registration,
        )
        view.pack(fill="both", expand=True)
        self.current_view = view

    def _show_attendance_view(self):
        """Show the main attendance screen."""
        self._clear_view()

        view = AttendanceView(
            self,
            employee_name=self.employee_name,
            on_punch_in=self._do_punch_in,
            on_punch_out=self._do_punch_out,
        )
        view.pack(fill="both", expand=True)
        self.current_view = view

        # Load today's status
        self.after(300, self._load_today_status)

        # Start WiFi monitoring
        self.after(1000, self._check_wifi)

        # Start sync manager
        self.sync_manager.start()

        # Update sync counter
        self.after(2000, self._update_sync_count)

    def _show_error(self, title: str, message: str):
        """Show an error screen with retry."""
        self._clear_view()

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True)

        center = ctk.CTkFrame(frame, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(center, text="⚠️", font=("Segoe UI", 48)).pack(pady=(0, 10))
        ctk.CTkLabel(
            center, text=title, font=FONTS["heading_md"],
            text_color=COLORS["warning"],
        ).pack(pady=(0, 8))
        ctk.CTkLabel(
            center, text=message, font=FONTS["body"],
            text_color=("#6B7280", "#94A3B8"),
            wraplength=380, justify="center",
        ).pack(pady=(0, 20))

        ctk.CTkButton(
            center, text="🔄  Retry", font=FONTS["button"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            corner_radius=10, height=42, width=160,
            command=self._retry_init,
        ).pack()

        self.current_view = frame

    def _clear_view(self):
        """Remove the current view."""
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None

    def _retry_init(self):
        """Retry initialization."""
        self._show_loading()
        self.after(500, self._initialize)

    def _retry_registration(self):
        """Re-check registration status."""
        self._show_loading()
        self.after(500, self._initialize)

    # ──── Attendance Actions ────

    def _load_today_status(self):
        """Load today's attendance status from server."""
        def _fetch():
            try:
                status = self.api_client.get_attendance_status(self.fingerprint)
                self.after(0, lambda: self._apply_status(status))
            except Exception as e:
                logger.warning(f"Could not load today's status: {e}")

        threading.Thread(target=_fetch, daemon=True).start()

    def _apply_status(self, status: dict):
        """Apply today's status to the UI, merging with unsynced local records."""
        if not isinstance(self.current_view, AttendanceView):
            return

        # Check local unsynced records to override server status if local is newer
        unsynced = self.offline_store.get_unsynced_records()
        
        has_checked_in = status.get("has_checked_in", False)
        has_checked_out = status.get("has_checked_out", False)
        check_in_time = status.get("check_in_time")
        check_out_time = status.get("check_out_time")
        
        for record in unsynced:
            try:
                record_time = datetime.fromisoformat(record["timestamp"])
                if record_time.date() == datetime.now().date():
                    if record["action"] == "punch_in":
                        has_checked_in = True
                        check_in_time = record_time.strftime("%I:%M %p")
                    elif record["action"] == "punch_out":
                        has_checked_out = True
                        check_out_time = record_time.strftime("%I:%M %p")
            except Exception as e:
                logger.warning(f"Error parsing local record timestamp: {e}")

        self.current_view.restore_attendance_state(
            has_checked_in=has_checked_in,
            has_checked_out=has_checked_out,
            check_in_time=check_in_time,
            check_out_time=check_out_time,
        )

    def _do_punch_in(self):
        """Perform punch in."""
        def _action():
            network = get_network_info()
            now = datetime.now()
            payload = {
                "device_fingerprint": self.fingerprint,
                "hostname": get_hostname(),
                "system_username": get_system_username(),
                "ip_address": network.ip_address,
                "mac_address": network.mac_address,
                "wifi_ssid": network.wifi_ssid,
                "wifi_bssid": network.wifi_bssid,
                "gateway_mac": network.gateway_mac,
                "gateway_ip": network.gateway_ip,
                "timestamp": now.isoformat(),
            }

            try:
                # Direct check on internet connection
                if check_internet_connectivity():
                    # Attempt punch-in directly with a short timeout of 2.0s
                    self.api_client.punch_in(payload, timeout=2.0)
                    time_str = now.strftime("%I:%M %p")
                    self.after(0, lambda: self.current_view.set_checked_in(time_str))
                else:
                    raise Exception("No internet connection")
            except APIError as e:
                # Real API validation failure (e.g. invalid code or range check failures)
                self.after(0, lambda: self.current_view.set_error(e.detail))
            except Exception as e:
                # Server is offline, timed out, or connection failed -> save offline
                logger.warning(f"Punch in failed (saving offline): {e}")
                self.offline_store.store_record(
                    action="punch_in",
                    device_fingerprint=self.fingerprint,
                    hostname=payload["hostname"],
                    system_username=payload["system_username"],
                    ip_address=payload["ip_address"],
                    mac_address=payload["mac_address"],
                    wifi_ssid=payload["wifi_ssid"],
                    wifi_bssid=payload["wifi_bssid"],
                    gateway_mac=payload["gateway_mac"],
                    gateway_ip=payload["gateway_ip"],
                    timestamp=now,
                )
                time_str = now.strftime("%I:%M %p")
                self.after(0, lambda: self.current_view.set_checked_in(time_str))
                self.after(0, lambda: show_toast(
                    self, "Saved offline — will sync when connection is restored", "warning"
                ))

        threading.Thread(target=_action, daemon=True).start()

    def _do_punch_out(self):
        """Perform punch out with sync and loading screen."""
        self._show_loading("Syncing offline records and punching out...\nThis may take a moment if the server is starting up.")

        def _action():
            network = get_network_info()
            now = datetime.now()
            payload = {
                "device_fingerprint": self.fingerprint,
                "hostname": get_hostname(),
                "system_username": get_system_username(),
                "ip_address": network.ip_address,
                "mac_address": network.mac_address,
                "wifi_ssid": network.wifi_ssid,
                "wifi_bssid": network.wifi_bssid,
                "gateway_mac": network.gateway_mac,
                "gateway_ip": network.gateway_ip,
                "timestamp": now.isoformat(),
            }

            try:
                if check_internet_connectivity():
                    # Sync any offline records (like Punch In) before we punch out
                    unsynced_count = self.offline_store.get_unsynced_count()
                    if unsynced_count > 0:
                        logger.info(f"Syncing {unsynced_count} offline records before punch out...")
                        self.sync_manager.sync_now()

                    # Punch out with a longer timeout (30.0s) to wait for cold start
                    self.api_client.punch_out(payload, timeout=30.0)
                    time_str = now.strftime("%I:%M %p")
                    self.after(0, lambda: self._on_punch_out_success(time_str))
                else:
                    raise Exception("No internet connection")
            except APIError as e:
                self.after(0, lambda: self._on_punch_out_failed(e.detail))
            except Exception as e:
                logger.warning(f"Punch out failed (saving offline): {e}")
                self.offline_store.store_record(
                    action="punch_out",
                    device_fingerprint=self.fingerprint,
                    hostname=payload["hostname"],
                    system_username=payload["system_username"],
                    ip_address=payload["ip_address"],
                    mac_address=payload["mac_address"],
                    wifi_ssid=payload["wifi_ssid"],
                    wifi_bssid=payload["wifi_bssid"],
                    gateway_mac=payload["gateway_mac"],
                    gateway_ip=payload["gateway_ip"],
                    timestamp=now,
                )
                time_str = now.strftime("%I:%M %p")
                self.after(0, lambda: self._on_punch_out_offline(time_str, "Saved offline — connection failed"))

        threading.Thread(target=_action, daemon=True).start()

    def _on_punch_out_success(self, time_str: str):
        """Called on the main thread after successful server punch out."""
        self._show_attendance_view()
        self.after(100, lambda: self.current_view.set_checked_out(time_str))

    def _on_punch_out_failed(self, error_message: str):
        """Called on the main thread if server rejected the punch out with an APIError."""
        self._show_attendance_view()
        self.after(100, lambda: self.current_view.set_error(error_message))

    def _on_punch_out_offline(self, time_str: str, toast_message: str):
        """Called on the main thread after saving punch out offline."""
        self._show_attendance_view()
        self.after(100, lambda: self.current_view.set_checked_out(time_str))
        self.after(200, lambda: show_toast(self, toast_message, "warning"))

    # ──── WiFi Monitoring ────

    def _check_wifi(self):
        """Periodically check WiFi connection status."""
        if not isinstance(self.current_view, AttendanceView):
            return

        def _validate():
            network = get_network_info()

            if self.wifi_settings:
                is_valid, message = validate_office_network(
                    network,
                    required_bssid=self.wifi_settings.get("wifi_bssid"),
                    required_gateway_mac=self.wifi_settings.get("gateway_mac"),
                    required_ssid=self.wifi_settings.get("wifi_ssid"),
                    required_gateway_ip=self.wifi_settings.get("gateway_ip"),
                )
                self.after(0, lambda: self.current_view.set_wifi_status(is_valid, message))
            else:
                # No WiFi settings configured — allow all
                self.after(0, lambda: self.current_view.set_wifi_status(
                    network.is_connected, "Network" if network.is_connected else "No Connection"
                ))

        threading.Thread(target=_validate, daemon=True).start()
        self.after(self._wifi_check_interval, self._check_wifi)

    # ──── Sync Callback ────

    def _on_sync_complete(self, result: dict):
        """Called when sync completes (from sync manager thread)."""
        if result.get("synced", 0) > 0:
            self.after(0, lambda: show_toast(
                self,
                f"Synced {result['synced']} offline record(s)",
                "success",
            ))
        self.after(0, self._update_sync_count)

    def _update_sync_count(self):
        """Update sync count in UI."""
        if isinstance(self.current_view, AttendanceView):
            count = self.offline_store.get_unsynced_count()
            self.current_view.set_sync_status(count)

    def on_closing(self):
        """Clean up on window close."""
        self.sync_manager.stop()
        self.destroy()
