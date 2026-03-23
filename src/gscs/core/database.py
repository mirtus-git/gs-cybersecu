"""SQLite database management using stdlib sqlite3 (zero external deps)."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

_db_path: Path | None = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS scripts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    category    TEXT NOT NULL,
    path        TEXT NOT NULL,
    description TEXT DEFAULT '',
    language    TEXT DEFAULT 'other',
    tags        TEXT DEFAULT '',
    dependencies TEXT DEFAULT '[]',
    author      TEXT DEFAULT '',
    version     TEXT DEFAULT '1.0.0',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    sha256      TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS execution_logs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id        INTEGER REFERENCES scripts(id) ON DELETE SET NULL,
    script_name      TEXT NOT NULL,
    executed_at      TEXT NOT NULL,
    args_used        TEXT DEFAULT '[]',
    sandbox_mode     TEXT DEFAULT 'none',
    exit_code        INTEGER DEFAULT 0,
    success          INTEGER DEFAULT 1,
    duration_seconds REAL DEFAULT 0.0,
    notes            TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS tag_index (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER REFERENCES scripts(id) ON DELETE CASCADE,
    tag       TEXT NOT NULL,
    UNIQUE(script_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_scripts_category ON scripts(category);
CREATE INDEX IF NOT EXISTS idx_scripts_name ON scripts(name);
CREATE INDEX IF NOT EXISTS idx_tag_index_tag ON tag_index(tag);
CREATE INDEX IF NOT EXISTS idx_logs_script_name ON execution_logs(script_name);
"""


def init_db(db_path: Path) -> None:
    """Initialize database and create schema."""
    global _db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _db_path = db_path
    with _connect() as conn:
        conn.executescript(_SCHEMA)


def get_db_path() -> Path:
    if _db_path is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db_path


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for auto-commit/rollback database connections."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
