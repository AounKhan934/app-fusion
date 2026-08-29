# Student Management System

A desktop application to manage student records, courses, attendance, and
grades — built with Python, Object-Oriented Programming, SQLite, and a
role-based login system.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite3-lightgrey)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-informational)

---

## Features

- **Login system** with password hashing (PBKDF2-SHA256 + per-user salt) — no plain-text passwords
- **Role-based access** — Admin / Teacher / Student, each with different permissions
- **Student CRUD** — add, update, delete, search (live filter)
- **Relational data model** — Courses, Enrollments, Attendance, and Grades, all linked to students via foreign keys
- **Attendance tracking** — mark Present/Absent per course/date, auto-calculated attendance %
- **Grade management** — record marks per course, auto-converted to letter grades
- **Analytics dashboard** — embedded charts: students per department, average marks per course
- **CSV export** — full student list
- **PDF report cards** — per-student, includes grades and attendance %
- **Persistent storage** using SQLite — data survives restarts

---

## Tech Stack

| Layer          | Technology                          |
|-----------------|--------------------------------------|
| Language        | Python 3.10+                        |
| GUI             | CustomTkinter + `ttk.Treeview`      |
| Database        | SQLite3 (built into Python)         |
| Charts          | Matplotlib (embedded in Tkinter)    |
| PDF generation  | fpdf2                                |
| Auth            | hashlib.pbkdf2_hmac (salted hashing) |

---

## Project Structure

```
student_management_system/
│
├── main.py                     # Entry point — shows Login, then main app
│
├── models/
│   └── student.py               # Student data model (OOP class)
│
├── services/
│   ├── database.py              # SQLite schema: students, courses, enrollments, attendance, grades, users
│   ├── student_manager.py       # Student CRUD + search + stats
│   ├── academic_manager.py      # Courses, enrollments, attendance, grades
│   ├── auth.py                  # Registration/login, password hashing
│   ├── validators.py            # Centralized input validation
│   └── reports.py               # CSV export + PDF report card generation
│
├── gui/
│   ├── login.py                 # Login / first-run admin setup / registration
│   ├── app.py                   # Main window (Students / Courses / Attendance / Grades tabs)
│   └── analytics.py             # Embedded matplotlib charts tab
│
├── data/
│   └── students.db              # Auto-created SQLite database (on first run)
│
├── requirements.txt
└── README.md
```

---

## Database Schema (Relational Design)

```
students (roll_no PK, name, age, department, cgpa)
courses  (course_code PK, course_name, credit_hours)
enrollments (id PK, roll_no FK -> students, course_code FK -> courses)
attendance  (id PK, roll_no FK, course_code FK, date, status)
grades      (id PK, roll_no FK, course_code FK, marks, grade)
users       (username PK, password_hash, salt, role)
```

Foreign keys (`ON DELETE CASCADE`) tie everything back to `students` and
`courses` — this is a genuine relational design, not a single flat table.

---

## OOP & Design Concepts Applied

| Concept                 | Where it's used |
|--------------------------|------------------|
| **Encapsulation**        | `Student` class bundles data; manager classes hide SQL behind clean methods |
| **Abstraction**          | GUI never writes SQL — it only calls `manager.add_student(...)`, `academic.enroll(...)`, etc. |
| **Custom Exceptions**    | `DuplicateRollNoError`, `StudentNotFoundError`, `AcademicError`, `AuthError`, `ValidationError` |
| **Separation of Concerns** | Models / Services / GUI are fully decoupled — swap SQLite or the GUI framework without touching the other layers |
| **Security**             | Passwords salted + hashed with PBKDF2 (100,000 iterations) — never stored in plain text |

---

## Setup & Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**
   ```bash
   python main.py
   ```

3. **First run** — no accounts exist yet, so you'll be asked to create the
   initial **Admin** account. After that, use the login screen (with a
   "Register New Account" option for Teacher/Student accounts).

The SQLite database (`data/students.db`) is created automatically on first run.

---

## Role Permissions

| Action                  | Admin | Teacher | Student |
|--------------------------|:-----:|:-------:|:-------:|
| View students/courses    |  ✅   |   ✅    |   ✅    |
| Add / update student     |  ✅   |   ✅    |   ❌    |
| Delete student           |  ✅   |   ❌    |   ❌    |
| Add course / enroll      |  ✅   |   ✅    |   ❌    |
| Mark attendance          |  ✅   |   ✅    |   ❌    |
| Record grades            |  ✅   |   ✅    |   ❌    |
| Export CSV / PDF reports |  ✅   |   ✅    |   ✅    |

---

## Packaging as a Standalone `.exe` (Windows)

So users can double-click and run it without installing Python:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name StudentManagementSystem main.py
```

The `.exe` will be created inside the `dist/` folder. Note: on first run
from a new location, it will create its own `data/students.db` next to
the executable.

---

## Possible Future Improvements

- Multi-campus support
- Fee/billing module
- Email notifications for low attendance
- Cloud sync (e.g., Firebase or a hosted PostgreSQL backend)

---

## Author

Muhammad Aoun Khan — BS Computer Science, University of Mianwali
