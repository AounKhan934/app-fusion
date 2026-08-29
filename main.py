"""
Entry point for the Student Management System.
Run with:  python main.py

Flow: Login window -> on success -> main StudentApp window (role-aware).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.login import LoginWindow
from gui.app import StudentApp


def launch_main_app(role: str, username: str):
    from services.database import Database
    db = Database()  # fresh connection for the main app window
    app = StudentApp(db, role, username)
    app.mainloop()


if __name__ == "__main__":
    login = LoginWindow(on_success=launch_main_app)
    login.mainloop()
