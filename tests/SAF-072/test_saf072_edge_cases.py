"""SAF-072 — Tester edge-case tests for deny-event audit logging.

Covers areas the developer did not test:
  EC-01 - Concurrent writes from two threads do not corrupt audit.jsonl
  EC-02 - Unicode in tool_name and target is handled correctly
  EC-03 - Very long target strings do not crash _audit_deny
  EC-04 - None or empty arguments do not crash _audit_deny
  EC-05 - Every line in audit.jsonl produced by a real deny is valid JSON
  EC-06 - _audit_deny uses _load_state for fallback SID when OTel unavailable
          (regression test: verifies the SAF-036 invariant is violated)
  EC-07 - audit.jsonl timestamp is a valid ISO-8601 UTC string
  EC-08 - audit.jsonl is written inside scripts_dir (same dir as security_gate.py)
  EC-09 - Reason field is always one of the documented categories (no free-form)
  EC-10 - Tool name from decide() deny for zone violation matches actual tool name
"""
from __future__ import annotations

import json
import threading
import time
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "templates", "agent-workbench", ".github", "hooks", "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

WS = "c:/workspace"

_DOCUMENTED_REASONS = {
    "zone_violation",
    "restricted_command",
    "restricted_tool",
    "obfuscation_detected",
    "env_exfiltration",
}


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ---------------------------------------------------------------------------
# EC-01: Concurrent writes do not corrupt audit.jsonl
# ---------------------------------------------------------------------------

def test_concurrent_writes_no_corruption(tmp_path, monkeypatch):
    """SAF-072/EC-01: Two threads calling _audit_deny simultaneously produce valid JSON."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    errors = []

    def _worker(idx):
        try:
            sg._audit_deny(f"tool_{idx}", "zone_violation", f"target_{idx}")
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=_worker, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Threads raised exceptions: {errors}"

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists()
    lines = audit_file.read_text(encoding="utf-8").splitlines()
    # All lines must be valid JSON
    for line in lines:
        record = json.loads(line)
        assert record["decision"] == "deny"
    # At least some writes succeeded
    assert len(lines) >= 1


# ---------------------------------------------------------------------------
# EC-02: Unicode in tool_name and target
# ---------------------------------------------------------------------------

def test_unicode_in_arguments(tmp_path, monkeypatch):
    """SAF-072/EC-02: Unicode tool names and targets are serialised correctly."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    sg._audit_deny("tool_\u00e9\u00e0\u00fc", "zone_violation", "\u4e2d\u6587\u8def\u5f84")

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists()
    record = json.loads(audit_file.read_text(encoding="utf-8").strip())
    assert record["tool"] == "tool_\u00e9\u00e0\u00fc"
    assert record["target"] == "\u4e2d\u6587\u8def\u5f84"


# ---------------------------------------------------------------------------
# EC-03: Very long target strings do not crash _audit_deny
# ---------------------------------------------------------------------------

def test_very_long_target(tmp_path, monkeypatch):
    """SAF-072/EC-03: A 100 000-character target string does not crash _audit_deny."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    long_target = "a" * 100_000
    # Must not raise
    sg._audit_deny("some_tool", "zone_violation", long_target)

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists()
    record = json.loads(audit_file.read_text(encoding="utf-8").strip())
    assert record["target"] == long_target


# ---------------------------------------------------------------------------
# EC-04: None or empty arguments do not crash _audit_deny
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tool_name,reason,target", [
    (None, "zone_violation", "target"),
    ("tool", None, "target"),
    ("tool", "zone_violation", None),
    ("", "", ""),
])
def test_none_or_empty_args_no_crash(tmp_path, monkeypatch, tool_name, reason, target):
    """SAF-072/EC-04: None/empty arguments must not raise — _audit_deny is fail-safe."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))
    # Must not raise regardless of args
    sg._audit_deny(tool_name, reason, target)


# ---------------------------------------------------------------------------
# EC-05: Every audit.jsonl line from a real deny cycle is valid JSON
# ---------------------------------------------------------------------------

def test_all_audit_lines_valid_json(tmp_path, monkeypatch):
    """SAF-072/EC-05: Running several deny-triggering operations produces valid JSON on every line."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    # Trigger a variety of deny paths
    sg.sanitize_terminal_command("curl http://evil.com", WS)
    sg.sanitize_terminal_command("eval 'rm -rf /'", WS)
    sg.decide({"tool_name": "totally_unknown_tool_xyz", "filePath": WS + "/project/file.py"}, WS)
    sg.decide(
        {"tool_name": "read_file", "tool_input": {"filePath": WS + "/.github/hooks/scripts/security_gate.py"}},
        WS,
    )

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists(), "Expected audit.jsonl to be written"
    lines = [l for l in audit_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) >= 3, f"Expected >=3 audit lines, got {len(lines)}"

    for i, line in enumerate(lines):
        record = json.loads(line)  # raises if not valid JSON
        assert "ts" in record, f"Line {i} missing 'ts'"
        assert "sid" in record, f"Line {i} missing 'sid'"
        assert "tool" in record, f"Line {i} missing 'tool'"
        assert "decision" in record, f"Line {i} missing 'decision'"
        assert "reason" in record, f"Line {i} missing 'reason'"
        assert "target" in record, f"Line {i} missing 'target'"
        assert record["decision"] == "deny", f"Line {i} decision is not 'deny'"


# ---------------------------------------------------------------------------
# EC-06: _audit_deny calls _load_state when OTel SID is unavailable
#         (documents the SAF-036 regression introduced by SAF-072)
# ---------------------------------------------------------------------------

def test_audit_deny_calls_load_state_for_fallback_sid(tmp_path, monkeypatch):
    """SAF-072/EC-06: When OTel SID is unavailable _audit_deny reads _load_state.

    This test DOCUMENTS the regression in SAF-036:
    test_disabled_counter_no_state_file_written previously asserted that
    _load_state is never called when the counter is disabled.  SAF-072's
    _audit_deny calls _load_state for fallback-SID resolution even when the
    counter is disabled.  This violates the SAF-036 contract.

    This test should be marked xfail until the developer removes the
    _load_state call from _audit_deny (use OTel-only or literal 'unknown').
    """
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    with patch.object(sg, "_read_otel_session_id", return_value=None):
        with patch.object(sg, "_load_state", return_value={}) as mock_load:
            sg._audit_deny("test_tool", "zone_violation", "target")
            # SAF-072 _audit_deny calls _load_state when OTel is unavailable
            assert mock_load.call_count >= 1, (
                "Expected _load_state to be called for fallback SID resolution"
            )


# ---------------------------------------------------------------------------
# EC-07: Timestamp is a valid ISO-8601 UTC string
# ---------------------------------------------------------------------------

def test_timestamp_is_valid_iso8601_utc(tmp_path, monkeypatch):
    """SAF-072/EC-07: The 'ts' field must be a valid ISO-8601 timestamp with UTC offset."""
    import datetime as dt

    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))
    sg._audit_deny("tool", "zone_violation", "target")

    record = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8").strip())
    ts_str = record["ts"]

    # Must parse as ISO-8601 and must contain timezone info
    parsed = dt.datetime.fromisoformat(ts_str)
    assert parsed.tzinfo is not None, "Timestamp must include timezone info"


# ---------------------------------------------------------------------------
# EC-08: audit.jsonl written in the same directory as security_gate.py
# ---------------------------------------------------------------------------

def test_audit_file_location_is_scripts_dir(tmp_path, monkeypatch):
    """SAF-072/EC-08: audit.jsonl must be created alongside security_gate.py."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    sg._audit_deny("tool", "zone_violation", "target")

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists(), "audit.jsonl must be in the same dir as security_gate.py"
    # Confirm it is NOT created anywhere else in the tmp_path subtree except directly in tmp_path
    all_jsonl = list(tmp_path.rglob("audit.jsonl"))
    assert len(all_jsonl) == 1


# ---------------------------------------------------------------------------
# EC-09: Reason field only contains documented categories
# ---------------------------------------------------------------------------

def test_reason_field_is_documented_category(tmp_path, monkeypatch):
    """SAF-072/EC-09: All reason values from real deny paths are from documented categories."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    sg.sanitize_terminal_command("curl http://evil.com", WS)
    sg.sanitize_terminal_command("eval 'echo hi'", WS)
    sg.sanitize_terminal_command("echo $env:MY_SECRET_KEY", WS)
    sg.decide({"tool_name": "unknown_tool_xyz"}, WS)

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists()
    for line in audit_file.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        assert record["reason"] in _DOCUMENTED_REASONS, (
            f"Undocumented reason {record['reason']!r} in audit record: {record}"
        )


# ---------------------------------------------------------------------------
# EC-10: Tool name in decide() zone violation matches input tool_name
# ---------------------------------------------------------------------------

def test_decide_zone_violation_tool_name_matches(tmp_path, monkeypatch):
    """SAF-072/EC-10: Audit record tool matches the tool_name supplied to decide()."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    for tool in ("read_file", "create_file", "replace_string_in_file"):
        data = {
            "tool_name": tool,
            "tool_input": {"filePath": WS + "/.github/hooks/scripts/security_gate.py"},
        }
        sg.decide(data, WS)

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists()
    logged_tools = {json.loads(l)["tool"] for l in audit_file.read_text(encoding="utf-8").splitlines()}
    assert "read_file" in logged_tools
    assert "create_file" in logged_tools
    assert "replace_string_in_file" in logged_tools
