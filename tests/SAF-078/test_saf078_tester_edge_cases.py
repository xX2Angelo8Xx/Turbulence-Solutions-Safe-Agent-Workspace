"""Tester edge-case tests for SAF-078: Feature Behavior Locking via Snapshots.

Covers scenarios not exercised by the Developer's unit tests:
- Bypass-attempt: decision change cannot silently pass without the flag
- --update-snapshots fallback when snapshot file cannot be found by description
- Snapshot assertion includes input/ws_root detail lines
- update_snapshots fixture default is False (flag not accidentally always-on)
- README procedure command is runnable at the documented scope
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOTS_DIR = REPO_ROOT / "tests" / "snapshots" / "security_gate"
TEST_SNAPSHOTS_PY = SNAPSHOTS_DIR / "test_snapshots.py"
SNAPSHOTS_README = REPO_ROOT / "tests" / "snapshots" / "README.md"

_SCRIPTS_DIR = str(
    REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_test_module(module_name: str = "_ts_edge"):
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, TEST_SNAPSHOTS_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_snapshot(description: str, decision: str) -> dict:
    return {
        "description": description,
        "ws_root": "/workspace",
        "input": {"tool_name": "read_file", "filePath": "/workspace/main.py"},
        "expected_decision": decision,
    }


# ---------------------------------------------------------------------------
# Security: bypass-attempt test
# Any decision change MUST produce an AssertionError; there is no silent pass.
# ---------------------------------------------------------------------------

def test_decision_change_never_passes_silently():
    """Decision change without --update-snapshots is always an AssertionError (not silent)."""
    import security_gate as sg

    mod = _load_test_module("_ts_bypass")
    snapshot = _make_snapshot("bypass-attempt-scenario", "deny")

    # Simulate: gate returns "allow" but snapshot says "deny"
    with patch.object(sg, "decide", return_value="allow"):
        # Must raise — cannot silently pass
        with pytest.raises(AssertionError) as exc_info:
            mod.test_security_gate_snapshot(snapshot, update_snapshots=False)

    error_msg = str(exc_info.value)
    # Must explicitly mention the change to be actionable
    assert "deny" in error_msg
    assert "allow" in error_msg
    assert "bypass-attempt-scenario" in error_msg


def test_bypass_with_update_flag_but_no_matching_file_still_raises(tmp_path):
    """If --update-snapshots is set but no matching JSON file exists, raise is expected."""
    import security_gate as sg

    mod = _load_test_module("_ts_no_match")
    # tmp_path is empty — no JSON files, so the lookup loop finds nothing
    original_dir = mod.SNAPSHOTS_DIR
    mod.SNAPSHOTS_DIR = tmp_path

    snapshot = _make_snapshot("saf078-no-file-scenario", "deny")

    try:
        with patch.object(sg, "decide", return_value="allow"):
            # Should raise because the file cannot be found
            with pytest.raises(AssertionError) as exc_info:
                mod.test_security_gate_snapshot(snapshot, update_snapshots=True)
    finally:
        mod.SNAPSHOTS_DIR = original_dir

    assert "saf078-no-file-scenario" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Error message completeness
# ---------------------------------------------------------------------------

def test_assertion_error_includes_input_and_ws_root_lines():
    """AssertionError message includes input and ws_root detail lines for diagnostics."""
    import security_gate as sg

    mod = _load_test_module("_ts_detail")
    snapshot = _make_snapshot("detail-check-scenario", "allow")

    with patch.object(sg, "decide", return_value="deny"):
        with pytest.raises(AssertionError) as exc_info:
            mod.test_security_gate_snapshot(snapshot, update_snapshots=False)

    msg = str(exc_info.value)
    # Diagnostic lines should appear
    assert "input:" in msg or "input" in msg, "Error must include input detail"
    assert "ws_root" in msg, "Error must include ws_root detail"


def test_assertion_error_wraps_decision_values_in_single_quotes():
    """AssertionError message wraps decision values in single quotes for readability."""
    import security_gate as sg

    mod = _load_test_module("_ts_quotes")
    snapshot = _make_snapshot("quote-check-scenario", "allow")

    with patch.object(sg, "decide", return_value="deny"):
        with pytest.raises(AssertionError) as exc_info:
            mod.test_security_gate_snapshot(snapshot, update_snapshots=False)

    msg = str(exc_info.value)
    assert "'allow'" in msg, "Old decision must be wrapped in single quotes"
    assert "'deny'" in msg, "New decision must be wrapped in single quotes"


# ---------------------------------------------------------------------------
# update_snapshots fixture defaults to False
# ---------------------------------------------------------------------------

def test_conftest_update_snapshots_fixture_default_is_false():
    """The update_snapshots fixture returns False by default (flag off without CLI arg).

    SAF-078 registers pytest_addoption in tests/snapshots/conftest.py (parent level)
    so the flag works both from tests/snapshots/ and tests/snapshots/security_gate/.
    """
    # The registration lives in the parent conftest, not the security_gate one.
    parent_conftest = REPO_ROOT / "tests" / "snapshots" / "conftest.py"
    content = parent_conftest.read_text(encoding="utf-8")
    assert "default=False" in content, (
        "pytest_addoption for --update-snapshots must default to False in "
        "tests/snapshots/conftest.py"
    )


# ---------------------------------------------------------------------------
# README procedure correctness
# ---------------------------------------------------------------------------

def test_readme_procedure_update_command_is_valid():
    """The README update procedure must contain a valid pytest --update-snapshots command.

    SAF-078 registers pytest_addoption in tests/snapshots/conftest.py (parent level),
    so both 'pytest tests/snapshots/' and 'pytest tests/snapshots/security_gate/'
    accept --update-snapshots without 'unrecognized arguments' errors.
    The README documents whichever valid form it chooses.
    """
    content = SNAPSHOTS_README.read_text(encoding="utf-8")

    lines_with_flag = [
        line.strip()
        for line in content.splitlines()
        if "--update-snapshots" in line and "pytest" in line
    ]

    assert lines_with_flag, "README must contain at least one pytest command with --update-snapshots"

    for cmd_line in lines_with_flag:
        # Command must target the snapshots tree (broad or specific scope is both fine)
        assert "tests/snapshots" in cmd_line, (
            f"README command '{cmd_line}' must target tests/snapshots or a subdirectory"
        )
