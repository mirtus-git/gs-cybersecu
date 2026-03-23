"""Dependency checker supporting multiple languages and package managers."""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
from dataclasses import dataclass, field


@dataclass
class DepReport:
    satisfied: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    optional_missing: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.missing) == 0


def check_dependencies(deps: list[str], optional: list[str] | None = None) -> DepReport:
    """
    Check a list of dependencies. Dependency format:
      - "nmap"              → system binary
      - "python:requests"   → Python package
      - "go:subfinder"      → Go binary in PATH
      - "ruby:nokogiri"     → Ruby gem
      - "cmd:custom check"  → arbitrary shell command (exit 0 = ok)
    """
    report = DepReport()
    optional_set = set(optional or [])

    all_deps = list(deps) + list(optional_set)
    for dep in all_deps:
        is_optional = dep in optional_set
        satisfied = _check_single(dep)
        if satisfied:
            report.satisfied.append(dep)
        elif is_optional:
            report.optional_missing.append(dep)
        else:
            report.missing.append(dep)

    return report


def _check_single(dep: str) -> bool:
    if ":" not in dep:
        return _check_binary(dep)
    prefix, name = dep.split(":", 1)
    checkers = {
        "python": _check_python_package,
        "go": _check_binary,
        "ruby": _check_ruby_gem,
        "cmd": _check_cmd,
    }
    checker = checkers.get(prefix.lower(), _check_binary)
    return checker(name)


def _check_binary(name: str) -> bool:
    return shutil.which(name) is not None


def _check_python_package(package: str) -> bool:
    # Normalize pip package name to importable module name
    module_name = package.replace("-", "_").replace(".", "_")
    return importlib.util.find_spec(module_name) is not None


def _check_ruby_gem(gem: str) -> bool:
    try:
        result = subprocess.run(
            ["gem", "list", "-i", gem],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and "true" in result.stdout.lower()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_cmd(command: str) -> bool:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def suggest_install(dep: str) -> str | None:
    """Return a suggested install command for a missing dependency."""
    if ":" not in dep:
        # Try to suggest apt/dnf based on distro
        return f"sudo apt install {dep}  # or: sudo dnf install {dep} / sudo pacman -S {dep}"
    prefix, name = dep.split(":", 1)
    suggestions = {
        "python": f"pip install {name}",
        "go": f"go install {name}@latest",
        "ruby": f"gem install {name}",
    }
    return suggestions.get(prefix.lower())
