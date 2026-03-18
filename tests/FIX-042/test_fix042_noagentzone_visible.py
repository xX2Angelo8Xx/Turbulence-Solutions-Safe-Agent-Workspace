"""tests/FIX-042/test_fix042_noagentzone_visible.py

Tests for FIX-042: Make NoAgentZone visible in VS Code file explorer.

Verifies that:
- **/NoAgentZone is removed from files.exclude in both settings files
- **/NoAgentZone is still present in search.exclude in both settings files
- .github and .vscode remain in files.exclude (unchanged)
- Default-Project and templates/coding settings.json are identical
- Security gate integrity hashes are valid for both copies
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_SETTINGS = REPO_ROOT / "Default-Project" / ".vscode" / "settings.json"
TEMPLATE_SETTINGS = REPO_ROOT / "templates" / "coding" / ".vscode" / "settings.json"

DEFAULT_GATE = REPO_ROOT / "Default-Project" / ".github" / "hooks" / "scripts" / "security_gate.py"
TEMPLATE_GATE = REPO_ROOT / "templates" / "coding" / ".github" / "hooks" / "scripts" / "security_gate.py"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_settings(path: Path) -> dict:
    return json.loads(path.read_bytes())


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _compute_canonical_gate_hash(content_bytes: bytes) -> str:
    canonical = re.sub(
        rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}',
        b"0" * 64,
        content_bytes,
    )
    return hashlib.sha256(canonical).hexdigest()


def _extract_hash(gate_path: Path, constant_name: str) -> str:
    content = gate_path.read_text(encoding="utf-8")
    pattern = rf'{re.escape(constant_name)}: str = "([0-9a-fA-F]{{64}})"'
    m = re.search(pattern, content)
    assert m is not None, f"{constant_name} not found in {gate_path}"
    return m.group(1)


# ---------------------------------------------------------------------------
# Tests — files.exclude
# ---------------------------------------------------------------------------

def test_noagentzone_not_in_files_exclude_default():
    """NoAgentZone must NOT appear in files.exclude in Default-Project settings."""
    settings = _read_settings(DEFAULT_SETTINGS)
    files_exclude = settings.get("files.exclude", {})
    assert "**/NoAgentZone" not in files_exclude, (
        "**/NoAgentZone found in files.exclude — it would hide the folder from human users"
    )


def test_noagentzone_not_in_files_exclude_template():
    """NoAgentZone must NOT appear in files.exclude in templates/coding settings."""
    settings = _read_settings(TEMPLATE_SETTINGS)
    files_exclude = settings.get("files.exclude", {})
    assert "**/NoAgentZone" not in files_exclude, (
        "**/NoAgentZone found in files.exclude — it would hide the folder from human users"
    )


# ---------------------------------------------------------------------------
# Tests — search.exclude
# ---------------------------------------------------------------------------

def test_noagentzone_still_in_search_exclude_default():
    """NoAgentZone must still be in search.exclude in Default-Project settings."""
    settings = _read_settings(DEFAULT_SETTINGS)
    search_exclude = settings.get("search.exclude", {})
    assert "**/NoAgentZone" in search_exclude, (
        "**/NoAgentZone missing from search.exclude — agents could discover its contents via search"
    )
    assert search_exclude["**/NoAgentZone"] is True


def test_noagentzone_still_in_search_exclude_template():
    """NoAgentZone must still be in search.exclude in templates/coding settings."""
    settings = _read_settings(TEMPLATE_SETTINGS)
    search_exclude = settings.get("search.exclude", {})
    assert "**/NoAgentZone" in search_exclude, (
        "**/NoAgentZone missing from search.exclude — agents could discover its contents via search"
    )
    assert search_exclude["**/NoAgentZone"] is True


# ---------------------------------------------------------------------------
# Tests — other files.exclude entries unchanged
# ---------------------------------------------------------------------------

def test_github_still_in_files_exclude():
    """.github must remain in files.exclude (unchanged by this fix)."""
    settings_default = _read_settings(DEFAULT_SETTINGS)
    settings_template = _read_settings(TEMPLATE_SETTINGS)
    assert settings_default.get("files.exclude", {}).get(".github") is True
    assert settings_template.get("files.exclude", {}).get(".github") is True


def test_vscode_still_in_files_exclude():
    """.vscode must remain in files.exclude (unchanged by this fix)."""
    settings_default = _read_settings(DEFAULT_SETTINGS)
    settings_template = _read_settings(TEMPLATE_SETTINGS)
    assert settings_default.get("files.exclude", {}).get(".vscode") is True
    assert settings_template.get("files.exclude", {}).get(".vscode") is True


# ---------------------------------------------------------------------------
# Tests — sync
# ---------------------------------------------------------------------------

def test_settings_files_are_in_sync():
    """Default-Project and templates/coding settings.json must be byte-identical."""
    default_bytes = DEFAULT_SETTINGS.read_bytes()
    template_bytes = TEMPLATE_SETTINGS.read_bytes()
    assert default_bytes == template_bytes, (
        "settings.json files are not in sync between Default-Project and templates/coding"
    )


# ---------------------------------------------------------------------------
# Tests — integrity hashes
# ---------------------------------------------------------------------------

def test_security_gate_hashes_valid():
    """SHA256 integrity hashes in both security_gate.py copies must match actual files."""
    for gate_path, settings_path, label in [
        (DEFAULT_GATE, DEFAULT_SETTINGS, "Default-Project"),
        (TEMPLATE_GATE, TEMPLATE_SETTINGS, "templates/coding"),
    ]:
        # Verify settings hash
        embedded_settings_hash = _extract_hash(gate_path, "_KNOWN_GOOD_SETTINGS_HASH")
        actual_settings_hash = _sha256_file(settings_path)
        assert embedded_settings_hash == actual_settings_hash, (
            f"[{label}] _KNOWN_GOOD_SETTINGS_HASH mismatch: "
            f"embedded={embedded_settings_hash}, actual={actual_settings_hash}"
        )

        # Verify gate canonical hash
        embedded_gate_hash = _extract_hash(gate_path, "_KNOWN_GOOD_GATE_HASH")
        gate_bytes = gate_path.read_bytes()
        actual_gate_hash = _compute_canonical_gate_hash(gate_bytes)
        assert embedded_gate_hash == actual_gate_hash, (
            f"[{label}] _KNOWN_GOOD_GATE_HASH mismatch: "
            f"embedded={embedded_gate_hash}, actual={actual_gate_hash}"
        )
