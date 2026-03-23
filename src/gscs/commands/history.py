"""gscs history — view execution logs."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gscs.services.logger import export_logs, get_logs
from gscs.ui.tables import print_logs


def run(args: argparse.Namespace) -> int:
    logs = get_logs(
        script_name=getattr(args, "script", None),
        last_n=getattr(args, "last", None),
    )

    if not logs:
        print("No execution history found.")
        return 0

    export_fmt = getattr(args, "export", None)
    if export_fmt:
        content = export_logs(logs, fmt=export_fmt)
        output = getattr(args, "output", None)
        if output:
            Path(output).write_text(content, encoding="utf-8")
            print(f"Exported {len(logs)} log(s) to {output}")
        else:
            sys.stdout.write(content)
    else:
        print_logs(logs)
    return 0
