"""SAF-022 — Tester edge-case tests.

Covers scenarios the Developer's tests do not explicitly target:
  - Bare 'NoAgentZone' key (without **) must not be present
  - files.exclude and search.exclude must have identical key sets
  - Exclude values are strict JSON booleans, not strings or ints
  - settings.json byte content is stable (no BOM, no CRLF inconsistency
    that would break hash verification)
  - NoAgentZone exclusion key name is exactly **/NoAgentZone — no leading
    or trailing whitespace that might silently survive JSON round-trips
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS = REPO_ROOT / "Default-Project" / ".vscode" / "settings.json"
TEMPLATE_SETTINGS = REPO_ROOT / "templates" / "coding" / ".vscode" / "settings.json"

GLOB_KEY = "**/NoAgentZone"
BARE_KEY = "NoAgentZone"


def _load_raw(path: Path) -> bytes:
    return path.read_bytes()


def _load_settings(path: Path) -> dict:
    import json
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Edge case: bare key must NOT be present alongside the glob key
# ---------------------------------------------------------------------------

class TestNoBareNoAgentZoneKey:
    """Bare 'NoAgentZone' (no **) must not appear alongside the glob key."""

    @pytest.mark.parametrize("label,path", [
        ("Default-Project", DEFAULT_SETTINGS),
        ("templates/coding", TEMPLATE_SETTINGS),
    ])
    def test_bare_key_absent_from_files_exclude(self, label, path):
        settings = _load_settings(path)
        assert BARE_KEY not in settings.get("files.exclude", {}), (
            f"[{label}] Bare key 'NoAgentZone' (without **/) found in files.exclude. "
            f"This is a redundant entry that could cause confusion."
        )

    @pytest.mark.parametrize("label,path", [
        ("Default-Project", DEFAULT_SETTINGS),
        ("templates/coding", TEMPLATE_SETTINGS),
    ])
    def test_bare_key_absent_from_search_exclude(self, label, path):
        settings = _load_settings(path)
        assert BARE_KEY not in settings.get("search.exclude", {}), (
            f"[{label}] Bare key 'NoAgentZone' (without **/) found in search.exclude."
        )


# ---------------------------------------------------------------------------
# Edge case: files.exclude and search.exclude must have the same key set
# ---------------------------------------------------------------------------

class TestExcludeSectionConsistency:
    """Both exclude sections must contain the same set of keys."""

    @pytest.mark.parametrize("label,path", [
        ("Default-Project", DEFAULT_SETTINGS),
        ("templates/coding", TEMPLATE_SETTINGS),
    ])
    def test_files_and_search_exclude_have_same_keys(self, label, path):
        settings = _load_settings(path)
        files_keys = set(settings.get("files.exclude", {}).keys())
        search_keys = set(settings.get("search.exclude", {}).keys())
        assert files_keys == search_keys, (
            f"[{label}] files.exclude and search.exclude have different key sets.\n"
            f"  Only in files.exclude:  {files_keys - search_keys}\n"
            f"  Only in search.exclude: {search_keys - files_keys}"
        )


# ---------------------------------------------------------------------------
# Edge case: all exclude values must be strict JSON booleans (True), not
# strings ("true"), integers (1), or other truthy types
# ---------------------------------------------------------------------------

class TestExcludeValueTypes:
    """All values in both exclude sections must be the Python bool True."""

    @pytest.mark.parametrize("label,path", [
        ("Default-Project", DEFAULT_SETTINGS),
        ("templates/coding", TEMPLATE_SETTINGS),
    ])
    def test_all_files_exclude_values_are_bool_true(self, label, path):
        settings = _load_settings(path)
        for key, val in settings.get("files.exclude", {}).items():
            assert val is True and isinstance(val, bool), (
                f"[{label}] files.exclude[{key!r}] = {val!r} (type {type(val).__name__}); "
                f"expected strict bool True"
            )

    @pytest.mark.parametrize("label,path", [
        ("Default-Project", DEFAULT_SETTINGS),
        ("templates/coding", TEMPLATE_SETTINGS),
    ])
    def test_all_search_exclude_values_are_bool_true(self, label, path):
        settings = _load_settings(path)
        for key, val in settings.get("search.exclude", {}).items():
            assert val is True and isinstance(val, bool), (
                f"[{label}] search.exclude[{key!r}] = {val!r} (type {type(val).__name__}); "
                f"expected strict bool True"
            )


# ---------------------------------------------------------------------------
# Edge case: settings.json must not have a UTF-8 BOM, which would corrupt the
# SHA256 hash and break the security gate check
# ---------------------------------------------------------------------------

class TestNoBOM:
    """settings.json files must not start with a UTF-8 BOM (EF BB BF)."""

    @pytest.mark.parametrize("label,path", [
        ("Default-Project", DEFAULT_SETTINGS),
        ("templates/coding", TEMPLATE_SETTINGS),
    ])
    def test_no_utf8_bom(self, label, path):
        raw = _load_raw(path)
        assert not raw.startswith(b"\xef\xbb\xbf"), (
            f"[{label}] settings.json has a UTF-8 BOM. "
            f"This will corrupt the SHA256 hash and break the security gate."
        )


# ---------------------------------------------------------------------------
# Edge case: key name must be exactly '**/NoAgentZone' with no extra whitespace
# ---------------------------------------------------------------------------

class TestExactKeyString:
    """The glob key must be the exact string '**/NoAgentZone'."""

    @pytest.mark.parametrize("label,path", [
        ("Default-Project", DEFAULT_SETTINGS),
        ("templates/coding", TEMPLATE_SETTINGS),
    ])
    def test_no_whitespace_in_key_files_exclude(self, label, path):
        settings = _load_settings(path)
        keys = list(settings.get("files.exclude", {}).keys())
        noagent_keys = [k for k in keys if "NoAgentZone" in k]
        for k in noagent_keys:
            assert k == GLOB_KEY, (
                f"[{label}] files.exclude has unexpected key {k!r}; "
                f"expected exactly {GLOB_KEY!r}"
            )

    @pytest.mark.parametrize("label,path", [
        ("Default-Project", DEFAULT_SETTINGS),
        ("templates/coding", TEMPLATE_SETTINGS),
    ])
    def test_no_whitespace_in_key_search_exclude(self, label, path):
        settings = _load_settings(path)
        keys = list(settings.get("search.exclude", {}).keys())
        noagent_keys = [k for k in keys if "NoAgentZone" in k]
        for k in noagent_keys:
            assert k == GLOB_KEY, (
                f"[{label}] search.exclude has unexpected key {k!r}; "
                f"expected exactly {GLOB_KEY!r}"
            )
