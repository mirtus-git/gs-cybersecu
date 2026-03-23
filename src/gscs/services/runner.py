"""Script execution orchestrator: dep check → sandbox → subprocess → log."""
from __future__ import annotations

import subprocess
import sys
import time
from typing import Optional

from gscs.core.config import Config
from gscs.core.models import Script
from gscs.services import dep_checker, logger, sandbox
from gscs.ui.console import console, warn


def _build_command(script: Script, extra_args: list[str]) -> list[str]:
    path = script.path
    lang = script.language
    if lang == "python":
        return [sys.executable, path] + extra_args
    if lang == "bash":
        return ["bash", path] + extra_args
    if lang == "go":
        return [path] + extra_args  # Pre-compiled binary
    if lang == "ruby":
        return ["ruby", path] + extra_args
    if lang == "perl":
        return ["perl", path] + extra_args
    return [path] + extra_args


def run_script(
    script: Script,
    extra_args: list[str],
    cfg: Config,
    sandbox_override: Optional[str] = None,
    dry_run: bool = False,
    force_no_sandbox: bool = False,
) -> int:
    """Execute a script safely. Returns exit code."""
    # 1. Integrity check
    from gscs.utils.hash import verify_integrity
    if script.sha256 and not verify_integrity(script):
        console.print(
            "[error]INTEGRITY FAILURE[/] Script has been modified since registration. "
            "Re-register with: gscs add --update"
        )
        return 2

    # 2. Dependency check
    deps = script.get_dependencies()
    if deps:
        report = dep_checker.check_dependencies(deps)
        if not report.ok:
            console.print("[error]Missing dependencies:[/]")
            for dep in report.missing:
                suggestion = dep_checker.suggest_install(dep)
                console.print(f"  - {dep}  →  {suggestion or 'install manually'}")
            return 1
        if report.optional_missing:
            warn(f"Optional deps not found: {', '.join(report.optional_missing)}")

    # 3. Select sandbox
    backend = sandbox.detect_sandbox(
        preference=sandbox_override or cfg.execution.sandbox,
        docker_images=cfg.execution.docker_images,
    )

    if backend.name() == "none" and cfg.execution.require_force_no_sandbox and not force_no_sandbox:
        warn("No sandbox available. Use --force to run without sandboxing.")
        return 1

    console.print(f"[info]Sandbox:[/] {backend.name()}" if backend.name() != "none"
                  else "[warning]Sandbox: none (unsandboxed)[/]")

    # 4. Build and optionally dry-run
    base_cmd = _build_command(script, extra_args)
    full_cmd = backend.wrap_command(base_cmd, script)

    if dry_run:
        console.print(f"[muted]DRY RUN:[/] {' '.join(full_cmd)}")
        return 0

    console.print(f"[highlight]Running:[/] {script.name}  {' '.join(extra_args)}\n")

    # 5. Execute with streaming output
    start = time.monotonic()
    exit_code = _execute_streaming(full_cmd, timeout=cfg.execution.timeout)
    duration = time.monotonic() - start

    # 6. Log execution
    logger.log_execution(
        script=script, args=extra_args, sandbox_mode=backend.name(),
        exit_code=exit_code, duration=duration,
    )

    status = "[success]SUCCESS[/]" if exit_code == 0 else f"[error]FAILED (exit={exit_code})[/]"
    console.print(f"\n{status}  [muted]duration={duration:.2f}s[/]")
    return exit_code


def _execute_streaming(cmd: list[str], timeout: int) -> int:
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        assert proc.stdout
        for line in proc.stdout:
            print(line, end="", flush=True)
        proc.wait(timeout=timeout)
        return proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        console.print(f"\n[error]TIMEOUT[/] Script killed after {timeout}s")
        return -1
    except FileNotFoundError as e:
        console.print(f"[error]Execution error:[/] {e}")
        return -1
    except PermissionError:
        console.print(f"[error]Permission denied:[/] {cmd[0]}")
        return -1
