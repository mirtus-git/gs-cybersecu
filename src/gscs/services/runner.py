"""Script execution orchestrator: dep check → sandbox → subprocess → log."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from gscs.core.config import Config
from gscs.core.models import Script
from gscs.services import dep_checker, logger, sandbox
from gscs.ui.console import console, warn


# Standard exit codes (aligned with POSIX / GNU timeout conventions)
EXIT_OK = 0
EXIT_DEPS_MISSING = 1
EXIT_INTEGRITY_FAIL = 2
EXIT_FILE_NOT_FOUND = 3
EXIT_PERMISSION_DENIED = 126   # POSIX: command found but not executable
EXIT_INTERPRETER_NOT_FOUND = 127  # POSIX: command not found
EXIT_TIMEOUT = 124             # GNU timeout convention


def _exit_reason(exit_code: int) -> str:
    """Human-readable reason for a non-zero exit code."""
    reasons = {
        EXIT_DEPS_MISSING: "missing dependencies",
        EXIT_INTEGRITY_FAIL: "integrity check failed",
        EXIT_FILE_NOT_FOUND: "script file not found",
        EXIT_PERMISSION_DENIED: "permission denied (not executable)",
        EXIT_INTERPRETER_NOT_FOUND: "interpreter not found in PATH",
        EXIT_TIMEOUT: "killed by timeout",
    }
    return reasons.get(exit_code, f"script exited with code {exit_code}")


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
    from gscs.utils.hash import verify_integrity

    # 1. File existence check (explicit, before integrity)
    script_path = Path(script.path)
    if not script_path.exists():
        console.print(
            f"[error]FILE NOT FOUND[/] Script no longer exists at: {script.path}\n"
            f"  Re-register with: gscs add <new_path> -n {script.name} --update"
        )
        return EXIT_FILE_NOT_FOUND

    # 2. Integrity check (SHA256)
    if script.sha256:
        if not verify_integrity(script):
            console.print(
                "[error]INTEGRITY FAILURE[/] Script has been modified since registration.\n"
                f"  Expected: {script.sha256[:16]}...\n"
                f"  Actual:   (mismatch)\n"
                f"  If intentional, re-register with: gscs add {script.path} -n {script.name} --update"
            )
            return EXIT_INTEGRITY_FAIL
    else:
        warn(
            f"No integrity hash for '{script.name}' — registered with --no-hash. "
            "Consider re-registering without --no-hash for tamper detection."
        )

    # 3. Dependency check
    deps = script.get_dependencies()
    if deps:
        report = dep_checker.check_dependencies(deps)
        if not report.ok:
            missing_count = len(report.missing)
            console.print(
                f"[error]DEPENDENCY ERROR[/] {missing_count} missing "
                f"{'dependency' if missing_count == 1 else 'dependencies'}:"
            )
            for dep in report.missing:
                suggestion = dep_checker.suggest_install(dep)
                console.print(f"  ✗ {dep}  →  {suggestion or 'install manually'}")
            console.print(
                f"\n  [muted]Run: gscs deps install {script.name}  to see install commands[/]"
            )
            return EXIT_DEPS_MISSING
        if report.optional_missing:
            warn(f"Optional deps not found: {', '.join(report.optional_missing)}")

    # 4. Select sandbox
    requested = sandbox_override or cfg.execution.sandbox
    backend = sandbox.detect_sandbox(
        preference=requested,
        docker_images=cfg.execution.docker_images,
    )

    if backend.name() == "none":
        if requested in ("firejail", "docker"):
            warn(
                f"Requested sandbox '{requested}' is not available on this system. "
                f"Install it or use --sandbox auto."
            )
        if cfg.execution.require_force_no_sandbox and not force_no_sandbox:
            warn(
                "No sandbox available and --force not set.\n"
                "  Install firejail: sudo apt install firejail\n"
                "  Or run unsandboxed: gscs run " + script.name + " --force"
            )
            return EXIT_DEPS_MISSING

    console.print(
        f"[info]Sandbox:[/] {backend.name()}"
        if backend.name() != "none"
        else "[warning]Sandbox: none (unsandboxed)[/]"
    )

    # 5. Build and optionally dry-run
    base_cmd = _build_command(script, extra_args)
    full_cmd = backend.wrap_command(base_cmd, script)

    if dry_run:
        console.print(f"[muted]DRY RUN:[/] {' '.join(full_cmd)}")
        return EXIT_OK

    console.print(f"[highlight]Running:[/] {script.name}  {' '.join(extra_args)}\n")

    # 6. Execute with streaming output
    start = time.monotonic()
    exit_code = _execute_streaming(full_cmd, timeout=cfg.execution.timeout, script=script)
    duration = time.monotonic() - start

    # 7. Log execution with failure reason
    notes = "" if exit_code == 0 else _exit_reason(exit_code)
    logger.log_execution(
        script=script, args=extra_args, sandbox_mode=backend.name(),
        exit_code=exit_code, duration=duration, notes=notes,
    )

    # 8. Final status with specific failure context
    if exit_code == EXIT_OK:
        status = "[success]SUCCESS[/]"
    elif exit_code == EXIT_TIMEOUT:
        status = f"[error]TIMEOUT[/] script killed after {cfg.execution.timeout}s"
    elif exit_code == EXIT_INTERPRETER_NOT_FOUND:
        status = f"[error]FAILED[/] interpreter not found — check language setting (gscs info {script.name})"
    elif exit_code == EXIT_PERMISSION_DENIED:
        status = f"[error]FAILED[/] permission denied — fix with: chmod +x {script.path}"
    else:
        status = f"[error]FAILED[/] script exited with code {exit_code}"

    console.print(f"\n{status}  [muted]duration={duration:.2f}s[/]")
    return exit_code


def _execute_streaming(cmd: list[str], timeout: int, script: Optional[Script] = None) -> int:
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
        proc.wait()
        console.print(f"\n[error]TIMEOUT[/] Script killed after {timeout}s (exit {EXIT_TIMEOUT})")
        return EXIT_TIMEOUT
    except FileNotFoundError:
        interpreter = cmd[0]
        name = script.name if script else cmd[-1]
        console.print(
            f"[error]INTERPRETER NOT FOUND[/] '{interpreter}' is not installed or not in PATH.\n"
            f"  Check the script language with: gscs info {name}\n"
            f"  Install example: sudo apt install {interpreter.split('/')[-1]}"
        )
        return EXIT_INTERPRETER_NOT_FOUND
    except PermissionError:
        console.print(
            f"[error]PERMISSION DENIED[/] Cannot execute: {cmd[0]}\n"
            f"  Fix with: chmod +x {cmd[0]}"
        )
        return EXIT_PERMISSION_DENIED
