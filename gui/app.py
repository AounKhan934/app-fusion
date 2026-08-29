"""
GUI layer — CustomTkinter, organized into tabs:
Students | Courses | Attendance | Grades | Analytics

Role-based access:
- Admin: full access (including delete + user management via login screen)
- Teacher: can manage grades/attendance, cannot delete students
- Student: read-only view

This file only handles PRESENTATION. Validation lives in
services/validators.py, data logic lives in services/*_manager.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

from models.student import Student
from services.database import Database
from services.student_manager import (
    StudentManager, DuplicateRollNoError, StudentNotFoundError,
)
from services.academic_manager import AcademicManager, AcademicError
from services.validators import (
    ValidationError, validate_roll_no, validate_name,
    validate_age, validate_department, validate_cgpa,
    validate_credit_hours, validate_date,
)
from services.reports import export_students_csv, generate_report_card
from gui.analytics import AnalyticsTab

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class StudentApp(ctk.CTk):
    def __init__(self, db: Database, role: str, username: str):
        super().__init__()
        self.db = db
        self.role = role
        self.username = username
        self.manager = StudentManager(self.db)
        self.academic = AcademicManager(self.db)

        self.title(f"Student Management System — {username} ({role})")
        self.geometry("1150x680")
        self.minsize(1000, 600)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)

        self.tab_students = self.tabview.add("Students")
        self.tab_courses = self.tabview.add("Courses")
        self.tab_attendance = self.tabview.add("Attendance")
        self.tab_grades = self.tabview.add("Grades")
        self.tab_analytics = self.tabview.add("Analytics")

        self._build_students_tab()
        self._build_courses_tab()
        self._build_attendance_tab()
        self._build_grades_tab()
        self._build_analytics_tab()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # =================================================================
    # STUDENTS TAB
    # =================================================================
    def _build_students_tab(self):
        tab = self.tab_students
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        panel = ctk.CTkFrame(tab, width=280, corner_radius=12)
        panel.grid(row=0, column=0, padx=(0, 10), sticky="ns")

        ctk.CTkLabel(panel, text="Student Details", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        self.entries = {}
        for label, key in [("Roll No", "roll_no"), ("Name", "name"), ("Age", "age"),
                            ("Department", "department"), ("CGPA", "cgpa")]:
            ctk.CTkLabel(panel, text=label).pack(anchor="w", padx=20, pady=(6, 0))
            entry = ctk.CTkEntry(panel, width=220)
            entry.pack(padx=20)
            self.entries[key] = entry

        btns = ctk.CTkFrame(panel, fg_color="transparent")
        btns.pack(pady=15)

        add_state = "normal" if self.role in ("Admin", "Teacher") else "disabled"
        delete_state = "normal" if self.role == "Admin" else "disabled"

        ctk.CTkButton(btns, text="Add", width=100, state=add_state, command=self._on_add).grid(row=0, column=0, padx=4, pady=4)
        ctk.CTkButton(btns, text="Update", width=100, state=add_state, command=self._on_update).grid(row=0, column=1, padx=4, pady=4)
        ctk.CTkButton(btns, text="Delete", width=100, state=delete_state, fg_color="#c0392b",
                      hover_color="#922b21", command=self._on_delete).grid(row=1, column=0, padx=4, pady=4)
        ctk.CTkButton(btns, text="Clear", width=100, command=self._clear_form).grid(row=1, column=1, padx=4, pady=4)

        ctk.CTkButton(panel, text="Export CSV", width=220, command=self._export_csv).pack(pady=(5, 5))
        ctk.CTkButton(panel, text="Generate PDF Report Card", width=220, command=self._generate_report).pack(pady=(0, 15))

        self.stats_label = ctk.CTkLabel(panel, text="", justify="left", text_color="gray")
        self.stats_label.pack(pady=(0, 15), padx=20, anchor="w")

        table_panel = ctk.CTkFrame(tab, corner_radius=12)
        table_panel.grid(row=0, column=1, sticky="nsew")
        table_panel.grid_rowconfigure(1, weight=1)
        table_panel.grid_columnconfigure(0, weight=1)

        search_frame = ctk.CTkFrame(table_panel, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search by Roll No, Name, or Department...")
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())
        ctk.CTkButton(search_frame, text="Show All", width=100, command=self._refresh_table).grid(row=0, column=1)

        self._style_treeview()
        columns = ("roll_no", "name", "age", "department", "cgpa")
        self.tree = ttk.Treeview(table_panel, columns=columns, show="headings")
        for col, head, w in zip(columns, ["Roll No", "Name", "Age", "Department", "CGPA"],
                                 [110, 200, 60, 160, 80]):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor="center")
        self.tree.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        scrollbar = ttk.Scrollbar(table_panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=10)

        self._refresh_table()

    def _style_treeview(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 11),
                         background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))
        style.map("Treeview", background=[("selected", "#1f6aa5")])

    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for s in self.manager.list_all():
            self.tree.insert("", "end", values=s.to_tuple())
        self._update_stats()
        self._refresh_course_student_dropdowns()

    def _update_stats(self):
        stats = self.manager.stats()
        self.stats_label.configure(text=f"Total Students: {stats['total']}\nAvg CGPA: {stats['avg_cgpa']}")

    def _on_row_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        for key, val in zip(["roll_no", "name", "age", "department", "cgpa"], values):
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, val)

    def _clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.tree.selection_remove(self.tree.selection())

    def _read_validated_student(self) -> Student:
        return Student(
            validate_roll_no(self.entries["roll_no"].get()),
            validate_name(self.entries["name"].get()),
            validate_age(self.entries["age"].get()),
            validate_department(self.entries["department"].get()),
            validate_cgpa(self.entries["cgpa"].get()),
        )

    def _on_add(self):
        try:
            student = self._read_validated_student()
            self.manager.add_student(student)
            messagebox.showinfo("Success", f"Student '{student.name}' added.")
            self._clear_form()
            self._refresh_table()
        except (ValidationError, DuplicateRollNoError) as e:
            messagebox.showerror("Error", str(e))

    def _on_update(self):
        try:
            student = self._read_validated_student()
            self.manager.update_student(student.roll_no, name=student.name, age=student.age,
                                         department=student.department, cgpa=student.cgpa)
            messagebox.showinfo("Success", f"Student '{student.roll_no}' updated.")
            self._clear_form()
            self._refresh_table()
        except (ValidationError, StudentNotFoundError) as e:
            messagebox.showerror("Error", str(e))

    def _on_delete(self):
        roll_no = self.entries["roll_no"].get().strip()
        if not roll_no:
            messagebox.showwarning("Missing Info", "Select or enter a Roll No to delete.")
            return
        if not messagebox.askyesno("Confirm", f"Delete student '{roll_no}'?"):
            return
        try:
            self.manager.delete_student(roll_no)
            messagebox.showinfo("Deleted", f"Student '{roll_no}' deleted.")
            self._clear_form()
            self._refresh_table()
        except StudentNotFoundError as e:
            messagebox.showerror("Error", str(e))

    def _on_search(self):
        keyword = self.search_entry.get().strip()
        for row in self.tree.get_children():
            self.tree.delete(row)
        results = self.manager.search(keyword) if keyword else self.manager.list_all()
        for s in results:
            self.tree.insert("", "end", values=s.to_tuple())

    def _export_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        export_students_csv(self.manager, filepath)
        messagebox.showinfo("Exported", f"Student list exported to:\n{filepath}")

    def _generate_report(self):
        roll_no = self.entries["roll_no"].get().strip()
        if not roll_no:
            messagebox.showwarning("Missing Info", "Select a student first.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not filepath:
            return
        try:
            generate_report_card(self.manager, self.academic, roll_no, filepath)
            messagebox.showinfo("Generated", f"Report card saved to:\n{filepath}")
        except StudentNotFoundError as e:
            messagebox.showerror("Error", str(e))

    # =================================================================
    # COURSES TAB
    # =================================================================
    def _build_courses_tab(self):
        tab = self.tab_courses
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        panel = ctk.CTkFrame(tab, width=280, corner_radius=12)
        panel.grid(row=0, column=0, padx=(0, 10), sticky="ns")

        ctk.CTkLabel(panel, text="Add Course", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        self.course_code_entry = ctk.CTkEntry(panel, width=220, placeholder_text="Course Code (e.g. CS101)")
        self.course_code_entry.pack(pady=6, padx=20)
        self.course_name_entry = ctk.CTkEntry(panel, width=220, placeholder_text="Course Name")
        self.course_name_entry.pack(pady=6, padx=20)
        self.credit_hours_entry = ctk.CTkEntry(panel, width=220, placeholder_text="Credit Hours")
        self.credit_hours_entry.pack(pady=6, padx=20)

        state = "normal" if self.role in ("Admin", "Teacher") else "disabled"
        ctk.CTkButton(panel, text="Add Course", width=220, state=state, command=self._on_add_course).pack(pady=15)

        ctk.CTkLabel(panel, text="Enroll Student", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        self.enroll_roll_menu = ctk.CTkOptionMenu(panel, values=["-"], width=220)
        self.enroll_roll_menu.pack(pady=6, padx=20)
        self.enroll_course_menu = ctk.CTkOptionMenu(panel, values=["-"], width=220)
        self.enroll_course_menu.pack(pady=6, padx=20)
        ctk.CTkButton(panel, text="Enroll", width=220, state=state, command=self._on_enroll).pack(pady=15)

        table_panel = ctk.CTkFrame(tab, corner_radius=12)
        table_panel.grid(row=0, column=1, sticky="nsew")
        table_panel.grid_rowconfigure(0, weight=1)
        table_panel.grid_columnconfigure(0, weight=1)

        columns = ("course_code", "course_name", "credit_hours")
        self.course_tree = ttk.Treeview(table_panel, columns=columns, show="headings")
        for col, head, w in zip(columns, ["Course Code", "Course Name", "Credit Hours"], [120, 260, 120]):
            self.course_tree.heading(col, text=head)
            self.course_tree.column(col, width=w, anchor="center")
        self.course_tree.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        self._refresh_courses_table()

    def _refresh_courses_table(self):
        for row in self.course_tree.get_children():
            self.course_tree.delete(row)
        for c in self.academic.list_courses():
            self.course_tree.insert("", "end", values=c)
        self._refresh_course_student_dropdowns()

    def _refresh_course_student_dropdowns(self):
        if not hasattr(self, "enroll_roll_menu"):
            return
        rolls = [s.roll_no for s in self.manager.list_all()] or ["-"]
        codes = [c[0] for c in self.academic.list_courses()] or ["-"]
        self.enroll_roll_menu.configure(values=rolls)
        self.enroll_course_menu.configure(values=codes)
        if hasattr(self, "att_roll_menu"):
            self.att_roll_menu.configure(values=rolls)
            self.att_course_menu.configure(values=codes)
            self.att_view_roll_menu.configure(values=rolls)
        if hasattr(self, "grade_roll_menu"):
            self.grade_roll_menu.configure(values=rolls)
            self.grade_course_menu.configure(values=codes)
            self.grade_view_roll_menu.configure(values=rolls)

    def _on_add_course(self):
        try:
            code = self.course_code_entry.get().strip()
            name = self.course_name_entry.get().strip()
            if not code or not name:
                raise ValidationError("Course code and name are required.")
            hours = validate_credit_hours(self.credit_hours_entry.get())
            self.academic.add_course(code, name, hours)
            messagebox.showinfo("Success", f"Course '{code}' added.")
            self.course_code_entry.delete(0, tk.END)
            self.course_name_entry.delete(0, tk.END)
            self.credit_hours_entry.delete(0, tk.END)
            self._refresh_courses_table()
        except (AcademicError, ValidationError) as e:
            messagebox.showerror("Error", str(e))

    def _on_enroll(self):
        roll_no = self.enroll_roll_menu.get()
        course_code = self.enroll_course_menu.get()
        if roll_no == "-" or course_code == "-":
            messagebox.showwarning("Missing Info", "Add students and courses first.")
            return
        try:
            self.academic.enroll(roll_no, course_code)
            messagebox.showinfo("Enrolled", f"{roll_no} enrolled in {course_code}.")
        except AcademicError as e:
            messagebox.showerror("Error", str(e))

    # =================================================================
    # ATTENDANCE TAB
    # =================================================================
    def _build_attendance_tab(self):
        tab = self.tab_attendance
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        panel = ctk.CTkFrame(tab, width=280, corner_radius=12)
        panel.grid(row=0, column=0, padx=(0, 10), sticky="ns")

        ctk.CTkLabel(panel, text="Mark Attendance", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        self.att_roll_menu = ctk.CTkOptionMenu(panel, values=["-"], width=220)
        self.att_roll_menu.pack(pady=6, padx=20)
        self.att_course_menu = ctk.CTkOptionMenu(panel, values=["-"], width=220)
        self.att_course_menu.pack(pady=6, padx=20)
        self.att_date_entry = ctk.CTkEntry(panel, width=220, placeholder_text="Date (YYYY-MM-DD)")
        self.att_date_entry.pack(pady=6, padx=20)
        self.att_status_menu = ctk.CTkOptionMenu(panel, values=["Present", "Absent"], width=220)
        self.att_status_menu.pack(pady=6, padx=20)

        state = "normal" if self.role in ("Admin", "Teacher") else "disabled"
        ctk.CTkButton(panel, text="Mark", width=220, state=state, command=self._on_mark_attendance).pack(pady=15)

        ctk.CTkLabel(panel, text="View Attendance For:", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(15, 5))
        self.att_view_roll_menu = ctk.CTkOptionMenu(panel, values=["-"], width=220, command=self._on_view_attendance)
        self.att_view_roll_menu.pack(pady=6, padx=20)
        self.att_pct_label = ctk.CTkLabel(panel, text="", text_color="gray")
        self.att_pct_label.pack(pady=10)

        table_panel = ctk.CTkFrame(tab, corner_radius=12)
        table_panel.grid(row=0, column=1, sticky="nsew")
        table_panel.grid_rowconfigure(0, weight=1)
        table_panel.grid_columnconfigure(0, weight=1)

        columns = ("date", "course", "status")
        self.att_tree = ttk.Treeview(table_panel, columns=columns, show="headings")
        for col, head, w in zip(columns, ["Date", "Course", "Status"], [140, 260, 120]):
            self.att_tree.heading(col, text=head)
            self.att_tree.column(col, width=w, anchor="center")
        self.att_tree.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

    def _on_mark_attendance(self):
        roll_no, course_code = self.att_roll_menu.get(), self.att_course_menu.get()
        status = self.att_status_menu.get()
        if roll_no == "-" or course_code == "-":
            messagebox.showwarning("Missing Info", "Fill in all fields (add students/courses first).")
            return
        try:
            date = validate_date(self.att_date_entry.get())
            self.academic.mark_attendance(roll_no, course_code, date, status)
        except (ValidationError, AcademicError) as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Marked", f"{status} recorded for {roll_no} on {date}.")
        self.att_date_entry.delete(0, tk.END)
        self._refresh_course_student_dropdowns()

    def _on_view_attendance(self, roll_no):
        for row in self.att_tree.get_children():
            self.att_tree.delete(row)
        if roll_no == "-":
            return
        for record in self.academic.attendance_for_student(roll_no):
            self.att_tree.insert("", "end", values=record)
        pct = self.academic.attendance_percentage(roll_no)
        self.att_pct_label.configure(text=f"Attendance: {pct}%")

    # =================================================================
    # GRADES TAB
    # =================================================================
    def _build_grades_tab(self):
        tab = self.tab_grades
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        panel = ctk.CTkFrame(tab, width=280, corner_radius=12)
        panel.grid(row=0, column=0, padx=(0, 10), sticky="ns")

        ctk.CTkLabel(panel, text="Record Grade", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        self.grade_roll_menu = ctk.CTkOptionMenu(panel, values=["-"], width=220)
        self.grade_roll_menu.pack(pady=6, padx=20)
        self.grade_course_menu = ctk.CTkOptionMenu(panel, values=["-"], width=220)
        self.grade_course_menu.pack(pady=6, padx=20)
        self.grade_marks_entry = ctk.CTkEntry(panel, width=220, placeholder_text="Marks (0-100)")
        self.grade_marks_entry.pack(pady=6, padx=20)

        state = "normal" if self.role in ("Admin", "Teacher") else "disabled"
        ctk.CTkButton(panel, text="Save Grade", width=220, state=state, command=self._on_save_grade).pack(pady=15)

        ctk.CTkLabel(panel, text="View Grades For:", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(15, 5))
        self.grade_view_roll_menu = ctk.CTkOptionMenu(panel, values=["-"], width=220, command=self._on_view_grades)
        self.grade_view_roll_menu.pack(pady=6, padx=20)

        table_panel = ctk.CTkFrame(tab, corner_radius=12)
        table_panel.grid(row=0, column=1, sticky="nsew")
        table_panel.grid_rowconfigure(0, weight=1)
        table_panel.grid_columnconfigure(0, weight=1)

        columns = ("course", "marks", "grade")
        self.grade_tree = ttk.Treeview(table_panel, columns=columns, show="headings")
        for col, head, w in zip(columns, ["Course", "Marks", "Grade"], [260, 120, 120]):
            self.grade_tree.heading(col, text=head)
            self.grade_tree.column(col, width=w, anchor="center")
        self.grade_tree.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

    def _on_save_grade(self):
        roll_no, course_code = self.grade_roll_menu.get(), self.grade_course_menu.get()
        if roll_no == "-" or course_code == "-":
            messagebox.showwarning("Missing Info", "Add students/courses and enroll first.")
            return
        try:
            marks = float(self.grade_marks_entry.get().strip())
            if not (0 <= marks <= 100):
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Marks must be a number between 0 and 100.")
            return
        self.academic.set_grade(roll_no, course_code, marks)
        messagebox.showinfo("Saved", f"Grade recorded for {roll_no} in {course_code}.")
        self.grade_marks_entry.delete(0, tk.END)

    def _on_view_grades(self, roll_no):
        for row in self.grade_tree.get_children():
            self.grade_tree.delete(row)
        if roll_no == "-":
            return
        for record in self.academic.grades_for_student(roll_no):
            self.grade_tree.insert("", "end", values=record)

    # =================================================================
    # ANALYTICS TAB
    # =================================================================
    def _build_analytics_tab(self):
        self.analytics_widget = AnalyticsTab(self.tab_analytics, self.manager, self.academic)
        self.analytics_widget.pack(fill="both", expand=True)

    def _on_close(self):
        self.db.close()
        self.destroy()
