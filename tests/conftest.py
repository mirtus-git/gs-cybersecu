"""Pytest fixtures for gs-cybersecu tests."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from gscs.core.config import Config, ExecutionConfig, StorageConfig, UIConfig
from gscs.core.database import init_db
from gscs.core.models import Language, Script


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Each test gets an isolated in-memory-equivalent SQLite database."""
    db_path = tmp_path / "test.db"
    init_db(db_path)
    yield db_path


@pytest.fixture
def sample_script(tmp_path) -> Script:
    """Create a real script file on disk for testing."""
    script_file = tmp_path / "test_recon.sh"
    script_file.write_text("#!/bin/bash\necho 'recon done'\n")
    s = Script(
        name="test-recon",
        category="recon",
        path=str(script_file),
        description="A test recon script",
        language=Language.BASH,
        author="tester",
    )
    s.set_tags(["test", "recon"])
    s.set_dependencies(["bash"])
    return s


@pytest.fixture
def cfg(tmp_path) -> Config:
    return Config(
        storage=StorageConfig(
            scripts_dir=tmp_path / "scripts",
            db_path=tmp_path / "test.db",
            logs_dir=tmp_path / "logs",
            log_retention_days=30,
        ),
        execution=ExecutionConfig(
            sandbox="none",
            timeout=30,
            require_force_no_sandbox=False,
            docker_images={},
        ),
        ui=UIConfig(format="table", show_integrity=False, page_size=20, theme="dark"),
        categories=["recon", "exploit", "post-exploit", "forensic", "custom"],
    )
