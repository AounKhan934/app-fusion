import sys
import os

# Ensure local imports work cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import ExpenseTrackerApp

def main():
    """Entry point for Expense Tracker & Report Generator Desktop Application."""
    app = ExpenseTrackerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
