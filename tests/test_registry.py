"""Tests for the script registry CRUD operations."""
from __future__ import annotations

import pytest

from gscs.services.registry import (
    add_script, delete_script, get_script, list_scripts,
    script_exists, update_script,
)


def test_add_and_get(sample_script):
    added = add_script(sample_script)
    assert added.id is not None
    fetched = get_script("test-recon")
    assert fetched is not None
    assert fetched.name == "test-recon"
    assert fetched.category == "recon"


def test_add_duplicate_raises(sample_script):
    add_script(sample_script)
    from gscs.core.models import Script
    import sqlite3
    duplicate = Script(name="test-recon", category="exploit", path=sample_script.path)
    with pytest.raises(Exception):  # sqlite3.IntegrityError via UNIQUE constraint
        add_script(duplicate)


def test_list_scripts(sample_script):
    add_script(sample_script)
    scripts = list_scripts()
    assert len(scripts) == 1
    assert scripts[0].name == "test-recon"


def test_list_filter_by_category(sample_script, tmp_path):
    add_script(sample_script)
    from gscs.core.models import Script
    other = Script(name="exploit-x", category="exploit", path=str(tmp_path / "x.sh"))
    (tmp_path / "x.sh").write_text("#!/bin/bash\n")
    add_script(other)

    recon_only = list_scripts(category="recon")
    assert len(recon_only) == 1
    assert recon_only[0].category == "recon"


def test_update_script(sample_script):
    add_script(sample_script)
    updated = update_script("test-recon", description="Updated description")
    assert updated is not None
    assert updated.description == "Updated description"


def test_delete_script(sample_script):
    add_script(sample_script)
    assert script_exists("test-recon")
    deleted = delete_script("test-recon")
    assert deleted is True
    assert not script_exists("test-recon")


def test_delete_nonexistent():
    assert delete_script("does-not-exist") is False
