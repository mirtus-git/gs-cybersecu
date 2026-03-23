"""Tests for the search engine."""
from __future__ import annotations

from gscs.core.models import Script
from gscs.services.registry import add_script
from gscs.services.search_engine import SearchFilter, search


def _make_script(tmp_path, name, category, language="bash", tags="", desc=""):
    f = tmp_path / f"{name}.sh"
    f.write_text("#!/bin/bash\n")
    s = Script(name=name, category=category, path=str(f), language=language, description=desc)
    s.set_tags([t.strip() for t in tags.split(",") if t.strip()])
    return add_script(s)


def test_search_by_keyword(tmp_path):
    _make_script(tmp_path, "port-scanner", "recon", desc="Fast port scanning tool")
    _make_script(tmp_path, "exploit-smb", "exploit", desc="SMB exploit")
    results = search(SearchFilter(keyword="port"))
    assert len(results) == 1
    assert results[0].name == "port-scanner"


def test_search_by_category(tmp_path):
    _make_script(tmp_path, "recon-a", "recon")
    _make_script(tmp_path, "exploit-b", "exploit")
    results = search(SearchFilter(category="recon"))
    assert len(results) == 1
    assert results[0].category == "recon"


def test_search_by_tags_and_logic(tmp_path):
    _make_script(tmp_path, "script-a", "recon", tags="nmap,stealth")
    _make_script(tmp_path, "script-b", "recon", tags="nmap")
    # Both tags required
    results = search(SearchFilter(tags=["nmap", "stealth"]))
    assert len(results) == 1
    assert results[0].name == "script-a"


def test_search_no_results(tmp_path):
    _make_script(tmp_path, "scanner", "recon")
    results = search(SearchFilter(keyword="nonexistentxyz"))
    assert results == []


def test_search_by_dependency(tmp_path):
    s = _make_script(tmp_path, "nmap-scanner", "recon")
    from gscs.services.registry import update_script
    import json
    update_script("nmap-scanner", dependencies=json.dumps(["nmap", "python:requests"]))
    results = search(SearchFilter(has_dep="nmap"))
    assert len(results) == 1
