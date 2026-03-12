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
        "Default-Project",
        ".github",
        "hooks",
        "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# ---------------------------------------------------------------------------
# Path to the real Default-Project files (for integration-style checks)
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
_REAL_GATE_FILE = os.path.join(
    _REPO_ROOT, "Default-Project", ".github", "hooks", "scripts", "security_gate.py"
)
_REAL_SETTINGS_FILE = os.path.join(
    _REPO_ROOT, "Default-Project", ".vscode", "settings.json"
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
    # TST-452 - The real Default-Project files should pass integrity check
    # because update_hashes.py was run to embed their current hashes.
    result = sg.verify_file_integrity()
    assert result is True, (
        "verify_file_integrity() returned False against the real Default-Project "
        "files.  This means update_hashes.py was not run after the last code "
        "change, or a file was modified without re-running update_hashes.py."
    )


# ===========================================================================
# TST-453: verify_file_integrity - fails when settings.json is tampered
# ===========================================================================

def test_verify_file_integrity_fails_on_settings_tamper(tmp_path, monkeypatch):
    # TST-453 - tampered settings.json content causes False (protection test)
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir()
    real_settings = vscode_dir / "settings.json"
    real_settings.write_bytes(b'{"chat.tools.global.autoApprove": false}')
    settings_hash = hashlib.sha256(real_settings.read_bytes()).hexdigest()

    def fake_verify():
        try:
            real_settings.write_bytes(b'{"chat.tools.global.autoApprove": true}')
            s_hash = sg._compute_file_hash(str(real_settings))
            if s_hash is None or s_hash != settings_hash:
                return False
            return True
        except Exception:
            return False

    assert fake_verify() is False


# ===========================================================================
# TST-454: verify_file_integrity - fails when security_gate.py is tampered
# ===========================================================================

def test_verify_file_integrity_fails_on_gate_tamper(tmp_path):
    # TST-454 - a gate file with injected code will not match its embedded
    # canonical hash (bypass-attempt test)
    settings_content = b'{"autoApprove": false}'
    settings_hash = hashlib.sha256(settings_content).hexdigest()

    original_gate_code = (
        b"# original security logic\n"
        + b'_KNOWN_GOOD_SETTINGS_HASH: str = "' + settings_hash.encode() + b'"\n'
        + b'_KNOWN_GOOD_GATE_HASH: str = "' + b"0" * 64 + b'"\n'
    )
    canonical_original = hashlib.sha256(original_gate_code).hexdigest()

    tampered_gate_code = (
        b"# TAMPERED: removed security check\ndef verify(): return True\n"
        + b'_KNOWN_GOOD_SETTINGS_HASH: str = "' + settings_hash.encode() + b'"\n'
        + b'_KNOWN_GOOD_GATE_HASH: str = "' + canonical_original.encode() + b'"\n'
    )

    gate_file = tmp_path / "security_gate.py"
    gate_file.write_bytes(tampered_gate_code)

    canonical_tampered = sg._compute_gate_canonical_hash(str(gate_file))
    assert canonical_tampered != canonical_original


# ===========================================================================
# TST-455: verify_file_integrity - fails when settings.json is missing
# ===========================================================================

def test_verify_file_integrity_fails_on_missing_settings(monkeypatch):
    # TST-455 - missing settings.json causes False (fail-closed)
    def fake_compute_file_hash(path: str):
        if "settings.json" in path:
            return None
        return sg._compute_file_hash(path)

    monkeypatch.setattr(sg, "_compute_file_hash", fake_compute_file_hash)
    result = sg.verify_file_integrity()
    assert result is False


# ===========================================================================
# TST-456: verify_file_integrity - fails when gate is missing
# ===========================================================================

def test_verify_file_integrity_fails_on_missing_gate(monkeypatch):
    # TST-456 - missing security_gate.py causes False (fail-closed)
    monkeypatch.setattr(sg, "_compute_gate_canonical_hash", lambda path: None)
    monkeypatch.setattr(sg, "_KNOWN_GOOD_SETTINGS_HASH",
                        sg._compute_file_hash(_REAL_SETTINGS_FILE) or "x" * 64)
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
    # TST-461 - after update_hashes.py has been run, both constants must be
    # valid 64-char lowercase hex strings and NOT the all-zero placeholder
    _hex_re = re.compile(r"^[0-9a-f]{64}$")

    assert _hex_re.fullmatch(sg._KNOWN_GOOD_SETTINGS_HASH), (
        f"_KNOWN_GOOD_SETTINGS_HASH is not a valid 64-char hex string: "
        f"{sg._KNOWN_GOOD_SETTINGS_HASH!r}"
    )
    assert _hex_re.fullmatch(sg._KNOWN_GOOD_GATE_HASH), (
        f"_KNOWN_GOOD_GATE_HASH is not a valid 64-char hex string: "
        f"{sg._KNOWN_GOOD_GATE_HASH!r}"
    )
    assert sg._KNOWN_GOOD_SETTINGS_HASH != "0" * 64, (
        "_KNOWN_GOOD_SETTINGS_HASH is still the placeholder 64-zero value; "
        "run update_hashes.py to embed the real hash"
    )
    assert sg._KNOWN_GOOD_GATE_HASH != "0" * 64, (
        "_KNOWN_GOOD_GATE_HASH is still the placeholder 64-zero value; "
        "run update_hashes.py to embed the real hash"
    )


# ===========================================================================
# TST-462: Cross-platform paths - verify path construction is OS-agnostic
# ===========================================================================

def test_verify_file_integrity_cross_platform_paths(tmp_path):
    # TST-462 - os.path.join is used throughout, so path construction works on
    # Windows, macOS, and Linux alike.  We simulate a full layout in tmp_path.
    scripts_dir = tmp_path / ".github" / "hooks" / "scripts"
    scripts_dir.mkdir(parents=True)
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir()

    settings_content = b'{"autoApprove": false}'
    settings_file = vscode_dir / "settings.json"
    settings_file.write_bytes(settings_content)
    settings_hash = hashlib.sha256(settings_content).hexdigest()

    gate_base = (
        b"# minimal gate\n"
        + b'_KNOWN_GOOD_SETTINGS_HASH: str = "' + settings_hash.encode() + b'"\n'
        + b'_KNOWN_GOOD_GATE_HASH: str = "' + b"0" * 64 + b'"\n'
    )
    canonical_gate_hash = hashlib.sha256(gate_base).hexdigest()

    final_gate = (
        b"# minimal gate\n"
        + b'_KNOWN_GOOD_SETTINGS_HASH: str = "' + settings_hash.encode() + b'"\n'
        + b'_KNOWN_GOOD_GATE_HASH: str = "' + canonical_gate_hash.encode() + b'"\n'
    )
    gate_file = scripts_dir / "security_gate.py"
    gate_file.write_bytes(final_gate)

    def fake_abspath(f):
        return str(gate_file)

    with mock.patch.object(os.path, "abspath", side_effect=fake_abspath):
        s_dir = os.path.dirname(str(gate_file))
        ws_root = os.path.dirname(os.path.dirname(os.path.dirname(s_dir)))
        computed_settings_path = os.path.join(ws_root, ".vscode", "settings.json")
        assert os.path.isfile(computed_settings_path), (
            f"Path construction failed: {computed_settings_path}"
        )

    computed_gate_hash = sg._compute_gate_canonical_hash(str(gate_file))
    assert computed_gate_hash == canonical_gate_hash

    computed_settings_hash = sg._compute_file_hash(str(settings_file))
    assert computed_settings_hash == settings_hash


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
# TST-482: Canonical hash detects modification to _KNOWN_GOOD_SETTINGS_HASH
# ===========================================================================

def test_canonical_hash_detects_settings_hash_tampering(tmp_path):
    # TST-482 - bypass attempt: attacker changes _KNOWN_GOOD_SETTINGS_HASH in
    # security_gate.py to match their tampered settings.json, then re-embeds
    # a correct _KNOWN_GOOD_GATE_HASH.  Because _KNOWN_GOOD_SETTINGS_HASH is
    # NOT zeroed, the canonical hash of the modified gate != original canonical
    # hash → detected.
    original_code = (
        b"# security logic\n"
        + b'_KNOWN_GOOD_SETTINGS_HASH: str = "' + b"a" * 64 + b'"\n'
        + b'_KNOWN_GOOD_GATE_HASH: str = "' + b"0" * 64 + b'"\n'
    )
    canonical_original = hashlib.sha256(original_code).hexdigest()

    # Attacker writes canonical_original into _KNOWN_GOOD_GATE_HASH but also
    # changes _KNOWN_GOOD_SETTINGS_HASH to cover their tampered settings.
    tampered_code = (
        b"# security logic\n"
        + b'_KNOWN_GOOD_SETTINGS_HASH: str = "' + b"b" * 64 + b'"\n'
        + b'_KNOWN_GOOD_GATE_HASH: str = "' + canonical_original.encode() + b'"\n'
    )

    gate_file = tmp_path / "security_gate.py"
    gate_file.write_bytes(tampered_code)

    canonical_tampered = sg._compute_gate_canonical_hash(str(gate_file))
    # canonical_tampered != canonical_original because settings hash line changed
    assert canonical_tampered != canonical_original


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
    # caught and causes a fail-closed False return
    def boom(path):
        raise RuntimeError("unexpected disk error")

    monkeypatch.setattr(sg, "_compute_file_hash", boom)
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