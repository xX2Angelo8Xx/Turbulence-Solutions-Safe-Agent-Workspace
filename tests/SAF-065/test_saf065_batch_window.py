"""
SAF-065: Tests for increased parallel denial batch window.

Verifies:
  - _DENY_BATCH_WINDOW_MS is set to 500 (increased from 100)
  - The batch window constant is accessible and correct
  - SAF-061 tests still pass (no regression)
"""
import pathlib

REPO_ROOT = pathlib.Path(__file__).parents[2]
GATE_PATH = (
    REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"
    / "security_gate.py"
)

import importlib.util
import sys


def _load_gate():
    spec = importlib.util.spec_from_file_location("security_gate", GATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_deny_batch_window_is_500():
    """_DENY_BATCH_WINDOW_MS must be 500ms after SAF-065 increase."""
    sg = _load_gate()
    assert sg._DENY_BATCH_WINDOW_MS == 500, (
        f"Expected _DENY_BATCH_WINDOW_MS == 500; got {sg._DENY_BATCH_WINDOW_MS}"
    )


def test_deny_batch_window_greater_than_100():
    """_DENY_BATCH_WINDOW_MS must be larger than the original 100ms."""
    sg = _load_gate()
    assert sg._DENY_BATCH_WINDOW_MS > 100, (
        "_DENY_BATCH_WINDOW_MS must exceed the original 100ms value"
    )


def test_lock_file_name_still_defined():
    """_LOCK_FILE_NAME must still be defined (not accidentally dropped)."""
    sg = _load_gate()
    assert hasattr(sg, "_LOCK_FILE_NAME"), "_LOCK_FILE_NAME constant must exist"
    assert sg._LOCK_FILE_NAME == ".hook_state.lock", (
        f"_LOCK_FILE_NAME must be '.hook_state.lock'; got {sg._LOCK_FILE_NAME!r}"
    )


def test_gate_source_mentions_saf065():
    """security_gate.py must reference SAF-065 to document the change."""
    content = GATE_PATH.read_text(encoding="utf-8")
    assert "SAF-065" in content, "security_gate.py must contain SAF-065 reference"


def test_gate_hash_is_non_trivial():
    """_KNOWN_GOOD_GATE_HASH must not be all zeros (update_hashes.py was run)."""
    sg = _load_gate()
    assert sg._KNOWN_GOOD_GATE_HASH != "0" * 64, (
        "update_hashes.py must have been run; _KNOWN_GOOD_GATE_HASH must not be zeroed"
    )
