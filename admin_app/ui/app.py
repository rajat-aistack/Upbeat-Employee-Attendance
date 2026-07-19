"""
Main Admin Application window with sidebar navigation.
"""
import customtkinter as ctk
import logging
from typing import Optional

from admin_app.config import APP_NAME, APP_VERSION, COMPANY_NAME, WINDOW_WIDTH, WINDOW_HEIGHT, SIDEBAR_WIDTH
from admin_app.ui.themes import COLORS, FONTS, SIDEBAR_ITEMS
from admin_app.ui.components import show_toast, LoadingSpinner
from admin_app.ui.login_view import LoginView
from admin_app.ui.dashboard_view import DashboardView
from admin_app.ui.employee_view import EmployeeView
from admin_app.ui.device_view import DeviceView
from admin_app.ui.reports_view import ReportsView
from admin_app.ui.settings_view import SettingsView
from admin_app.services.api_client import AdminAPIClient

logger = logging.getLogger(__name__)


def set_window_icon(window):
    """Set window title bar icon from assets/icon.ico, compatible with PyInstaller bundle."""
    import sys
    import os
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    icon_path = os.path.join(base_path, "assets", "icon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "icon.ico")
        
    if os.path.exists(icon_path):
        try:
            window.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")


class AdminApp(ctk.CTk):
    """Main admin application with sidebar navigation."""

    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} — {COMPANY_NAME}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(960, 600)
        set_window_icon(self)

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (WINDOW_WIDTH // 2)
        y = (self.winfo_screenheight() // 2) - (WINDOW_HEIGHT // 2)
        self.geometry(f"+{x}+{y}")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # API client
        self.api_client = AdminAPIClient()

        # State
        self.current_view: Optional[ctk.CTkFrame] = None
        self.current_view_name: Optional[str] = None
        self.sidebar_buttons = {}

        # Check if already authenticated
        if self.api_client.is_authenticated:
            self._show_loading("Connecting to server...\n(Waking up server, this may take a moment)")
            self.after(500, self._check_initial_health)
        else:
            # Show login
            self._show_login()

    def _show_login(self, error_message: str = None):
        """Show login view."""
        self._clear_all()
        login_view = LoginView(self, self.api_client, on_login_success=self._on_login_success)
        if error_message:
            login_view.status_label.configure(text=error_message)
        login_view.pack(fill="both", expand=True)
        self.current_view = login_view

    def _on_login_success(self):
        """Called after successful login."""
        self._clear_all()
        self._build_main_layout()

    def _build_main_layout(self):
        """Build the main layout with sidebar and content area."""
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self.main_container,
            width=SIDEBAR_WIDTH,
            fg_color=("#FFFFFF", "#0F172A"),
            corner_radius=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

        # Content area
        self.content_area = ctk.CTkFrame(
            self.main_container,
            fg_color=("#F1F5F9", "#111827"),
            corner_radius=0,
        )
        self.content_area.pack(side="left", fill="both", expand=True)

        # Show dashboard by default
        self._show_view("dashboard")

    def _build_sidebar(self):
        """Build the sidebar navigation."""
        # Logo section
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(20, 24))

        ctk.CTkLabel(
            logo_frame, text="⚡", font=("Segoe UI", 28),
        ).pack()

        ctk.CTkLabel(
            logo_frame, text="UPBEAT", font=("Segoe UI", 16, "bold"),
            text_color=COLORS["primary"],
        ).pack()

        ctk.CTkLabel(
            logo_frame, text="Attendance Admin", font=FONTS["caption"],
            text_color=("#9CA3AF", "#64748B"),
        ).pack()

        # Divider
        ctk.CTkFrame(self.sidebar, height=1,
                      fg_color=("#E5E7EB", "#1E293B")).pack(fill="x", padx=16, pady=(0, 12))

        # Navigation items
        nav_label = ctk.CTkLabel(
            self.sidebar, text="  NAVIGATION", font=FONTS["sidebar_header"],
            text_color=("#9CA3AF", "#4B5563"), anchor="w",
        )
        nav_label.pack(fill="x", padx=20, pady=(0, 6))

        for item in SIDEBAR_ITEMS:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {item['icon']}  {item['label']}",
                font=FONTS["sidebar"],
                height=42,
                anchor="w",
                corner_radius=10,
                fg_color="transparent",
                hover_color=("#EEF2FF", "#1E293B"),
                text_color=("#374151", "#D1D5DB"),
                command=lambda v=item['view']: self._show_view(v),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.sidebar_buttons[item['view']] = btn

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)

        # Bottom section
        ctk.CTkFrame(self.sidebar, height=1,
                      fg_color=("#E5E7EB", "#1E293B")).pack(fill="x", padx=16, pady=(0, 8))

        # Logged in user
        if self.api_client.username:
            user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            user_frame.pack(fill="x", padx=16, pady=(0, 4))

            ctk.CTkLabel(
                user_frame, text=f"👤  {self.api_client.username}",
                font=FONTS["body_sm"], text_color=("#6B7280", "#94A3B8"),
                anchor="w",
            ).pack(fill="x")

        # Logout button
        ctk.CTkButton(
            self.sidebar,
            text="🚪  Logout",
            font=FONTS["sidebar"],
            height=38,
            anchor="w",
            corner_radius=10,
            fg_color="transparent",
            hover_color=("#FEE2E2", "#7F1D1D"),
            text_color=COLORS["danger"],
            command=self._logout,
        ).pack(fill="x", padx=12, pady=(0, 4))

        # Version
        ctk.CTkLabel(
            self.sidebar, text=f"v{APP_VERSION}", font=FONTS["caption"],
            text_color=("#D1D5DB", "#374151"),
        ).pack(pady=(4, 16))

    def _show_view(self, view_name: str):
        """Switch the content area to a different view."""
        if self.current_view_name == view_name:
            return

        # Update sidebar active state
        for name, btn in self.sidebar_buttons.items():
            if name == view_name:
                btn.configure(
                    fg_color=(COLORS["primary_bg"], "#1E293B"),
                    text_color=(COLORS["primary"], COLORS["primary_light"]),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("#374151", "#D1D5DB"),
                )

        # Clear current content
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None

        # Create new view
        view_map = {
            "dashboard": lambda: DashboardView(self.content_area, self.api_client),
            "employees": lambda: EmployeeView(self.content_area, self.api_client),
            "devices": lambda: DeviceView(self.content_area, self.api_client),
            "reports": lambda: ReportsView(self.content_area, self.api_client),
            "settings": lambda: SettingsView(self.content_area, self.api_client),
        }

        factory = view_map.get(view_name)
        if factory:
            view = factory()
            view.pack(fill="both", expand=True)
            self.current_view = view
            self.current_view_name = view_name

    def _logout(self):
        """Log out and return to login screen."""
        self.api_client.logout()
        self.current_view = None
        self.current_view_name = None
        self.sidebar_buttons = {}
        self._show_login()

    def _clear_all(self):
        """Remove all widgets."""
        for widget in self.winfo_children():
            widget.destroy()
        self.current_view = None
        self.current_view_name = None
        self.sidebar_buttons = {}

    def _show_loading(self, text="Connecting to server..."):
        """Show full-screen loading spinner."""
        self._clear_all()
        
        self.loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.loading_frame.pack(fill="both", expand=True)

        center = ctk.CTkFrame(self.loading_frame, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(center, text="⚡", font=("Segoe UI", 48)).pack(pady=(0, 10))
        ctk.CTkLabel(
            center, text=COMPANY_NAME, font=FONTS["heading_lg"],
            text_color=COLORS["primary"],
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            center, text=APP_NAME, font=FONTS["body"],
            text_color=("#94A3B8", "#64748B"),
        ).pack(pady=(0, 20))

        self.loading_spinner = LoadingSpinner(center, text=text)
        self.loading_spinner.pack()
        self.current_view = self.loading_frame

    def _show_error(self, title: str, message: str, retry_cmd):
        """Show error screen with retry and manual login options."""
        self._clear_all()
        
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
            wraplength=400, justify="center",
        ).pack(pady=(0, 20))

        ctk.CTkButton(
            center, text="🔄  Retry", font=FONTS["button"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            corner_radius=10, height=42, width=160,
            command=retry_cmd,
        ).pack(pady=4)

        ctk.CTkButton(
            center, text="🚪  Go to Login", font=FONTS["button"],
            fg_color="transparent", hover_color=("#E5E7EB", "#374151"),
            text_color=("#374151", "#D1D5DB"), border_width=1,
            border_color=("#D1D5DB", "#4B5563"), corner_radius=10,
            height=42, width=160,
            command=lambda: self._show_login(),
        ).pack(pady=4)

        self.current_view = frame

    def _check_initial_health(self):
        """Background health check with retries for Render cold starts."""
        import threading
        import time

        def _check():
            retries = 3
            connected = False
            for attempt in range(retries):
                try:
                    if self.api_client.check_health():
                        connected = True
                        break
                except Exception:
                    pass
                if attempt < retries - 1:
                    time.sleep(3)
            
            if connected:
                self.after(0, self._build_main_layout)
            else:
                self.after(0, lambda: self._show_error(
                    "Connection Error",
                    "Could not connect to the API server.\nPlease check if the server is running or try again.",
                    self._check_initial_health
                ))

        threading.Thread(target=_check, daemon=True).start()

    def login_admin(self, username, password):
        """Centralized admin login handler with a loading screen."""
        import threading
        
        self._show_loading("Signing in to server...\n(Waking up server, this may take up to a minute)")
        
        def _login_thread():
            try:
                self.api_client.login(username, password)
                self.after(0, self._on_login_success)
            except Exception as e:
                detail = getattr(e, 'detail', str(e))
                self.after(0, lambda: self._on_login_failed(detail))

        threading.Thread(target=_login_thread, daemon=True).start()

    def _on_login_failed(self, error_message):
        """Called when login fails to restore login screen with error."""
        self._show_login(error_message=error_message)
