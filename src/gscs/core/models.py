"""Data models using stdlib dataclasses (no external ORM needed)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


class Category:
    RECON = "recon"
    EXPLOIT = "exploit"
    POST_EXPLOIT = "post-exploit"
    FORENSIC = "forensic"
    CUSTOM = "custom"

    ALL = [RECON, EXPLOIT, POST_EXPLOIT, FORENSIC, CUSTOM]


class Language:
    PYTHON = "python"
    BASH = "bash"
    GO = "go"
    RUBY = "ruby"
    PERL = "perl"
    OTHER = "other"

    ALL = [PYTHON, BASH, GO, RUBY, PERL, OTHER]


@dataclass
class Script:
    name: str
    category: str
    path: str
    id: Optional[int] = None
    description: str = ""
    language: str = Language.OTHER
    tags: str = ""          # Comma-separated for display
    dependencies: str = "[]"  # JSON array
    author: str = ""
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sha256: str = ""

    def get_dependencies(self) -> list[str]:
        try:
            return json.loads(self.dependencies)
        except (json.JSONDecodeError, TypeError):
            return []

    def get_tags(self) -> list[str]:
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def set_dependencies(self, deps: list[str]) -> None:
        self.dependencies = json.dumps(deps)

    def set_tags(self, tags: list[str]) -> None:
        self.tags = ", ".join(tags)

    @classmethod
    def from_row(cls, row: tuple) -> "Script":
        """Build from a sqlite3 row (ordered by DB column order)."""
        return cls(
            id=row[0],
            name=row[1],
            category=row[2],
            path=row[3],
            description=row[4] or "",
            language=row[5] or Language.OTHER,
            tags=row[6] or "",
            dependencies=row[7] or "[]",
            author=row[8] or "",
            version=row[9] or "1.0.0",
            created_at=row[10] or datetime.now(timezone.utc).isoformat(),
            updated_at=row[11] or datetime.now(timezone.utc).isoformat(),
            sha256=row[12] or "",
        )


@dataclass
class ExecutionLog:
    script_name: str
    id: Optional[int] = None
    script_id: Optional[int] = None
    executed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    args_used: str = "[]"   # JSON array
    sandbox_mode: str = "none"
    exit_code: int = 0
    success: bool = True
    duration_seconds: float = 0.0
    notes: str = ""

    def get_args(self) -> list[str]:
        try:
            return json.loads(self.args_used)
        except (json.JSONDecodeError, TypeError):
            return []

    @classmethod
    def from_row(cls, row: tuple) -> "ExecutionLog":
        return cls(
            id=row[0],
            script_id=row[1],
            script_name=row[2] or "",
            executed_at=row[3] or datetime.now(timezone.utc).isoformat(),
            args_used=row[4] or "[]",
            sandbox_mode=row[5] or "none",
            exit_code=row[6] or 0,
            success=bool(row[7]),
            duration_seconds=float(row[8] or 0.0),
            notes=row[9] or "",
        )
