import re

TITLE_RE = re.compile(r"^\d+\.\d+\.[a-zA-Z0-9]+$")


def validate_title(title: str) -> str:
    """Validate and return an exercise title in Sheet.Number.Subexercise format."""
    if not TITLE_RE.match(title):
        raise ValueError(
            f"Invalid title '{title}'. "
            "Expected Sheet.Number.Subexercise (e.g. '1.3.a', '4.12.b', '2.5.1')."
        )
    return title


def validate_grade(grade: int) -> int:
    """Validate that grade is an integer in [1, 5]."""
    if not isinstance(grade, int) or isinstance(grade, bool):
        raise TypeError(f"Grade must be an integer, got {type(grade).__name__}.")
    if not 1 <= grade <= 5:
        raise ValueError(f"Grade must be between 1 and 5, got {grade}.")
    return grade


def validate_course_name(name: str) -> str:
    """Validate that a course name is non-empty."""
    name = name.strip()
    if not name:
        raise ValueError("Course name must not be empty.")
    return name
