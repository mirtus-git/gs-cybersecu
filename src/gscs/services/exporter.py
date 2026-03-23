"""Export and import the script library as a portable JSON archive."""
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from gscs import __version__
from gscs.core.models import Script

_ARCHIVE_VERSION = "1"


def export_library(
    scripts: list[Script],
    include_content: bool = True,
) -> str:
    """Serialize scripts (and optionally their file content) to a JSON string."""
    entries = []
    for s in scripts:
        entry: dict = {
            "name": s.name,
            "category": s.category,
            "path": s.path,
            "description": s.description,
            "language": s.language,
            "tags": s.tags,
            "dependencies": s.dependencies,
            "author": s.author,
            "version": s.version,
            "sha256": s.sha256,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        if include_content:
            try:
                raw = Path(s.path).read_bytes()
                entry["content_b64"] = base64.b64encode(raw).decode()
            except (FileNotFoundError, PermissionError) as exc:
                entry["content_b64"] = None
                entry["content_error"] = str(exc)
        entries.append(entry)

    archive = {
        "gscs_archive_version": _ARCHIVE_VERSION,
        "gscs_version": __version__,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "script_count": len(entries),
        "scripts": entries,
    }
    return json.dumps(archive, indent=2, ensure_ascii=False)


def import_library(
    json_text: str,
    scripts_dir: Path,
    skip_existing: bool = False,
    restore_files: bool = True,
) -> tuple[list[Script], list[str]]:
    """
    Parse an archive and return (scripts_to_add, warnings).

    Does NOT persist to the database — the caller must call registry.add_script().
    If restore_files=True, script files are written to scripts_dir when content_b64 is present.
    """
    try:
        archive = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid archive format: {exc}") from exc

    if archive.get("gscs_archive_version") != _ARCHIVE_VERSION:
        raise ValueError(
            f"Unsupported archive version: {archive.get('gscs_archive_version')!r}. "
            f"Expected '{_ARCHIVE_VERSION}'."
        )

    warnings: list[str] = []
    scripts: list[Script] = []

    for entry in archive.get("scripts", []):
        name = entry.get("name", "").strip()
        if not name:
            warnings.append("Skipped entry with missing name.")
            continue

        # Resolve file path: restore content or keep original path
        script_path = entry.get("path", "")
        content_b64 = entry.get("content_b64")

        if restore_files and content_b64:
            lang = entry.get("language", "other")
            ext = _lang_ext(lang)
            dest = scripts_dir / f"{name}{ext}"
            try:
                scripts_dir.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(base64.b64decode(content_b64))
                if lang in ("bash", "python", "perl", "ruby"):
                    import os
                    os.chmod(dest, 0o755)
                script_path = str(dest)
            except Exception as exc:
                warnings.append(f"'{name}': could not restore file — {exc}. Using original path.")
        elif not Path(script_path).exists():
            warnings.append(
                f"'{name}': original file not found at {script_path}. "
                "Import without --restore-files may require manual path fix."
            )

        s = Script(
            name=name,
            category=entry.get("category", "custom"),
            path=script_path,
            description=entry.get("description", ""),
            language=entry.get("language", "other"),
            tags=entry.get("tags", ""),
            dependencies=entry.get("dependencies", "[]"),
            author=entry.get("author", ""),
            version=entry.get("version", "1.0.0"),
            sha256=entry.get("sha256", ""),
        )
        scripts.append(s)

    return scripts, warnings


def _lang_ext(language: str) -> str:
    return {
        "python": ".py",
        "bash": ".sh",
        "ruby": ".rb",
        "perl": ".pl",
        "go": "",
    }.get(language, ".sh")
