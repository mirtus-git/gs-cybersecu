"""gscs template — list, preview and generate script templates."""
from __future__ import annotations

import argparse
from pathlib import Path

from gscs.services.template_manager import get_template, list_templates, search_templates
from gscs.ui.console import console, error, info, success, warn


def run(args: argparse.Namespace) -> int:
    action = args.template_cmd
    if action == "list":
        return _cmd_list(args)
    if action == "show":
        return _cmd_show(args)
    if action == "use":
        return _cmd_use(args)
    error("Unknown template subcommand.")
    return 1


def _cmd_list(args: argparse.Namespace) -> int:
    keyword = getattr(args, "keyword", None)
    if keyword:
        names = search_templates(keyword)
        if not names:
            warn(f"No templates matching '{keyword}'.")
            return 0
        templates = [(n,) + t[1:] for n, *t in list_templates() if n in names]
    else:
        templates = list_templates()

    try:
        from rich.table import Table
        from gscs.ui.console import console as rich_console
        table = Table(title="Available Templates", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="bold magenta", min_width=30)
        table.add_column("Category", style="cyan", min_width=14)
        table.add_column("Language", style="green", min_width=10)
        table.add_column("Description")
        for name, category, language, description in templates:
            table.add_row(name, category, language, description)
        rich_console.print(table)
    except ImportError:
        print(f"{'NAME':<35} {'CATEGORY':<14} {'LANG':<10} DESCRIPTION")
        print("-" * 80)
        for name, category, language, description in templates:
            print(f"{name:<35} {category:<14} {language:<10} {description}")

    console.print(
        f"\n[muted]Use: gscs template show <name>   to preview[/]\n"
        f"[muted]Use: gscs template use <name> -o <file>  to generate[/]"
    )
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    tmpl = get_template(args.name)
    if not tmpl:
        error(f"Template '{args.name}' not found.")
        _suggest(args.name)
        return 1

    console.print(
        f"\n[bold]{args.name}[/]\n"
        f"  Category:    {tmpl['category']}\n"
        f"  Language:    {tmpl['language']}\n"
        f"  Description: {tmpl['description']}\n"
        f"  Tags:        {', '.join(tmpl['tags'])}\n"
        f"  Deps:        {', '.join(tmpl['deps']) or '(none)'}\n"
    )
    console.print("[muted]─── content ───────────────────────────────[/]")
    print(tmpl["content"])
    return 0


def _cmd_use(args: argparse.Namespace) -> int:
    tmpl = get_template(args.name)
    if not tmpl:
        error(f"Template '{args.name}' not found.")
        _suggest(args.name)
        return 1

    output_path = Path(args.output)

    if output_path.exists() and not args.force:
        error(f"File already exists: {output_path}  (use --force to overwrite)")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(tmpl["content"], encoding="utf-8")

    # Make shell/python scripts executable
    if tmpl["language"] in ("bash", "python", "perl", "ruby"):
        import os
        os.chmod(output_path, 0o755)

    success(f"Template written to: {output_path}")

    if tmpl["deps"]:
        info(f"Dependencies needed: {', '.join(tmpl['deps'])}")

    if args.register:
        from gscs.services import registry
        from gscs.core.models import Script
        from gscs.utils.hash import compute_sha256
        from gscs.utils.validators import sanitize_script_name, sanitize_tags

        script_name = sanitize_script_name(args.name.split("/")[-1].replace("-", "_"))
        tag_list = sanitize_tags(", ".join(tmpl["tags"]))
        sha = compute_sha256(output_path)

        if registry.script_exists(script_name):
            warn(f"Script '{script_name}' already registered. Use gscs add --update to overwrite.")
        else:
            s = Script(
                name=script_name,
                category=tmpl["category"],
                path=str(output_path.resolve()),
                description=tmpl["description"],
                language=tmpl["language"],
                sha256=sha,
            )
            s.set_tags(tag_list)
            s.set_dependencies(tmpl["deps"])
            registry.add_script(s)
            success(f"Script '{script_name}' registered in library.")

    return 0


def _suggest(name: str) -> None:
    matches = search_templates(name)
    if matches:
        console.print(f"[muted]Did you mean: {', '.join(matches[:3])}?[/]")
    else:
        console.print("[muted]Run: gscs template list  to see all available templates[/]")
