"""
Report generation — CSV export (all students) and a per-student
PDF report card (courses, grades, attendance %).
"""

import csv
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from services.student_manager import StudentManager
from services.academic_manager import AcademicManager


def export_students_csv(manager: StudentManager, filepath: str) -> None:
    students = manager.list_all()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Roll No", "Name", "Age", "Department", "CGPA"])
        for s in students:
            writer.writerow(s.to_tuple())


def generate_report_card(
    student_manager: StudentManager,
    academic_manager: AcademicManager,
    roll_no: str,
    filepath: str,
) -> None:
    student = student_manager.get_student(roll_no)
    grades = academic_manager.grades_for_student(roll_no)
    attendance_pct = academic_manager.attendance_percentage(roll_no)

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Student Report Card", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Roll No: {student.roll_no}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Name: {student.name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Department: {student.department}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Age: {student.age}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Overall CGPA: {student.cgpa}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Attendance: {attendance_pct}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Course Grades", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(90, 8, "Course", border=1)
    pdf.cell(45, 8, "Marks", border=1)
    pdf.cell(45, 8, "Grade", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 11)
    if grades:
        for course_name, marks, grade in grades:
            pdf.cell(90, 8, course_name, border=1)
            pdf.cell(45, 8, str(marks), border=1)
            pdf.cell(45, 8, grade, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    else:
        pdf.cell(180, 8, "No grades recorded yet.", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(filepath)
