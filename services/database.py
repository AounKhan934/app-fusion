"""
Database layer — the ONLY file that knows raw SQL exists.
Now includes a full relational schema (not just one flat table):

  students  <-- enrollments --> courses
  students  --> attendance (per course, per date)
  students  --> grades (per course)
  users     --> login accounts with roles (admin / teacher / student)

Foreign keys tie everything back to students.roll_no and courses.course_code,
which is what makes this a real relational design instead of a single table.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "students.db")


class Database:
    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self) -> None:
        c = self.cursor

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                roll_no     TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                age         INTEGER NOT NULL CHECK (age > 0),
                department  TEXT NOT NULL,
                cgpa        REAL NOT NULL CHECK (cgpa >= 0 AND cgpa <= 4.0)
            )
            """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                course_code   TEXT PRIMARY KEY,
                course_name   TEXT NOT NULL,
                credit_hours  INTEGER NOT NULL CHECK (credit_hours > 0)
            )
            """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS enrollments (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no      TEXT NOT NULL REFERENCES students(roll_no) ON DELETE CASCADE,
                course_code  TEXT NOT NULL REFERENCES courses(course_code) ON DELETE CASCADE,
                UNIQUE(roll_no, course_code)
            )
            """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no      TEXT NOT NULL REFERENCES students(roll_no) ON DELETE CASCADE,
                course_code  TEXT NOT NULL REFERENCES courses(course_code) ON DELETE CASCADE,
                date         TEXT NOT NULL,
                status       TEXT NOT NULL CHECK (status IN ('Present', 'Absent')),
                UNIQUE(roll_no, course_code, date)
            )
            """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS grades (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no      TEXT NOT NULL REFERENCES students(roll_no) ON DELETE CASCADE,
                course_code  TEXT NOT NULL REFERENCES courses(course_code) ON DELETE CASCADE,
                marks        REAL NOT NULL CHECK (marks >= 0 AND marks <= 100),
                grade        TEXT NOT NULL,
                UNIQUE(roll_no, course_code)
            )
            """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username        TEXT PRIMARY KEY,
                password_hash   TEXT NOT NULL,
                salt            TEXT NOT NULL,
                role            TEXT NOT NULL CHECK (role IN ('Admin', 'Teacher', 'Student'))
            )
            """
        )

        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
