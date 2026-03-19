"""Edge-case tests for SAF-011: Hash Update Script — Tester additions

Tests beyond the Developer's baseline.  Focus areas:
  - Boundary conditions (empty files, multiple hash occurrences)
  - Behavioral characterisation (canonical hash with no constant)
  - Output correctness (success messages contain actual hashes)
  - Regex coverage (uppercase hex in existing constant)
  - BUG-027 explicit resolution check (file at exact commented path)
  - Path resolution soundness (resolve() returns absolute paths)
  - Write integrity (bytes on disk match computed bytes)
  - IOError propagation (hard failure on disk write error)

Test IDs:
  TST-642  test_empty_settings_file_hashes_correctly
  TST-643  test_patch_hash_multiple_occurrences_replaces_first_only
  TST-644  test_canonical_hash_missing_gate_constant_returns_raw_hash
  TST-645  test_output_messages_contain_actual_hashes
  TST-646  test_patch_hash_matches_uppercase_hex
  TST-647  test_bug027_resolved_update_hashes_at_commented_path
  TST-648  test_resolve_paths_returns_absolute_paths
  TST-649  test_write_integrity_bytes_match_expected
  TST-650  test_update_hashes_write_error_propagates
"""
from __future__ import annotations

import hashlib
import re
import shutil
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "templates" / "coding" / ".github" / "hooks" / "scripts"
_GATE_PATH = _SCRIPTS_DIR / "security_gate.py"
_SETTINGS_PATH = _REPO_ROOT / "templates" / "coding" / ".vscode" / "settings.json"
_UPDATE_HASHES_PATH = _SCRIPTS_DIR / "update_hashes.py"

# Import module under test (already on sys.path from the main test file,
# but be defensive in case this file is run standalone).
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import update_hashes as uh  # noqa: E402


# ===========================================================================
# TST-642: _sha256_file on a zero-byte file equals the SHA256 empty-string digest
# ===========================================================================

def test_empty_settings_file_hashes_correctly(tmp_path):
    """An empty settings.json must hash to the well-known SHA256 empty digest."""
    empty = tmp_path / "settings.json"
    empty.write_bytes(b"")
    result = uh._sha256_file(empty)
    expected = hashlib.sha256(b"").hexdigest()
    assert result == expected, (
        f"Empty file hash mismatch: {result!r} != {expected!r}"
    )
    assert len(result) == 64, "SHA256 digest must be 64 hex characters"
    assert result == result.lower(), "SHA256 digest must be lowercase"


# ===========================================================================
# TST-643: _patch_hash with count=1 only replaces the FIRST occurrence
# ===========================================================================

def test_patch_hash_multiple_occurrences_replaces_first_only():
    """If the hash constant appears twice, only the first line is patched."""
    old_hash = "1" * 64
    new_hash = "2" * 64
    # Two identical constant lines
    content = (
        b'_KNOWN_GOOD_SETTINGS_HASH: str = "' + old_hash.encode() + b'"\n'
        b'_KNOWN_GOOD_SETTINGS_HASH: str = "' + old_hash.encode() + b'"\n'
    )
    result = uh._patch_hash(content, uh._SETTINGS_HASH_RE, new_hash)
    # First line should now hold new_hash
    assert new_hash.encode() in result
    # Second original occurrence should still be present (only first replaced)
    assert old_hash.encode() in result
    occurrences_of_new = result.count(new_hash.encode())
    assert occurrences_of_new == 1, (
        f"Expected exactly 1 replacement, found {occurrences_of_new}"
    )


# ===========================================================================
# TST-644: _compute_canonical_gate_hash when _KNOWN_GOOD_GATE_HASH is absent
# ===========================================================================

def test_canonical_hash_missing_gate_constant_returns_raw_hash():
    """With no gate constant in the content, re.sub makes no substitution
    and the function returns SHA256 of the unmodified bytes."""
    content = b"no gate constant here\nsome other content\n"
    result = uh._compute_canonical_gate_hash(content)
    expected = hashlib.sha256(content).hexdigest()
    assert result == expected, (
        "When gate constant is absent, canonical hash should equal "
        "SHA256 of unchanged content"
    )


# ===========================================================================
# TST-645: update_hashes() prints both new hash values in stdout
# ===========================================================================

def test_output_messages_contain_actual_hashes(tmp_path, capsys):
    """Success messages must include the newly computed hash values."""
    workspace_root = tmp_path / "workspace"
    vscode_dir = workspace_root / ".vscode"
    vscode_dir.mkdir(parents=True)
    github_dir = workspace_root / ".github" / "hooks" / "scripts"
    github_dir.mkdir(parents=True)

    shutil.copy(_SETTINGS_PATH, vscode_dir / "settings.json")
    shutil.copy(_GATE_PATH, github_dir / "security_gate.py")

    def _mock_resolve():
        return (github_dir / "security_gate.py", vscode_dir / "settings.json")

    with patch.object(uh, "_resolve_paths", _mock_resolve):
        uh.update_hashes()

    captured = capsys.readouterr()

    # Compute what the hashes should be so we can verify the values in output.
    expected_settings_hash = uh._sha256_file(vscode_dir / "settings.json")
    assert expected_settings_hash in captured.out, (
        "Output must contain the new settings hash value"
    )
    # The gate hash appears in output too; just verify it looks like a 64-char hex string.
    hex_pattern = re.compile(r"[0-9a-f]{64}")
    matches = hex_pattern.findall(captured.out)
    assert len(matches) >= 2, (
        f"Expected at least 2 hash values in output, found: {captured.out!r}"
    )
    assert "updated successfully" in captured.out.lower(), (
        "Output must confirm successful update"
    )


# ===========================================================================
# TST-646: _patch_hash regex matches UPPERCASE hex in existing constant
# ===========================================================================

def test_patch_hash_matches_uppercase_hex():
    """The regex [0-9a-fA-F]{64} accepts uppercase hex; replacement always
    produces the lowercase hash from hashlib."""
    old_hash_upper = "ABCDEF" * 10 + "0123" * 1  # 64 chars uppercase hex
    assert len(old_hash_upper) == 64
    new_hash = "f" * 64

    content = (
        b'_KNOWN_GOOD_SETTINGS_HASH: str = "' + old_hash_upper.encode() + b'"\n'
    )
    result = uh._patch_hash(content, uh._SETTINGS_HASH_RE, new_hash)
    assert new_hash.encode() in result, "New hash must be embedded after replacement"
    assert old_hash_upper.encode() not in result, (
        "Uppercase old hash must be gone after replacement"
    )


# ===========================================================================
# TST-647: BUG-027 explicitly resolved — update_hashes.py at the exact path
#          referenced in security_gate.py comments
# ===========================================================================

def test_bug027_resolved_update_hashes_at_commented_path():
    """security_gate.py references .github/hooks/scripts/update_hashes.py in
    its inline comments.  This test verifies the file exists at that relative
    path so BUG-027 cannot silently recur."""
    gate_content = _GATE_PATH.read_text(encoding="utf-8")
    # Extract the relative path referenced in comments.
    # Comments say: .github/hooks/scripts/update_hashes.py
    match = re.search(r"\.github/hooks/scripts/update_hashes\.py", gate_content)
    assert match, (
        "security_gate.py should contain a comment referencing "
        ".github/hooks/scripts/update_hashes.py"
    )
    # The referenced path is relative to templates/coding/ workspace root.
    workspace_root = _REPO_ROOT / "templates" / "coding"
    referenced_path = workspace_root / ".github" / "hooks" / "scripts" / "update_hashes.py"
    assert referenced_path.is_file(), (
        f"BUG-027 regression: update_hashes.py missing from {referenced_path}"
    )


# ===========================================================================
# TST-648: _resolve_paths() returns fully resolved absolute paths (no '..')
# ===========================================================================

def test_resolve_paths_returns_absolute_paths():
    """_resolve_paths must return Path objects with no unresolved traversal
    components.  Both paths must be absolute."""
    gate_path, settings_path = uh._resolve_paths()

    assert gate_path.is_absolute(), "gate_path must be absolute"
    assert settings_path.is_absolute(), "settings_path must be absolute"

    # No '..' segments should survive Path.resolve()
    assert ".." not in gate_path.parts, (
        f"gate_path contains unresolved traversal: {gate_path}"
    )
    assert ".." not in settings_path.parts, (
        f"settings_path contains unresolved traversal: {settings_path}"
    )

    # Gate path should end with security_gate.py in the scripts directory
    assert gate_path.name == "security_gate.py", (
        f"gate_path should point to security_gate.py, got: {gate_path.name}"
    )
    assert settings_path.name == "settings.json", (
        f"settings_path should point to settings.json, got: {settings_path.name}"
    )


# ===========================================================================
# TST-649: Write integrity — bytes written to disk equal the computed bytes
# ===========================================================================

def test_write_integrity_bytes_match_expected(tmp_path):
    """After update_hashes() runs, read the file back and verify the bytes
    are exactly what the computation should have produced."""
    workspace_root = tmp_path / "workspace"
    vscode_dir = workspace_root / ".vscode"
    vscode_dir.mkdir(parents=True)
    github_dir = workspace_root / ".github" / "hooks" / "scripts"
    github_dir.mkdir(parents=True)

    shutil.copy(_SETTINGS_PATH, vscode_dir / "settings.json")
    gate_file = github_dir / "security_gate.py"
    shutil.copy(_GATE_PATH, gate_file)

    def _mock_resolve():
        return (gate_file, vscode_dir / "settings.json")

    with patch.object(uh, "_resolve_paths", _mock_resolve):
        uh.update_hashes()

    # Manually reproduce the expected computation
    new_settings_hash = uh._sha256_file(vscode_dir / "settings.json")
    # Re-read the gate file from disk (as update_hashes just wrote it)
    disk_content = gate_file.read_bytes()

    # Verify both hash constants are present with 64-char lowercase hex values
    settings_match = re.search(
        rb'_KNOWN_GOOD_SETTINGS_HASH: str = "([0-9a-f]{64})"', disk_content
    )
    gate_match = re.search(
        rb'_KNOWN_GOOD_GATE_HASH: str = "([0-9a-f]{64})"', disk_content
    )
    assert settings_match, "On-disk content must have a valid settings hash"
    assert gate_match, "On-disk content must have a valid gate hash"

    embedded_settings = settings_match.group(1).decode()
    assert embedded_settings == new_settings_hash, (
        f"On-disk settings hash {embedded_settings!r} != "
        f"expected {new_settings_hash!r}"
    )

    # Verify the canonical hash self-consistency:
    # hashing the on-disk content canonically (gate hash zeroed) should
    # equal the embedded gate hash.
    canonical_hash = uh._compute_canonical_gate_hash(disk_content)
    embedded_gate = gate_match.group(1).decode()
    assert embedded_gate == canonical_hash, (
        f"Embedded gate hash {embedded_gate!r} does not match "
        f"canonical re-computation {canonical_hash!r}"
    )


# ===========================================================================
# TST-650: IOError during write propagates (no silent swallow)
# ===========================================================================

def test_update_hashes_write_error_propagates(tmp_path):
    """If gate_path.write_bytes() raises an OSError, the exception must
    propagate out of update_hashes() — it must not be silently swallowed."""
    gate_file = tmp_path / "security_gate.py"
    settings_file = tmp_path / "settings.json"
    shutil.copy(_GATE_PATH, gate_file)
    shutil.copy(_SETTINGS_PATH, settings_file)

    def _mock_resolve():
        return (gate_file, settings_file)

    original_write = Path.write_bytes

    def _fail_write(self, data):
        if self.name == "security_gate.py":
            raise OSError("Simulated disk write failure")
        return original_write(self, data)

    with patch.object(uh, "_resolve_paths", _mock_resolve):
        with patch.object(Path, "write_bytes", _fail_write):
            with pytest.raises(OSError, match="Simulated disk write failure"):
                uh.update_hashes()
