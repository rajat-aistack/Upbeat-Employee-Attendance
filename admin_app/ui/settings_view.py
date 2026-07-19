"""
Settings view — office WiFi, timing, and sync configuration.
"""
import customtkinter as ctk
import threading
from admin_app.ui.themes import COLORS, FONTS
from admin_app.ui.components import show_toast


class SettingsView(ctk.CTkFrame):
    """Office settings configuration."""

    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.api_client = api_client
        self.entries = {}
        self._build_ui()
        self.after(300, self._load_settings)

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 12))

        ctk.CTkLabel(header, text="Office Settings", font=FONTS["heading_xl"],
                      text_color=("#0F172A", "#F8FAFC")).pack(side="left")

        # Scrollable content
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # WiFi Configuration Section
        self._section(content, "📶  Office WiFi Configuration",
                     "Configure the authorized office network. Attendance will only work when employees are connected to this network.")

        wifi_card = ctk.CTkFrame(content, fg_color=("#FFFFFF", "#1E293B"), corner_radius=14)
        wifi_card.pack(fill="x", pady=(0, 16))

        wifi_inner = ctk.CTkFrame(wifi_card, fg_color="transparent")
        wifi_inner.pack(fill="x", padx=20, pady=16)

        self._field(wifi_inner, "WiFi Network Name (SSID)", "wifi_ssid", "e.g., UpbeatOffice")
        self._field(wifi_inner, "WiFi BSSID (Router MAC)", "wifi_bssid", "e.g., aa:bb:cc:dd:ee:ff")
        self._field(wifi_inner, "Gateway MAC Address", "gateway_mac", "e.g., aa:bb:cc:dd:ee:ff")
        self._field(wifi_inner, "Gateway IP Address", "gateway_ip", "e.g., 192.168.1.1")

        # Detect current network button
        ctk.CTkButton(
            wifi_inner, text="🔍  Detect Current Network", font=FONTS["button"],
            height=38, fg_color="transparent", border_width=1,
            border_color=COLORS["primary"], text_color=COLORS["primary"],
            hover_color=("#E5E7EB", "#334155"), corner_radius=10,
            command=self._detect_network,
        ).pack(fill="x", pady=(8, 0))

        # Office Timing Section
        self._section(content, "🕐  Office Timing",
                     "Set office hours and grace periods for late arrival detection.")

        timing_card = ctk.CTkFrame(content, fg_color=("#FFFFFF", "#1E293B"), corner_radius=14)
        timing_card.pack(fill="x", pady=(0, 16))

        timing_inner = ctk.CTkFrame(timing_card, fg_color="transparent")
        timing_inner.pack(fill="x", padx=20, pady=16)

        row = ctk.CTkFrame(timing_inner, fg_color="transparent")
        row.pack(fill="x", pady=(0, 8))

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._field(left, "Office Start Time", "office_start_time", "e.g., 09:00")

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self._field(right, "Office End Time", "office_end_time", "e.g., 18:00")

        row2 = ctk.CTkFrame(timing_inner, fg_color="transparent")
        row2.pack(fill="x")

        left2 = ctk.CTkFrame(row2, fg_color="transparent")
        left2.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._field(left2, "Grace Period (minutes)", "grace_period_minutes", "e.g., 15")

        right2 = ctk.CTkFrame(row2, fg_color="transparent")
        right2.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self._field(right2, "Late Threshold (minutes)", "late_threshold_minutes", "e.g., 30")

        # Sync Section
        self._section(content, "🔄  Sync Settings", "")

        sync_card = ctk.CTkFrame(content, fg_color=("#FFFFFF", "#1E293B"), corner_radius=14)
        sync_card.pack(fill="x", pady=(0, 16))

        sync_inner = ctk.CTkFrame(sync_card, fg_color="transparent")
        sync_inner.pack(fill="x", padx=20, pady=16)

        self._field(sync_inner, "Sync Interval (seconds)", "sync_interval_seconds", "e.g., 300")

        # Save button
        ctk.CTkButton(
            content, text="💾  Save Settings", font=FONTS["button_lg"],
            height=48, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            corner_radius=12, command=self._save_settings,
        ).pack(fill="x", pady=(8, 0))

    def _section(self, parent, title: str, description: str):
        ctk.CTkLabel(parent, text=title, font=FONTS["heading_sm"],
                      text_color=("#0F172A", "#F8FAFC"), anchor="w").pack(fill="x", pady=(12, 2))
        if description:
            ctk.CTkLabel(parent, text=description, font=FONTS["caption"],
                          text_color=("#6B7280", "#94A3B8"), anchor="w",
                          wraplength=700).pack(fill="x", pady=(0, 8))

    def _field(self, parent, label: str, key: str, placeholder: str):
        ctk.CTkLabel(parent, text=label, font=FONTS["body_sm"],
                      text_color=("#374151", "#D1D5DB"), anchor="w").pack(fill="x", pady=(6, 2))
        entry = ctk.CTkEntry(
            parent, height=38, corner_radius=8, font=FONTS["body"],
            placeholder_text=placeholder,
            fg_color=("#F1F5F9", "#0F172A"), border_color=("#E2E8F0", "#334155"),
        )
        entry.pack(fill="x", pady=(0, 4))
        self.entries[key] = entry

    def _load_settings(self):
        def _fetch():
            try:
                settings = self.api_client.get_settings()
                self.after(0, lambda: self._populate(settings))
            except Exception as e:
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           f"Failed to load settings: {getattr(e, 'detail', str(e))}", "error"))
        threading.Thread(target=_fetch, daemon=True).start()

    def _populate(self, settings: dict):
        for key, entry in self.entries.items():
            value = settings.get(key, "")
            if value is not None:
                entry.delete(0, "end")
                entry.insert(0, str(value))

    def _detect_network(self):
        """Auto-detect current network settings."""
        def _detect():
            try:
                from employee_app.services.wifi_validator import get_network_info
                info = get_network_info()
                self.after(0, lambda: self._fill_network(info))
            except ImportError:
                # Inline detection if employee_app not available
                import subprocess, re, platform
                try:
                    output = subprocess.run(["netsh", "wlan", "show", "interfaces"],
                                           capture_output=True, text=True, timeout=10,
                                           creationflags=subprocess.CREATE_NO_WINDOW).stdout
                    ssid = bssid = None
                    for line in output.split("\n"):
                        line = line.strip()
                        if line.startswith("SSID") and "BSSID" not in line:
                            m = re.search(r"SSID\s*:\s*(.+)", line)
                            if m: ssid = m.group(1).strip()
                        elif "BSSID" in line:
                            m = re.search(r"BSSID\s*:\s*(.+)", line)
                            if m: bssid = m.group(1).strip().lower()

                    self.after(0, lambda: self._fill_raw(ssid, bssid))
                except Exception:
                    self.after(0, lambda: show_toast(self.winfo_toplevel(),
                               "Could not detect network", "error"))

        threading.Thread(target=_detect, daemon=True).start()

    def _fill_network(self, info):
        if info.wifi_ssid and "wifi_ssid" in self.entries:
            self.entries["wifi_ssid"].delete(0, "end")
            self.entries["wifi_ssid"].insert(0, info.wifi_ssid)
        if info.wifi_bssid and "wifi_bssid" in self.entries:
            self.entries["wifi_bssid"].delete(0, "end")
            self.entries["wifi_bssid"].insert(0, info.wifi_bssid)
        if info.gateway_mac and "gateway_mac" in self.entries:
            self.entries["gateway_mac"].delete(0, "end")
            self.entries["gateway_mac"].insert(0, info.gateway_mac)
        if info.gateway_ip and "gateway_ip" in self.entries:
            self.entries["gateway_ip"].delete(0, "end")
            self.entries["gateway_ip"].insert(0, info.gateway_ip)
        show_toast(self.winfo_toplevel(), "Network detected and filled", "success")

    def _fill_raw(self, ssid, bssid):
        if ssid and "wifi_ssid" in self.entries:
            self.entries["wifi_ssid"].delete(0, "end")
            self.entries["wifi_ssid"].insert(0, ssid)
        if bssid and "wifi_bssid" in self.entries:
            self.entries["wifi_bssid"].delete(0, "end")
            self.entries["wifi_bssid"].insert(0, bssid)
        show_toast(self.winfo_toplevel(), "Network partially detected", "info")

    def _save_settings(self):
        data = {}
        for key, entry in self.entries.items():
            val = entry.get().strip()
            if val:
                # Convert numeric fields
                if key in ("grace_period_minutes", "late_threshold_minutes", "sync_interval_seconds"):
                    try:
                        data[key] = int(val)
                    except ValueError:
                        show_toast(self.winfo_toplevel(), f"{key} must be a number", "warning")
                        return
                else:
                    data[key] = val

        def _save():
            try:
                self.api_client.update_settings(data)
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           "Settings saved successfully", "success"))
            except Exception as e:
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           f"Error: {getattr(e, 'detail', str(e))}", "error"))

        threading.Thread(target=_save, daemon=True).start()
