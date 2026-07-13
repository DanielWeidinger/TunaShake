import os
import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS courses (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS exercises (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id     INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title         TEXT    NOT NULL,
    solution_path TEXT,
    source_path   TEXT,
    priority      INTEGER NOT NULL DEFAULT 0,
    tag           TEXT,
    UNIQUE(course_id, title, tag)
);

CREATE TABLE IF NOT EXISTS trials (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    grade       INTEGER CHECK(grade IS NULL OR (grade >= 1 AND grade <= 5)),
    timestamp   TEXT    NOT NULL,
    note        TEXT
);
"""


def get_db_path() -> Path:
    """Return the database path, respecting TUNASHAKE_DB env override."""
    env = os.environ.get("TUNASHAKE_DB")
    if env:
        return Path(env)
    data_dir = Path.home() / ".local" / "share" / "tunashake"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "tunashake.db"


def get_connection() -> sqlite3.Connection:
    """Open (or create) the SQLite database, initialize schema, return connection."""
    path = get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    # Migrations: add columns that may not exist in older databases.
    for migration in [
        "ALTER TABLE exercises ADD COLUMN source_path TEXT",
        "ALTER TABLE exercises ADD COLUMN priority INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE exercises ADD COLUMN tag TEXT",
    ]:
        try:
            conn.execute(migration)
            conn.commit()
        except Exception:
            pass  # Column already exists.

    # Migration: trials.grade must allow NULL (for skipped exercises).
    # SQLite cannot ALTER TABLE to change a NOT NULL column, so we recreate.
    _migrate_trials_grade(conn)
    # Migration: exercises unique constraint must include tag so same-titled
    # exercises from different tags can coexist in one course.
    _migrate_exercises_unique(conn)

    return conn


def _migrate_exercises_unique(conn: sqlite3.Connection) -> None:
    """Widen the exercises UNIQUE constraint from (course_id, title) to
    (course_id, title, tag) so the same exercise number can appear in one
    course under different tags.
    """
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='exercises'"
    ).fetchone()
    if not row or not row["sql"]:
        return
    if "title, tag" in row["sql"]:
        return  # already migrated

    conn.execute(
        """
        CREATE TABLE __exercises_new (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id     INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            title         TEXT    NOT NULL,
            solution_path TEXT,
            source_path   TEXT,
            priority      INTEGER NOT NULL DEFAULT 0,
            tag           TEXT,
            UNIQUE(course_id, title, tag)
        )
        """
    )
    conn.execute(
        "INSERT INTO __exercises_new "
        "(id, course_id, title, solution_path, source_path, priority, tag) "
        "SELECT id, course_id, title, solution_path, source_path, priority, tag "
        "FROM exercises"
    )
    with conn:
        conn.execute("DROP TABLE exercises")
        conn.execute("ALTER TABLE __exercises_new RENAME TO exercises")


def _migrate_trials_grade(conn: sqlite3.Connection) -> None:
    """Recreate trials table to allow NULL grade (for skipped entries).

    Older schemas have ``grade INTEGER NOT NULL CHECK(grade >= 1 AND grade <= 5)``.
    We need to change it to allow NULL so skipped entries can be stored.
    Since SQLite does not support ALTER COLUMN, we recreate the table.
    """
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='trials'"
    ).fetchone()
    if not row or not row["sql"]:
        return

    sql = row["sql"]
    grade_part = sql.split("grade")[1].split(",")[0]
    if "NOT NULL" not in grade_part:
        return

    conn.execute(
        """
        CREATE TABLE __trials_new (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
            grade       INTEGER CHECK(grade IS NULL OR (grade >= 1 AND grade <= 5)),
            timestamp   TEXT    NOT NULL,
            note        TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO __trials_new (id, exercise_id, grade, timestamp, note) "
        "SELECT id, exercise_id, grade, timestamp, note FROM trials"
    )
    with conn:
        conn.execute("DROP TABLE trials")
        conn.execute("ALTER TABLE __trials_new RENAME TO trials")
