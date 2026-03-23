"""Sandbox backends: Firejail, Docker, and NoSandbox (with warning)."""
from __future__ import annotations

import shutil
from typing import Protocol

from gscs.core.models import Script


class SandboxBackend(Protocol):
    def wrap_command(self, cmd: list[str], script: Script) -> list[str]: ...
    def is_available(self) -> bool: ...
    def name(self) -> str: ...


class FirejailBackend:
    """Lightweight sandbox using Firejail profiles."""

    def __init__(self, base_opts: list[str] | None = None, category_opts: dict | None = None):
        self._base_opts = base_opts or ["--noprofile", "--noroot", "--net=none"]
        self._category_opts = category_opts or {}

    def is_available(self) -> bool:
        return shutil.which("firejail") is not None

    def name(self) -> str:
        return "firejail"

    def wrap_command(self, cmd: list[str], script: Script) -> list[str]:
        extra = self._category_opts.get(script.category, [])
        return ["firejail"] + self._base_opts + extra + ["--"] + cmd


class DockerBackend:
    """Full isolation via Docker containers."""

    def __init__(self, images: dict[str, str] | None = None):
        self._images = images or {
            "python": "python:3.12-slim",
            "bash": "debian:bookworm-slim",
            "go": "golang:1.22-bookworm",
            "ruby": "ruby:3.3-slim",
            "other": "debian:bookworm-slim",
        }

    def is_available(self) -> bool:
        if shutil.which("docker") is None:
            return False
        import subprocess
        try:
            r = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            return r.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def name(self) -> str:
        return "docker"

    def wrap_command(self, cmd: list[str], script: Script) -> list[str]:
        import os
        script_dir = os.path.dirname(os.path.abspath(script.path))
        image = self._images.get(script.language, self._images["other"])
        return [
            "docker", "run", "--rm",
            "--network", "none",
            "-v", f"{script_dir}:/work:ro",
            "-w", "/work",
            image,
        ] + cmd


class NoSandbox:
    """No sandboxing — requires --force flag if configured."""

    def is_available(self) -> bool:
        return True

    def name(self) -> str:
        return "none"

    def wrap_command(self, cmd: list[str], script: Script) -> list[str]:
        return cmd


def detect_sandbox(
    preference: str = "auto",
    firejail_opts: dict | None = None,
    docker_images: dict | None = None,
) -> SandboxBackend:
    """
    Select the best available sandbox backend.
    preference: 'auto' | 'firejail' | 'docker' | 'none'
    """
    fj = FirejailBackend(
        base_opts=firejail_opts.get("base_opts") if firejail_opts else None,
        category_opts=firejail_opts.get("category_opts") if firejail_opts else None,
    )
    docker = DockerBackend(images=docker_images)
    no_sb = NoSandbox()

    if preference == "firejail":
        return fj if fj.is_available() else no_sb
    if preference == "docker":
        return docker if docker.is_available() else no_sb
    if preference == "none":
        return no_sb
    # auto
    if fj.is_available():
        return fj
    if docker.is_available():
        return docker
    return no_sb
