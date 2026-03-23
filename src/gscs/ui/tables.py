"""Table formatters. Rich tables when available, plain ASCII fallback."""
from __future__ import annotations

from gscs.core.models import ExecutionLog, Script
from gscs.services.dep_checker import DepReport
from gscs.ui.console import HAS_RICH, console

_CATEGORY_COLORS = {
    "recon": "blue",
    "exploit": "red",
    "post-exploit": "yellow",
    "forensic": "green",
    "custom": "magenta",
}


def print_scripts(scripts: list[Script], show_integrity: bool = False) -> None:
    if HAS_RICH:
        _rich_scripts(scripts, show_integrity)
    else:
        _plain_scripts(scripts, show_integrity)


def print_logs(logs: list[ExecutionLog]) -> None:
    if HAS_RICH:
        _rich_logs(logs)
    else:
        _plain_logs(logs)


def print_dep_report(report: DepReport) -> None:
    if HAS_RICH:
        _rich_dep_report(report)
    else:
        _plain_dep_report(report)


# ─── Rich renderers ────────────────────────────────────────────────────────────

def _rich_scripts(scripts: list[Script], show_integrity: bool) -> None:
    from rich.table import Table
    from rich.text import Text

    t = Table(
        show_header=True, header_style="bold cyan", border_style="dim",
        title=f"[bold]{len(scripts)} script(s)[/]",
    )
    t.add_column("Name", style="bold white", no_wrap=True)
    t.add_column("Category", no_wrap=True)
    t.add_column("Lang", no_wrap=True)
    t.add_column("Description")
    t.add_column("Tags", style="dim")
    t.add_column("Created", style="dim", no_wrap=True)
    if show_integrity:
        t.add_column("Hash", no_wrap=True)

    for s in scripts:
        color = _CATEGORY_COLORS.get(s.category, "white")
        row = [
            s.name,
            Text(s.category, style=color),
            s.language,
            s.description[:60] + ("…" if len(s.description) > 60 else ""),
            s.tags or "—",
            s.created_at[:10],
        ]
        if show_integrity:
            from gscs.utils.hash import verify_integrity
            ok = verify_integrity(s)
            row.append(Text("ok", style="green") if ok else Text("FAIL", style="bold red"))
        t.add_row(*[str(r) if not isinstance(r, Text) else r for r in row])
    console.print(t)


def _rich_logs(logs: list[ExecutionLog]) -> None:
    from rich.table import Table
    from rich.text import Text

    t = Table(
        show_header=True, header_style="bold cyan", border_style="dim",
        title=f"[bold]{len(logs)} execution(s)[/]",
    )
    t.add_column("#", style="dim", no_wrap=True)
    t.add_column("Script", style="bold white", no_wrap=True)
    t.add_column("Date", no_wrap=True)
    t.add_column("Sandbox", no_wrap=True)
    t.add_column("Exit", no_wrap=True)
    t.add_column("Duration", no_wrap=True)
    t.add_column("Args", style="dim")

    for log in logs:
        exit_t = (
            Text("0 ✓", style="green") if log.success
            else Text(f"{log.exit_code} ✗", style="red")
        )
        t.add_row(
            str(log.id), log.script_name, log.executed_at[:16],
            log.sandbox_mode, exit_t, f"{log.duration_seconds:.2f}s",
            " ".join(log.get_args()) or "—",
        )
    console.print(t)


def _rich_dep_report(report: DepReport) -> None:
    from rich.table import Table
    from rich.text import Text

    t = Table(show_header=True, header_style="bold cyan", border_style="dim")
    t.add_column("Dependency")
    t.add_column("Status", no_wrap=True)
    for dep in report.satisfied:
        t.add_row(dep, Text("ok", style="green"))
    for dep in report.missing:
        t.add_row(dep, Text("MISSING", style="bold red"))
    for dep in report.optional_missing:
        t.add_row(dep, Text("optional/missing", style="yellow"))
    console.print(t)


# ─── Plain ASCII fallbacks ─────────────────────────────────────────────────────

def _plain_scripts(scripts: list[Script], show_integrity: bool) -> None:
    print(f"\n{'Scripts':=<60}")
    header = f"{'NAME':<25} {'CAT':<14} {'LANG':<8} {'DESCRIPTION':<35}"
    if show_integrity:
        header += " HASH"
    print(header)
    print("-" * len(header))
    for s in scripts:
        row = f"{s.name:<25} {s.category:<14} {s.language:<8} {s.description[:35]:<35}"
        if show_integrity:
            from gscs.utils.hash import verify_integrity
            row += " OK" if verify_integrity(s) else " FAIL"
        print(row)
    print(f"Total: {len(scripts)}\n")


def _plain_logs(logs: list[ExecutionLog]) -> None:
    print(f"\n{'Execution Logs':=<70}")
    for log in logs:
        status = "OK" if log.success else f"FAIL({log.exit_code})"
        print(
            f"[{log.executed_at[:16]}] {log.script_name:<25} "
            f"{status:<10} {log.sandbox_mode:<10} {log.duration_seconds:.2f}s"
        )
    print()


def _plain_dep_report(report: DepReport) -> None:
    print(f"\n{'Dependency Check':=<40}")
    for d in report.satisfied:
        print(f"  [OK]      {d}")
    for d in report.missing:
        print(f"  [MISSING] {d}")
    for d in report.optional_missing:
        print(f"  [OPT]     {d}")
    print()
