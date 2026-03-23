"""CRUD operations for the script registry (stdlib sqlite3)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from gscs.core.database import get_conn
from gscs.core.models import Script


def add_script(script: Script) -> Script:
    """Persist a new script and rebuild its tag index."""
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO scripts
               (name, category, path, description, language, tags, dependencies,
                author, version, created_at, updated_at, sha256)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                script.name, script.category, script.path, script.description,
                script.language, script.tags, script.dependencies,
                script.author, script.version, now, now, script.sha256,
            ),
        )
        script.id = cur.lastrowid
        script.created_at = now
        script.updated_at = now
        _sync_tags(conn, script)
    return script


def get_script(name: str) -> Optional[Script]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM scripts WHERE name = ?", (name,)
        ).fetchone()
        return Script.from_row(tuple(row)) if row else None


def get_script_by_id(script_id: int) -> Optional[Script]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM scripts WHERE id = ?", (script_id,)
        ).fetchone()
        return Script.from_row(tuple(row)) if row else None


def list_scripts(category: Optional[str] = None) -> list[Script]:
    with get_conn() as conn:
        if category:
            rows = conn.execute(
                "SELECT * FROM scripts WHERE category = ? ORDER BY name", (category,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM scripts ORDER BY name").fetchall()
        return [Script.from_row(tuple(r)) for r in rows]


def update_script(name: str, **kwargs) -> Optional[Script]:
    now = datetime.now(timezone.utc).isoformat()
    kwargs["updated_at"] = now
    cols = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [name]
    with get_conn() as conn:
        conn.execute(f"UPDATE scripts SET {cols} WHERE name = ?", vals)
        row = conn.execute("SELECT * FROM scripts WHERE name = ?", (name,)).fetchone()
        if not row:
            return None
        script = Script.from_row(tuple(row))
        _sync_tags(conn, script)
    return script


def delete_script(name: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM scripts WHERE name = ?", (name,))
        return cur.rowcount > 0


def script_exists(name: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM scripts WHERE name = ?", (name,)
        ).fetchone()
        return row is not None


def _sync_tags(conn, script: Script) -> None:
    conn.execute("DELETE FROM tag_index WHERE script_id = ?", (script.id,))
    for tag in script.get_tags():
        conn.execute(
            "INSERT OR IGNORE INTO tag_index (script_id, tag) VALUES (?,?)",
            (script.id, tag.lower()),
        )
