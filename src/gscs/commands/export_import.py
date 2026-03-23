"""gscs export / gscs import — portable library archive."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gscs.core.config import load_config
from gscs.services import registry
from gscs.services.exporter import export_library, import_library
from gscs.ui.console import console, error, info, success, warn


def run_export(args: argparse.Namespace) -> int:
    cfg = load_config()
    category = getattr(args, "category", None)
    if category and category != "all":
        scripts = registry.list_scripts(category=category)
    else:
        scripts = registry.list_scripts()

    if not scripts:
        warn("No scripts found to export.")
        return 0

    include_content = not getattr(args, "no_content", False)
    json_text = export_library(scripts, include_content=include_content)

    output = getattr(args, "output", None)
    if output:
        out_path = Path(output)
        out_path.write_text(json_text, encoding="utf-8")
        success(
            f"Exported {len(scripts)} script{'s' if len(scripts) != 1 else ''} "
            f"to: {out_path}"
        )
        if not include_content:
            info("File contents not included (--no-content). Paths only.")
    else:
        print(json_text)

    return 0


def run_import(args: argparse.Namespace) -> int:
    cfg = load_config()
    archive_path = Path(args.archive)

    if not archive_path.exists():
        error(f"Archive file not found: {archive_path}")
        return 1

    try:
        json_text = archive_path.read_text(encoding="utf-8")
    except Exception as exc:
        error(f"Cannot read archive: {exc}")
        return 1

    scripts_dir = cfg.storage.scripts_dir
    restore = not getattr(args, "no_restore", False)
    skip_existing = getattr(args, "skip_existing", False)
    dry_run = getattr(args, "dry_run", False)

    try:
        scripts, warnings = import_library(
            json_text,
            scripts_dir=scripts_dir,
            skip_existing=skip_existing,
            restore_files=restore,
        )
    except ValueError as exc:
        error(str(exc))
        return 1

    for w in warnings:
        warn(w)

    if not scripts:
        warn("No scripts found in archive.")
        return 0

    if dry_run:
        console.print(f"[muted]DRY RUN — would import {len(scripts)} script(s):[/]")
        for s in scripts:
            exists = registry.script_exists(s.name)
            status = "[yellow]exists[/]" if exists else "[green]new[/]"
            console.print(f"  {status}  {s.name}  [{s.category}/{s.language}]")
        return 0

    added = 0
    skipped = 0
    updated = 0

    for s in scripts:
        exists = registry.script_exists(s.name)
        if exists:
            if skip_existing:
                skipped += 1
                continue
            if getattr(args, "update", False):
                registry.update_script(
                    s.name,
                    category=s.category,
                    path=s.path,
                    description=s.description,
                    language=s.language,
                    tags=s.tags,
                    dependencies=s.dependencies,
                    author=s.author,
                    sha256=s.sha256,
                )
                updated += 1
                continue
            # Prompt user
            confirm = input(
                f"Script '{s.name}' already exists. Overwrite? [y/N/a(ll)] "
            ).strip().lower()
            if confirm == "a":
                args.update = True
                registry.update_script(s.name, **{
                    k: getattr(s, k)
                    for k in ("category", "path", "description", "language",
                              "tags", "dependencies", "author", "sha256")
                })
                updated += 1
            elif confirm == "y":
                registry.update_script(s.name, **{
                    k: getattr(s, k)
                    for k in ("category", "path", "description", "language",
                              "tags", "dependencies", "author", "sha256")
                })
                updated += 1
            else:
                skipped += 1
        else:
            registry.add_script(s)
            added += 1

    parts = []
    if added:
        parts.append(f"{added} added")
    if updated:
        parts.append(f"{updated} updated")
    if skipped:
        parts.append(f"{skipped} skipped")

    success(f"Import complete: {', '.join(parts) or 'nothing changed'}.")
    return 0
