"""
Analytics tab — embeds matplotlib charts inside the CustomTkinter GUI.
Pulls straight from StudentManager.stats() and AcademicManager, so
there's no duplicate data logic here — this file only draws.
"""

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services.student_manager import StudentManager
from services.academic_manager import AcademicManager


class AnalyticsTab(ctk.CTkFrame):
    def __init__(self, master, student_manager: StudentManager, academic_manager: AcademicManager):
        super().__init__(master, fg_color="transparent")
        self.student_manager = student_manager
        self.academic_manager = academic_manager

        ctk.CTkButton(self, text="Refresh Charts", command=self.refresh).pack(pady=(10, 5))

        self.chart_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.refresh()

    def refresh(self):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        stats = self.student_manager.stats()
        departments = stats["departments"]
        avg_marks = self.academic_manager.average_marks_per_course()

        fig = Figure(figsize=(9, 4), dpi=100)
        fig.patch.set_alpha(0)

        # Pie chart: students per department
        ax1 = fig.add_subplot(1, 2, 1)
        if departments:
            ax1.pie(departments.values(), labels=departments.keys(), autopct="%1.0f%%")
        else:
            ax1.text(0.5, 0.5, "No data yet", ha="center")
        ax1.set_title("Students per Department")

        # Bar chart: average marks per course
        ax2 = fig.add_subplot(1, 2, 2)
        if avg_marks:
            ax2.bar(avg_marks.keys(), avg_marks.values(), color="#1f6aa5")
            ax2.set_ylabel("Average Marks")
            ax2.tick_params(axis="x", rotation=30)
        else:
            ax2.text(0.5, 0.5, "No grades recorded yet", ha="center")
        ax2.set_title("Average Marks per Course")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
