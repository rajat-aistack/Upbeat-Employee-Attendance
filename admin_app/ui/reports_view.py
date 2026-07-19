"""
Reports view — date-range attendance reports with export.
"""
import customtkinter as ctk
import threading
import os
from datetime import datetime, date, timedelta
from admin_app.ui.themes import COLORS, FONTS
from admin_app.ui.components import show_toast
from admin_app.services.export_service import export_to_csv, export_to_excel, export_to_pdf


class ReportsView(ctk.CTkFrame):
    """Attendance report generation with filters and export."""

    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.api_client = api_client
        self.report_data = []
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 12))

        ctk.CTkLabel(header, text="Attendance Reports", font=FONTS["heading_xl"],
                      text_color=("#0F172A", "#F8FAFC")).pack(side="left")

        # Filters
        filter_card = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#1E293B"), corner_radius=14)
        filter_card.pack(fill="x", padx=24, pady=(0, 12))

        filter_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_inner.pack(fill="x", padx=16, pady=14)

        # Quick date buttons
        quick_frame = ctk.CTkFrame(filter_inner, fg_color="transparent")
        quick_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(quick_frame, text="Quick Select:", font=FONTS["body_sm"],
                      text_color=("#6B7280", "#94A3B8")).pack(side="left", padx=(0, 8))

        today = date.today()
        presets = [
            ("Today", today, today),
            ("This Week", today - timedelta(days=today.weekday()), today),
            ("This Month", today.replace(day=1), today),
            ("Last 30 Days", today - timedelta(days=30), today),
        ]
        for label, start, end in presets:
            ctk.CTkButton(
                quick_frame, text=label, font=FONTS["caption"], height=30, width=90,
                fg_color="transparent", hover_color=("#E5E7EB", "#334155"),
                text_color=COLORS["primary"], border_width=1, border_color=COLORS["primary"],
                corner_radius=8,
                command=lambda s=start, e=end: self._set_dates(s, e),
            ).pack(side="left", padx=3)

        # Date inputs row
        date_row = ctk.CTkFrame(filter_inner, fg_color="transparent")
        date_row.pack(fill="x")

        ctk.CTkLabel(date_row, text="From:", font=FONTS["body_sm"]).pack(side="left")
        self.start_entry = ctk.CTkEntry(
            date_row, width=120, height=36, corner_radius=8, font=FONTS["body"],
            placeholder_text="YYYY-MM-DD",
            fg_color=("#F1F5F9", "#0F172A"), border_color=("#E2E8F0", "#334155"),
        )
        self.start_entry.pack(side="left", padx=(4, 16))
        self.start_entry.insert(0, today.replace(day=1).isoformat())

        ctk.CTkLabel(date_row, text="To:", font=FONTS["body_sm"]).pack(side="left")
        self.end_entry = ctk.CTkEntry(
            date_row, width=120, height=36, corner_radius=8, font=FONTS["body"],
            placeholder_text="YYYY-MM-DD",
            fg_color=("#F1F5F9", "#0F172A"), border_color=("#E2E8F0", "#334155"),
        )
        self.end_entry.pack(side="left", padx=(4, 16))
        self.end_entry.insert(0, today.isoformat())

        ctk.CTkButton(
            date_row, text="📊  Generate Report", font=FONTS["button"], height=36, width=160,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            corner_radius=10, command=self._generate_report,
        ).pack(side="left", padx=(8, 0))

        # Export buttons
        export_frame = ctk.CTkFrame(date_row, fg_color="transparent")
        export_frame.pack(side="right")

        for label, cmd in [("CSV", self._export_csv), ("Excel", self._export_excel), ("PDF", self._export_pdf)]:
            ctk.CTkButton(
                export_frame, text=f"📥 {label}", font=FONTS["caption"], height=32, width=80,
                fg_color=("#E5E7EB", "#374151"), hover_color=("#D1D5DB", "#4B5563"),
                text_color=("#374151", "#E5E7EB"), corner_radius=8, command=cmd,
            ).pack(side="left", padx=3)

        # Summary stats
        self.summary_frame = ctk.CTkFrame(self, fg_color=("#F0F4FF", "#0F172A"), corner_radius=12)
        self.summary_frame.pack(fill="x", padx=24, pady=(0, 8))

        self.summary_label = ctk.CTkLabel(
            self.summary_frame, text="Generate a report to see results",
            font=FONTS["body"], text_color=("#6B7280", "#94A3B8"),
        )
        self.summary_label.pack(pady=12)

        # Results table
        self.table_frame = ctk.CTkScrollableFrame(
            self, fg_color=("#FFFFFF", "#1E293B"), corner_radius=14,
        )
        self.table_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self._create_header()

    def _create_header(self):
        hdr = ctk.CTkFrame(self.table_frame, fg_color=("#F1F5F9", "#0F172A"), corner_radius=8)
        hdr.pack(fill="x", padx=4, pady=4)

        cols = [("Employee", 160), ("Date", 100), ("Check In", 90), ("Check Out", 90),
                ("Hours", 70), ("Status", 70), ("Late", 50), ("Remarks", 140)]
        for text, w in cols:
            ctk.CTkLabel(hdr, text=text, font=FONTS["table_header"],
                          text_color=("#374151", "#94A3B8"), width=w, anchor="w").pack(
                side="left", padx=6, pady=8)

    def _set_dates(self, start: date, end: date):
        self.start_entry.delete(0, "end")
        self.start_entry.insert(0, start.isoformat())
        self.end_entry.delete(0, "end")
        self.end_entry.insert(0, end.isoformat())
        self._generate_report()

    def _generate_report(self):
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()

        if not start or not end:
            show_toast(self.winfo_toplevel(), "Please enter start and end dates", "warning")
            return

        def _fetch():
            try:
                result = self.api_client.get_attendance_report(start, end)
                summary = self.api_client.get_report_summary(start, end)
                self.report_data = result.get("records", [])
                self.after(0, lambda: self._render_results(summary))
            except Exception as e:
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                           f"Error: {getattr(e, 'detail', str(e))}", "error"))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_results(self, summary: dict):
        # Update summary
        summary_text = (
            f"📊 {summary.get('total_records', 0)} records  |  "
            f"✅ {summary.get('total_present', 0)} present  |  "
            f"⏰ {summary.get('total_late', 0)} late  |  "
            f"⚠️ {summary.get('total_missing_checkout', 0)} missing checkout"
        )
        if summary.get("avg_check_in_time"):
            summary_text += f"  |  🕐 Avg check-in: {summary['avg_check_in_time']}"
        if summary.get("avg_working_hours"):
            summary_text += f"  |  ⏱ Avg hours: {summary['avg_working_hours']}"
        self.summary_label.configure(text=summary_text)

        # Clear table rows
        children = self.table_frame.winfo_children()
        for child in children[1:]:
            child.destroy()

        if not self.report_data:
            ctk.CTkLabel(self.table_frame, text="No records found", font=FONTS["body"],
                          text_color=("#9CA3AF", "#64748B")).pack(pady=40)
            return

        for i, record in enumerate(self.report_data):
            row = ctk.CTkFrame(
                self.table_frame,
                fg_color=("#FFFFFF", "#1E293B") if i % 2 == 0 else ("#F9FAFB", "#162032"),
                corner_radius=6,
            )
            row.pack(fill="x", padx=4, pady=1)

            check_in = self._fmt_time(record.get("check_in_at"))
            check_out = self._fmt_time(record.get("check_out_at"))

            vals = [
                (record.get("employee_name", ""), 160),
                (record.get("date", ""), 100),
                (check_in, 90),
                (check_out, 90),
                (record.get("working_hours", "—"), 70),
                (record.get("status", ""), 70),
                ("Yes" if record.get("is_late") else "No", 50),
                (record.get("remarks", "") or "", 140),
            ]
            for val, w in vals:
                color = COLORS["danger"] if val == "Yes" else ("#1E293B", "#E2E8F0")
                ctk.CTkLabel(row, text=str(val), font=FONTS["table_body"],
                              width=w, anchor="w", text_color=color).pack(
                    side="left", padx=6, pady=8)

    def _fmt_time(self, dt_str):
        if not dt_str:
            return "—"
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%I:%M %p")
        except Exception:
            return str(dt_str)

    def _export_csv(self):
        if not self.report_data:
            show_toast(self.winfo_toplevel(), "No data to export", "warning")
            return
        try:
            path = export_to_csv(self.report_data)
            show_toast(self.winfo_toplevel(), f"CSV saved to exports folder", "success")
            os.startfile(os.path.dirname(path))
        except Exception as e:
            show_toast(self.winfo_toplevel(), f"Export failed: {e}", "error")

    def _export_excel(self):
        if not self.report_data:
            show_toast(self.winfo_toplevel(), "No data to export", "warning")
            return
        try:
            path = export_to_excel(self.report_data)
            show_toast(self.winfo_toplevel(), f"Excel saved to exports folder", "success")
            os.startfile(os.path.dirname(path))
        except Exception as e:
            show_toast(self.winfo_toplevel(), f"Export failed: {e}", "error")

    def _export_pdf(self):
        if not self.report_data:
            show_toast(self.winfo_toplevel(), "No data to export", "warning")
            return
        try:
            path = export_to_pdf(self.report_data)
            show_toast(self.winfo_toplevel(), f"PDF saved to exports folder", "success")
            os.startfile(os.path.dirname(path))
        except Exception as e:
            show_toast(self.winfo_toplevel(), f"Export failed: {e}", "error")
