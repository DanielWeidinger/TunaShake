from dataclasses import dataclass
from datetime import datetime


@dataclass
class Course:
    id: int
    name: str


@dataclass
class Exercise:
    id: int
    course_id: int
    title: str
    solution_path: str | None = None
    source_path: str | None = None
    priority: int = 0


@dataclass
class Trial:
    id: int
    exercise_id: int
    grade: int
    timestamp: datetime
    note: str | None = None
