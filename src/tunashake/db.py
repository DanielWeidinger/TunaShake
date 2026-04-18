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
    UNIQUE(course_id, title)
);

CREATE TABLE IF NOT EXISTS trials (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    grade       INTEGER NOT NULL CHECK(grade >= 1 AND grade <= 5),
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
    return conn
