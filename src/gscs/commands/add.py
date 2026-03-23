"""gscs add — register a script."""
from __future__ import annotations

import argparse

from gscs.core.models import Script
from gscs.services import registry
from gscs.ui.console import error, success
from gscs.utils.hash import compute_sha256
from gscs.utils.validators import ValidationError, sanitize_script_name, sanitize_tags, validate_path


def run(args: argparse.Namespace) -> int:
    try:
        script_path = validate_path(args.path)
        script_name = sanitize_script_name(args.name or script_path.stem)
        tag_list = sanitize_tags(args.tags)
        dep_list = [d.strip() for d in args.deps.split(",") if d.strip()]
    except ValidationError as e:
        error(str(e))
        return 1

    if registry.script_exists(script_name):
        if not args.update:
            error(f"Script '{script_name}' already exists. Use --update to overwrite.")
            return 1

    sha = "" if args.no_hash else compute_sha256(script_path)

    s = Script(
        name=script_name,
        category=args.category,
        path=str(script_path),
        description=args.desc,
        language=args.lang,
        author=args.author,
        sha256=sha,
    )
    s.set_tags(tag_list)
    s.set_dependencies(dep_list)

    if args.update and registry.script_exists(script_name):
        registry.update_script(
            script_name,
            category=args.category,
            path=str(script_path),
            description=args.desc,
            language=args.lang,
            tags=s.tags,
            dependencies=s.dependencies,
            author=args.author,
            sha256=sha,
        )
        success(f"Script '{script_name}' updated [{args.category} / {args.lang}]")
    else:
        registry.add_script(s)
        success(f"Script '{script_name}' registered [{args.category} / {args.lang}]")
    return 0
