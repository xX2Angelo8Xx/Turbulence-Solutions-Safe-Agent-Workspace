"""Tests for SAF-078: Feature Behavior Locking via Snapshots.

Verifies that:
- decision-mismatch produces the canonical error message
- --update-snapshots rewrites snapshot files in-place
- README and agent-workflow.md contain required documentation
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Locate key paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOTS_DIR = REPO_ROOT / "tests" / "snapshots" / "security_gate"
TEST_SNAPSHOTS_PY = SNAPSHOTS_DIR / "test_snapshots.py"
SNAPSHOTS_README = REPO_ROOT / "tests" / "snapshots" / "README.md"
AGENT_WORKFLOW_MD = REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md"

# Ensure security_gate is importable
_SCRIPTS_DIR = str(
    REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


# ---------------------------------------------------------------------------
# Helpers — minimal stub for calling the snapshot test function directly
# ---------------------------------------------------------------------------

def _make_snapshot(description: str, decision: str, input_obj: dict | None = None) -> dict:
    return {
        "description": description,
        "ws_root": "/workspace",
        "input": input_obj or {"tool_name": "read_file", "filePath": "/workspace/main.py"},
        "expected_decision": decision,
    }


def _run_snapshot_test(snapshot: dict, *, update_snapshots: bool = False) -> None:
    """Invoke the snapshot test function directly, bypassing pytest collection."""
    # Import fresh to avoid module-level caching of _SNAPSHOTS
    import importlib, importlib.util

    spec = importlib.util.spec_from_file_location("_ts", TEST_SNAPSHOTS_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.test_security_gate_snapshot(snapshot, update_snapshots=update_snapshots)


# ---------------------------------------------------------------------------
# 1. Passing case — decision matches
# ---------------------------------------------------------------------------

def test_snapshot_passes_when_decision_matches():
    """No exception raised when actual decision equals expected_decision."""
    import security_gate as sg

    # Pick a real allow scenario from the existing snapshots
    f = SNAPSHOTS_DIR / "allow_always_allow_tool.json"
    snapshot = json.loads(f.read_text(encoding="utf-8"))

    # Patch sg.decide to always return the expected decision
    with patch.object(sg, "decide", return_value=snapshot["expected_decision"]):
        # Should not raise
        _run_snapshot_test(snapshot)


# ---------------------------------------------------------------------------
# 2. Failure message contains canonical text
# ---------------------------------------------------------------------------

def test_snapshot_fails_with_decision_change_message():
    """AssertionError message includes the canonical --update-snapshots hint."""
    import security_gate as sg

    snapshot = _make_snapshot("deny a known bad tool", "deny")

    with patch.object(sg, "decide", return_value="allow"):
        with pytest.raises(AssertionError) as exc_info:
            _run_snapshot_test(snapshot)

    msg = str(exc_info.value)
    assert "--update-snapshots" in msg, "Error message must mention --update-snapshots flag"
    assert "dev-log.md" in msg, "Error message must mention dev-log.md"
    assert "## Behavior Changes" in msg, "Error message must mention ## Behavior Changes section"


def test_snapshot_message_includes_scenario_name():
    """AssertionError message includes the scenario description."""
    import security_gate as sg

    description = "unique-scenario-for-saf078-test"
    snapshot = _make_snapshot(description, "deny")

    with patch.object(sg, "decide", return_value="allow"):
        with pytest.raises(AssertionError) as exc_info:
            _run_snapshot_test(snapshot)

    assert description in str(exc_info.value)


def test_snapshot_message_includes_both_decisions():
    """AssertionError message includes both the old and new decision values."""
    import security_gate as sg

    snapshot = _make_snapshot("allow a file read", "allow")

    with patch.object(sg, "decide", return_value="deny"):
        with pytest.raises(AssertionError) as exc_info:
            _run_snapshot_test(snapshot)

    msg = str(exc_info.value)
    # Old decision
    assert "'allow'" in msg, "Error message must show the old (expected) decision"
    # New decision
    assert "'deny'" in msg, "Error message must show the new (actual) decision"


# ---------------------------------------------------------------------------
# 3. --update-snapshots rewrites file
# ---------------------------------------------------------------------------

def test_update_snapshots_flag_rewrites_file(tmp_path):
    """When --update-snapshots is set, the snapshot JSON file is rewritten."""
    import security_gate as sg

    # Create a temp snapshot file with decision "deny"
    snap_file = tmp_path / "deny_test_scenario.json"
    snap_data = {
        "description": "saf078-rewrite-test",
        "ws_root": "/workspace",
        "input": {"tool_name": "read_file", "filePath": "/workspace/main.py"},
        "expected_decision": "deny",
    }
    snap_file.write_text(json.dumps(snap_data, indent=2), encoding="utf-8")

    # Import the test module and patch SNAPSHOTS_DIR to point to tmp_path
    import importlib.util
    spec = importlib.util.spec_from_file_location("_ts", TEST_SNAPSHOTS_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    original_dir = mod.SNAPSHOTS_DIR
    mod.SNAPSHOTS_DIR = tmp_path

    try:
        with patch.object(sg, "decide", return_value="allow"):
            # Should NOT raise — should rewrite instead
            mod.test_security_gate_snapshot(snap_data, update_snapshots=True)
    finally:
        mod.SNAPSHOTS_DIR = original_dir

    # Confirm the file was rewritten
    updated = json.loads(snap_file.read_text(encoding="utf-8"))
    assert updated["expected_decision"] == "allow", (
        "Snapshot file must be rewritten with the actual decision when "
        "--update-snapshots is used"
    )


def test_update_snapshots_flag_passes_after_rewrite(tmp_path):
    """After rewrite, re-running without --update-snapshots passes cleanly."""
    import security_gate as sg

    snap_file = tmp_path / "allow_post_update.json"
    snap_data = {
        "description": "saf078-post-rewrite-pass",
        "ws_root": "/workspace",
        "input": {"tool_name": "read_file", "filePath": "/workspace/main.py"},
        "expected_decision": "allow",  # already correct
    }
    snap_file.write_text(json.dumps(snap_data, indent=2), encoding="utf-8")

    import importlib.util
    spec = importlib.util.spec_from_file_location("_ts2", TEST_SNAPSHOTS_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with patch.object(sg, "decide", return_value="allow"):
        # No exception — decision matches snapshot
        mod.test_security_gate_snapshot(snap_data, update_snapshots=False)


# ---------------------------------------------------------------------------
# 4. Documentation checks
# ---------------------------------------------------------------------------

def test_readme_documents_update_snapshots_flag():
    """tests/snapshots/README.md must mention --update-snapshots."""
    content = SNAPSHOTS_README.read_text(encoding="utf-8")
    assert "--update-snapshots" in content, (
        "tests/snapshots/README.md must document the --update-snapshots flag"
    )


def test_readme_documents_devlog_requirement():
    """tests/snapshots/README.md must mention dev-log.md behavior change requirement."""
    content = SNAPSHOTS_README.read_text(encoding="utf-8")
    assert "dev-log.md" in content, (
        "tests/snapshots/README.md must mention the dev-log.md requirement"
    )
    assert "Behavior Changes" in content, (
        "tests/snapshots/README.md must mention the '## Behavior Changes' section"
    )


def test_readme_snapshot_is_documentation():
    """README must state 'the snapshot IS the documentation' principle."""
    content = SNAPSHOTS_README.read_text(encoding="utf-8")
    # Accept any capitalisation variant
    assert "snapshot IS the documentation" in content or \
           "snapshot is the documentation" in content.lower(), (
        "tests/snapshots/README.md must state 'the snapshot IS the documentation'"
    )


def test_devlog_template_has_behavior_changes_section():
    """docs/work-rules/agent-workflow.md dev-log template must include ## Behavior Changes."""
    content = AGENT_WORKFLOW_MD.read_text(encoding="utf-8")
    assert "## Behavior Changes" in content, (
        "docs/work-rules/agent-workflow.md dev-log template must include "
        "an optional '## Behavior Changes' section"
    )


def test_devlog_template_behavior_changes_mentions_update_snapshots():
    """The ## Behavior Changes section in the template must reference --update-snapshots."""
    content = AGENT_WORKFLOW_MD.read_text(encoding="utf-8")
    # Find the section
    idx = content.find("## Behavior Changes")
    assert idx != -1, "## Behavior Changes section not found"
    section = content[idx: idx + 500]
    assert "--update-snapshots" in section, (
        "The ## Behavior Changes section must mention --update-snapshots"
    )


def test_conftest_registers_update_snapshots_option():
    """tests/snapshots/conftest.py must register --update-snapshots via pytest_addoption."""
    parent_conftest = REPO_ROOT / "tests" / "snapshots" / "conftest.py"
    content = parent_conftest.read_text(encoding="utf-8")
    assert "--update-snapshots" in content, (
        "tests/snapshots/conftest.py must register --update-snapshots via pytest_addoption"
    )
    assert "pytest_addoption" in content, (
        "tests/snapshots/conftest.py must define pytest_addoption to register the flag"
    )
