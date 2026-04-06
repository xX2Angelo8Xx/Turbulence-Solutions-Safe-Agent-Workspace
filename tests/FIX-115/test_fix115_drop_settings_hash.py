"""FIX-115: Drop settings.json from integrity hash check

Regression tests verifying:
- _KNOWN_GOOD_SETTINGS_HASH is absent from security_gate.py
- verify_file_integrity() returns True even if settings.json is missing/modified
- update_hashes.py no longer embeds a settings hash
- _SETTINGS_HASH_RE is absent from update_hashes.py
- Gate self-hash still works correctly

These tests prevent BUG-194 from recurring: VS Code auto-migrating settings
keys used to break verify_file_integrity() and block all tool calls.
"""
from __future__ import annotations

import hashlib
import importlib
import re
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"
_GATE_PATH = _SCRIPTS_DIR / "security_gate.py"
_SETTINGS_PATH = _REPO_ROOT / "templates" / "agent-workbench" / ".vscode" / "settings.json"
_UPDATE_HASHES_PATH = _SCRIPTS_DIR / "update_hashes.py"

if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import security_gate as sg  # noqa: E402
import update_hashes as uh  # noqa: E402


# ===========================================================================
# TST-FIX115-001: _KNOWN_GOOD_SETTINGS_HASH is absent from security_gate module
# ===========================================================================

def test_settings_hash_constant_absent_from_module():
    """FIX-115 regression: _KNOWN_GOOD_SETTINGS_HASH must NOT be a module-level
    constant in security_gate.py. Its presence would reintroduce BUG-194."""
    assert not hasattr(sg, "_KNOWN_GOOD_SETTINGS_HASH"), (
        "_KNOWN_GOOD_SETTINGS_HASH is present in security_gate.py. "
        "FIX-115 removes this constant to prevent BUG-194."
    )


# ===========================================================================
# TST-FIX115-002: _KNOWN_GOOD_SETTINGS_HASH is absent from gate source file
# ===========================================================================

def test_settings_hash_constant_absent_from_source():
    """FIX-115 regression: verify _KNOWN_GOOD_SETTINGS_HASH is not a live
    constant definition in security_gate.py source."""
    content = _GATE_PATH.read_text(encoding="utf-8")
    m = re.search(r'_KNOWN_GOOD_SETTINGS_HASH: str = "[0-9a-fA-F]{64}"', content)
    assert m is None, (
        "_KNOWN_GOOD_SETTINGS_HASH constant found in security_gate.py source. "
        "FIX-115 should have removed it."
    )


# ===========================================================================
# TST-FIX115-003: verify_file_integrity passes even when settings.json missing
# ===========================================================================

def test_verify_file_integrity_passes_with_missing_settings(monkeypatch):
    """FIX-115 regression (BUG-194): missing settings.json must NOT cause
    verify_file_integrity() to return False. Only gate hash is checked."""
    # Patch gate canonical hash to return the known-good value unconditionally
    monkeypatch.setattr(sg, "_compute_gate_canonical_hash",
                        lambda path: sg._KNOWN_GOOD_GATE_HASH)
    result = sg.verify_file_integrity()
    assert result is True, (
        "verify_file_integrity() returned False — settings.json absence should "
        "not matter after FIX-115."
    )


# ===========================================================================
# TST-FIX115-004: verify_file_integrity passes even when settings.json is modified
# ===========================================================================

def test_verify_file_integrity_passes_with_modified_settings(tmp_path, monkeypatch):
    """FIX-115 regression (BUG-194): a modified settings.json (e.g., VS Code
    migration) must NOT cause verify_file_integrity() to return False."""
    # Simulate VS Code replacing keys in settings.json
    fake_settings = tmp_path / ".vscode" / "settings.json"
    fake_settings.parent.mkdir(parents=True)
    fake_settings.write_bytes(b'{"chat.agent.sandboxFileSystem.mac": true}')

    # Patch gate hash so integrity passes
    monkeypatch.setattr(sg, "_compute_gate_canonical_hash",
                        lambda path: sg._KNOWN_GOOD_GATE_HASH)

    result = sg.verify_file_integrity()
    assert result is True, (
        "verify_file_integrity() returned False despite only settings.json changing. "
        "This is BUG-194 \u2014 FIX-115 must prevent this."
    )


# ===========================================================================
# TST-FIX115-005: verify_file_integrity still fails when gate is tampered
# ===========================================================================

def test_verify_file_integrity_still_fails_on_gate_tamper(monkeypatch):
    """Gate self-hash check must still work: tampering with security_gate.py
    must still cause verify_file_integrity() to return False."""
    # Return a wrong hash to simulate a tampered gate
    monkeypatch.setattr(sg, "_compute_gate_canonical_hash",
                        lambda path: "0" * 64)
    result = sg.verify_file_integrity()
    assert result is False, (
        "verify_file_integrity() must still fail when gate hash doesn't match "
        "(gate tamper detection must be intact after FIX-115)"
    )


# ===========================================================================
# TST-FIX115-006: _SETTINGS_HASH_RE absent from update_hashes module
# ===========================================================================

def test_settings_hash_re_absent_from_update_hashes():
    """FIX-115 regression: _SETTINGS_HASH_RE must NOT exist in update_hashes.
    Its presence would indicate the settings hash was not fully removed."""
    assert not hasattr(uh, "_SETTINGS_HASH_RE"), (
        "_SETTINGS_HASH_RE is still present in update_hashes.py. "
        "FIX-115 removes it since settings hash is no longer embedded."
    )


# ===========================================================================
# TST-FIX115-007: update_hashes._resolve_paths returns a single Path
# ===========================================================================

def test_update_hashes_resolve_paths_returns_single_path():
    """FIX-115: _resolve_paths() must return a single Path (gate path only),
    not a tuple. The settings path is no longer resolved."""
    result = uh._resolve_paths()
    assert isinstance(result, Path), (
        f"_resolve_paths() should return a Path, got: {type(result)}"
    )
    assert result.name == "security_gate.py"


# ===========================================================================
# TST-FIX115-008: update_hashes runs without settings.json present
# ===========================================================================

def test_update_hashes_works_without_settings_json(tmp_path):
    """FIX-115: update_hashes.py must succeed even when no settings.json
    exists anywhere near the workspace."""
    github_dir = tmp_path / ".github" / "hooks" / "scripts"
    github_dir.mkdir(parents=True)
    gate_file = github_dir / "security_gate.py"
    shutil.copy(_GATE_PATH, gate_file)
    # Deliberately do NOT create any settings.json

    def _mock_resolve():
        return gate_file

    with patch.object(uh, "_resolve_paths", _mock_resolve):
        # Must not raise SystemExit or any other exception
        uh.update_hashes()

    # Gate must still have a valid hash
    content = gate_file.read_bytes()
    m = re.search(rb'_KNOWN_GOOD_GATE_HASH: str = "([0-9a-f]{64})"', content)
    assert m is not None, "Gate hash must be embedded after update"


# ===========================================================================
# TST-FIX115-009: update_hashes output contains no settings hash line
# ===========================================================================

def test_update_hashes_output_no_settings_mention(tmp_path, capsys):
    """FIX-115: update_hashes.py output must not mention settings hash."""
    github_dir = tmp_path / ".github" / "hooks" / "scripts"
    github_dir.mkdir(parents=True)
    gate_file = github_dir / "security_gate.py"
    shutil.copy(_GATE_PATH, gate_file)

    def _mock_resolve():
        return gate_file

    with patch.object(uh, "_resolve_paths", _mock_resolve):
        uh.update_hashes()

    captured = capsys.readouterr()
    assert "_KNOWN_GOOD_SETTINGS_HASH" not in captured.out, (
        "update_hashes.py output must not mention _KNOWN_GOOD_SETTINGS_HASH after FIX-115"
    )


# ===========================================================================
# TST-FIX115-010: Real security_gate.py verify_file_integrity passes
# ===========================================================================

def test_real_security_gate_integrity_passes():
    """After FIX-115, verify_file_integrity() on the real security_gate.py
    must return True without depending on settings.json at all."""
    result = sg.verify_file_integrity()
    assert result is True, (
        "verify_file_integrity() returned False for the real security_gate.py. "
        "The gate hash may be stale \u2014 run update_hashes.py to fix."
    )
