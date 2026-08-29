"""
StudentManager — the service/business-logic layer.
GUI code never touches SQL directly; it only calls methods here.
This is what lets you swap SQLite for PostgreSQL later without
touching a single line of GUI code (industry-style separation of concerns).
"""

import sqlite3
from models.student import Student
from services.database import Database


class DuplicateRollNoError(Exception):
    pass


class StudentNotFoundError(Exception):
    pass


class StudentManager:
    def __init__(self, db: Database):
        self.db = db

    # ---------- CREATE ----------
    def add_student(self, student: Student) -> None:
        try:
            self.db.cursor.execute(
                "INSERT INTO students VALUES (?, ?, ?, ?, ?)", student.to_tuple()
            )
            self.db.conn.commit()
        except sqlite3.IntegrityError:
            raise DuplicateRollNoError(
                f"Roll No '{student.roll_no}' already exists."
            )

    # ---------- READ ----------
    def get_student(self, roll_no: str) -> Student:
        self.db.cursor.execute(
            "SELECT * FROM students WHERE roll_no = ?", (roll_no,)
        )
        row = self.db.cursor.fetchone()
        if row is None:
            raise StudentNotFoundError(f"No student with Roll No '{roll_no}'.")
        return Student.from_row(row)

    def list_all(self) -> list[Student]:
        self.db.cursor.execute("SELECT * FROM students ORDER BY roll_no")
        return [Student.from_row(r) for r in self.db.cursor.fetchall()]

    def search(self, keyword: str) -> list[Student]:
        """Search by roll_no, name, or department (partial match)."""
        like = f"%{keyword}%"
        self.db.cursor.execute(
            """
            SELECT * FROM students
            WHERE roll_no LIKE ? OR name LIKE ? OR department LIKE ?
            ORDER BY roll_no
            """,
            (like, like, like),
        )
        return [Student.from_row(r) for r in self.db.cursor.fetchall()]

    # ---------- UPDATE ----------
    def update_student(self, roll_no: str, **fields) -> None:
        """
        Update one or more fields, e.g.:
        update_student("BSCS21001", name="New Name", cgpa=3.9)
        """
        if not fields:
            return
        # Make sure the record exists first (raises StudentNotFoundError if not)
        self.get_student(roll_no)

        allowed = {"name", "age", "department", "cgpa"}
        set_clause = ", ".join(f"{k} = ?" for k in fields if k in allowed)
        values = [v for k, v in fields.items() if k in allowed]
        values.append(roll_no)

        self.db.cursor.execute(
            f"UPDATE students SET {set_clause} WHERE roll_no = ?", values
        )
        self.db.conn.commit()

    # ---------- DELETE ----------
    def delete_student(self, roll_no: str) -> None:
        self.get_student(roll_no)  # raises if missing
        self.db.cursor.execute("DELETE FROM students WHERE roll_no = ?", (roll_no,))
        self.db.conn.commit()

    # ---------- STATS (nice extra for "industry" feel) ----------
    def stats(self) -> dict:
        students = self.list_all()
        if not students:
            return {"total": 0, "avg_cgpa": 0, "departments": {}}
        avg_cgpa = round(sum(s.cgpa for s in students) / len(students), 2)
        departments: dict[str, int] = {}
        for s in students:
            departments[s.department] = departments.get(s.department, 0) + 1
        return {"total": len(students), "avg_cgpa": avg_cgpa, "departments": departments}
