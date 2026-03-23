"""gscs search — search scripts."""
from __future__ import annotations

import argparse
import json
from datetime import date

from gscs.services.search_engine import SearchFilter, search
from gscs.ui.console import error, info
from gscs.ui.tables import print_scripts


def run(args: argparse.Namespace) -> int:
    after_date = before_date = None
    try:
        if getattr(args, "after", None):
            after_date = date.fromisoformat(args.after)
        if getattr(args, "before", None):
            before_date = date.fromisoformat(args.before)
    except ValueError as e:
        error(f"Invalid date: {e}")
        return 1

    f = SearchFilter(
        keyword=args.keyword,
        category=args.category,
        tags=args.tags or [],
        language=getattr(args, "language", None),
        created_after=after_date,
        created_before=before_date,
        has_dep=getattr(args, "dep", None),
        author=getattr(args, "author", None),
        limit=args.limit,
    )
    results = search(f)

    if not results:
        info("No scripts found matching your criteria.")
        return 0

    if args.format == "json":
        print(json.dumps(
            [{"name": s.name, "category": s.category, "language": s.language,
              "description": s.description, "tags": s.get_tags(),
              "dependencies": s.get_dependencies(), "path": s.path}
             for s in results],
            indent=2,
        ))
    else:
        print_scripts(results)
    return 0
