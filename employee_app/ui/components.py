"""
Reusable UI components for the Employee Application.
Toast notifications, status badges, animated elements.
"""
import customtkinter as ctk
from typing import Optional
import threading


class ToastNotification(ctk.CTkFrame):
    """Animated toast notification that slides in and auto-dismisses."""

    def __init__(
        self,
        master,
        message: str,
        toast_type: str = "info",  # info, success, error, warning
        duration: int = 4000,
        **kwargs,
    ):
        # Color mapping
        colors = {
            "info": ("#3B82F6", "#DBEAFE", "#1E40AF"),
            "success": ("#10B981", "#D1FAE5", "#065F46"),
            "error": ("#EF4444", "#FEE2E2", "#991B1B"),
            "warning": ("#F59E0B", "#FEF3C7", "#92400E"),
        }
        accent, bg_light, text_dark = colors.get(toast_type, colors["info"])

        super().__init__(
            master,
            fg_color=accent,
            corner_radius=12,
            **kwargs,
        )

        # Icon mapping
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
        }

        # Content
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(padx=16, pady=12, fill="x")

        icon_label = ctk.CTkLabel(
            content_frame,
            text=icons.get(toast_type, "ℹ️"),
            font=("Segoe UI", 18),
            text_color="#FFFFFF",
        )
        icon_label.pack(side="left", padx=(0, 10))

        msg_label = ctk.CTkLabel(
            content_frame,
            text=message,
            font=("Segoe UI", 13),
            text_color="#FFFFFF",
            wraplength=350,
            justify="left",
        )
        msg_label.pack(side="left", fill="x", expand=True)

        # Close button
        close_btn = ctk.CTkButton(
            content_frame,
            text="✕",
            font=("Segoe UI", 14),
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=accent,
            text_color="#FFFFFF",
            corner_radius=14,
            command=self._dismiss,
        )
        close_btn.pack(side="right", padx=(10, 0))

        # Auto-dismiss
        self._dismiss_timer = self.after(duration, self._dismiss)

    def _dismiss(self):
        """Animate out and destroy."""
        try:
            if self._dismiss_timer:
                self.after_cancel(self._dismiss_timer)
        except (ValueError, AttributeError):
            pass
        try:
            self.destroy()
        except Exception:
            pass


class StatusBadge(ctk.CTkFrame):
    """A colored status badge with icon and text."""

    def __init__(
        self,
        master,
        text: str,
        badge_type: str = "info",  # info, success, error, warning, neutral
        **kwargs,
    ):
        colors = {
            "info": ("#3B82F6", "#1E3A5F"),
            "success": ("#10B981", "#064E3B"),
            "error": ("#EF4444", "#7F1D1D"),
            "warning": ("#F59E0B", "#78350F"),
            "neutral": ("#6B7280", "#374151"),
        }
        text_color, bg_color = colors.get(badge_type, colors["neutral"])

        super().__init__(master, fg_color=bg_color, corner_radius=8, **kwargs)

        ctk.CTkLabel(
            self,
            text=text,
            font=("Segoe UI", 11, "bold"),
            text_color=text_color,
        ).pack(padx=10, pady=4)


class PulsingDot(ctk.CTkFrame):
    """A small colored dot indicator."""

    def __init__(self, master, color: str = "#10B981", size: int = 10, **kwargs):
        super().__init__(
            master,
            width=size,
            height=size,
            corner_radius=size // 2,
            fg_color=color,
            **kwargs,
        )


class LoadingSpinner(ctk.CTkFrame):
    """A simple text-based loading indicator."""

    def __init__(self, master, text: str = "Loading...", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._index = 0
        self._running = True

        self._label = ctk.CTkLabel(
            self,
            text=f"{self._frames[0]} {text}",
            font=("Segoe UI", 13),
            text_color="#94A3B8",
        )
        self._label.pack()
        self._text = text
        self._animate()

    def _animate(self):
        if not self._running:
            return
        self._index = (self._index + 1) % len(self._frames)
        try:
            self._label.configure(text=f"{self._frames[self._index]} {self._text}")
            self.after(100, self._animate)
        except Exception:
            pass

    def stop(self):
        self._running = False

    def destroy(self):
        self._running = False
        super().destroy()


def show_toast(master, message: str, toast_type: str = "info", duration: int = 4000):
    """Helper to show a toast notification at the bottom of a window."""
    toast = ToastNotification(
        master,
        message=message,
        toast_type=toast_type,
        duration=duration,
    )
    toast.place(relx=0.5, rely=0.95, anchor="s", relwidth=0.9)
    # Lift above other widgets
    toast.lift()
    return toast
