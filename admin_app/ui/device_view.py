"""
Device management view — registration, replacement, status management.
"""
import customtkinter as ctk
import threading
from admin_app.ui.themes import COLORS, FONTS
from admin_app.ui.components import show_toast, ConfirmDialog


class DeviceView(ctk.CTkFrame):
    """Device list with registration and management."""

    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.api_client = api_client
        self.devices = []
        self.employees = []
        self._build_ui()
        self.after(300, self.refresh)

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 12))

        ctk.CTkLabel(header, text="Device Management", font=FONTS["heading_xl"],
                      text_color=("#0F172A", "#F8FAFC")).pack(side="left")

        ctk.CTkButton(
            header, text="🖥️  Register New Device", font=FONTS["button"], width=190, height=38,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            corner_radius=10, command=self._show_register_dialog,
        ).pack(side="right")

        # Table
        self.table_frame = ctk.CTkScrollableFrame(
            self, fg_color=("#FFFFFF", "#1E293B"), corner_radius=14,
        )
        self.table_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self._create_header()

    def _create_header(self):
        hdr = ctk.CTkFrame(self.table_frame, fg_color=("#F1F5F9", "#0F172A"), corner_radius=8)
        hdr.pack(fill="x", padx=4, pady=4)

        cols = [("Employee", 150), ("Computer", 130), ("Code", 110),
                ("Status", 80), ("Registered", 100), ("Last Seen", 100), ("Actions", 160)]
        for text, w in cols:
            ctk.CTkLabel(hdr, text=text, font=FONTS["table_header"],
                          text_color=("#374151", "#94A3B8"), width=w, anchor="w").pack(
                side="left", padx=6, pady=8)

    def _render_devices(self):
        children = self.table_frame.winfo_children()
        for child in children[1:]:
            child.destroy()

        if not self.devices:
            ctk.CTkLabel(self.table_frame, text="No devices found", font=FONTS["body"],
                          text_color=("#9CA3AF", "#64748B")).pack(pady=40)
            return

        for i, dev in enumerate(self.devices):
            row = ctk.CTkFrame(
                self.table_frame,
                fg_color=("#FFFFFF", "#1E293B") if i % 2 == 0 else ("#F9FAFB", "#162032"),
                corner_radius=6,
            )
            row.pack(fill="x", padx=4, pady=1)

            emp_name = dev.get("employee_name") or "—"
            ctk.CTkLabel(row, text=emp_name, font=("Segoe UI Semibold", 12),
                          width=150, anchor="w").pack(side="left", padx=6, pady=10)

            ctk.CTkLabel(row, text=dev.get("hostname", "—"), font=FONTS["table_body"],
                          width=130, anchor="w").pack(side="left", padx=6, pady=10)

            ctk.CTkLabel(row, text=dev.get("registration_code", ""), font=("Consolas", 11),
                          width=110, anchor="w", text_color=COLORS["primary"]).pack(
                side="left", padx=6, pady=10)

            status = dev.get("status", "pending")
            status_colors = {
                "active": COLORS["success"], "pending": COLORS["warning"],
                "inactive": COLORS["danger"], "replaced": COLORS["gray_400"],
            }
            ctk.CTkLabel(row, text=status.title(), font=FONTS["table_body"],
                          width=80, anchor="w",
                          text_color=status_colors.get(status, COLORS["gray_500"])).pack(
                side="left", padx=6, pady=10)

            reg_date = self._format_date(dev.get("registered_at"))
            ctk.CTkLabel(row, text=reg_date, font=FONTS["table_body"],
                          width=100, anchor="w").pack(side="left", padx=6, pady=10)

            last_seen = self._format_date(dev.get("last_seen"))
            ctk.CTkLabel(row, text=last_seen, font=FONTS["table_body"],
                          width=100, anchor="w").pack(side="left", padx=6, pady=10)

            actions = ctk.CTkFrame(row, fg_color="transparent", width=160)
            actions.pack(side="left", padx=6)

            if status == "active":
                ctk.CTkButton(actions, text="Deactivate", font=FONTS["caption"],
                               width=70, height=26, fg_color=COLORS["warning"], corner_radius=6,
                               command=lambda d=dev: self._change_status(d, "inactive")).pack(
                    side="left", padx=2)
            elif status == "pending":
                ctk.CTkButton(actions, text="Register", font=FONTS["caption"],
                               width=65, height=26, fg_color=COLORS["success"], corner_radius=6,
                               command=lambda d=dev: self._show_assign_dialog(d)).pack(
                    side="left", padx=2)
            elif status == "inactive":
                ctk.CTkButton(actions, text="Activate", font=FONTS["caption"],
                               width=60, height=26, fg_color=COLORS["success"], corner_radius=6,
                               command=lambda d=dev: self._change_status(d, "active")).pack(
                    side="left", padx=2)

            ctk.CTkButton(actions, text="Remove", font=FONTS["caption"],
                           width=60, height=26, fg_color=COLORS["danger"], corner_radius=6,
                           command=lambda d=dev: self._change_status(d, "removed")).pack(
                side="left", padx=2)

    def _format_date(self, dt_str):
        if not dt_str:
            return "—"
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%b %d, %Y")
        except Exception:
            return "—"

    def refresh(self):
        def _fetch():
            try:
                result = self.api_client.list_devices()
                self.devices = result.get("devices", [])
                emp_result = self.api_client.list_employees()
                self.employees = emp_result.get("employees", [])
                self.after(0, self._render_devices)
            except Exception as e:
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           f"Error: {getattr(e, 'detail', str(e))}", "error"))
        threading.Thread(target=_fetch, daemon=True).start()

    def _show_register_dialog(self):
        RegisterDeviceDialog(self.winfo_toplevel(), self.api_client,
                            self.employees, on_save=self.refresh)

    def _show_assign_dialog(self, device: dict):
        RegisterDeviceDialog(self.winfo_toplevel(), self.api_client,
                            self.employees, device=device, on_save=self.refresh)

    def _change_status(self, device: dict, new_status: str):
        def _action():
            try:
                self.api_client.update_device_status(device["id"], new_status)
                self.after(0, self.refresh)
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           f"Device status updated to {new_status}", "success"))
            except Exception as e:
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           str(getattr(e, 'detail', e)), "error"))
        threading.Thread(target=_action, daemon=True).start()


class RegisterDeviceDialog(ctk.CTkToplevel):
    """Dialog to register/assign a device to an employee."""

    def __init__(self, master, api_client, employees, device=None, on_save=None):
        super().__init__(master)
        self.api_client = api_client
        self.employees = [e for e in employees if e.get("status") == "active"]
        self.device = device
        self.on_save = on_save

        self.title("Register Device")
        self.geometry("440x340")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - 220
        y = master.winfo_rooty() + (master.winfo_height() // 2) - 170
        self.geometry(f"+{x}+{y}")

        self._build_form()

    def _build_form(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(frame, text="🖥️  Register Device", font=FONTS["heading_md"]).pack(pady=(0, 16))

        # Registration code
        ctk.CTkLabel(frame, text="Registration Code", font=FONTS["body_sm"],
                      anchor="w").pack(fill="x")
        self.code_entry = ctk.CTkEntry(
            frame, height=38, corner_radius=8, font=("Consolas", 14),
            placeholder_text="e.g., ABC-123-XYZ",
            fg_color=("#F1F5F9", "#0F172A"), border_color=("#E2E8F0", "#334155"),
        )
        self.code_entry.pack(fill="x", pady=(4, 12))

        if self.device:
            self.code_entry.insert(0, self.device.get("registration_code", ""))
            self.code_entry.configure(state="disabled")

        # Employee dropdown
        ctk.CTkLabel(frame, text="Assign to Employee", font=FONTS["body_sm"],
                      anchor="w").pack(fill="x")

        emp_names = [f"{e['name']} ({e['employee_id']})" for e in self.employees]
        self.employee_dropdown = ctk.CTkComboBox(
            frame, values=emp_names or ["No active employees"],
            font=FONTS["body"], height=38, corner_radius=8,
            fg_color=("#F1F5F9", "#0F172A"), border_color=("#E2E8F0", "#334155"),
        )
        self.employee_dropdown.pack(fill="x", pady=(4, 12))
        if emp_names:
            self.employee_dropdown.set(emp_names[0])

        self.status_label = ctk.CTkLabel(frame, text="", font=FONTS["caption"],
                                          text_color=COLORS["danger"])
        self.status_label.pack(pady=(8, 4))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(btn_frame, text="Cancel", font=FONTS["button"], height=40, width=120,
                       fg_color="transparent", border_width=1, corner_radius=10,
                       border_color=("#D1D5DB", "#4B5563"),
                       text_color=("#374151", "#D1D5DB"),
                       command=self.destroy).pack(side="left", expand=True, padx=(0, 8))

        ctk.CTkButton(btn_frame, text="Register", font=FONTS["button"], height=40, width=120,
                       fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                       corner_radius=10, command=self._do_register).pack(side="right", expand=True, padx=(8, 0))

    def _do_register(self):
        code = self.code_entry.get().strip()
        selected = self.employee_dropdown.get()

        if not code:
            self.status_label.configure(text="Registration code is required")
            return
        if not self.employees:
            self.status_label.configure(text="No active employees available")
            return

        # Find selected employee
        emp = None
        for e in self.employees:
            if f"{e['name']} ({e['employee_id']})" == selected:
                emp = e
                break
        if not emp:
            self.status_label.configure(text="Please select an employee")
            return

        def _action():
            try:
                self.api_client.register_device(code, emp["id"])
                self.after(0, self.destroy)
                if self.on_save:
                    self.after(100, self.on_save)
            except Exception as e:
                detail = getattr(e, 'detail', str(e))
                self.after(0, lambda: self.status_label.configure(text=detail))

        threading.Thread(target=_action, daemon=True).start()
