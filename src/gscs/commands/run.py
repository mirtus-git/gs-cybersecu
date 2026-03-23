"""gscs run — execute a script safely."""
from __future__ import annotations

import argparse
import shlex

from gscs.core.config import load_config
from gscs.services import registry
from gscs.services.runner import run_script
from gscs.ui.console import error


def run(args: argparse.Namespace) -> int:
    script = registry.get_script(args.name)
    if not script:
        error(f"Script '{args.name}' not found. Use 'gscs list' to see available scripts.")
        return 1

    extra_args = shlex.split(args.args) if args.args else []
    cfg = load_config()

    return run_script(
        script=script,
        extra_args=extra_args,
        cfg=cfg,
        sandbox_override=args.sandbox,
        dry_run=args.dry_run,
        force_no_sandbox=args.force,
    )
