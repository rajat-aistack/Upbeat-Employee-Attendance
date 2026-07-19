"""
Theme definitions for the Admin Application.
"""

COLORS = {
    "primary": "#6366F1",
    "primary_hover": "#4F46E5",
    "primary_light": "#818CF8",
    "primary_bg": "#EEF2FF",
    "success": "#10B981",
    "success_hover": "#059669",
    "danger": "#EF4444",
    "danger_hover": "#DC2626",
    "warning": "#F59E0B",
    "info": "#3B82F6",
    "gray_50": "#F9FAFB",
    "gray_100": "#F3F4F6",
    "gray_200": "#E5E7EB",
    "gray_300": "#D1D5DB",
    "gray_400": "#9CA3AF",
    "gray_500": "#6B7280",
    "gray_600": "#4B5563",
    "gray_700": "#374151",
    "gray_800": "#1F2937",
    "gray_900": "#111827",
}

FONTS = {
    "heading_xl": ("Segoe UI", 28, "bold"),
    "heading_lg": ("Segoe UI", 22, "bold"),
    "heading_md": ("Segoe UI", 18, "bold"),
    "heading_sm": ("Segoe UI", 15, "bold"),
    "body_lg": ("Segoe UI", 15),
    "body": ("Segoe UI", 13),
    "body_sm": ("Segoe UI", 12),
    "caption": ("Segoe UI", 11),
    "button": ("Segoe UI Semibold", 13),
    "button_lg": ("Segoe UI Semibold", 15),
    "mono": ("Consolas", 14),
    "stat_value": ("Segoe UI", 32, "bold"),
    "stat_label": ("Segoe UI", 12),
    "sidebar": ("Segoe UI Semibold", 13),
    "sidebar_header": ("Segoe UI", 11, "bold"),
    "table_header": ("Segoe UI Semibold", 12),
    "table_body": ("Segoe UI", 12),
}

SIDEBAR_ITEMS = [
    {"icon": "📊", "label": "Dashboard", "view": "dashboard"},
    {"icon": "👥", "label": "Employees", "view": "employees"},
    {"icon": "🖥️", "label": "Devices", "view": "devices"},
    {"icon": "📋", "label": "Reports", "view": "reports"},
    {"icon": "⚙️", "label": "Settings", "view": "settings"},
]
