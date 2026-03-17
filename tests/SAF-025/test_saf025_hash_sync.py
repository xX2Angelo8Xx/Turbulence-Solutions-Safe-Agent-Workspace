"""Tests for SAF-025: Update security_gate.py Integrity Hashes

Verifies that SHA256 integrity hashes in security_gate.py are correct for the
final v2.0.0 security files, and that Default-Project/ and templates/coding/
are byte-for-byte identical for all security-critical hook files.

Test IDs:
  TST-1632  test_security_gate_files_are_identical
  TST-1633  test_settings_json_files_are_identical
  TST-1634  test_zone_classifier_files_are_identical
  TST-1635  test_update_hashes_files_are_identical
  TST-1636  test_require_approval_json_files_are_identical
  TST-1637  test_require_approval_ps1_files_are_identical
  TST-1638  test_require_approval_sh_files_are_identical
  TST-1639  test_embedded_settings_hash_matches_actual_file
  TST-1640  test_embedded_gate_hash_matches_canonical_hash
  TST-1641  test_verify_file_integrity_passes_default_project
  TST-1642  test_verify_file_integrity_passes_templates_copy
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_DP_SCRIPTS = _REPO_ROOT / "Default-Project" / ".github" / "hooks" / "scripts"
_TC_SCRIPTS = _REPO_ROOT / "templates" / "coding" / ".github" / "hooks" / "scripts"

_DP_HOOKS = _REPO_ROOT / "Default-Project" / ".github" / "hooks"
_TC_HOOKS = _REPO_ROOT / "templates" / "coding" / ".github" / "hooks"

_DP_GATE = _DP_SCRIPTS / "security_gate.py"
_TC_GATE = _TC_SCRIPTS / "security_gate.py"

_DP_SETTINGS = _REPO_ROOT / "Default-Project" / ".vscode" / "settings.json"
_TC_SETTINGS = _REPO_ROOT / "templates" / "coding" / ".vscode" / "settings.json"

# Make security_gate importable
if str(_DP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_DP_SCRIPTS))

import security_gate as sg  # noqa: E402


# ===========================================================================
# TST-1632: security_gate.py is byte-for-byte identical in both locations
# ===========================================================================

def test_security_gate_files_are_identical():
    # TST-1632 — security_gate.py in Default-Project and templates/coding must
    # be byte-for-byte identical so agent workspaces receive the same protection.
    assert _DP_GATE.is_file(), f"Missing: {_DP_GATE}"
    assert _TC_GATE.is_file(), f"Missing: {_TC_GATE}"
    assert _DP_GATE.read_bytes() == _TC_GATE.read_bytes(), (
        "security_gate.py differs between Default-Project and templates/coding. "
        "Run sync to make them identical."
    )


# ===========================================================================
# TST-1633: settings.json is byte-for-byte identical in both locations
# ===========================================================================

def test_settings_json_files_are_identical():
    # TST-1633 — settings.json must be identical so the embedded hash is valid
    # in both deployment locations.
    assert _DP_SETTINGS.is_file(), f"Missing: {_DP_SETTINGS}"
    assert _TC_SETTINGS.is_file(), f"Missing: {_TC_SETTINGS}"
    assert _DP_SETTINGS.read_bytes() == _TC_SETTINGS.read_bytes(), (
        "settings.json differs between Default-Project and templates/coding."
    )


# ===========================================================================
# TST-1634: zone_classifier.py is byte-for-byte identical in both locations
# ===========================================================================

def test_zone_classifier_files_are_identical():
    # TST-1634 — zone_classifier.py must be in sync between both locations.
    dp = _DP_SCRIPTS / "zone_classifier.py"
    tc = _TC_SCRIPTS / "zone_classifier.py"
    assert dp.is_file(), f"Missing: {dp}"
    assert tc.is_file(), f"Missing: {tc}"
    assert dp.read_bytes() == tc.read_bytes(), (
        "zone_classifier.py differs between Default-Project and templates/coding."
    )


# ===========================================================================
# TST-1635: update_hashes.py is byte-for-byte identical in both locations
# ===========================================================================

def test_update_hashes_files_are_identical():
    # TST-1635 — update_hashes.py must be in sync between both locations.
    dp = _DP_SCRIPTS / "update_hashes.py"
    tc = _TC_SCRIPTS / "update_hashes.py"
    assert dp.is_file(), f"Missing: {dp}"
    assert tc.is_file(), f"Missing: {tc}"
    assert dp.read_bytes() == tc.read_bytes(), (
        "update_hashes.py differs between Default-Project and templates/coding."
    )


# ===========================================================================
# TST-1636: require-approval.json is byte-for-byte identical in both locations
# ===========================================================================

def test_require_approval_json_files_are_identical():
    # TST-1636 — require-approval.json must be in sync between both locations.
    dp = _DP_HOOKS / "require-approval.json"
    tc = _TC_HOOKS / "require-approval.json"
    assert dp.is_file(), f"Missing: {dp}"
    assert tc.is_file(), f"Missing: {tc}"
    assert dp.read_bytes() == tc.read_bytes(), (
        "require-approval.json differs between Default-Project and templates/coding."
    )


# ===========================================================================
# TST-1637: require-approval.ps1 is byte-for-byte identical in both locations
# ===========================================================================

def test_require_approval_ps1_files_are_identical():
    # TST-1637 — require-approval.ps1 must be in sync between both locations.
    dp = _DP_SCRIPTS / "require-approval.ps1"
    tc = _TC_SCRIPTS / "require-approval.ps1"
    assert dp.is_file(), f"Missing: {dp}"
    assert tc.is_file(), f"Missing: {tc}"
    assert dp.read_bytes() == tc.read_bytes(), (
        "require-approval.ps1 differs between Default-Project and templates/coding."
    )


# ===========================================================================
# TST-1638: require-approval.sh is byte-for-byte identical in both locations
# ===========================================================================

def test_require_approval_sh_files_are_identical():
    # TST-1638 — require-approval.sh must be in sync between both locations.
    dp = _DP_SCRIPTS / "require-approval.sh"
    tc = _TC_SCRIPTS / "require-approval.sh"
    assert dp.is_file(), f"Missing: {dp}"
    assert tc.is_file(), f"Missing: {tc}"
    assert dp.read_bytes() == tc.read_bytes(), (
        "require-approval.sh differs between Default-Project and templates/coding."
    )


# ===========================================================================
# TST-1639: Embedded settings hash matches actual settings.json
# ===========================================================================

def test_embedded_settings_hash_matches_actual_file():
    # TST-1639 — The _KNOWN_GOOD_SETTINGS_HASH constant in security_gate.py
    # must equal the SHA256 of the actual settings.json on disk.
    content = _DP_GATE.read_bytes()
    m = re.search(rb'_KNOWN_GOOD_SETTINGS_HASH: str = "([0-9a-f]{64})"', content)
    assert m is not None, "_KNOWN_GOOD_SETTINGS_HASH constant not found in security_gate.py"
    embedded = m.group(1).decode()

    actual = hashlib.sha256(_DP_SETTINGS.read_bytes()).hexdigest()
    assert embedded == actual, (
        f"Embedded settings hash ({embedded[:16]}…) does not match "
        f"actual settings.json hash ({actual[:16]}…). "
        "Run update_hashes.py to fix."
    )


# ===========================================================================
# TST-1640: Embedded gate hash matches canonical gate hash
# ===========================================================================

def test_embedded_gate_hash_matches_canonical_hash():
    # TST-1640 — The _KNOWN_GOOD_GATE_HASH constant in security_gate.py must
    # equal the canonical SHA256 of security_gate.py itself (with the hash
    # constant zeroed out before hashing).
    content = _DP_GATE.read_bytes()

    # Extract embedded hash
    m = re.search(rb'_KNOWN_GOOD_GATE_HASH: str = "([0-9a-f]{64})"', content)
    assert m is not None, "_KNOWN_GOOD_GATE_HASH constant not found in security_gate.py"
    embedded = m.group(1).decode()

    # Compute canonical hash (zero out the gate hash constant before hashing)
    canonical = re.sub(
        rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}',
        b"0" * 64,
        content,
    )
    actual = hashlib.sha256(canonical).hexdigest()

    assert embedded == actual, (
        f"Embedded gate hash ({embedded[:16]}…) does not match "
        f"canonical gate hash ({actual[:16]}…). "
        "Run update_hashes.py to fix."
    )


# ===========================================================================
# TST-1641: verify_file_integrity() returns True for Default-Project files
# ===========================================================================

def test_verify_file_integrity_passes_default_project():
    # TST-1641 — The real Default-Project security_gate.py should pass its own
    # integrity check, confirming hashes were correctly updated.
    result = sg.verify_file_integrity()
    assert result is True, (
        "verify_file_integrity() returned False for Default-Project files. "
        "The embedded hashes are stale — run update_hashes.py."
    )


# ===========================================================================
# TST-1642: templates/coding security_gate.py has correct embedded hashes
# ===========================================================================

def test_verify_file_integrity_passes_templates_copy():
    # TST-1642 — The templates/coding security_gate.py must contain the same
    # embedded hashes as Default-Project's copy. Since TST-1632 verified the
    # files are byte-for-byte identical, we verify the hash constants are present
    # and non-zero in the templates copy, avoiding any importlib side effects
    # (no __pycache__ must be written into templates/coding).
    content = _TC_GATE.read_bytes()

    m_settings = re.search(
        rb'_KNOWN_GOOD_SETTINGS_HASH: str = "([0-9a-f]{64})"', content
    )
    m_gate = re.search(
        rb'_KNOWN_GOOD_GATE_HASH: str = "([0-9a-f]{64})"', content
    )

    assert m_settings is not None, (
        "_KNOWN_GOOD_SETTINGS_HASH not found in templates/coding security_gate.py"
    )
    assert m_gate is not None, (
        "_KNOWN_GOOD_GATE_HASH not found in templates/coding security_gate.py"
    )

    embedded_settings = m_settings.group(1).decode()
    embedded_gate = m_gate.group(1).decode()

    # Hashes must not be all-zeros (placeholder value)
    assert embedded_settings != "0" * 64, (
        "templates/coding security_gate.py has placeholder settings hash (all zeros)"
    )
    assert embedded_gate != "0" * 64, (
        "templates/coding security_gate.py has placeholder gate hash (all zeros)"
    )

    # Verify settings hash matches actual settings.json
    actual_settings = hashlib.sha256(_TC_SETTINGS.read_bytes()).hexdigest()
    assert embedded_settings == actual_settings, (
        f"templates/coding embedded settings hash does not match "
        f"templates/coding settings.json"
    )

    # Verify gate hash matches canonical gate hash
    canonical = re.sub(
        rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}',
        b"0" * 64,
        content,
    )
    actual_gate = hashlib.sha256(canonical).hexdigest()
    assert embedded_gate == actual_gate, (
        f"templates/coding embedded gate hash does not match canonical gate hash"
    )


# ===========================================================================
# TST-1645: Hash constants appear exactly once in security_gate.py
# ===========================================================================

def test_hash_constants_appear_exactly_once():
    # TST-1645 (Tester edge-case) — Each hash constant must appear exactly once.
    # More than one occurrence would mean a duplicate definition that could
    # confuse update_hashes.py and lead to stale embedded hashes.
    content = _DP_GATE.read_bytes()

    settings_occurrences = len(re.findall(rb'_KNOWN_GOOD_SETTINGS_HASH: str = "[0-9a-fA-F]{64}"', content))
    gate_occurrences = len(re.findall(rb'_KNOWN_GOOD_GATE_HASH: str = "[0-9a-fA-F]{64}"', content))

    assert settings_occurrences == 1, (
        f"_KNOWN_GOOD_SETTINGS_HASH constant appears {settings_occurrences} times "
        f"in security_gate.py — expected exactly 1"
    )
    assert gate_occurrences == 1, (
        f"_KNOWN_GOOD_GATE_HASH constant appears {gate_occurrences} times "
        f"in security_gate.py — expected exactly 1"
    )


# ===========================================================================
# TST-1646: Canonical gate hash is NOT affected by settings hash value
# ===========================================================================

def test_canonical_hash_independent_of_settings_hash():
    # TST-1646 (Tester edge-case) — The canonical hash computation only zeros
    # _KNOWN_GOOD_GATE_HASH, not _KNOWN_GOOD_SETTINGS_HASH. If settings hash were
    # also zeroed, the canonical computation would be wrong.
    content = _DP_GATE.read_bytes()

    # Compute canonical hash using the standard (gate-only zeroing) approach
    canonical_standard = re.sub(
        rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}',
        b"0" * 64,
        content,
    )
    hash_standard = hashlib.sha256(canonical_standard).hexdigest()

    # Compute with BOTH constants zeroed out
    canonical_both = re.sub(
        rb'(?<=_KNOWN_GOOD_SETTINGS_HASH: str = ")[0-9a-fA-F]{64}',
        b"0" * 64,
        canonical_standard,
    )
    hash_both = hashlib.sha256(canonical_both).hexdigest()

    # The two hashes MUST differ — if they are equal, the settings hash constant
    # does not appear in the file at all, which is a bug.
    assert hash_standard != hash_both, (
        "Canonical hash is identical whether or not settings hash is zeroed. "
        "_KNOWN_GOOD_SETTINGS_HASH may be absent from security_gate.py."
    )

    # The embedded gate hash must match the STANDARD (gate-only) approach, not
    # the both-zeroed approach.
    m = re.search(rb'_KNOWN_GOOD_GATE_HASH: str = "([0-9a-f]{64})"', content)
    assert m is not None, "_KNOWN_GOOD_GATE_HASH not found"
    embedded = m.group(1).decode()
    assert embedded == hash_standard, (
        "Embedded gate hash does not match gate-only canonical hash. "
        "update_hashes.py may be zeroing too many constants."
    )


# ===========================================================================
# TST-1647: No __pycache__ in templates/coding
# ===========================================================================

def test_no_pycache_in_templates_coding():
    # TST-1647 (Tester edge-case) — Importing security_gate from the
    # templates/coding location must not create a __pycache__ directory there.
    # Such a directory would pollute the template that gets copied to agent
    # workspaces on first use.
    tc_pycache = _TC_SCRIPTS / "__pycache__"
    assert not tc_pycache.exists(), (
        f"__pycache__ directory was created inside templates/coding: {tc_pycache}. "
        "This pollutes the template. The import chain must avoid writing bytecode "
        "into templates/coding (use sys.path with Default-Project only)."
    )
