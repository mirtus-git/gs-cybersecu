"""Tests for the dependency checker."""
from __future__ import annotations

from gscs.services.dep_checker import check_dependencies, suggest_install


def test_satisfied_binary():
    # 'sh' exists on all Linux systems
    report = check_dependencies(["sh"])
    assert "sh" in report.satisfied
    assert report.ok


def test_missing_binary():
    report = check_dependencies(["this-binary-does-not-exist-xyz123"])
    assert not report.ok
    assert "this-binary-does-not-exist-xyz123" in report.missing


def test_python_package_stdlib():
    # json is always available
    report = check_dependencies(["python:json"])
    assert "python:json" in report.satisfied


def test_python_package_missing():
    report = check_dependencies(["python:nonexistent_package_xyz123"])
    assert not report.ok


def test_suggest_install():
    suggestion = suggest_install("nmap")
    assert "nmap" in suggestion

    suggestion = suggest_install("python:requests")
    assert "pip install requests" in suggestion

    suggestion = suggest_install("go:subfinder")
    assert "go install" in suggestion
