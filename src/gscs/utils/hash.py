"""SHA256 integrity fingerprinting for registered scripts."""
from __future__ import annotations

import hashlib
from pathlib import Path

from gscs.core.models import Script


def compute_sha256(path: str | Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_integrity(script: Script) -> bool:
    """Return True if script file matches its registered SHA256."""
    if not script.sha256:
        return True  # No hash registered → skip check
    try:
        current = compute_sha256(script.path)
        return current == script.sha256
    except (FileNotFoundError, PermissionError):
        return False
