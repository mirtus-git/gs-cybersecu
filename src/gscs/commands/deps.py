"""gscs deps — check or display install commands for dependencies."""
from __future__ import annotations

import argparse

from gscs.services import dep_checker, registry
from gscs.ui.console import error, info, success, warn
from gscs.ui.tables import print_dep_report


def run(args: argparse.Namespace) -> int:
    script = registry.get_script(args.name)
    if not script:
        error(f"Script '{args.name}' not found.")
        return 1

    deps = script.get_dependencies()
    if not deps:
        info(f"Script '{args.name}' has no declared dependencies.")
        return 0

    report = dep_checker.check_dependencies(deps)
    print_dep_report(report)

    if args.deps_cmd == "install":
        if not report.missing:
            success("All dependencies are satisfied.")
            return 0
        print("\nInstall commands for missing dependencies:")
        for dep in report.missing:
            suggestion = dep_checker.suggest_install(dep)
            print(f"  {dep}:  {suggestion or '(install manually)'}")

    return 0 if report.ok else 1
