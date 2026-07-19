"""
Registration view — shown when the device is not yet registered.
Displays the registration code for the admin to enter.
"""
import customtkinter as ctk
import logging
from typing import Optional

from employee_app.ui.themes import COLORS, FONTS

logger = logging.getLogger(__name__)


class RegistrationView(ctk.CTkFrame):
    """First-time device registration screen."""

    def __init__(
        self,
        master,
        registration_code: str,
        hostname: str,
        device_name: str = "",
        message: str = "",
        on_retry: callable = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_retry = on_retry
        self.registration_code = registration_code

        self._build_ui(registration_code, hostname, device_name, message)

    def _build_ui(self, code: str, hostname: str, device_name: str, message: str):
        """Build the registration view layout."""
        # Scrollable container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=20)

        # ── Icon / Header ──
        icon_label = ctk.CTkLabel(
            container,
            text="🖥️",
            font=("Segoe UI", 56),
        )
        icon_label.pack(pady=(20, 5))

        title_label = ctk.CTkLabel(
            container,
            text="Computer Not Registered",
            font=FONTS["heading_md"],
            text_color=COLORS["warning"],
        )
        title_label.pack(pady=(0, 8))

        desc_label = ctk.CTkLabel(
            container,
            text="This computer needs to be registered before\nyou can record attendance.",
            font=FONTS["body"],
            text_color=("#475569", "#94A3B8"),
            justify="center",
        )
        desc_label.pack(pady=(0, 20))

        # ── Registration Code Card ──
        code_card = ctk.CTkFrame(
            container,
            fg_color=("#F0F4FF", "#1E293B"),
            corner_radius=16,
            border_width=2,
            border_color=COLORS["primary"],
        )
        code_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            code_card,
            text="Your Registration Code",
            font=FONTS["body_sm"],
            text_color=("#6366F1", "#818CF8"),
        ).pack(pady=(16, 4))

        # Large code display
        self.code_label = ctk.CTkLabel(
            code_card,
            text=code,
            font=FONTS["mono_lg"],
            text_color=("#1E293B", "#F8FAFC"),
        )
        self.code_label.pack(pady=(4, 12))

        # Copy button
        copy_btn = ctk.CTkButton(
            code_card,
            text="📋  Copy Registration Code",
            font=FONTS["button"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=10,
            height=40,
            command=self._copy_code,
        )
        copy_btn.pack(pady=(0, 16), padx=20, fill="x")

        # ── Device Info ──
        info_card = ctk.CTkFrame(
            container,
            fg_color=("#F8FAFC", "#0F172A"),
            corner_radius=12,
        )
        info_card.pack(fill="x", pady=(0, 16))

        self._add_info_row(info_card, "Computer Name", hostname, first=True)
        self._add_info_row(info_card, "Device Name", device_name or hostname)

        if message:
            ctk.CTkLabel(
                info_card,
                text=message,
                font=FONTS["caption"],
                text_color=("#6B7280", "#64748B"),
                wraplength=380,
                justify="center",
            ).pack(pady=(4, 12), padx=16)

        # ── Instructions ──
        steps_card = ctk.CTkFrame(
            container,
            fg_color=("#FFFBEB", "#1C1917"),
            corner_radius=12,
        )
        steps_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            steps_card,
            text="📝  What to do next",
            font=FONTS["heading_sm"],
            text_color=("#92400E", "#FBBF24"),
            anchor="w",
        ).pack(padx=16, pady=(12, 8), anchor="w")

        steps = [
            "1. Copy the registration code above",
            "2. Give it to your office administrator",
            "3. Wait for admin to register this computer",
            "4. Restart this application",
        ]
        for step in steps:
            ctk.CTkLabel(
                steps_card,
                text=step,
                font=FONTS["body_sm"],
                text_color=("#78350F", "#D4A574"),
                anchor="w",
            ).pack(padx=24, pady=2, anchor="w")

        # Bottom padding
        ctk.CTkLabel(steps_card, text="").pack(pady=4)

        # ── Retry Button ──
        retry_btn = ctk.CTkButton(
            container,
            text="🔄  Check Registration Status",
            font=FONTS["button"],
            fg_color="transparent",
            hover_color=("#E2E8F0", "#334155"),
            text_color=COLORS["primary"],
            border_width=2,
            border_color=COLORS["primary"],
            corner_radius=10,
            height=42,
            command=self._on_retry_click,
        )
        retry_btn.pack(fill="x", pady=(0, 10))

    def _add_info_row(self, parent, label: str, value: str, first: bool = False):
        """Add a label-value row."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(12 if first else 4, 4))

        ctk.CTkLabel(
            row,
            text=label,
            font=FONTS["caption"],
            text_color=("#6B7280", "#64748B"),
            width=120,
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text=value,
            font=("Segoe UI", 12, "bold"),
            text_color=("#1E293B", "#E2E8F0"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

    def _copy_code(self):
        """Copy registration code to clipboard."""
        try:
            self.clipboard_clear()
            self.clipboard_append(self.registration_code)
            # Visual feedback
            self.code_label.configure(text_color=COLORS["success"])
            self.after(1500, lambda: self.code_label.configure(
                text_color=("#1E293B", "#F8FAFC")
            ))
        except Exception as e:
            logger.error(f"Clipboard error: {e}")

    def _on_retry_click(self):
        """Handle retry button click."""
        if self.on_retry:
            self.on_retry()
