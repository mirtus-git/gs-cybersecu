"""
Terminal output helpers. Rich is used when installed; plain text otherwise.
Install rich for pretty output: pip install gs-cybersecu[rich]
"""
from __future__ import annotations

try:
    from rich.console import Console as _RichConsole
    from rich.theme import Theme as _Theme

    _theme = _Theme({
        "info": "cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "muted": "dim white",
        "highlight": "bold magenta",
    })
    console = _RichConsole(theme=_theme)
    HAS_RICH = True

except ImportError:
    HAS_RICH = False

    class _PlainConsole:
        """Minimal Rich-compatible console backed by plain print."""

        def print(self, *args, **kwargs) -> None:
            # Strip Rich markup tags [bold red]...[/]
            import re
            text = " ".join(str(a) for a in args)
            text = re.sub(r"\[/?[^\]]*\]", "", text)
            end = kwargs.get("end", "\n")
            print(text, end=end)

        def rule(self, title: str = "", **kwargs) -> None:
            print(f"\n{'─' * 20} {title} {'─' * 20}")

        def print_json(self, data: str) -> None:
            print(data)

    console = _PlainConsole()


def success(msg: str) -> None:
    console.print(f"[success]✓[/] {msg}" if HAS_RICH else f"[OK] {msg}")


def error(msg: str) -> None:
    console.print(f"[error]✗[/] {msg}" if HAS_RICH else f"[ERROR] {msg}")


def warn(msg: str) -> None:
    console.print(f"[warning]![/] {msg}" if HAS_RICH else f"[WARN] {msg}")


def info(msg: str) -> None:
    console.print(f"[info]i[/] {msg}" if HAS_RICH else f"[INFO] {msg}")
