"""
Theme definitions for the Employee Application.
Modern, professional dark/light themes using CustomTkinter.
"""

# Color palette
COLORS = {
    # Primary brand colors
    "primary": "#6366F1",        # Indigo
    "primary_hover": "#4F46E5",
    "primary_light": "#818CF8",
    
    # Status colors
    "success": "#10B981",        # Emerald green
    "success_hover": "#059669",
    "success_light": "#34D399",
    "danger": "#EF4444",         # Red
    "danger_hover": "#DC2626",
    "danger_light": "#F87171",
    "warning": "#F59E0B",        # Amber
    "warning_light": "#FBBF24",
    "info": "#3B82F6",           # Blue
    "info_light": "#60A5FA",
    
    # Neutral palette
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
    "gray_950": "#030712",
}

DARK_THEME = {
    "bg_primary": "#0F172A",       # Deep navy
    "bg_secondary": "#1E293B",     # Slate
    "bg_card": "#1E293B",
    "bg_input": "#334155",
    "bg_hover": "#334155",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "border": "#334155",
    "border_focus": "#6366F1",
    "shadow": "rgba(0, 0, 0, 0.3)",
}

LIGHT_THEME = {
    "bg_primary": "#FFFFFF",
    "bg_secondary": "#F8FAFC",
    "bg_card": "#FFFFFF",
    "bg_input": "#F1F5F9",
    "bg_hover": "#E2E8F0",
    "text_primary": "#0F172A",
    "text_secondary": "#475569",
    "text_muted": "#94A3B8",
    "border": "#E2E8F0",
    "border_focus": "#6366F1",
    "shadow": "rgba(0, 0, 0, 0.08)",
}

# Font configuration
FONTS = {
    "heading_xl": ("Segoe UI", 32, "bold"),
    "heading_lg": ("Segoe UI", 24, "bold"),
    "heading_md": ("Segoe UI", 20, "bold"),
    "heading_sm": ("Segoe UI", 16, "bold"),
    "body_lg": ("Segoe UI", 16),
    "body": ("Segoe UI", 14),
    "body_sm": ("Segoe UI", 12),
    "caption": ("Segoe UI", 11),
    "mono": ("Consolas", 18, "bold"),
    "mono_lg": ("Consolas", 24, "bold"),
    "clock": ("Segoe UI", 48, "bold"),
    "date": ("Segoe UI", 16),
    "name": ("Segoe UI", 28, "bold"),
    "button": ("Segoe UI Semibold", 15),
    "button_lg": ("Segoe UI Semibold", 17),
}
