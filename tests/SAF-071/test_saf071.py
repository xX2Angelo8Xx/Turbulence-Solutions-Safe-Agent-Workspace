"""SAF-071 tests: Verify security_gate integrity hashes are correct after update."""
import hashlib
import importlib.util
import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPTS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates"
    / "agent-workbench"
    / ".github"
    / "hooks"
    / "scripts"
)
GATE_PATH = SCRIPTS_DIR / "security_gate.py"
WORKSPACE_ROOT = SCRIPTS_DIR.parent.parent.parent
SETTINGS_PATH = WORKSPACE_ROOT / ".vscode" / "settings.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_security_gate():
    spec = importlib.util.spec_from_file_location("security_gate", str(GATE_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _canonical_gate_hash(gate_bytes: bytes) -> str:
    canonical = re.sub(
        rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}',
        b"0" * 64,
        gate_bytes,
    )
    return hashlib.sha256(canonical).hexdigest()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_verify_file_integrity_returns_true():
    """verify_file_integrity() must return True after hash update."""
    mod = _load_security_gate()
    assert mod.verify_file_integrity() is True


def test_settings_hash_matches_actual_file():
    """_KNOWN_GOOD_SETTINGS_HASH must equal SHA256 of the actual settings.json."""
    mod = _load_security_gate()
    actual_hash = _sha256_file(SETTINGS_PATH)
    assert mod._KNOWN_GOOD_SETTINGS_HASH == actual_hash


def test_gate_self_hash_matches_actual_file():
    """_KNOWN_GOOD_GATE_HASH must equal canonical SHA256 of security_gate.py."""
    mod = _load_security_gate()
    gate_bytes = GATE_PATH.read_bytes()
    actual_canonical = _canonical_gate_hash(gate_bytes)
    assert mod._KNOWN_GOOD_GATE_HASH == actual_canonical


def test_hash_constants_are_64_char_hex():
    """Both hash constants must be exactly 64 lowercase hex characters."""
    mod = _load_security_gate()
    hex_re = re.compile(r"^[0-9a-f]{64}$")
    assert hex_re.match(mod._KNOWN_GOOD_SETTINGS_HASH), (
        f"_KNOWN_GOOD_SETTINGS_HASH is not a valid 64-char hex string: "
        f"{mod._KNOWN_GOOD_SETTINGS_HASH!r}"
    )
    assert hex_re.match(mod._KNOWN_GOOD_GATE_HASH), (
        f"_KNOWN_GOOD_GATE_HASH is not a valid 64-char hex string: "
        f"{mod._KNOWN_GOOD_GATE_HASH!r}"
    )


# ---------------------------------------------------------------------------
# Edge-case tests (Tester Agent addition)
# ---------------------------------------------------------------------------

def test_two_hash_constants_are_distinct():
    """_KNOWN_GOOD_SETTINGS_HASH and _KNOWN_GOOD_GATE_HASH protect different
    files and must never collide; a collision would indicate one file was not
    properly hashed."""
    mod = _load_security_gate()
    assert mod._KNOWN_GOOD_SETTINGS_HASH != mod._KNOWN_GOOD_GATE_HASH, (
        "Both hash constants are identical — at least one was not updated correctly."
    )


def test_verify_file_integrity_idempotent():
    """Calling verify_file_integrity() twice in succession must return True
    both times (no side effects that corrupt state between calls)."""
    mod = _load_security_gate()
    assert mod.verify_file_integrity() is True
    assert mod.verify_file_integrity() is True


def test_gate_hash_constant_is_not_placeholder():
    """_KNOWN_GOOD_GATE_HASH must not be the all-zeros placeholder that
    update_hashes.py uses during the canonical-hash computation step."""
    mod = _load_security_gate()
    assert mod._KNOWN_GOOD_GATE_HASH != "0" * 64, (
        "_KNOWN_GOOD_GATE_HASH is still the zeros placeholder — update_hashes.py "
        "did not write back the real hash."
    )


def test_settings_hash_constant_is_not_placeholder():
    """_KNOWN_GOOD_SETTINGS_HASH must not be the old stub value (all-zeros or
    all-same-digit) that would indicate an incomplete hash update."""
    mod = _load_security_gate()
    # All-zeros is the canonical placeholder; all-same-char is a degenerate case
    assert mod._KNOWN_GOOD_SETTINGS_HASH != "0" * 64
    assert len(set(mod._KNOWN_GOOD_SETTINGS_HASH)) > 4, (
        "_KNOWN_GOOD_SETTINGS_HASH looks like a stub/placeholder — too few unique "
        f"hex digits: {mod._KNOWN_GOOD_SETTINGS_HASH!r}"
    )


def test_canonical_hash_computation_is_stable():
    """Running _canonical_gate_hash on the current gate file twice should
    produce the same digest (deterministic, no hidden I/O or randomness)."""
    gate_bytes = GATE_PATH.read_bytes()
    h1 = _canonical_gate_hash(gate_bytes)
    h2 = _canonical_gate_hash(gate_bytes)
    assert h1 == h2, "Canonical hash is not deterministic."


def test_settings_json_file_exists():
    """settings.json must exist at the path expected by security_gate.py.
    If it is missing the hash can never match and the gate will always deny."""
    assert SETTINGS_PATH.exists(), (
        f"settings.json not found at {SETTINGS_PATH}; integrity check will always fail."
    )


def test_gate_file_exists():
    """security_gate.py itself must be present for the self-hash to work."""
    assert GATE_PATH.exists(), f"security_gate.py not found at {GATE_PATH}"
