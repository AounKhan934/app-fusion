"""
Centralized input validation.
Keeping validation separate (instead of scattered inside the GUI code)
is a common production pattern — one place to fix, one place to test.
"""


from datetime import datetime


class ValidationError(Exception):
    pass


def validate_roll_no(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValidationError("Roll No cannot be empty.")
    return value


def validate_name(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValidationError("Name cannot be empty.")
    if any(ch.isdigit() for ch in value):
        raise ValidationError("Name should not contain numbers.")
    return value


def validate_age(value: str) -> int:
    try:
        age = int(value)
    except ValueError:
        raise ValidationError("Age must be a whole number.")
    if not (1 <= age <= 100):
        raise ValidationError("Age must be between 1 and 100.")
    return age


def validate_department(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValidationError("Department cannot be empty.")
    return value


def validate_cgpa(value: str) -> float:
    try:
        cgpa = float(value)
    except ValueError:
        raise ValidationError("CGPA must be a number.")
    if not (0.0 <= cgpa <= 4.0):
        raise ValidationError("CGPA must be between 0.0 and 4.0.")
    return cgpa


def validate_credit_hours(value: str) -> int:
    try:
        hours = int(value)
    except ValueError:
        raise ValidationError("Credit Hours must be a whole number.")
    if not (1 <= hours <= 6):
        raise ValidationError("Credit Hours must be between 1 and 6.")
    return hours


def validate_date(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValidationError("Date cannot be empty.")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValidationError("Date must be in YYYY-MM-DD format.")
    return value
