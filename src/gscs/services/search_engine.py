"""Advanced search engine using raw SQL (no ORM)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from gscs.core.database import get_conn
from gscs.core.models import Script


@dataclass
class SearchFilter:
    keyword: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = field(default_factory=list)  # AND semantics
    language: Optional[str] = None
    created_after: Optional[date] = None
    created_before: Optional[date] = None
    has_dep: Optional[str] = None
    author: Optional[str] = None
    limit: int = 100


def search(f: SearchFilter) -> list[Script]:
    """Execute a filtered search and return matched scripts."""
    conditions: list[str] = []
    params: list = []

    if f.category:
        conditions.append("s.category = ?")
        params.append(f.category)

    if f.language:
        conditions.append("s.language = ?")
        params.append(f.language)

    if f.keyword:
        kw = f"%{f.keyword.lower()}%"
        conditions.append("(LOWER(s.name) LIKE ? OR LOWER(s.description) LIKE ?)")
        params.extend([kw, kw])

    if f.created_after:
        conditions.append("s.created_at >= ?")
        params.append(f.created_after.isoformat())

    if f.created_before:
        conditions.append("s.created_at <= ?")
        params.append(f.created_before.isoformat() + "T23:59:59")

    if f.has_dep:
        conditions.append("LOWER(s.dependencies) LIKE ?")
        params.append(f"%{f.has_dep.lower()}%")

    if f.author:
        conditions.append("LOWER(s.author) LIKE ?")
        params.append(f"%{f.author.lower()}%")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT s.* FROM scripts s {where} ORDER BY s.name LIMIT ?"
    params.append(f.limit)

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        results = [Script.from_row(tuple(r)) for r in rows]

        # Tag filtering (AND semantics via tag_index)
        if f.tags:
            required = {t.lower() for t in f.tags}
            filtered = []
            for script in results:
                script_tags = {
                    row[0]
                    for row in conn.execute(
                        "SELECT tag FROM tag_index WHERE script_id = ?", (script.id,)
                    ).fetchall()
                }
                if required.issubset(script_tags):
                    filtered.append(script)
            return filtered

        return results
