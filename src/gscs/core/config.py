"""Config loader: JSON by default, YAML optional. Zero required deps."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# YAML is optional
try:
    import yaml as _yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

_PKG_ROOT = Path(__file__).parent.parent.parent.parent
_DEFAULT_CONFIG_YAML = _PKG_ROOT / "config" / "default_config.yaml"
_DEFAULT_CONFIG_JSON = _PKG_ROOT / "config" / "default_config.json"
_USER_CONFIG_DIR = Path.home() / ".config" / "gscs"
_USER_CONFIG_YAML = _USER_CONFIG_DIR / "config.yaml"
_USER_CONFIG_JSON = _USER_CONFIG_DIR / "config.json"
_LOCAL_YAML = Path(".gs-cybersecu.yaml")
_LOCAL_JSON = Path(".gs-cybersecu.json")


@dataclass(frozen=True)
class StorageConfig:
    scripts_dir: Path
    db_path: Path
    logs_dir: Path
    log_retention_days: int


@dataclass(frozen=True)
class ExecutionConfig:
    sandbox: str
    timeout: int
    require_force_no_sandbox: bool
    docker_images: dict


@dataclass(frozen=True)
class UIConfig:
    format: str
    show_integrity: bool
    page_size: int
    theme: str


@dataclass(frozen=True)
class Config:
    storage: StorageConfig
    execution: ExecutionConfig
    ui: UIConfig
    categories: list


def _expand(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p)))


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _load_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        if path.suffix in (".yaml", ".yml"):
            if _HAS_YAML:
                return _yaml.safe_load(f) or {}
            else:
                # Try to read as JSON fallback (won't work for YAML but won't crash)
                return {}
        return json.load(f)


def _default_data() -> dict:
    """Hardcoded defaults — no file required."""
    return {
        "storage": {
            "scripts_dir": "~/.local/share/gscs/scripts",
            "db_path": "~/.local/share/gscs/gscs.db",
            "logs_dir": "~/.local/share/gscs/logs",
            "log_retention_days": 90,
        },
        "execution": {
            "sandbox": "auto",
            "timeout": 300,
            "require_force_no_sandbox": True,
            "docker_images": {
                "python": "python:3.12-slim",
                "bash": "debian:bookworm-slim",
                "go": "golang:1.22-bookworm",
                "ruby": "ruby:3.3-slim",
                "other": "debian:bookworm-slim",
            },
        },
        "ui": {
            "format": "table",
            "show_integrity": False,
            "page_size": 20,
            "theme": "dark",
        },
        "categories": ["recon", "exploit", "post-exploit", "forensic", "custom"],
    }


def ensure_user_config() -> None:
    """Create user config as JSON if not present."""
    _USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not _USER_CONFIG_YAML.exists() and not _USER_CONFIG_JSON.exists():
        # Try to copy from package default YAML first
        data = _load_file(_DEFAULT_CONFIG_YAML) or _load_file(_DEFAULT_CONFIG_JSON) or _default_data()
        with open(_USER_CONFIG_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def load_config() -> Config:
    """Load config: defaults → user config → local override → env vars."""
    ensure_user_config()

    data = _default_data()
    # User config (YAML preferred if pyyaml present, else JSON)
    user = _load_file(_USER_CONFIG_YAML) or _load_file(_USER_CONFIG_JSON)
    if user:
        data = _deep_merge(data, user)
    # Local project override
    local = _load_file(_LOCAL_YAML) or _load_file(_LOCAL_JSON)
    if local:
        data = _deep_merge(data, local)
    # Env var overrides
    for env_key, (section, key) in {
        "GSCS_DB_PATH": ("storage", "db_path"),
        "GSCS_SCRIPTS_DIR": ("storage", "scripts_dir"),
        "GSCS_LOGS_DIR": ("storage", "logs_dir"),
        "GSCS_SANDBOX": ("execution", "sandbox"),
        "GSCS_TIMEOUT": ("execution", "timeout"),
    }.items():
        val = os.environ.get(env_key)
        if val is not None:
            data.setdefault(section, {})[key] = val

    s = data["storage"]
    e = data["execution"]
    u = data["ui"]

    return Config(
        storage=StorageConfig(
            scripts_dir=_expand(s["scripts_dir"]),
            db_path=_expand(s["db_path"]),
            logs_dir=_expand(s["logs_dir"]),
            log_retention_days=int(s["log_retention_days"]),
        ),
        execution=ExecutionConfig(
            sandbox=e["sandbox"],
            timeout=int(e["timeout"]),
            require_force_no_sandbox=bool(e["require_force_no_sandbox"]),
            docker_images=e.get("docker_images", {}),
        ),
        ui=UIConfig(
            format=u.get("format", "table"),
            show_integrity=bool(u.get("show_integrity", False)),
            page_size=int(u.get("page_size", 20)),
            theme=u.get("theme", "dark"),
        ),
        categories=data.get("categories", ["recon", "exploit", "post-exploit", "forensic", "custom"]),
    )
