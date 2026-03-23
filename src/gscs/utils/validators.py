"""Input validation and sanitization helpers."""
from __future__ import annotations

import re
from pathlib import Path


_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+$")
_MAX_NAME_LEN = 128


class ValidationError(ValueError):
    pass


def sanitize_script_name(name: str) -> str:
    """Validate and normalize a script name."""
    name = name.strip()
    if not name:
        raise ValidationError("Script name cannot be empty.")
    if len(name) > _MAX_NAME_LEN:
        raise ValidationError(f"Script name too long (max {_MAX_NAME_LEN} chars).")
    if not _SAFE_NAME_RE.match(name):
        raise ValidationError(
            f"Invalid script name '{name}'. "
            "Only alphanumeric, hyphens, underscores, and dots are allowed."
        )
    return name.lower()


def validate_path(path_str: str) -> Path:
    """Validate that a script path is absolute, exists, and is not a directory."""
    path = Path(path_str).resolve()
    if not path.exists():
        raise ValidationError(f"Path does not exist: {path}")
    if path.is_dir():
        raise ValidationError(f"Path is a directory, not a file: {path}")
    # Prevent path traversal tricks
    try:
        path.relative_to("/")  # Ensures absolute path on Linux
    except ValueError:
        raise ValidationError(f"Invalid path: {path}")
    return path


def validate_category(category: str, allowed: list[str]) -> str:
    """Validate that the category is in the allowed list."""
    category = category.lower().strip()
    if category not in [c.lower() for c in allowed]:
        raise ValidationError(
            f"Unknown category '{category}'. Allowed: {', '.join(allowed)}"
        )
    return category


def sanitize_tags(tags_str: str) -> list[str]:
    """Parse and sanitize a comma-separated tags string."""
    tags = []
    for tag in tags_str.split(","):
        tag = tag.strip().lower()
        if tag and _SAFE_NAME_RE.match(tag):
            tags.append(tag)
    return tags
