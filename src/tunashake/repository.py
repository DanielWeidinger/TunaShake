import sqlite3
from datetime import datetime, timezone
from typing import Optional

from tunashake.models import Course, Exercise, Trial


# ── helpers ────────────────────────────────────────────────────────────────────

def _row_to_course(row: sqlite3.Row) -> Course:
    return Course(id=row["id"], name=row["name"])


def _row_to_exercise(row: sqlite3.Row) -> Exercise:
    return Exercise(
        id=row["id"],
        course_id=row["course_id"],
        title=row["title"],
        solution_path=row["solution_path"],
        source_path=row["source_path"],
        priority=row["priority"],
        tag=row["tag"],
    )


def _row_to_trial(row: sqlite3.Row) -> Trial:
    return Trial(
        id=row["id"],
        exercise_id=row["exercise_id"],
        grade=row["grade"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        note=row["note"],
    )


# ── courses ────────────────────────────────────────────────────────────────────

def create_course(conn: sqlite3.Connection, name: str) -> Course:
    cur = conn.execute("INSERT INTO courses (name) VALUES (?)", (name,))
    conn.commit()
    return Course(id=cur.lastrowid, name=name)


def get_course_by_name(conn: sqlite3.Connection, name: str) -> Optional[Course]:
    row = conn.execute(
        "SELECT id, name FROM courses WHERE name = ?", (name,)
    ).fetchone()
    return _row_to_course(row) if row else None


def list_courses(conn: sqlite3.Connection) -> list[Course]:
    rows = conn.execute("SELECT id, name FROM courses ORDER BY name").fetchall()
    return [_row_to_course(r) for r in rows]


# ── exercises ──────────────────────────────────────────────────────────────────

def create_exercise(
    conn: sqlite3.Connection,
    course_id: int,
    title: str,
    solution_path: Optional[str] = None,
    source_path: Optional[str] = None,
    priority: int = 0,
    tag: Optional[str] = None,
) -> Exercise:
    cur = conn.execute(
        "INSERT INTO exercises (course_id, title, solution_path, source_path, priority, tag) VALUES (?, ?, ?, ?, ?, ?)",
        (course_id, title, solution_path, source_path, priority, tag),
    )
    conn.commit()
    return Exercise(id=cur.lastrowid, course_id=course_id, title=title, solution_path=solution_path, source_path=source_path, priority=priority, tag=tag)


def get_exercise(
    conn: sqlite3.Connection, course_id: int, title: str, tag: Optional[str] = None
) -> Optional[Exercise]:
    query = (
        "SELECT id, course_id, title, solution_path, source_path, priority, tag FROM exercises "
        "WHERE course_id = ? AND title = ?"
    )
    params: list = [course_id, title]
    if tag is not None:
        query += " AND tag = ?"
        params.append(tag)
    row = conn.execute(query, params).fetchone()
    return _row_to_exercise(row) if row else None


def list_exercises(
    conn: sqlite3.Connection,
    course_id: int,
    tag: Optional[str] = None,
    pattern: Optional[str] = None,
) -> list[Exercise]:
    query = "SELECT id, course_id, title, solution_path, source_path, priority, tag FROM exercises WHERE course_id = ?"
    params: list = [course_id]
    if tag is not None:
        query += " AND tag = ?"
        params.append(tag)
    if pattern is not None:
        query += " AND title LIKE ?"
        params.append(pattern)
    query += " ORDER BY title"
    rows = conn.execute(query, params).fetchall()
    return [_row_to_exercise(r) for r in rows]


def set_exercise_priority(
    conn: sqlite3.Connection, exercise_id: int, priority: int
) -> None:
    conn.execute(
        "UPDATE exercises SET priority = ? WHERE id = ?",
        (priority, exercise_id),
    )
    conn.commit()


def set_exercise_source(
    conn: sqlite3.Connection, exercise_id: int, source_path: str
) -> None:
    conn.execute(
        "UPDATE exercises SET source_path = ? WHERE id = ?",
        (source_path, exercise_id),
    )
    conn.commit()


def set_exercise_solution(
    conn: sqlite3.Connection, exercise_id: int, solution_path: str
) -> None:
    conn.execute(
        "UPDATE exercises SET solution_path = ? WHERE id = ?",
        (solution_path, exercise_id),
    )
    conn.commit()


def set_exercise_tag(
    conn: sqlite3.Connection, exercise_id: int, tag: Optional[str]
) -> None:
    conn.execute(
        "UPDATE exercises SET tag = ? WHERE id = ?",
        (tag, exercise_id),
    )
    conn.commit()


# ── trials ─────────────────────────────────────────────────────────────────────

def create_trial(
    conn: sqlite3.Connection,
    exercise_id: int,
    grade: int | None,
    note: Optional[str] = None,
) -> Trial:
    ts = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO trials (exercise_id, grade, timestamp, note) VALUES (?, ?, ?, ?)",
        (exercise_id, grade, ts, note),
    )
    conn.commit()
    return Trial(
        id=cur.lastrowid,
        exercise_id=exercise_id,
        grade=grade,
        timestamp=datetime.fromisoformat(ts),
        note=note,
    )


def get_trials_for_exercise(
    conn: sqlite3.Connection, exercise_id: int
) -> list[Trial]:
    rows = conn.execute(
        "SELECT id, exercise_id, grade, timestamp, note FROM trials "
        "WHERE exercise_id = ? ORDER BY timestamp",
        (exercise_id,),
    ).fetchall()
    return [_row_to_trial(r) for r in rows]


def get_trials_for_course(
    conn: sqlite3.Connection, course_id: int
) -> dict[int, list[Trial]]:
    """Return {exercise_id: [Trial, ...]} for every exercise in the course."""
    rows = conn.execute(
        """
        SELECT t.id, t.exercise_id, t.grade, t.timestamp, t.note
        FROM   trials t
        JOIN   exercises e ON e.id = t.exercise_id
        WHERE  e.course_id = ?
        ORDER  BY t.timestamp
        """,
        (course_id,),
    ).fetchall()
    result: dict[int, list[Trial]] = {}
    for r in rows:
        result.setdefault(r["exercise_id"], []).append(_row_to_trial(r))
    return result
