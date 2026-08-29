"""
AcademicManager — handles the relational side of the system:
courses, enrollments, attendance, and grades — all linked back
to students via foreign keys (roll_no / course_code).
"""

import sqlite3
from services.database import Database


class AcademicError(Exception):
    pass


def marks_to_grade(marks: float) -> str:
    if marks >= 90:
        return "A"
    if marks >= 80:
        return "B"
    if marks >= 70:
        return "C"
    if marks >= 60:
        return "D"
    return "F"


class AcademicManager:
    def __init__(self, db: Database):
        self.db = db

    # ---------- COURSES ----------
    def add_course(self, code: str, name: str, credit_hours: int) -> None:
        try:
            self.db.cursor.execute(
                "INSERT INTO courses VALUES (?, ?, ?)", (code, name, credit_hours)
            )
            self.db.conn.commit()
        except sqlite3.IntegrityError:
            raise AcademicError(f"Course code '{code}' already exists.")

    def list_courses(self) -> list[tuple]:
        self.db.cursor.execute("SELECT * FROM courses ORDER BY course_code")
        return self.db.cursor.fetchall()

    def delete_course(self, code: str) -> None:
        self.db.cursor.execute("DELETE FROM courses WHERE course_code = ?", (code,))
        self.db.conn.commit()

    # ---------- ENROLLMENTS ----------
    def enroll(self, roll_no: str, course_code: str) -> None:
        try:
            self.db.cursor.execute(
                "INSERT INTO enrollments (roll_no, course_code) VALUES (?, ?)",
                (roll_no, course_code),
            )
            self.db.conn.commit()
        except sqlite3.IntegrityError:
            raise AcademicError("Student is already enrolled in this course (or invalid IDs).")

    def student_courses(self, roll_no: str) -> list[tuple]:
        self.db.cursor.execute(
            """
            SELECT c.course_code, c.course_name, c.credit_hours
            FROM courses c
            JOIN enrollments e ON c.course_code = e.course_code
            WHERE e.roll_no = ?
            """,
            (roll_no,),
        )
        return self.db.cursor.fetchall()

    # ---------- ATTENDANCE ----------
    def mark_attendance(self, roll_no: str, course_code: str, date: str, status: str) -> None:
        """Re-marking the same student/course/date overwrites the previous
        status instead of creating a duplicate row (which used to silently
        skew attendance_percentage())."""
        try:
            self.db.cursor.execute(
                """
                INSERT INTO attendance (roll_no, course_code, date, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(roll_no, course_code, date)
                DO UPDATE SET status = excluded.status
                """,
                (roll_no, course_code, date, status),
            )
            self.db.conn.commit()
        except sqlite3.IntegrityError:
            raise AcademicError("Could not record attendance (invalid student or course).")

    def attendance_for_student(self, roll_no: str) -> list[tuple]:
        self.db.cursor.execute(
            """
            SELECT a.date, c.course_name, a.status
            FROM attendance a
            JOIN courses c ON a.course_code = c.course_code
            WHERE a.roll_no = ?
            ORDER BY a.date DESC
            """,
            (roll_no,),
        )
        return self.db.cursor.fetchall()

    def attendance_percentage(self, roll_no: str) -> float:
        self.db.cursor.execute(
            "SELECT status FROM attendance WHERE roll_no = ?", (roll_no,)
        )
        rows = self.db.cursor.fetchall()
        if not rows:
            return 0.0
        present = sum(1 for r in rows if r[0] == "Present")
        return round(present / len(rows) * 100, 1)

    # ---------- GRADES ----------
    def set_grade(self, roll_no: str, course_code: str, marks: float) -> None:
        grade = marks_to_grade(marks)
        self.db.cursor.execute(
            """
            INSERT INTO grades (roll_no, course_code, marks, grade)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(roll_no, course_code)
            DO UPDATE SET marks = excluded.marks, grade = excluded.grade
            """,
            (roll_no, course_code, marks, grade),
        )
        self.db.conn.commit()

    def grades_for_student(self, roll_no: str) -> list[tuple]:
        self.db.cursor.execute(
            """
            SELECT c.course_name, g.marks, g.grade
            FROM grades g
            JOIN courses c ON g.course_code = c.course_code
            WHERE g.roll_no = ?
            """,
            (roll_no,),
        )
        return self.db.cursor.fetchall()

    def average_marks_per_course(self) -> dict:
        self.db.cursor.execute(
            """
            SELECT c.course_name, AVG(g.marks)
            FROM grades g JOIN courses c ON g.course_code = c.course_code
            GROUP BY c.course_name
            """
        )
        return {name: round(avg, 1) for name, avg in self.db.cursor.fetchall()}
