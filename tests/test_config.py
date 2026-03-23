"""Tests for config loading."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gscs.core.config import Config, _deep_merge, _expand, load_config


def test_deep_merge():
    base = {"a": {"x": 1, "y": 2}, "b": 3}
    override = {"a": {"y": 99, "z": 100}, "c": 4}
    result = _deep_merge(base, override)
    assert result["a"]["x"] == 1
    assert result["a"]["y"] == 99
    assert result["a"]["z"] == 100
    assert result["b"] == 3
    assert result["c"] == 4


def test_expand_home():
    result = _expand("~/.config")
    assert not str(result).startswith("~")


def test_load_config_returns_config(tmp_path, monkeypatch):
    # Patch user config dir to tmp to avoid touching real config
    monkeypatch.setenv("GSCS_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr("gscs.core.config._USER_CONFIG_DIR", tmp_path / "config")
    monkeypatch.setattr("gscs.core.config._USER_CONFIG_YAML", tmp_path / "config" / "config.yaml")
    monkeypatch.setattr("gscs.core.config._USER_CONFIG_JSON", tmp_path / "config" / "config.json")
    cfg = load_config()
    assert isinstance(cfg, Config)
    assert str(cfg.storage.db_path) == str(tmp_path / "test.db")


def test_load_config_json_override(tmp_path, monkeypatch):
    override = {"execution": {"timeout": 999}}
    override_file = tmp_path / ".gs-cybersecu.json"
    override_file.write_text(json.dumps(override))
    monkeypatch.setattr("gscs.core.config._LOCAL_JSON", override_file)
    monkeypatch.setattr("gscs.core.config._USER_CONFIG_DIR", tmp_path / "config")
    monkeypatch.setattr("gscs.core.config._USER_CONFIG_YAML", tmp_path / "config" / "config.yaml")
    monkeypatch.setattr("gscs.core.config._USER_CONFIG_JSON", tmp_path / "config" / "config.json")
    cfg = load_config()
    assert cfg.execution.timeout == 999
