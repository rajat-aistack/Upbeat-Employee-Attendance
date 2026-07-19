"""
Attendance view — the main daily attendance screen.
Displays clock, employee name, punch in/out buttons, and status.
"""
import customtkinter as ctk
import logging
from datetime import datetime
from typing import Optional, Callable

from employee_app.ui.themes import COLORS, FONTS
from employee_app.ui.components import show_toast, StatusBadge, PulsingDot

logger = logging.getLogger(__name__)


class AttendanceView(ctk.CTkFrame):
    """Main attendance screen with clock, employee info, and punch buttons."""

    def __init__(
        self,
        master,
        employee_name: str,
        on_punch_in: Optional[Callable] = None,
        on_punch_out: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.employee_name = employee_name
        self.on_punch_in = on_punch_in
        self.on_punch_out = on_punch_out

        # State
        self._has_checked_in = False
        self._has_checked_out = False
        self._clock_running = True
        self._wifi_status = True
        self._sync_count = 0

        self._build_ui()
        self._update_clock()

    def _build_ui(self):
        """Build the attendance view layout."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=16)

        # ── Top Status Bar ──
        status_bar = ctk.CTkFrame(container, fg_color="transparent", height=30)
        status_bar.pack(fill="x", pady=(0, 8))

        # WiFi indicator
        self.wifi_frame = ctk.CTkFrame(status_bar, fg_color="transparent")
        self.wifi_frame.pack(side="left")

        self.wifi_dot = PulsingDot(self.wifi_frame, color=COLORS["success"], size=8)
        self.wifi_dot.pack(side="left", padx=(0, 6))

        self.wifi_label = ctk.CTkLabel(
            self.wifi_frame,
            text="Office Network",
            font=FONTS["caption"],
            text_color=COLORS["success"],
        )
        self.wifi_label.pack(side="left")

        # Sync indicator
        self.sync_frame = ctk.CTkFrame(status_bar, fg_color="transparent")
        self.sync_frame.pack(side="right")

        self.sync_label = ctk.CTkLabel(
            self.sync_frame,
            text="",
            font=FONTS["caption"],
            text_color=("#9CA3AF", "#64748B"),
        )
        self.sync_label.pack(side="right")

        # ── Company Name ──
        company_label = ctk.CTkLabel(
            container,
            text="UPBEAT EXPOSITION",
            font=("Segoe UI", 11, "bold"),
            text_color=COLORS["primary_light"],
        )
        company_label.pack(pady=(8, 0))

        # ── Date Display ──
        self.date_label = ctk.CTkLabel(
            container,
            text="",
            font=FONTS["date"],
            text_color=("#475569", "#94A3B8"),
        )
        self.date_label.pack(pady=(4, 0))

        # ── Clock ──
        self.clock_label = ctk.CTkLabel(
            container,
            text="00:00:00",
            font=FONTS["clock"],
            text_color=("#0F172A", "#F8FAFC"),
        )
        self.clock_label.pack(pady=(4, 0))

        # AM/PM label
        self.ampm_label = ctk.CTkLabel(
            container,
            text="AM",
            font=("Segoe UI", 18),
            text_color=("#6B7280", "#64748B"),
        )
        self.ampm_label.pack(pady=(0, 16))

        # ── Welcome Card ──
        welcome_card = ctk.CTkFrame(
            container,
            fg_color=("#F0F4FF", "#1E293B"),
            corner_radius=16,
        )
        welcome_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            welcome_card,
            text="Welcome",
            font=FONTS["body"],
            text_color=("#6366F1", "#818CF8"),
        ).pack(pady=(16, 0))

        ctk.CTkLabel(
            welcome_card,
            text=self.employee_name,
            font=FONTS["name"],
            text_color=("#1E293B", "#F8FAFC"),
        ).pack(pady=(2, 4))

        # Status badges frame
        self.badge_frame = ctk.CTkFrame(welcome_card, fg_color="transparent")
        self.badge_frame.pack(pady=(0, 14))

        self.status_badge = StatusBadge(
            self.badge_frame,
            text="Ready",
            badge_type="info",
        )
        self.status_badge.pack()

        # ── Punch Buttons ──
        buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 12))

        # Punch In button
        self.punch_in_btn = ctk.CTkButton(
            buttons_frame,
            text="☀️   Punch In",
            font=FONTS["button_lg"],
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            corner_radius=14,
            height=56,
            command=self._handle_punch_in,
        )
        self.punch_in_btn.pack(fill="x", pady=(0, 10))

        # Punch Out button
        self.punch_out_btn = ctk.CTkButton(
            buttons_frame,
            text="🌙   Punch Out",
            font=FONTS["button_lg"],
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            corner_radius=14,
            height=56,
            command=self._handle_punch_out,
        )
        self.punch_out_btn.pack(fill="x")

        # ── Status Message ──
        self.status_frame = ctk.CTkFrame(
            container,
            fg_color="transparent",
            corner_radius=12,
        )
        self.status_frame.pack(fill="x", pady=(12, 0))

        self.check_in_status = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=FONTS["body_sm"],
            text_color=("#475569", "#94A3B8"),
        )
        self.check_in_status.pack(pady=(4, 0))

        self.check_out_status = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=FONTS["body_sm"],
            text_color=("#475569", "#94A3B8"),
        )
        self.check_out_status.pack(pady=(0, 4))

    def _update_clock(self):
        """Update the live clock display every second."""
        if not self._clock_running:
            return

        now = datetime.now()
        time_str = now.strftime("%I:%M:%S")
        ampm = now.strftime("%p")
        date_str = now.strftime("%A, %B %d, %Y")

        try:
            self.clock_label.configure(text=time_str)
            self.ampm_label.configure(text=ampm)
            self.date_label.configure(text=date_str)
        except Exception:
            return

        self.after(1000, self._update_clock)

    def _handle_punch_in(self):
        """Handle punch in button click."""
        if self._has_checked_in:
            show_toast(self.winfo_toplevel(), "Already checked in today", "warning")
            return

        self.punch_in_btn.configure(state="disabled", text="⏳  Processing...")
        if self.on_punch_in:
            self.on_punch_in()

    def _handle_punch_out(self):
        """Handle punch out button click."""
        if not self._has_checked_in:
            show_toast(self.winfo_toplevel(), "You must check in first", "warning")
            return
        if self._has_checked_out:
            show_toast(self.winfo_toplevel(), "Already checked out today", "warning")
            return

        self.punch_out_btn.configure(state="disabled", text="⏳  Processing...")
        if self.on_punch_out:
            self.on_punch_out()

    # ──── Public Methods for Controller ────

    def set_checked_in(self, time_str: str):
        """Update UI after successful punch in."""
        self._has_checked_in = True
        self.punch_in_btn.configure(
            state="disabled",
            text="✅  Checked In",
            fg_color=("#9CA3AF", "#4B5563"),
        )
        self.check_in_status.configure(
            text=f"Checked in at {time_str}",
            text_color=COLORS["success"],
        )
        self._update_badge("Checked In", "success")
        show_toast(self.winfo_toplevel(), f"Punch In successful at {time_str}", "success")

    def set_checked_out(self, time_str: str):
        """Update UI after successful punch out."""
        self._has_checked_out = True
        self.punch_out_btn.configure(
            state="disabled",
            text="✅  Checked Out",
            fg_color=("#9CA3AF", "#4B5563"),
        )
        self.check_out_status.configure(
            text=f"Checked out at {time_str}",
            text_color=COLORS["info"],
        )
        self._update_badge("Day Complete", "info")
        show_toast(self.winfo_toplevel(), f"Punch Out successful at {time_str}", "success")

    def set_error(self, message: str):
        """Show error state and re-enable buttons."""
        if not self._has_checked_in:
            self.punch_in_btn.configure(state="normal", text="☀️   Punch In")
        if self._has_checked_in and not self._has_checked_out:
            self.punch_out_btn.configure(state="normal", text="🌙   Punch Out")
        show_toast(self.winfo_toplevel(), message, "error")

    def set_wifi_status(self, connected: bool, message: str = ""):
        """Update WiFi status indicator."""
        self._wifi_status = connected
        if connected:
            self.wifi_dot.configure(fg_color=COLORS["success"])
            self.wifi_label.configure(
                text="Office Network",
                text_color=COLORS["success"],
            )
            self.punch_in_btn.configure(state="normal" if not self._has_checked_in else "disabled")
            self.punch_out_btn.configure(
                state="normal" if (self._has_checked_in and not self._has_checked_out) else "disabled"
            )
        else:
            self.wifi_dot.configure(fg_color=COLORS["danger"])
            self.wifi_label.configure(
                text=message or "Not Connected",
                text_color=COLORS["danger"],
            )
            self.punch_in_btn.configure(state="disabled")
            self.punch_out_btn.configure(state="disabled")

    def set_sync_status(self, pending_count: int):
        """Update sync indicator."""
        self._sync_count = pending_count
        if pending_count > 0:
            self.sync_label.configure(
                text=f"🔄 {pending_count} pending sync",
                text_color=COLORS["warning"],
            )
        else:
            self.sync_label.configure(text="")

    def restore_attendance_state(
        self,
        has_checked_in: bool,
        has_checked_out: bool,
        check_in_time: Optional[str] = None,
        check_out_time: Optional[str] = None,
    ):
        """Restore UI state from server data (e.g., on app restart)."""
        if has_checked_in:
            self._has_checked_in = True
            self.punch_in_btn.configure(
                state="disabled",
                text="✅  Checked In",
                fg_color=("#9CA3AF", "#4B5563"),
            )
            if check_in_time:
                self.check_in_status.configure(
                    text=f"Checked in at {check_in_time}",
                    text_color=COLORS["success"],
                )

        if has_checked_out:
            self._has_checked_out = True
            self.punch_out_btn.configure(
                state="disabled",
                text="✅  Checked Out",
                fg_color=("#9CA3AF", "#4B5563"),
            )
            if check_out_time:
                self.check_out_status.configure(
                    text=f"Checked out at {check_out_time}",
                    text_color=COLORS["info"],
                )
            self._update_badge("Day Complete", "info")
        elif has_checked_in:
            self._update_badge("Checked In", "success")

    def _update_badge(self, text: str, badge_type: str):
        """Update the status badge."""
        for widget in self.badge_frame.winfo_children():
            widget.destroy()
        self.status_badge = StatusBadge(self.badge_frame, text=text, badge_type=badge_type)
        self.status_badge.pack()

    def destroy(self):
        """Clean up."""
        self._clock_running = False
        super().destroy()
