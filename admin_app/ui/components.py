"""
Reusable UI components for the Admin Application.
"""
import customtkinter as ctk
from admin_app.ui.themes import COLORS, FONTS


class StatCard(ctk.CTkFrame):
    """Dashboard stat card with icon, value, and label."""

    def __init__(self, master, icon: str, value, label: str, color: str = None, **kwargs):
        super().__init__(master, corner_radius=14, fg_color=("#FFFFFF", "#1E293B"), **kwargs)

        accent = color or COLORS["primary"]

        # Left color accent bar
        bar = ctk.CTkFrame(self, width=4, corner_radius=2, fg_color=accent)
        bar.pack(side="left", fill="y", padx=(0, 0), pady=8)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=14)

        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(top_row, text=icon, font=("Segoe UI", 22)).pack(side="left")

        self.value_label = ctk.CTkLabel(
            top_row, text=str(value), font=FONTS["stat_value"],
            text_color=("#0F172A", "#F8FAFC"),
        )
        self.value_label.pack(side="right")

        ctk.CTkLabel(
            content, text=label, font=FONTS["stat_label"],
            text_color=("#6B7280", "#94A3B8"), anchor="w",
        ).pack(fill="x", pady=(6, 0))

    def set_value(self, value):
        self.value_label.configure(text=str(value))


class ToastNotification(ctk.CTkFrame):
    """Toast notification popup."""

    def __init__(self, master, message: str, toast_type: str = "info", duration: int = 3500, **kwargs):
        color_map = {
            "info": "#3B82F6", "success": "#10B981",
            "error": "#EF4444", "warning": "#F59E0B",
        }
        icon_map = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}

        super().__init__(master, fg_color=color_map.get(toast_type, "#3B82F6"), corner_radius=12, **kwargs)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(padx=14, pady=10, fill="x")

        ctk.CTkLabel(content, text=icon_map.get(toast_type, "ℹ️"), font=("Segoe UI", 16),
                      text_color="#FFF").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(content, text=message, font=FONTS["body"], text_color="#FFF",
                      wraplength=400, justify="left").pack(side="left", fill="x", expand=True)
        ctk.CTkButton(content, text="✕", width=26, height=26, corner_radius=13,
                       fg_color="transparent", hover_color=color_map.get(toast_type, "#3B82F6"),
                       text_color="#FFF", command=self._dismiss).pack(side="right")

        self._timer = self.after(duration, self._dismiss)

    def _dismiss(self):
        try:
            self.after_cancel(self._timer)
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


def show_toast(master, message: str, toast_type: str = "info", duration: int = 3500):
    toast = ToastNotification(master, message, toast_type, duration)
    toast.place(relx=0.5, rely=0.97, anchor="s", relwidth=0.4)
    toast.lift()
    return toast


class ConfirmDialog(ctk.CTkToplevel):
    """Confirmation dialog."""

    def __init__(self, master, title: str, message: str, on_confirm=None, danger=False):
        super().__init__(master)
        self.title(title)
        self.geometry("420x200")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - 210
        y = master.winfo_rooty() + (master.winfo_height() // 2) - 100
        self.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(frame, text=title, font=FONTS["heading_md"]).pack(pady=(0, 10))
        ctk.CTkLabel(frame, text=message, font=FONTS["body"],
                      text_color=("#6B7280", "#94A3B8"), wraplength=360).pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(
            btn_frame, text="Cancel", font=FONTS["button"], width=120, height=38,
            fg_color="transparent", hover_color=("#E5E7EB", "#374151"),
            text_color=("#374151", "#D1D5DB"), border_width=1,
            border_color=("#D1D5DB", "#4B5563"), corner_radius=10,
            command=self.destroy,
        ).pack(side="left", expand=True, padx=(0, 8))

        confirm_color = COLORS["danger"] if danger else COLORS["primary"]
        confirm_hover = COLORS["danger_hover"] if danger else COLORS["primary_hover"]

        ctk.CTkButton(
            btn_frame, text="Confirm", font=FONTS["button"], width=120, height=38,
            fg_color=confirm_color, hover_color=confirm_hover, corner_radius=10,
            command=lambda: (on_confirm() if on_confirm else None, self.destroy()),
        ).pack(side="right", expand=True, padx=(8, 0))


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
            font=FONTS.get("body", ("Segoe UI", 13)),
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

