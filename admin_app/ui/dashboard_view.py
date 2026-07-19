"""
Admin dashboard with stat cards and overview.
"""
import customtkinter as ctk
import threading
from admin_app.ui.themes import COLORS, FONTS
from admin_app.ui.components import StatCard, show_toast


class DashboardView(ctk.CTkFrame):
    """Dashboard with statistics cards."""

    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.api_client = api_client
        self._build_ui()
        self.after(300, self.refresh)

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 16))

        ctk.CTkLabel(header, text="Dashboard", font=FONTS["heading_xl"],
                      text_color=("#0F172A", "#F8FAFC")).pack(side="left")

        refresh_btn = ctk.CTkButton(
            header, text="🔄  Refresh", font=FONTS["button"], width=110, height=36,
            fg_color="transparent", hover_color=("#E5E7EB", "#334155"),
            text_color=COLORS["primary"], border_width=1, border_color=COLORS["primary"],
            corner_radius=10, command=self.refresh,
        )
        refresh_btn.pack(side="right")

        # Stats grid
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=24, pady=(0, 16))

        # Row 1 - Attendance overview
        row1 = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))
        row1.columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")

        self.card_present = StatCard(row1, "✅", 0, "Present Today", COLORS["success"])
        self.card_present.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.card_absent = StatCard(row1, "❌", 0, "Absent Today", COLORS["danger"])
        self.card_absent.grid(row=0, column=1, sticky="nsew", padx=8)

        self.card_in = StatCard(row1, "🟢", 0, "Currently In", COLORS["info"])
        self.card_in.grid(row=0, column=2, sticky="nsew", padx=8)

        self.card_out = StatCard(row1, "🔵", 0, "Checked Out", COLORS["primary"])
        self.card_out.grid(row=0, column=3, sticky="nsew", padx=(8, 0))

        # Row 2 - Alerts
        row2 = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        row2.pack(fill="x")
        row2.columnconfigure((0, 1, 2, 3), weight=1, uniform="stat2")

        self.card_pending = StatCard(row2, "⏳", 0, "Pending Registrations", COLORS["warning"])
        self.card_pending.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.card_late = StatCard(row2, "⏰", 0, "Late Arrivals", COLORS["warning"])
        self.card_late.grid(row=0, column=1, sticky="nsew", padx=8)

        self.card_missing = StatCard(row2, "⚠️", 0, "Missing Checkout", COLORS["danger"])
        self.card_missing.grid(row=0, column=2, sticky="nsew", padx=8)

        self.card_total = StatCard(row2, "👥", 0, "Total Employees", COLORS["primary"])
        self.card_total.grid(row=0, column=3, sticky="nsew", padx=(8, 0))

        # Quick actions section
        actions_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#1E293B"), corner_radius=14)
        actions_frame.pack(fill="x", padx=24, pady=(8, 16))

        ctk.CTkLabel(actions_frame, text="Quick Actions", font=FONTS["heading_sm"],
                      text_color=("#0F172A", "#F8FAFC")).pack(padx=20, pady=(16, 12), anchor="w")

        btn_row = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))

        actions = [
            ("👤  Add Employee", COLORS["success"], "employees"),
            ("🖥️  Register Device", COLORS["info"], "devices"),
            ("📋  View Reports", COLORS["primary"], "reports"),
            ("⚙️  Settings", COLORS["gray_600"], "settings"),
        ]
        for text, color, view in actions:
            btn = ctk.CTkButton(
                btn_row, text=text, font=FONTS["button"], height=40,
                fg_color=color, corner_radius=10,
                command=lambda v=view: self._navigate(v),
            )
            btn.pack(side="left", padx=(0, 10), expand=True, fill="x")

        # Welcome message
        welcome = ctk.CTkFrame(self, fg_color=("#F0F4FF", "#0F172A"), corner_radius=14)
        welcome.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        ctk.CTkLabel(welcome, text="Welcome to Upbeat Attendance Admin",
                      font=FONTS["heading_md"], text_color=COLORS["primary"]).pack(pady=(24, 8))
        ctk.CTkLabel(welcome, text="Manage employees, devices, and attendance from this dashboard.\n"
                     "Use the sidebar to navigate between sections.",
                      font=FONTS["body"], text_color=("#6B7280", "#94A3B8"),
                      wraplength=500, justify="center").pack(pady=(0, 24))

    def _navigate(self, view_name: str):
        """Navigate to a view via the main app."""
        app = self.winfo_toplevel()
        if hasattr(app, '_show_view'):
            app._show_view(view_name)

    def refresh(self):
        """Fetch dashboard stats from API."""
        def _fetch():
            try:
                stats = self.api_client.get_dashboard_stats()
                self.after(0, lambda: self._update_stats(stats))
            except Exception as e:
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           f"Failed to load dashboard: {getattr(e, 'detail', str(e))}", "error"))

        threading.Thread(target=_fetch, daemon=True).start()

    def _update_stats(self, stats: dict):
        self.card_present.set_value(stats.get("present_today", 0))
        self.card_absent.set_value(stats.get("absent_today", 0))
        self.card_in.set_value(stats.get("checked_in", 0))
        self.card_out.set_value(stats.get("checked_out", 0))
        self.card_pending.set_value(stats.get("pending_registrations", 0))
        self.card_late.set_value(stats.get("late_arrivals", 0))
        self.card_missing.set_value(stats.get("missing_checkout", 0))
        self.card_total.set_value(stats.get("total_employees", 0))
