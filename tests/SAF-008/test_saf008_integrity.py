"""Tests for SAF-008: Hook File Integrity

Verifies that security_gate.py computes SHA256 hashes of security_gate.py
and .vscode/settings.json on startup, compares them against embedded
known-good values, and denies all tool calls when a mismatch is detected.

Test IDs:
  TST-446  test_compute_file_hash_valid_file
  TST-447  test_compute_file_hash_missing_file
  TST-448  test_compute_file_hash_different_content
  TST-449  test_compute_gate_canonical_hash_returns_string
  TST-450  test_compute_gate_canonical_hash_missing_file
  TST-451  test_compute_gate_canonical_hash_independent_of_gate_hash
  TST-452  test_verify_file_integrity_passes_with_good_hashes
  TST-453  test_verify_file_integrity_fails_on_settings_tamper
  TST-454  test_verify_file_integrity_fails_on_gate_tamper
  TST-455  test_verify_file_integrity_fails_on_missing_settings
  TST-456  test_verify_file_integrity_fails_on_missing_gate
  TST-457  test_main_denies_on_integrity_failure_protection
  TST-458  test_main_denies_with_integrity_warning_message
  TST-459  test_bypass_only_gate_hash_changed
  TST-460  test_bypass_updating_gate_hash_to_match_tampered_file
  TST-461  test_integrity_constants_are_valid_hex
  TST-462  test_verify_file_integrity_cross_platform_paths
"""
from __future__ import annotations

import hashlib
import importlib
import io
import json
import os
import re
import sys
import tempfile
import unittest.mock as mock

import pytest

# ---------------------------------------------------------------------------
# Make security_gate importable from its non-standard location
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "templates", "agent-workbench",
        ".github",
        "hooks",
        "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# ---------------------------------------------------------------------------
# Path to the real templates/coding files (for integration-style checks)
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
_REAL_GATE_FILE = os.path.join(
    _REPO_ROOT, "templates", "agent-workbench", ".github", "hooks", "scripts", "security_gate.py"
)
_REAL_SETTINGS_FILE = os.path.join(
    _REPO_ROOT, "templates", "agent-workbench", ".vscode", "settings.json"
)


# ===========================================================================
# TST-446: _compute_file_hash - valid file returns correct SHA256
# ===========================================================================

def test_compute_file_hash_valid_file(tmp_path):
    # TST-446 - _compute_file_hash returns the correct SHA256 for a real file
    f = tmp_path / "data.bin"
    content = b"hello integrity"
    f.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()
    result = sg._compute_file_hash(str(f))
    assert result == expected


# ===========================================================================
# TST-447: _compute_file_hash - missing file returns None
# ===========================================================================

def test_compute_file_hash_missing_file(tmp_path):
    # TST-447 - non-existent file returns None (fail-closed)
    absent = str(tmp_path / "does_not_exist.bin")
    assert sg._compute_file_hash(absent) is None


# ===========================================================================
# TST-448: _compute_file_hash - different content -> different hash
# ===========================================================================

def test_compute_file_hash_different_content(tmp_path):
    # TST-448 - distinct file contents produce distinct hashes
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_bytes(b"content_a")
    f2.write_bytes(b"content_b")

    h1 = sg._compute_file_hash(str(f1))
    h2 = sg._compute_file_hash(str(f2))
    assert h1 != h2


# ===========================================================================
# TST-449: _compute_gate_canonical_hash - returns 64-char hex string
# ===========================================================================

def test_compute_gate_canonical_hash_returns_string(tmp_path):
    # TST-449 - canonical hash of a file containing the constant returns a
    # valid 64-character lowercase hex string
    gate = tmp_path / "security_gate.py"
    gate.write_bytes(
        b'_KNOWN_GOOD_GATE_HASH: str = "' + b"a" * 64 + b'"\n'
        + b"print('hello')\n"
    )
    result = sg._compute_gate_canonical_hash(str(gate))
    assert result is not None
    assert len(result) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", result)


# ===========================================================================
# TST-450: _compute_gate_canonical_hash - missing file returns None
# ===========================================================================

def test_compute_gate_canonical_hash_missing_file(tmp_path):
    # TST-450 - non-existent file returns None (fail-closed)
    absent = str(tmp_path / "ghost.py")
    assert sg._compute_gate_canonical_hash(absent) is None


# ===========================================================================
# TST-451: Canonical hash is independent of _KNOWN_GOOD_GATE_HASH value
# ===========================================================================

def test_compute_gate_canonical_hash_independent_of_gate_hash(tmp_path):
    # TST-451 - changing only the _KNOWN_GOOD_GATE_HASH value does NOT change
    # the canonical hash (the constant is zeroed before hashing)
    base = b"some important security code\nmore code\n"
    hash_line_a = b'_KNOWN_GOOD_GATE_HASH: str = "' + b"a" * 64 + b'"\n'
    hash_line_b = b'_KNOWN_GOOD_GATE_HASH: str = "' + b"b" * 64 + b'"\n'

    gate_a = tmp_path / "gate_a.py"
    gate_b = tmp_path / "gate_b.py"
    gate_a.write_bytes(base + hash_line_a)
    gate_b.write_bytes(base + hash_line_b)

    canonical_a = sg._compute_gate_canonical_hash(str(gate_a))
    canonical_b = sg._compute_gate_canonical_hash(str(gate_b))
    assert canonical_a is not None
    assert canonical_b is not None
    assert canonical_a == canonical_b


# ===========================================================================
# TST-452: verify_file_integrity - passes with good hashes (real files)
# ===========================================================================

def test_verify_file_integrity_passes_with_good_hashes():
    # TST-452 - The real templates/coding files should pass integrity check
    # because update_hashes.py was run to embed their current hashes.
    result = sg.verify_file_integrity()
    assert result is True, (
        "verify_file_integrity() returned False against the real templates/coding "
        "files.  This means update_hashes.py was not run after the last code "
        "change, or a file was modified without re-running update_hashes.py."
    )


# ===========================================================================
# TST-453: verify_file_integrity - settings.json tamper does NOT fail (FIX-115)
# ===========================================================================

def test_verify_file_integrity_ignores_settings_tamper(monkeypatch):
    # TST-453 / FIX-115 - settings.json changes must NOT fail the integrity
    # check. VS Code auto-migrates settings keys; breaking on that would block
    # all tool calls (BUG-194). Only security_gate.py hash is verified.
    monkeypatch.setattr(sg, "_compute_gate_canonical_hash",
                        lambda path: sg._KNOWN_GOOD_GATE_HASH)
    result = sg.verify_file_integrity()
    assert result is True, (
        "verify_file_integrity() must return True regardless of settings.json state "
        "(FIX-115: settings.json is no longer hash-checked)"
    )


# ===========================================================================
# TST-454: verify_file_integrity - fails when security_gate.py is tampered
# ===========================================================================

def test_verify_file_integrity_fails_on_gate_tamper(tmp_path):
    # TST-454 - a gate file with injected code will not match its embedded
    # canonical hash (bypass-attempt test)
    original_gate_code = (
        b"# original security logic\n"
        + b'_KNOWN_GOOD_GATE_HASH: str = "' + b"0" * 64 + b'"\n'
    )
    canonical_original = hashlib.sha256(original_gate_code).hexdigest()

    tampered_gate_code = (
        b"# TAMPERED: removed security check\ndef verify(): return True\n"
        + b'_KNOWN_GOOD_GATE_HASH: str = "' + canonical_original.encode() + b'"\n'
    )

    gate_file = tmp_path / "security_gate.py"
    gate_file.write_bytes(tampered_gate_code)

    canonical_tampered = sg._compute_gate_canonical_hash(str(gate_file))
    assert canonical_tampered != canonical_original


# ===========================================================================
# TST-455: verify_file_integrity - missing settings.json does NOT fail (FIX-115)
# ===========================================================================

def test_verify_file_integrity_passes_on_missing_settings(monkeypatch):
    # TST-455 / FIX-115 - missing settings.json must NOT cause False.
    # Settings are no longer hash-checked; only security_gate.py is verified.
    monkeypatch.setattr(sg, "_compute_gate_canonical_hash",
                        lambda path: sg._KNOWN_GOOD_GATE_HASH)
    result = sg.verify_file_integrity()
    assert result is True, (
        "verify_file_integrity() must return True even when settings.json is "
        "absent (FIX-115: settings.json is no longer part of the integrity check)"
    )


# ===========================================================================
# TST-456: verify_file_integrity - fails when gate hash cannot be computed
# ===========================================================================

def test_verify_file_integrity_fails_on_missing_gate(monkeypatch):
    # TST-456 - if _compute_gate_canonical_hash returns None, verify_file_integrity
    # returns False (fail-closed). This covers missing or unreadable gate file.
    monkeypatch.setattr(sg, "_compute_gate_canonical_hash", lambda path: None)
    result = sg.verify_file_integrity()
    assert result is False


# ===========================================================================
# TST-457: main() denies all when integrity fails - protection test
# ===========================================================================

def test_main_denies_on_integrity_failure_protection(monkeypatch, capsys):
    # TST-457 - when verify_file_integrity() returns False, main() must output
    # a deny response with exit code 0 (protection test)
    monkeypatch.setattr(sg, "verify_file_integrity", lambda: False)
    monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))

    with pytest.raises(SystemExit) as exc_info:
        sg.main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    decision = payload["hookSpecificOutput"]["permissionDecision"]
    assert decision == "deny"


# ===========================================================================
# TST-458: main() deny response contains integrity warning text
# ===========================================================================

def test_main_denies_with_integrity_warning_message(monkeypatch, capsys):
    # TST-458 - the deny reason includes the integrity-failure warning message
    monkeypatch.setattr(sg, "verify_file_integrity", lambda: False)
    monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))

    with pytest.raises(SystemExit):
        sg.main()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    reason = payload["hookSpecificOutput"].get("permissionDecisionReason", "")
    assert "integrity" in reason.lower() or "SECURITY ALERT" in reason


# ===========================================================================
# TST-459: Bypass - changing only _KNOWN_GOOD_GATE_HASH does NOT bypass
# ===========================================================================

def test_bypass_only_gate_hash_changed(tmp_path):
    # TST-459 - if an attacker changes _KNOWN_GOOD_GATE_HASH only, the
    # canonical hash (which zeros that constant) is unchanged, so the
    # embedded hash will no longer match the canonical hash -> detected
    original_code = b"# real security logic\npasses = True\n"
    constant_line = b'_KNOWN_GOOD_GATE_HASH: str = "' + b"0" * 64 + b'"\n'

    gate_original = tmp_path / "gate_original.py"
    gate_original.write_bytes(original_code + constant_line)

    canonical_original = sg._compute_gate_canonical_hash(str(gate_original))
    assert canonical_original is not None

    attacker_hash = "d" * 64
    modified_gate = tmp_path / "gate_modified.py"
    modified_gate.write_bytes(
        original_code
        + b'_KNOWN_GOOD_GATE_HASH: str = "' + attacker_hash.encode() + b'"\n'
    )

    canonical_modified = sg._compute_gate_canonical_hash(str(modified_gate))
    assert canonical_modified == canonical_original
    assert attacker_hash != canonical_original


# ===========================================================================
# TST-460: Bypass - modifying functional code will not match committed hash
# ===========================================================================

def test_bypass_updating_gate_hash_to_match_tampered_file(tmp_path):
    # TST-460 - if an attacker modifies functional code (not the hash line),
    # the canonical hash changes; the tampered canonical hash != original hash
    original_code = b"# original safety check: return deny\n"
    tampered_code = b"# BYPASS: always return allow\n"
    constant_line = b'_KNOWN_GOOD_GATE_HASH: str = "' + b"0" * 64 + b'"\n'

    gate_original = tmp_path / "gate_orig.py"
    gate_original.write_bytes(original_code + constant_line)
    canonical_original = sg._compute_gate_canonical_hash(str(gate_original))

    gate_tampered = tmp_path / "gate_tampered.py"
    gate_tampered.write_bytes(tampered_code + constant_line)
    canonical_tampered = sg._compute_gate_canonical_hash(str(gate_tampered))

    assert canonical_original != canonical_tampered, (
        "Tampered functional code must produce a different canonical hash"
    )


# ===========================================================================
# TST-461: Integrity constants are 64-char lowercase hex strings (not zeros)
# ===========================================================================

def test_integrity_constants_are_valid_hex():
    # TST-461 / FIX-115 - after update_hashes.py has been run, _KNOWN_GOOD_GATE_HASH
    # must be a valid 64-char lowercase hex string and NOT the all-zero placeholder.
    # _KNOWN_GOOD_SETTINGS_HASH was removed by FIX-115; verify it is absent.
    _hex_re = re.compile(r"^[0-9a-f]{64}$")

    assert not hasattr(sg, "_KNOWN_GOOD_SETTINGS_HASH"), (
        "_KNOWN_GOOD_SETTINGS_HASH must NOT exist in security_gate.py after FIX-115. "
        "Settings hash checking was removed to fix BUG-194."
    )
    assert _hex_re.fullmatch(sg._KNOWN_GOOD_GATE_HASH), (
        f"_KNOWN_GOOD_GATE_HASH is not a valid 64-char hex string: "
        f"{sg._KNOWN_GOOD_GATE_HASH!r}"
    )
    assert sg._KNOWN_GOOD_GATE_HASH != "0" * 64, (
        "_KNOWN_GOOD_GATE_HASH is still the placeholder 64-zero value; "
        "run update_hashes.py to embed the real hash"
    )


# ===========================================================================
# TST-462: Cross-platform paths - gate canonical hash works on any OS
# ===========================================================================

def test_verify_file_integrity_cross_platform_paths(tmp_path):
    # TST-462 / FIX-115 - verify_file_integrity() only checks security_gate.py.
    # Confirm the canonical hash function works correctly on any OS using
    # os.path.abspath for gate path resolution.
    scripts_dir = tmp_path / ".github" / "hooks" / "scripts"
    scripts_dir.mkdir(parents=True)

    gate_base = (
        b"# minimal gate\n"
        + b'_KNOWN_GOOD_GATE_HASH: str = "' + b"0" * 64 + b'"\n'
    )
    canonical_gate_hash = hashlib.sha256(gate_base).hexdigest()

    final_gate = (
        b"# minimal gate\n"
        + b'_KNOWN_GOOD_GATE_HASH: str = "' + canonical_gate_hash.encode() + b'"\n'
    )
    gate_file = scripts_dir / "security_gate.py"
    gate_file.write_bytes(final_gate)

    computed_gate_hash = sg._compute_gate_canonical_hash(str(gate_file))
    assert computed_gate_hash == canonical_gate_hash


# ===========================================================================
# TST-481: _compute_file_hash handles an empty file correctly
# ===========================================================================

def test_compute_file_hash_empty_file(tmp_path):
    # TST-481 - empty file returns SHA256("") (valid hash, not None)
    f = tmp_path / "empty.bin"
    f.write_bytes(b"")
    expected = hashlib.sha256(b"").hexdigest()
    result = sg._compute_file_hash(str(f))
    assert result == expected
    assert len(result) == 64


# ===========================================================================
# TST-482: FIX-115 — _KNOWN_GOOD_SETTINGS_HASH is absent from security_gate.py
# ===========================================================================

def test_settings_hash_constant_absent_from_module(tmp_path):
    # TST-482 / FIX-115 - _KNOWN_GOOD_SETTINGS_HASH must NOT be present in
    # the security_gate module after FIX-115.  Its presence would indicate the
    # fix was not applied or was reverted.
    assert not hasattr(sg, "_KNOWN_GOOD_SETTINGS_HASH"), (
        "_KNOWN_GOOD_SETTINGS_HASH is still present in security_gate.py. "
        "FIX-115 removes it to prevent BUG-194: VS Code settings migrations "
        "breaking the integrity check."
    )
    # Also verify the gate source file itself does not contain the constant
    gate_source = open(_REAL_GATE_FILE, encoding="utf-8").read()
    assert "_KNOWN_GOOD_SETTINGS_HASH" not in gate_source or (
        "_KNOWN_GOOD_SETTINGS_HASH was removed" in gate_source
        or "removed by FIX-115" in gate_source
    ), (
        "_KNOWN_GOOD_SETTINGS_HASH found as an active constant in security_gate.py source. "
        "FIX-115 should have removed it."
    )


# ===========================================================================
# TST-483: _compute_gate_canonical_hash returns hash when no constant line
# ===========================================================================

def test_canonical_hash_no_constant_line(tmp_path):
    # TST-483 - file without the _KNOWN_GOOD_GATE_HASH line still produces
    # a valid hash (no crash), but the result won't match _KNOWN_GOOD_GATE_HASH
    gate = tmp_path / "minimal.py"
    gate.write_bytes(b"# just some code\nprint('hi')\n")
    result = sg._compute_gate_canonical_hash(str(gate))
    # Must return a valid 64-char hex string (not None, not crash)
    assert result is not None
    assert len(result) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", result)
    # Must NOT equal embedded hash (different content)
    assert result != sg._KNOWN_GOOD_GATE_HASH


# ===========================================================================
# TST-484: main() does NOT consume stdin before the integrity check
# ===========================================================================

def test_main_stdin_not_consumed_on_integrity_failure(monkeypatch, capsys):
    # TST-484 - when integrity fails, stdin must NOT be read (reading stdin
    # first would be a logic ordering error).  We patch stdin with a spy that
    # tracks whether .read() is called before the deny response is emitted.
    read_called_order: list[str] = []

    class SpyStdin:
        def read(self, n=-1):
            read_called_order.append("read")
            return ""

    monkeypatch.setattr(sg, "verify_file_integrity", lambda: False)
    monkeypatch.setattr(sys, "stdin", SpyStdin())

    with pytest.raises(SystemExit):
        sg.main()

    captured = capsys.readouterr()
    # deny must be in stdout
    payload = json.loads(captured.out)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    # stdin.read() must NOT have been called at all
    assert "read" not in read_called_order, (
        "stdin was consumed before the integrity check denial was emitted"
    )


# ===========================================================================
# TST-485: verify_file_integrity returns False on unexpected exception
# ===========================================================================

def test_verify_file_integrity_returns_false_on_exception(monkeypatch):
    # TST-485 - any unexpected exception inside verify_file_integrity is
    # caught and causes a fail-closed False return.
    # FIX-115: verify_file_integrity no longer calls _compute_file_hash;
    # it calls _compute_gate_canonical_hash. Patch that instead.
    def boom(path):
        raise RuntimeError("unexpected disk error")

    monkeypatch.setattr(sg, "_compute_gate_canonical_hash", boom)
    result = sg.verify_file_integrity()
    assert result is False


# ===========================================================================
# TST-486: Canonical hash correctly zeroes uppercase hex values
# ===========================================================================

def test_canonical_hash_uppercase_hex_recognized(tmp_path):
    # TST-486 - the regex [0-9a-fA-F]{64} accepts uppercase hex in the
    # _KNOWN_GOOD_GATE_HASH constant; both cases produce the same canonical
    # hash (zeroed), so the scheme is case-insensitive for the hash value.
    base = b"# security code\npasses = True\n"
    lower_line = b'_KNOWN_GOOD_GATE_HASH: str = "' + b"a" * 64 + b'"\n'
    upper_line = b'_KNOWN_GOOD_GATE_HASH: str = "' + b"A" * 64 + b'"\n'

    gate_lower = tmp_path / "gate_lower.py"
    gate_upper = tmp_path / "gate_upper.py"
    gate_lower.write_bytes(base + lower_line)
    gate_upper.write_bytes(base + upper_line)

    canonical_lower = sg._compute_gate_canonical_hash(str(gate_lower))
    canonical_upper = sg._compute_gate_canonical_hash(str(gate_upper))

    assert canonical_lower is not None
    assert canonical_upper is not None
    # Both yield the same canonical hash (uppercase A and lowercase a are both
    # replaced with zeros)
    assert canonical_lower == canonical_upper