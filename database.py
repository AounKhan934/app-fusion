import sqlite3
import os
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from models import Expense, DEFAULT_CATEGORIES, DEFAULT_PAYMENT_METHODS

DB_NAME = "expenses.db"

class DatabaseManager:
    def __init__(self, db_path: str = DB_NAME, auto_seed: bool = True):
        self.db_path = db_path
        self.auto_seed = auto_seed
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Context manager that guarantees connection is closed properly on Windows."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        """Initializes database tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Expenses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    date TEXT NOT NULL,
                    payment_method TEXT DEFAULT 'Cash',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Monthly Budgets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month TEXT UNIQUE NOT NULL, -- Format: YYYY-MM
                    budget_limit REAL NOT NULL
                )
            """)

            # Custom Categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)

            # Insert default categories if table is empty
            cursor.execute("SELECT COUNT(*) FROM categories")
            if cursor.fetchone()[0] == 0:
                for cat in DEFAULT_CATEGORIES:
                    cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

            # Seed sample expenses if expenses table is empty on first launch
            cursor.execute("SELECT COUNT(*) FROM expenses")
            if self.auto_seed and cursor.fetchone()[0] == 0:
                self._seed_sample_records_internal(cursor)

            conn.commit()

    def _seed_sample_records_internal(self, cursor):
        sample_expenses = [
            ("Grocery Market Haul", 84.50, "Groceries", "Debit Card", "Weekly fresh produce and pantry items"),
            ("Electricity & Water Bill", 125.00, "Bills", "Bank Transfer", "Monthly residential utility bill"),
            ("Uber Ride to Airport", 34.20, "Travel", "Credit Card", "Business trip transportation"),
            ("Italian Dinner with Friends", 68.40, "Food", "Credit Card", "Pasta & dessert downtown"),
            ("Online Python Course", 49.99, "Education", "UPI / Online", "Advanced algorithms certification"),
            ("Cinema & Snacks", 28.50, "Entertainment", "Cash", "Weekend movie tickets with popcorn"),
            ("Prescription Medication", 22.80, "Health", "Cash", "Pharmacy essentials & vitamins"),
            ("New Running Shoes", 89.90, "Shopping", "Credit Card", "Athletic footwear sale"),
            ("Mobile Phone Plan", 35.00, "Bills", "UPI / Online", "Monthly unlimited 5G data"),
            ("Coffee & Bakery", 12.75, "Food", "Cash", "Morning espresso and croissant"),
            ("Gasoline Refill", 45.00, "Travel", "Debit Card", "Full tank refill at Shell"),
            ("High-Speed Internet Bill", 60.00, "Bills", "Bank Transfer", "Fiber broadband subscription"),
            ("Supermarket Snack Stock", 31.60, "Groceries", "Debit Card", "Snacks and sparkling water"),
            ("Bookstore Purchase", 24.50, "Education", "Cash", "Clean Code book and notebook"),
            ("Streaming Service", 15.99, "Entertainment", "Credit Card", "Monthly 4K streaming sub"),
            ("Dental Checkup", 75.00, "Health", "Credit Card", "Routine dental cleaning"),
            ("Casual Work Shirts", 55.00, "Shopping", "Credit Card", "2 button-down shirts"),
            ("Lunch Buffet", 19.50, "Food", "UPI / Online", "Team lunch"),
            ("Train Monthly Pass", 65.00, "Travel", "Debit Card", "Metro commuting pass"),
            ("Home Cleaning Supplies", 27.30, "Groceries", "Cash", "Detergent and cleaning tools"),
        ]
        today = datetime.now()
        for i, (title, amount, category, method, notes) in enumerate(sample_expenses):
            days_ago = (i * 3) % 55
            item_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT INTO expenses (title, amount, category, date, payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, amount, category, item_date, method, notes))

        curr_month = today.strftime("%Y-%m-%d")[:7]
        cursor.execute("""
            INSERT OR IGNORE INTO budgets (month, budget_limit)
            VALUES (?, ?)
        """, (curr_month, 800.0))

    def get_categories(self) -> List[str]:
        """Returns all category names sorted."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM categories ORDER BY name ASC")
            rows = cursor.fetchall()
            return [row["name"] for row in rows]

    def add_category(self, name: str) -> bool:
        """Adds a custom category."""
        clean_name = name.strip()
        if not clean_name:
            return False
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (clean_name,))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def add_expense(self, expense: Expense) -> int:
        """Inserts a new expense and returns its ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (title, amount, category, date, payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (expense.title.strip(), expense.amount, expense.category, expense.date, expense.payment_method, expense.notes))
            conn.commit()
            return cursor.lastrowid

    def update_expense(self, expense: Expense) -> bool:
        """Updates an existing expense."""
        if not expense.id:
            return False
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE expenses
                SET title = ?, amount = ?, category = ?, date = ?, payment_method = ?, notes = ?
                WHERE id = ?
            """, (expense.title.strip(), expense.amount, expense.category, expense.date, expense.payment_method, expense.notes, expense.id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_expense(self, expense_id: int) -> bool:
        """Deletes an expense by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_expense(self, expense_id: int) -> Optional[Expense]:
        """Retrieves a single expense by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, amount, category, date, payment_method, notes, created_at
                FROM expenses WHERE id = ?
            """, (expense_id,))
            row = cursor.fetchone()
            if row:
                return Expense.from_row(tuple(row))
            return None

    def get_all_expenses(self) -> List[Expense]:
        """Returns all expenses sorted by date descending."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, amount, category, date, payment_method, notes, created_at
                FROM expenses
                ORDER BY date DESC, id DESC
            """)
            rows = cursor.fetchall()
            return [Expense.from_row(tuple(r)) for r in rows]

    def filter_expenses(
        self,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        search_keyword: Optional[str] = None,
        payment_method: Optional[str] = None
    ) -> List[Expense]:
        """Filter and search expenses based on multiple criteria."""
        conditions = []
        params = []

        if category and category != "All":
            conditions.append("category = ?")
            params.append(category)

        if payment_method and payment_method != "All":
            conditions.append("payment_method = ?")
            params.append(payment_method)

        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)

        if min_amount is not None:
            conditions.append("amount >= ?")
            params.append(min_amount)

        if max_amount is not None:
            conditions.append("amount <= ?")
            params.append(max_amount)

        if search_keyword:
            conditions.append("(title LIKE ? OR notes LIKE ?)")
            pattern = f"%{search_keyword.strip()}%"
            params.extend([pattern, pattern])

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT id, title, amount, category, date, payment_method, notes, created_at
            FROM expenses
            {where_clause}
            ORDER BY date DESC, id DESC
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [Expense.from_row(tuple(r)) for r in rows]

    def get_category_summary(self, month: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns total amounts grouped by category (optionally filtered by YYYY-MM)."""
        params = []
        where_clause = ""
        if month:
            where_clause = "WHERE strftime('%Y-%m', date) = ?"
            params.append(month)

        query = f"""
            SELECT category, SUM(amount) as total_amount, COUNT(id) as count
            FROM expenses
            {where_clause}
            GROUP BY category
            ORDER BY total_amount DESC
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [{"category": r["category"], "total_amount": float(r["total_amount"]), "count": r["count"]} for r in rows]

    def get_monthly_summary(self) -> List[Dict[str, Any]]:
        """Returns aggregated totals grouped by year-month."""
        query = """
            SELECT strftime('%Y-%m', date) as month,
                   SUM(amount) as total_amount,
                   COUNT(id) as count,
                   AVG(amount) as avg_amount
            FROM expenses
            GROUP BY month
            ORDER BY month ASC
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                {
                    "month": r["month"],
                    "total_amount": float(r["total_amount"]),
                    "count": r["count"],
                    "avg_amount": float(r["avg_amount"])
                }
                for r in rows if r["month"]
            ]

    def get_daily_trend(self, month: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns spending per day for a given month or recent 30 days."""
        params = []
        if month:
            where_clause = "WHERE strftime('%Y-%m', date) = ?"
            params.append(month)
        else:
            where_clause = "WHERE date >= date('now', '-30 days')"

        query = f"""
            SELECT date, SUM(amount) as daily_total, COUNT(id) as count
            FROM expenses
            {where_clause}
            GROUP BY date
            ORDER BY date ASC
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [{"date": r["date"], "daily_total": float(r["daily_total"]), "count": r["count"]} for r in rows]

    def get_overall_stats(self) -> Dict[str, Any]:
        """Calculates high-level overall statistics."""
        current_month = datetime.now().strftime("%Y-%m")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Total spending & count
            cursor.execute("SELECT SUM(amount), COUNT(id), AVG(amount), MAX(amount) FROM expenses")
            total, count, avg, max_val = cursor.fetchone()

            # Current month total & count
            cursor.execute("SELECT SUM(amount), COUNT(id) FROM expenses WHERE strftime('%Y-%m', date) = ?", (current_month,))
            curr_month_total, curr_month_count = cursor.fetchone()

            # Top category all time
            cursor.execute("""
                SELECT category, SUM(amount) as total
                FROM expenses
                GROUP BY category
                ORDER BY total DESC
                LIMIT 1
            """)
            top_cat_row = cursor.fetchone()

            # Top category this month
            cursor.execute("""
                SELECT category, SUM(amount) as total
                FROM expenses
                WHERE strftime('%Y-%m', date) = ?
                GROUP BY category
                ORDER BY total DESC
                LIMIT 1
            """, (current_month,))
            top_curr_cat_row = cursor.fetchone()

            return {
                "total_spending": float(total or 0.0),
                "total_count": int(count or 0),
                "average_expense": float(avg or 0.0),
                "highest_expense": float(max_val or 0.0),
                "current_month": current_month,
                "current_month_spending": float(curr_month_total or 0.0),
                "current_month_count": int(curr_month_count or 0),
                "top_category": top_cat_row["category"] if top_cat_row else "None",
                "top_category_amount": float(top_cat_row["total"]) if top_cat_row else 0.0,
                "curr_top_category": top_curr_cat_row["category"] if top_curr_cat_row else "None",
                "curr_top_category_amount": float(top_curr_cat_row["total"]) if top_curr_cat_row else 0.0,
            }

    def set_budget(self, month: str, limit: float) -> bool:
        """Sets or updates the budget limit for a month (YYYY-MM)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO budgets (month, budget_limit)
                VALUES (?, ?)
                ON CONFLICT(month) DO UPDATE SET budget_limit = excluded.budget_limit
            """, (month, limit))
            conn.commit()
            return True

    def get_budget(self, month: str) -> Optional[float]:
        """Gets the budget for a specific month (YYYY-MM)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT budget_limit FROM budgets WHERE month = ?", (month,))
            row = cursor.fetchone()
            return float(row["budget_limit"]) if row else None

    def clear_all_expenses(self):
        """Removes all expense records."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses")
            conn.commit()

    def seed_sample_data(self):
        """Populates the database with realistic sample expense records."""
        sample_expenses = [
            ("Grocery Market Haul", 84.50, "Groceries", "Debit Card", "Weekly fresh produce and pantry items"),
            ("Electricity & Water Bill", 125.00, "Bills", "Bank Transfer", "Monthly residential utility bill"),
            ("Uber Ride to Airport", 34.20, "Travel", "Credit Card", "Business trip transportation"),
            ("Italian Dinner with Friends", 68.40, "Food", "Credit Card", "Pasta & dessert downtown"),
            ("Online Python Course", 49.99, "Education", "UPI / Online", "Advanced algorithms certification"),
            ("Cinema & Snacks", 28.50, "Entertainment", "Cash", "Weekend movie tickets with popcorn"),
            ("Prescription Medication", 22.80, "Health", "Cash", "Pharmacy essentials & vitamins"),
            ("New Running Shoes", 89.90, "Shopping", "Credit Card", "Athletic footwear sale"),
            ("Mobile Phone Plan", 35.00, "Bills", "UPI / Online", "Monthly unlimited 5G data"),
            ("Coffee & Bakery", 12.75, "Food", "Cash", "Morning espresso and croissant"),
            ("Gasoline Refill", 45.00, "Travel", "Debit Card", "Full tank refill at Shell"),
            ("High-Speed Internet Bill", 60.00, "Bills", "Bank Transfer", "Fiber broadband subscription"),
            ("Supermarket Snack Stock", 31.60, "Groceries", "Debit Card", "Snacks and sparkling water"),
            ("Bookstore Purchase", 24.50, "Education", "Cash", "Clean Code book and notebook"),
            ("Streaming Service", 15.99, "Entertainment", "Credit Card", "Monthly 4K streaming sub"),
            ("Dental Checkup", 75.00, "Health", "Credit Card", "Routine dental cleaning"),
            ("Casual Work Shirts", 55.00, "Shopping", "Credit Card", "2 button-down shirts"),
            ("Lunch Buffet", 19.50, "Food", "UPI / Online", "Team lunch"),
            ("Train Monthly Pass", 65.00, "Travel", "Debit Card", "Metro commuting pass"),
            ("Home Cleaning Supplies", 27.30, "Groceries", "Cash", "Detergent and cleaning tools"),
        ]

        today = datetime.now()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Add sample data spread across the last 60 days
            for i, (title, amount, category, method, notes) in enumerate(sample_expenses):
                days_ago = (i * 3) % 55
                item_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                cursor.execute("""
                    INSERT INTO expenses (title, amount, category, date, payment_method, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, amount, category, item_date, method, notes))
            
            # Set a sample budget for current month
            curr_month = today.strftime("%Y-%m-%d")[:7]
            cursor.execute("""
                INSERT OR IGNORE INTO budgets (month, budget_limit)
                VALUES (?, ?)
            """, (curr_month, 800.0))

            conn.commit()
