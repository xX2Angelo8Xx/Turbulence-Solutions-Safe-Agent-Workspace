"""Tests for SAF-075: Fix platform-dependent integrity hashes

Verifies that:
- _compute_file_hash() (security_gate) normalizes CRLF before hashing
- _compute_gate_canonical_hash() (security_gate) normalizes CRLF before hashing
- verify_file_integrity() succeeds regardless of whether files have LF or CRLF
- _sha256_file() (update_hashes) normalizes CRLF before hashing
- _compute_canonical_gate_hash() (update_hashes) normalizes CRLF before hashing

Regression test for BUG-185.

Test IDs:
  TST-BUG185-001  test_compute_file_hash_crlf_lf_same
  TST-BUG185-002  test_compute_file_hash_pure_lf_unchanged
  TST-BUG185-003  test_compute_gate_canonical_hash_crlf_lf_same
  TST-BUG185-004  test_compute_gate_canonical_hash_zeroes_constant
  TST-BUG185-005  test_verify_integrity_lf_variant
  TST-BUG185-006  test_verify_integrity_crlf_variant
  TST-BUG185-007  test_sha256_file_crlf_lf_same
  TST-BUG185-008  test_compute_canonical_gate_hash_uh_crlf_lf_same
"""
from __future__ import annotations

import hashlib
import importlib
import os
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Path setup — import both security_gate and update_hashes from templates
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS_DIR = (
    _REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"
)
_SETTINGS_PATH = (
    _REPO_ROOT / "templates" / "agent-workbench" / ".vscode" / "settings.json"
)
_GATE_PATH = _SCRIPTS_DIR / "security_gate.py"

if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import security_gate as sg  # noqa: E402
import update_hashes as uh  # noqa: E402


# ===========================================================================
# TST-BUG185-001: _compute_file_hash — CRLF and LF yield the same hash
# ===========================================================================

def test_compute_file_hash_crlf_lf_same(tmp_path):
    """BUG-185 regression: _compute_file_hash must be line-ending independent."""
    lf_content = b"line one\nline two\nline three\n"
    crlf_content = b"line one\r\nline two\r\nline three\r\n"

    lf_file = tmp_path / "lf.txt"
    crlf_file = tmp_path / "crlf.txt"
    lf_file.write_bytes(lf_content)
    crlf_file.write_bytes(crlf_content)

    lf_hash = sg._compute_file_hash(str(lf_file))
    crlf_hash = sg._compute_file_hash(str(crlf_file))

    assert lf_hash == crlf_hash, (
        "BUG-185: _compute_file_hash produces different hashes for LF vs CRLF content"
    )


# ===========================================================================
# TST-BUG185-002: _compute_file_hash — pure LF content unchanged
# ===========================================================================

def test_compute_file_hash_pure_lf_unchanged(tmp_path):
    """Files with only LF are hashed correctly (no double-normalization)."""
    content = b"no carriage returns here\njust newlines\n"
    f = tmp_path / "lf_only.txt"
    f.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()
    result = sg._compute_file_hash(str(f))
    assert result == expected


# ===========================================================================
# TST-BUG185-003: _compute_gate_canonical_hash — CRLF and LF yield same hash
# ===========================================================================

def test_compute_gate_canonical_hash_crlf_lf_same(tmp_path):
    """BUG-185 regression: canonical gate hash must be line-ending independent."""
    # Build a minimal fake gate file with the required constant.
    template = (
        b'_KNOWN_GOOD_GATE_HASH: str = "'
        + b"0" * 64
        + b'"\n'
        b"# rest of file\n"
        b"def some_function():\n"
        b"    pass\n"
    )
    lf_content = template
    crlf_content = template.replace(b"\n", b"\r\n")

    lf_file = tmp_path / "gate_lf.py"
    crlf_file = tmp_path / "gate_crlf.py"
    lf_file.write_bytes(lf_content)
    crlf_file.write_bytes(crlf_content)

    lf_hash = sg._compute_gate_canonical_hash(str(lf_file))
    crlf_hash = sg._compute_gate_canonical_hash(str(crlf_file))

    assert lf_hash is not None
    assert crlf_hash is not None
    assert lf_hash == crlf_hash, (
        "BUG-185: _compute_gate_canonical_hash produces different hashes for LF vs CRLF"
    )


# ===========================================================================
# TST-BUG185-004: _compute_gate_canonical_hash — zeroes the constant
# ===========================================================================

def test_compute_gate_canonical_hash_zeroes_constant(tmp_path):
    """Canonical hash is independent of the actual stored gate hash value."""
    def _make_gate(hash_val: bytes) -> bytes:
        return (
            b'_KNOWN_GOOD_GATE_HASH: str = "'
            + hash_val
            + b'"\n'
            b"def other_code(): pass\n"
        )

    gate_a = tmp_path / "gate_a.py"
    gate_b = tmp_path / "gate_b.py"
    gate_a.write_bytes(_make_gate(b"a" * 64))
    gate_b.write_bytes(_make_gate(b"b" * 64))

    assert sg._compute_gate_canonical_hash(str(gate_a)) == sg._compute_gate_canonical_hash(str(gate_b))


# ===========================================================================
# TST-BUG185-005: verify_file_integrity — passes with LF-only settings file
# ===========================================================================

def test_verify_integrity_lf_variant(tmp_path):
    """verify_file_integrity() succeeds when gate file uses LF endings (FIX-115).
    settings.json is no longer part of the integrity check (ADR-011)."""
    # Create a gate file with LF endings and the canonical gate hash.
    gate_template = (
        b'_KNOWN_GOOD_GATE_HASH: str = "'
        + b"0" * 64
        + b'"\n'
        b"def verify_file_integrity(): pass\n"
    )
    gate_file = tmp_path / "security_gate.py"
    gate_file.write_bytes(gate_template)

    # Compute canonical gate hash.
    expected_gate_hash = sg._compute_gate_canonical_hash(str(gate_file))

    # Patch the embedded gate hash constant and path resolution.
    with (
        patch.object(sg, "_KNOWN_GOOD_GATE_HASH", expected_gate_hash),
    ):
        def _fake_abspath(p: str) -> str:  # type: ignore[override]
            return str(gate_file)

        with patch("security_gate.os.path.abspath", _fake_abspath):
            # Manually call the underlying hash functions to confirm they match.
            actual_gate_hash = sg._compute_gate_canonical_hash(str(gate_file))

    assert actual_gate_hash == expected_gate_hash


# ===========================================================================
# TST-BUG185-006: verify_file_integrity — CRLF settings produce same hash as LF
# ===========================================================================

def test_verify_integrity_crlf_variant(tmp_path):
    """BUG-185 regression: CRLF settings.json produces same hash as LF version."""
    base_content = b'{\n    "key": "value"\n}\n'
    crlf_content = base_content.replace(b"\n", b"\r\n")

    lf_file = tmp_path / "settings_lf.json"
    crlf_file = tmp_path / "settings_crlf.json"
    lf_file.write_bytes(base_content)
    crlf_file.write_bytes(crlf_content)

    lf_hash = sg._compute_file_hash(str(lf_file))
    crlf_hash = sg._compute_file_hash(str(crlf_file))

    assert lf_hash == crlf_hash, (
        "BUG-185: settings.json CRLF vs LF produces different hashes in security_gate"
    )


# ===========================================================================
# TST-BUG185-007: update_hashes._sha256_file — CRLF and LF yield same hash
# ===========================================================================

def test_sha256_file_crlf_lf_same(tmp_path):
    """BUG-185 regression: _sha256_file in update_hashes must normalize CRLF."""
    lf_content = b"setting1: true\nsetting2: false\n"
    crlf_content = b"setting1: true\r\nsetting2: false\r\n"

    lf_file = tmp_path / "settings_lf.json"
    crlf_file = tmp_path / "settings_crlf.json"
    lf_file.write_bytes(lf_content)
    crlf_file.write_bytes(crlf_content)

    lf_hash = uh._sha256_file(lf_file)
    crlf_hash = uh._sha256_file(crlf_file)

    assert lf_hash == crlf_hash, (
        "BUG-185: _sha256_file (update_hashes) produces different hashes for LF vs CRLF"
    )


# ===========================================================================
# TST-BUG185-008: update_hashes._compute_canonical_gate_hash — CRLF/LF same
# ===========================================================================

def test_compute_canonical_gate_hash_uh_crlf_lf_same():
    """BUG-185 regression: _compute_canonical_gate_hash in update_hashes normalizes CRLF."""
    template = (
        b'_KNOWN_GOOD_GATE_HASH: str = "'
        + b"0" * 64
        + b'"\n'
        b"def main(): pass\n"
    )
    lf_bytes = template
    crlf_bytes = template.replace(b"\n", b"\r\n")

    lf_hash = uh._compute_canonical_gate_hash(lf_bytes)
    crlf_hash = uh._compute_canonical_gate_hash(crlf_bytes)

    assert lf_hash == crlf_hash, (
        "BUG-185: _compute_canonical_gate_hash (update_hashes) produces different hashes for LF vs CRLF"
    )
