"""
Student model — represents a single student record.
Keeping this as a plain data class (encapsulation) separates the
"what a student IS" from "how students are stored/managed".
"""

from dataclasses import dataclass


@dataclass
class Student:
    roll_no: str
    name: str
    age: int
    department: str
    cgpa: float

    def to_tuple(self) -> tuple:
        """Convert to a tuple in the exact column order of the DB table."""
        return (self.roll_no, self.name, self.age, self.department, self.cgpa)

    @staticmethod
    def from_row(row: tuple) -> "Student":
        """Build a Student object back from a DB row."""
        return Student(
            roll_no=row[0],
            name=row[1],
            age=row[2],
            department=row[3],
            cgpa=row[4],
        )

    def __str__(self) -> str:
        return (
            f"[{self.roll_no}] {self.name} | {self.department} "
            f"| Age: {self.age} | CGPA: {self.cgpa}"
        )
