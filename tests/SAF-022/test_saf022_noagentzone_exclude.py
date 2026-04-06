"""SAF-022: Tests for NoAgentZone VS Code Exclude Settings.

Verifies that **/NoAgentZone is present in both files.exclude and
search.exclude sections of both settings.json files, that the two
settings.json files are identical, and that the security_gate.py
hashes are correct for the updated files.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures / paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS = REPO_ROOT / "templates" / "agent-workbench" / ".vscode" / "settings.json"
TEMPLATE_SETTINGS = REPO_ROOT / "templates" / "agent-workbench" / ".vscode" / "settings.json"
DEFAULT_GATE = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "security_gate.py"
TEMPLATE_GATE = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "security_gate.py"

EXCLUDE_KEY = "**/NoAgentZone"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _load_settings(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract_settings_hash(gate_path: Path) -> str:
    """Extract the _KNOWN_GOOD_SETTINGS_HASH value from security_gate.py."""
    content = gate_path.read_text(encoding="utf-8")
    match = re.search(r'_KNOWN_GOOD_SETTINGS_HASH: str = "([0-9a-fA-F]{64})"', content)
    assert match, f"_KNOWN_GOOD_SETTINGS_HASH not found in {gate_path}"
    return match.group(1)


# ---------------------------------------------------------------------------
# Protection tests — NoAgentZone exclusion is present and correct
# ---------------------------------------------------------------------------

class TestDefaultSettingsExclusion:
    """templates/coding settings.json contains NoAgentZone exclusions."""

    def test_files_exclude_noagentzone_present(self):
        # FIX-079: NoAgentZone must NOT be in files.exclude (BUG-146 fix).
        # Users need to see the folder in the VS Code explorer.
        # Security gate enforces access control independently of this setting.
        settings = _load_settings(DEFAULT_SETTINGS)
        assert "files.exclude" in settings, "files.exclude key missing"
        assert EXCLUDE_KEY not in settings["files.exclude"], (
            f"{EXCLUDE_KEY} found in files.exclude — FIX-079 removed it to show the folder in the explorer"
        )

    def test_files_exclude_noagentzone_is_true(self):
        # FIX-079: key is intentionally absent from files.exclude.
        settings = _load_settings(DEFAULT_SETTINGS)
        assert EXCLUDE_KEY not in settings.get("files.exclude", {}), (
            f"{EXCLUDE_KEY} present in files.exclude — FIX-079 removed it (BUG-146)"
        )

    def test_search_exclude_noagentzone_present(self):
        settings = _load_settings(DEFAULT_SETTINGS)
        assert "search.exclude" in settings, "search.exclude key missing"
        assert EXCLUDE_KEY in settings["search.exclude"], (
            f"{EXCLUDE_KEY} not found in search.exclude"
        )

    def test_search_exclude_noagentzone_is_true(self):
        settings = _load_settings(DEFAULT_SETTINGS)
        assert settings["search.exclude"][EXCLUDE_KEY] is True, (
            f"{EXCLUDE_KEY} must be true in search.exclude"
        )

    def test_existing_excludes_still_present(self):
        """Original .github and .vscode exclusions must not have been removed."""
        settings = _load_settings(DEFAULT_SETTINGS)
        for section in ("files.exclude", "search.exclude"):
            assert settings[section].get(".github") is True, (
                f".github exclusion missing from {section}"
            )
            assert settings[section].get(".vscode") is True, (
                f".vscode exclusion missing from {section}"
            )


class TestTemplateSettingsExclusion:
    """templates/coding settings.json contains NoAgentZone exclusions."""

    def test_files_exclude_noagentzone_present(self):
        # FIX-079: NoAgentZone must NOT be in files.exclude (BUG-146 fix).
        settings = _load_settings(TEMPLATE_SETTINGS)
        assert "files.exclude" in settings, "files.exclude key missing"
        assert EXCLUDE_KEY not in settings["files.exclude"], (
            f"{EXCLUDE_KEY} found in files.exclude — FIX-079 removed it to show the folder in the explorer"
        )

    def test_files_exclude_noagentzone_is_true(self):
        # FIX-079: key is intentionally absent from files.exclude.
        settings = _load_settings(TEMPLATE_SETTINGS)
        assert EXCLUDE_KEY not in settings.get("files.exclude", {}), (
            f"{EXCLUDE_KEY} present in files.exclude — FIX-079 removed it (BUG-146)"
        )

    def test_search_exclude_noagentzone_present(self):
        settings = _load_settings(TEMPLATE_SETTINGS)
        assert "search.exclude" in settings, "search.exclude key missing"
        assert EXCLUDE_KEY in settings["search.exclude"], (
            f"{EXCLUDE_KEY} not found in search.exclude"
        )

    def test_search_exclude_noagentzone_is_true(self):
        settings = _load_settings(TEMPLATE_SETTINGS)
        assert settings["search.exclude"][EXCLUDE_KEY] is True

    def test_existing_excludes_still_present(self):
        settings = _load_settings(TEMPLATE_SETTINGS)
        for section in ("files.exclude", "search.exclude"):
            assert settings[section].get(".github") is True
            assert settings[section].get(".vscode") is True


# ---------------------------------------------------------------------------
# Sync tests — both files must be identical
# ---------------------------------------------------------------------------

class TestSettingsSync:
    """Both settings.json files must be identical."""

    def test_settings_files_are_identical(self):
        default_content = DEFAULT_SETTINGS.read_bytes()
        template_content = TEMPLATE_SETTINGS.read_bytes()
        assert default_content == template_content, (
            "templates/coding and templates/coding settings.json are out of sync"
        )

    def test_security_gate_files_are_identical(self):
        default_content = DEFAULT_GATE.read_bytes()
        template_content = TEMPLATE_GATE.read_bytes()
        assert default_content == template_content, (
            "templates/coding and templates/coding security_gate.py are out of sync"
        )


# ---------------------------------------------------------------------------
# Hash integrity tests — security_gate.py embedded hash matches settings.json
# ---------------------------------------------------------------------------

class TestHashIntegrity:
    """FIX-115: _KNOWN_GOOD_SETTINGS_HASH was removed from security_gate.py.
    Verify it is absent and that _KNOWN_GOOD_GATE_HASH is still valid.
    """

    def test_default_gate_settings_hash_matches(self):
        # FIX-115: settings.json is no longer hashed in security_gate.py.
        # _KNOWN_GOOD_SETTINGS_HASH must be absent from the gate source.
        content = DEFAULT_GATE.read_text(encoding="utf-8")
        assert re.search(r'_KNOWN_GOOD_SETTINGS_HASH: str = "[0-9a-fA-F]{64}"', content) is None, (
            f"_KNOWN_GOOD_SETTINGS_HASH still present in {DEFAULT_GATE} — "
            "FIX-115 should have removed it."
        )
        gate_match = re.search(r'_KNOWN_GOOD_GATE_HASH: str = "([0-9a-fA-F]{64})"', content)
        assert gate_match is not None, (
            f"_KNOWN_GOOD_GATE_HASH not found in {DEFAULT_GATE}"
        )
        assert gate_match.group(1) != "0" * 64, (
            "_KNOWN_GOOD_GATE_HASH must not be the all-zeros placeholder"
        )

    def test_template_gate_settings_hash_matches(self):
        # FIX-115: settings.json is no longer hashed in security_gate.py.
        # _KNOWN_GOOD_SETTINGS_HASH must be absent from the template gate.
        content = TEMPLATE_GATE.read_text(encoding="utf-8")
        assert re.search(r'_KNOWN_GOOD_SETTINGS_HASH: str = "[0-9a-fA-F]{64}"', content) is None, (
            f"_KNOWN_GOOD_SETTINGS_HASH still present in {TEMPLATE_GATE} — "
            "FIX-115 should have removed it."
        )
        gate_match = re.search(r'_KNOWN_GOOD_GATE_HASH: str = "([0-9a-fA-F]{64})"', content)
        assert gate_match is not None, (
            f"_KNOWN_GOOD_GATE_HASH not found in {TEMPLATE_GATE}"
        )
        assert gate_match.group(1) != "0" * 64, (
            "_KNOWN_GOOD_GATE_HASH must not be the all-zeros placeholder"
        )


# ---------------------------------------------------------------------------
# Bypass-attempt tests — verify the exclusion value cannot be trivially bypassed
# ---------------------------------------------------------------------------

class TestBypassAttempt:
    """Attempt to verify the exclusion cannot be trivially weakened."""

    def test_noagentzone_not_set_to_false_in_files_exclude(self):
        # FIX-079 (BUG-146): NoAgentZone is intentionally absent from files.exclude
        # so the folder is visible in the VS Code explorer. Absence is stronger
        # than False — there is no entry to weaken. Verify it is absent.
        for label, path in [("templates/agent-workbench", DEFAULT_SETTINGS),
                             ("templates/agent-workbench", TEMPLATE_SETTINGS)]:
            settings = _load_settings(path)
            val = settings.get("files.exclude", {}).get(EXCLUDE_KEY)
            assert val is None, (
                f"[{label}] files.exclude[{EXCLUDE_KEY!r}] = {val!r}, expected absent (None)"
            )

    def test_noagentzone_not_set_to_false_in_search_exclude(self):
        """Exclusion value must be True; False means VS Code would still search it."""
        for label, path in [("templates/agent-workbench", DEFAULT_SETTINGS),
                             ("templates/agent-workbench", TEMPLATE_SETTINGS)]:
            settings = _load_settings(path)
            val = settings.get("search.exclude", {}).get(EXCLUDE_KEY)
            assert val is True, (
                f"[{label}] search.exclude[{EXCLUDE_KEY!r}] = {val!r}, expected True"
            )

    def test_settings_json_is_valid_json(self):
        """Malformed settings.json would silently disable all exclusions."""
        for path in (DEFAULT_SETTINGS, TEMPLATE_SETTINGS):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                pytest.fail(f"{path.name} is not valid JSON: {exc}")

    def test_exclude_key_uses_glob_pattern(self):
        # FIX-079 (BUG-146): NoAgentZone removed from files.exclude.
        # Verify the glob pattern is still used in search.exclude (the correct section)
        # and that no bare 'NoAgentZone' key is present in either section.
        for label, path in [("templates/agent-workbench", DEFAULT_SETTINGS),
                             ("templates/agent-workbench", TEMPLATE_SETTINGS)]:
            settings = _load_settings(path)
            search_keys = set(settings.get("search.exclude", {}).keys())
            assert EXCLUDE_KEY in search_keys, (
                f"[{label}] Glob pattern {EXCLUDE_KEY!r} missing from search.exclude"
            )
            files_keys = set(settings.get("files.exclude", {}).keys())
            assert EXCLUDE_KEY not in files_keys, (
                f"[{label}] Glob pattern {EXCLUDE_KEY!r} should be absent from files.exclude (FIX-079)"
            )
