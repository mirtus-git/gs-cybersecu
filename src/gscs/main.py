"""
GS-CYBERsecu CLI entry point.
Uses stdlib argparse — zero external dependencies required.
"""
from __future__ import annotations

import argparse
import sys

from gscs import __version__
from gscs.core.config import load_config
from gscs.core.database import init_db
from gscs.ui.console import error


def _init() -> None:
    """Initialize DB and config on every CLI invocation."""
    cfg = load_config()
    init_db(cfg.storage.db_path)
    # Set up file logger
    from gscs.services.logger import setup_file_logger
    setup_file_logger(cfg.storage.logs_dir)
    # Purge old logs if retention is set
    from gscs.services.logger import purge_old_logs
    if cfg.storage.log_retention_days > 0:
        purge_old_logs(cfg.storage.log_retention_days)


def _cmd_add(args: argparse.Namespace) -> int:
    from gscs.commands.add import run
    return run(args)


def _cmd_search(args: argparse.Namespace) -> int:
    from gscs.commands.search import run
    return run(args)


def _cmd_run(args: argparse.Namespace) -> int:
    from gscs.commands.run import run
    return run(args)


def _cmd_list(args: argparse.Namespace) -> int:
    from gscs.services.registry import list_scripts
    from gscs.ui.tables import print_scripts
    import json

    scripts = list_scripts(category=args.category if args.category != "all" else None)
    if args.format == "json":
        print(json.dumps(
            [{"name": s.name, "category": s.category, "language": s.language,
              "description": s.description, "tags": s.get_tags(), "path": s.path}
             for s in scripts],
            indent=2,
        ))
    else:
        print_scripts(scripts)
    return 0


def _cmd_history(args: argparse.Namespace) -> int:
    from gscs.commands.history import run
    return run(args)


def _cmd_deps(args: argparse.Namespace) -> int:
    from gscs.commands.deps import run
    return run(args)


def _cmd_remove(args: argparse.Namespace) -> int:
    from gscs.services.registry import delete_script, script_exists
    from gscs.ui.console import success, warn

    if not script_exists(args.name):
        error(f"Script '{args.name}' not found.")
        return 1
    if not args.force:
        confirm = input(f"Delete '{args.name}'? [y/N] ").strip().lower()
        if confirm != "y":
            warn("Aborted.")
            return 0
    delete_script(args.name)
    success(f"Script '{args.name}' deleted.")
    return 0


def _cmd_info(args: argparse.Namespace) -> int:
    from gscs.services.registry import get_script
    from gscs.ui.console import console, error

    s = get_script(args.name)
    if not s:
        error(f"Script '{args.name}' not found.")
        return 1
    from gscs.utils.hash import verify_integrity
    integrity = "ok" if verify_integrity(s) else "FAIL"
    console.print(
        f"\n[bold]{s.name}[/]\n"
        f"  Category:     {s.category}\n"
        f"  Language:     {s.language}\n"
        f"  Description:  {s.description or '—'}\n"
        f"  Author:       {s.author or '—'}\n"
        f"  Version:      {s.version}\n"
        f"  Tags:         {s.tags or '—'}\n"
        f"  Dependencies: {', '.join(s.get_dependencies()) or '—'}\n"
        f"  Path:         {s.path}\n"
        f"  SHA256:       {s.sha256 or '—'}\n"
        f"  Integrity:    {integrity}\n"
        f"  Created:      {s.created_at[:10]}\n"
        f"  Updated:      {s.updated_at[:10]}\n"
    )
    return 0


def _cmd_gui(_args: argparse.Namespace) -> int:
    from gscs.commands.gui import run
    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gscs",
        description="GS-CYBERsecu — Cybersecurity script manager for Linux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  gscs add /opt/scripts/recon.py -c recon -t "nmap,port-scan" -d "Fast port scanner"
  gscs search nmap --category recon
  gscs run recon --args "-t 192.168.1.0/24"
  gscs list --category exploit
  gscs history --last 20
  gscs deps check recon
  gscs gui
        """,
    )
    parser.add_argument("--version", action="version", version=f"gscs {__version__}")

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── add ──────────────────────────────────────────────────────────────────
    p_add = sub.add_parser("add", help="Register a script into the library")
    p_add.add_argument("path", help="Path to the script file")
    p_add.add_argument("-n", "--name", help="Script name (default: filename stem)")
    p_add.add_argument("-c", "--category", default="custom",
                       choices=["recon", "exploit", "post-exploit", "forensic", "custom"],
                       help="Script category")
    p_add.add_argument("-l", "--lang", default="other",
                       choices=["python", "bash", "go", "ruby", "perl", "other"],
                       help="Script language")
    p_add.add_argument("-t", "--tags", default="", help="Comma-separated tags")
    p_add.add_argument("-d", "--desc", default="", help="Short description")
    p_add.add_argument("--deps", default="", help="Comma-separated dependencies")
    p_add.add_argument("-a", "--author", default="")
    p_add.add_argument("-u", "--update", action="store_true", help="Update if exists")
    p_add.add_argument("--no-hash", action="store_true", help="Skip SHA256 fingerprinting")
    p_add.set_defaults(func=_cmd_add)

    # ── search ────────────────────────────────────────────────────────────────
    p_search = sub.add_parser("search", help="Search scripts with advanced filters")
    p_search.add_argument("keyword", nargs="?", help="Keyword (name/description)")
    p_search.add_argument("-c", "--category")
    p_search.add_argument("-t", "--tag", action="append", dest="tags", metavar="TAG",
                          help="Filter by tag (repeatable, AND logic)")
    p_search.add_argument("-l", "--lang", dest="language")
    p_search.add_argument("--after", help="Created after YYYY-MM-DD")
    p_search.add_argument("--before", help="Created before YYYY-MM-DD")
    p_search.add_argument("--dep", help="Filter by dependency name")
    p_search.add_argument("--author")
    p_search.add_argument("-f", "--format", choices=["table", "json"], default="table")
    p_search.add_argument("--limit", type=int, default=100)
    p_search.set_defaults(func=_cmd_search)

    # ── run ───────────────────────────────────────────────────────────────────
    p_run = sub.add_parser("run", help="Execute a script safely")
    p_run.add_argument("name", help="Script name")
    p_run.add_argument("--args", default="", help="Arguments to pass to the script")
    p_run.add_argument("--sandbox", choices=["auto", "firejail", "docker", "none"],
                       default=None, help="Override sandbox backend")
    p_run.add_argument("--dry-run", action="store_true", help="Show command without executing")
    p_run.add_argument("--force", action="store_true", help="Run without sandbox (no prompt)")
    p_run.set_defaults(func=_cmd_run)

    # ── list ──────────────────────────────────────────────────────────────────
    p_list = sub.add_parser("list", help="List all registered scripts")
    p_list.add_argument("-c", "--category", default=None,
                        choices=["recon", "exploit", "post-exploit", "forensic", "custom", "all"])
    p_list.add_argument("-f", "--format", choices=["table", "json"], default="table")
    p_list.set_defaults(func=_cmd_list)

    # ── history ───────────────────────────────────────────────────────────────
    p_hist = sub.add_parser("history", help="View execution history")
    p_hist.add_argument("--script", help="Filter by script name")
    p_hist.add_argument("--last", type=int, default=None, metavar="N", help="Show last N entries")
    p_hist.add_argument("--export", choices=["json", "csv"], metavar="FORMAT",
                        help="Export logs to file")
    p_hist.add_argument("--output", default=None, help="Output file path (default: stdout)")
    p_hist.set_defaults(func=_cmd_history)

    # ── deps ──────────────────────────────────────────────────────────────────
    p_deps = sub.add_parser("deps", help="Check or install script dependencies")
    deps_sub = p_deps.add_subparsers(dest="deps_cmd", metavar="<action>")
    deps_sub.required = True
    p_deps_check = deps_sub.add_parser("check", help="Check dependencies for a script")
    p_deps_check.add_argument("name", help="Script name")
    p_deps_install = deps_sub.add_parser("install", help="Show install commands for missing deps")
    p_deps_install.add_argument("name", help="Script name")
    p_deps.set_defaults(func=_cmd_deps)

    # ── remove ────────────────────────────────────────────────────────────────
    p_rm = sub.add_parser("remove", help="Remove a script from the library", aliases=["rm"])
    p_rm.add_argument("name", help="Script name")
    p_rm.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    p_rm.set_defaults(func=_cmd_remove)

    # ── info ──────────────────────────────────────────────────────────────────
    p_info = sub.add_parser("info", help="Show full details for a script")
    p_info.add_argument("name", help="Script name")
    p_info.set_defaults(func=_cmd_info)

    # ── gui ───────────────────────────────────────────────────────────────────
    p_gui = sub.add_parser("gui", help="Launch the Tkinter GUI")
    p_gui.set_defaults(func=_cmd_gui)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        _init()
    except Exception as e:
        print(f"[ERROR] Initialization failed: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        code = args.func(args)
        sys.exit(code or 0)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
