import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Tuple, List

DEFAULT_CATEGORIES = [
    "Food",
    "Travel",
    "Bills",
    "Shopping",
    "Groceries",
    "Entertainment",
    "Health",
    "Education",
    "Other"
]

DEFAULT_PAYMENT_METHODS = [
    "Cash",
    "Credit Card",
    "Debit Card",
    "UPI / Online",
    "Bank Transfer",
    "Other"
]

@dataclass
class Expense:
    title: str
    amount: float
    category: str
    date: str  # Format: YYYY-MM-DD
    payment_method: str = "Cash"
    notes: str = ""
    id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # row: (id, title, amount, category, date, payment_method, notes, created_at)
        return cls(
            id=row[0],
            title=row[1],
            amount=float(row[2]),
            category=row[3],
            date=row[4],
            payment_method=row[5] if len(row) > 5 and row[5] else "Cash",
            notes=row[6] if len(row) > 6 and row[6] is not None else "",
            created_at=row[7] if len(row) > 7 else None
        )

def validate_expense_input(title: str, amount_str: str, category: str, date_str: str) -> Tuple[bool, str]:
    """Validates form input fields for expense entry."""
    if not title or not title.strip():
        return False, "Title cannot be empty."
    
    if len(title.strip()) > 100:
        return False, "Title must be under 100 characters."

    try:
        amount = float(amount_str)
        if amount <= 0:
            return False, "Amount must be a positive number greater than 0."
        if amount > 1_000_000_000:
            return False, "Amount exceeds maximum allowed limit."
    except ValueError:
        return False, "Amount must be a valid number (e.g. 25.50)."

    if not category or not category.strip():
        return False, "Category must be selected."

    if not date_str or not date_str.strip():
        return False, "Date cannot be empty."

    # Validate date format YYYY-MM-DD
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(date_pattern, date_str.strip()):
        return False, "Date must be in YYYY-MM-DD format (e.g. 2026-09-14)."

    try:
        datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        return False, "Invalid calendar date provided."

    return True, "Validation successful."
