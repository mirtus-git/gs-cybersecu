"""gscs gui — launch the Tkinter GUI (lazy import)."""
from __future__ import annotations

from gscs.ui.console import error


def run() -> int:
    try:
        import tkinter  # noqa: F401 — check availability before importing app
    except ImportError:
        error(
            "Tkinter is not available on this system.\n"
            "Install it with: sudo apt install python3-tk  "
            "# or: sudo dnf install python3-tkinter"
        )
        return 1

    try:
        from gscs.ui.gui_app import launch
        launch()
        return 0
    except Exception as e:
        error(f"GUI failed to start: {e}")
        return 1
