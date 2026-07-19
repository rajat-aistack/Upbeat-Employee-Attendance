"""
Admin login screen.
"""
import customtkinter as ctk
import threading
from admin_app.ui.themes import COLORS, FONTS
from admin_app.ui.components import show_toast


class LoginView(ctk.CTkFrame):
    """Admin login form."""

    def __init__(self, master, api_client, on_login_success=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.api_client = api_client
        self.on_login_success = on_login_success
        self._build_ui()

    def _build_ui(self):
        # Center card
        card = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#1E293B"), corner_radius=20, width=420)
        card.place(relx=0.5, rely=0.5, anchor="center")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=40, pady=40)

        ctk.CTkLabel(inner, text="⚡", font=("Segoe UI", 42)).pack(pady=(0, 4))
        ctk.CTkLabel(inner, text="Upbeat Attendance", font=FONTS["heading_lg"],
                      text_color=COLORS["primary"]).pack(pady=(0, 2))
        ctk.CTkLabel(inner, text="Admin Panel", font=FONTS["body"],
                      text_color=("#6B7280", "#94A3B8")).pack(pady=(0, 28))

        # Username
        ctk.CTkLabel(inner, text="Username", font=FONTS["body_sm"],
                      text_color=("#374151", "#D1D5DB"), anchor="w").pack(fill="x")
        self.username_entry = ctk.CTkEntry(
            inner, height=42, corner_radius=10, font=FONTS["body"],
            placeholder_text="Enter username",
            fg_color=("#F1F5F9", "#0F172A"), border_color=("#E2E8F0", "#334155"),
        )
        self.username_entry.pack(fill="x", pady=(4, 14))
        self.username_entry.insert(0, "admin")

        # Password
        ctk.CTkLabel(inner, text="Password", font=FONTS["body_sm"],
                      text_color=("#374151", "#D1D5DB"), anchor="w").pack(fill="x")
        self.password_entry = ctk.CTkEntry(
            inner, height=42, corner_radius=10, font=FONTS["body"],
            placeholder_text="Enter password", show="•",
            fg_color=("#F1F5F9", "#0F172A"), border_color=("#E2E8F0", "#334155"),
        )
        self.password_entry.pack(fill="x", pady=(4, 24))
        self.password_entry.bind("<Return>", lambda e: self._do_login())

        # Login button
        self.login_btn = ctk.CTkButton(
            inner, text="Sign In", font=FONTS["button_lg"], height=46,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            corner_radius=12, command=self._do_login,
        )
        self.login_btn.pack(fill="x")

        # Status
        self.status_label = ctk.CTkLabel(
            inner, text="", font=FONTS["caption"],
            text_color=COLORS["danger"],
        )
        self.status_label.pack(pady=(12, 0))

    def _do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.status_label.configure(text="Please enter username and password")
            return

        self.status_label.configure(text="")
        
        if hasattr(self.master, "login_admin"):
            self.master.login_admin(username, password)

