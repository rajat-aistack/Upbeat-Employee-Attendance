"""
Employee management view — CRUD operations.
"""
import customtkinter as ctk
import threading
from admin_app.ui.themes import COLORS, FONTS
from admin_app.ui.components import show_toast, ConfirmDialog


class EmployeeView(ctk.CTkFrame):
    """Employee list with add/edit/delete capabilities."""

    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.api_client = api_client
        self.employees = []
        self._build_ui()
        self.after(300, self.refresh)

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 12))

        ctk.CTkLabel(header, text="Employee Management", font=FONTS["heading_xl"],
                      text_color=("#0F172A", "#F8FAFC")).pack(side="left")

        ctk.CTkButton(
            header, text="➕  Add Employee", font=FONTS["button"], width=160, height=38,
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
            corner_radius=10, command=self._show_add_dialog,
        ).pack(side="right")

        # Search bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=24, pady=(0, 12))

        self.search_entry = ctk.CTkEntry(
            search_frame, height=38, corner_radius=10, font=FONTS["body"],
            placeholder_text="🔍  Search by name or ID...",
            fg_color=("#F1F5F9", "#0F172A"), border_color=("#E2E8F0", "#334155"),
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.refresh())

        ctk.CTkButton(
            search_frame, text="Search", font=FONTS["button"], width=90, height=38,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            corner_radius=10, command=self.refresh,
        ).pack(side="left")

        # Table container
        self.table_frame = ctk.CTkScrollableFrame(
            self, fg_color=("#FFFFFF", "#1E293B"), corner_radius=14,
        )
        self.table_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # Table header
        self._create_table_header()

    def _create_table_header(self):
        hdr = ctk.CTkFrame(self.table_frame, fg_color=("#F1F5F9", "#0F172A"), corner_radius=8)
        hdr.pack(fill="x", padx=4, pady=(4, 4))

        cols = [("ID", 80), ("Name", 180), ("Department", 120), ("Designation", 120),
                ("Status", 80), ("Actions", 200)]
        for text, width in cols:
            ctk.CTkLabel(hdr, text=text, font=FONTS["table_header"],
                          text_color=("#374151", "#94A3B8"), width=width, anchor="w").pack(
                side="left", padx=8, pady=8)

    def _render_employees(self):
        """Render employee rows."""
        # Clear existing rows (keep header)
        children = self.table_frame.winfo_children()
        for child in children[1:]:
            child.destroy()

        if not self.employees:
            ctk.CTkLabel(self.table_frame, text="No employees found", font=FONTS["body"],
                          text_color=("#9CA3AF", "#64748B")).pack(pady=40)
            return

        for i, emp in enumerate(self.employees):
            row = ctk.CTkFrame(
                self.table_frame,
                fg_color=("#FFFFFF", "#1E293B") if i % 2 == 0 else ("#F9FAFB", "#162032"),
                corner_radius=6,
            )
            row.pack(fill="x", padx=4, pady=1)

            ctk.CTkLabel(row, text=emp.get("employee_id", ""), font=FONTS["table_body"],
                          width=80, anchor="w", text_color=COLORS["primary"]).pack(
                side="left", padx=8, pady=10)

            ctk.CTkLabel(row, text=emp.get("name", ""), font=("Segoe UI Semibold", 12),
                          width=180, anchor="w").pack(side="left", padx=8, pady=10)

            ctk.CTkLabel(row, text=emp.get("department", ""), font=FONTS["table_body"],
                          width=120, anchor="w").pack(side="left", padx=8, pady=10)

            ctk.CTkLabel(row, text=emp.get("designation", ""), font=FONTS["table_body"],
                          width=120, anchor="w").pack(side="left", padx=8, pady=10)

            status = emp.get("status", "active")
            status_color = COLORS["success"] if status == "active" else COLORS["danger"]
            ctk.CTkLabel(row, text=status.title(), font=FONTS["table_body"],
                          width=80, anchor="w", text_color=status_color).pack(
                side="left", padx=8, pady=10)

            # Action buttons
            actions = ctk.CTkFrame(row, fg_color="transparent", width=200)
            actions.pack(side="left", padx=8)

            ctk.CTkButton(actions, text="Edit", font=FONTS["caption"], width=50, height=28,
                           fg_color=COLORS["info"], corner_radius=6,
                           command=lambda e=emp: self._show_edit_dialog(e)).pack(side="left", padx=2)

            if status == "active":
                ctk.CTkButton(actions, text="Deactivate", font=FONTS["caption"], width=75, height=28,
                               fg_color=COLORS["warning"], corner_radius=6,
                               command=lambda e=emp: self._toggle_status(e, "inactive")).pack(side="left", padx=2)
            else:
                ctk.CTkButton(actions, text="Activate", font=FONTS["caption"], width=65, height=28,
                               fg_color=COLORS["success"], corner_radius=6,
                               command=lambda e=emp: self._toggle_status(e, "active")).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="Delete", font=FONTS["caption"], width=55, height=28,
                           fg_color=COLORS["danger"], corner_radius=6,
                           command=lambda e=emp: self._confirm_delete(e)).pack(side="left", padx=2)

    def refresh(self):
        search = self.search_entry.get().strip()
        def _fetch():
            try:
                result = self.api_client.list_employees(search=search or None)
                self.employees = result.get("employees", [])
                self.after(0, self._render_employees)
            except Exception as e:
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           f"Error: {getattr(e, 'detail', str(e))}", "error"))
        threading.Thread(target=_fetch, daemon=True).start()

    def _show_add_dialog(self):
        EmployeeFormDialog(self.winfo_toplevel(), self.api_client, on_save=self.refresh)

    def _show_edit_dialog(self, employee: dict):
        EmployeeFormDialog(self.winfo_toplevel(), self.api_client,
                          employee=employee, on_save=self.refresh)

    def _toggle_status(self, employee: dict, new_status: str):
        def _action():
            try:
                self.api_client.update_employee_status(employee["id"], new_status)
                self.after(0, self.refresh)
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           f"{employee['name']} {new_status}", "success"))
            except Exception as e:
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           str(getattr(e, 'detail', e)), "error"))
        threading.Thread(target=_action, daemon=True).start()

    def _confirm_delete(self, employee: dict):
        ConfirmDialog(
            self.winfo_toplevel(),
            "Delete Employee",
            f"Are you sure you want to permanently delete {employee['name']}?\n"
            "This will also delete all their attendance records.",
            on_confirm=lambda: self._do_delete(employee),
            danger=True,
        )

    def _do_delete(self, employee: dict):
        def _action():
            try:
                self.api_client.delete_employee(employee["id"])
                self.after(0, self.refresh)
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           f"{employee['name']} deleted", "success"))
            except Exception as e:
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           str(getattr(e, 'detail', e)), "error"))
        threading.Thread(target=_action, daemon=True).start()


class EmployeeFormDialog(ctk.CTkToplevel):
    """Add/Edit employee form dialog."""

    def __init__(self, master, api_client, employee=None, on_save=None):
        super().__init__(master)
        self.api_client = api_client
        self.employee = employee
        self.on_save = on_save
        self.is_edit = employee is not None

        self.title("Edit Employee" if self.is_edit else "Add Employee")
        self.geometry("480x520")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - 240
        y = master.winfo_rooty() + (master.winfo_height() // 2) - 260
        self.geometry(f"+{x}+{y}")

        self._build_form()

    def _build_form(self):
        frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=16)

        title = "Edit Employee" if self.is_edit else "New Employee"
        ctk.CTkLabel(frame, text=title, font=FONTS["heading_md"]).pack(pady=(0, 16))

        fields = [
            ("Employee ID", "employee_id", "e.g., UPB-001"),
            ("Full Name", "name", "Employee full name"),
            ("Department", "department", "e.g., Sales, Engineering"),
            ("Designation", "designation", "e.g., Manager, Executive"),
            ("Mobile Number", "mobile", "Phone number"),
        ]

        self.entries = {}
        for label, key, placeholder in fields:
            ctk.CTkLabel(frame, text=label, font=FONTS["body_sm"],
                          text_color=("#374151", "#D1D5DB"), anchor="w").pack(fill="x", pady=(8, 2))
            entry = ctk.CTkEntry(
                frame, height=38, corner_radius=8, font=FONTS["body"],
                placeholder_text=placeholder,
                fg_color=("#F1F5F9", "#0F172A"), border_color=("#E2E8F0", "#334155"),
            )
            entry.pack(fill="x")

            if self.is_edit and self.employee.get(key):
                entry.insert(0, str(self.employee[key]))
            if self.is_edit and key == "employee_id":
                entry.configure(state="disabled")

            self.entries[key] = entry

        # Status label
        self.status_label = ctk.CTkLabel(frame, text="", font=FONTS["caption"],
                                          text_color=COLORS["danger"])
        self.status_label.pack(pady=(12, 4))

        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(btn_frame, text="Cancel", font=FONTS["button"], height=40, width=120,
                       fg_color="transparent", border_width=1, corner_radius=10,
                       border_color=("#D1D5DB", "#4B5563"),
                       text_color=("#374151", "#D1D5DB"),
                       command=self.destroy).pack(side="left", expand=True, padx=(0, 8))

        ctk.CTkButton(btn_frame, text="Save", font=FONTS["button"], height=40, width=120,
                       fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                       corner_radius=10, command=self._save).pack(side="right", expand=True, padx=(8, 0))

    def _save(self):
        data = {k: v.get().strip() for k, v in self.entries.items()}

        # Validate
        required = ["employee_id", "name", "department", "designation"]
        for key in required:
            if not data.get(key):
                self.status_label.configure(text=f"{key.replace('_', ' ').title()} is required")
                return

        def _action():
            try:
                if self.is_edit:
                    update = {k: v for k, v in data.items() if k != "employee_id"}
                    self.api_client.update_employee(self.employee["id"], update)
                else:
                    self.api_client.create_employee(data)

                self.after(0, self.destroy)
                if self.on_save:
                    self.after(100, self.on_save)
            except Exception as e:
                detail = getattr(e, 'detail', str(e))
                self.after(0, lambda: self.status_label.configure(text=detail))

        threading.Thread(target=_action, daemon=True).start()
