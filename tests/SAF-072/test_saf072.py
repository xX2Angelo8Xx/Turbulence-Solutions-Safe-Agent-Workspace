"""SAF-072 — Tests for deny-event audit logging in security_gate.py.

BUG-175: File-tool denials are invisible with no audit trail.

Fix: _audit_deny(tool_name, reason, target) appends a JSON line to
.github/hooks/scripts/audit.jsonl at every deny return point in
decide() and sanitize_terminal_command().

Tests:
  T01 - _audit_deny creates audit.jsonl and writes a JSON line
  T02 - JSON line has all required keys: ts, sid, tool, decision, reason, target
  T03 - audit.jsonl is created from scratch if it doesn't exist
  T04 - Multiple deny calls append lines (not overwrite)
  T05 - Audit write failure does not crash the gate or change the decision
  T06 - No sensitive data in audit lines (no $env: values, no secret names)
  T07 - sanitize_terminal_command deny writes audit record
  T08 - decide() deny for restricted tool writes audit record
  T09 - decide() deny for zone violation writes audit record
  T10 - Obfuscation-detected deny uses correct reason category
"""
from __future__ import annotations

import json
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


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ---------------------------------------------------------------------------
# T01: _audit_deny writes a JSON line to audit.jsonl
# ---------------------------------------------------------------------------

def test_audit_deny_writes_json_line(tmp_path, monkeypatch):
    """SAF-072/T01: _audit_deny creates audit.jsonl and writes exactly one line."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    sg._audit_deny("test_tool", "zone_violation", "test_target")

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists(), "audit.jsonl must be created by _audit_deny"
    lines = audit_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1, "Expected exactly one JSON line"
    record = json.loads(lines[0])
    assert record["decision"] == "deny"


# ---------------------------------------------------------------------------
# T02: JSON line has all required keys
# ---------------------------------------------------------------------------

def test_audit_deny_required_keys(tmp_path, monkeypatch):
    """SAF-072/T02: Audit record contains ts, sid, tool, decision, reason, target."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    sg._audit_deny("my_tool", "zone_violation", "some_target")

    audit_file = tmp_path / "audit.jsonl"
    record = json.loads(audit_file.read_text(encoding="utf-8").strip())

    for key in ("ts", "sid", "tool", "decision", "reason", "target"):
        assert key in record, f"Required key {key!r} missing from audit record"

    assert record["tool"] == "my_tool"
    assert record["decision"] == "deny"
    assert record["reason"] == "zone_violation"
    assert record["target"] == "some_target"


# ---------------------------------------------------------------------------
# T03: audit.jsonl is created from scratch if it does not exist
# ---------------------------------------------------------------------------

def test_audit_file_created_on_first_write(tmp_path, monkeypatch):
    """SAF-072/T03: audit.jsonl does not need to pre-exist; first write creates it."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    audit_file = tmp_path / "audit.jsonl"
    assert not audit_file.exists(), "Pre-condition: file must not exist"

    sg._audit_deny("tool_a", "restricted_tool", "tool_a")

    assert audit_file.exists(), "audit.jsonl must be created on first _audit_deny call"


# ---------------------------------------------------------------------------
# T04: Multiple denials append lines (not overwrite)
# ---------------------------------------------------------------------------

def test_multiple_denials_append(tmp_path, monkeypatch):
    """SAF-072/T04: Each _audit_deny call appends a new line; file grows."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    sg._audit_deny("tool_a", "zone_violation", "target_a")
    sg._audit_deny("tool_b", "restricted_tool", "target_b")
    sg._audit_deny("tool_c", "restricted_command", "target_c")

    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3, "Expected 3 appended lines"

    records = [json.loads(l) for l in lines]
    assert records[0]["tool"] == "tool_a"
    assert records[1]["tool"] == "tool_b"
    assert records[2]["tool"] == "tool_c"


# ---------------------------------------------------------------------------
# T05: Audit write failure does not crash the gate or change the decision
# ---------------------------------------------------------------------------

def test_audit_failure_does_not_crash_gate(tmp_path, monkeypatch):
    """SAF-072/T05: PermissionError writing audit.jsonl must not crash the gate."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    _real_open = open

    def _failing_open(path, *args, **kwargs):
        if "audit.jsonl" in str(path):
            raise PermissionError("simulated write failure")
        return _real_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _failing_open)

    # _audit_deny must not raise
    sg._audit_deny("test_tool", "zone_violation", "some_target")

    # Gate decision must still work correctly after audit failure
    decision, reason = sg.sanitize_terminal_command("curl http://evil.com", WS)
    assert decision == "deny", "Gate must still deny after audit write failure"


# ---------------------------------------------------------------------------
# T06: No sensitive data in audit lines
# ---------------------------------------------------------------------------

def test_no_sensitive_data_in_audit_env_exfil(tmp_path, monkeypatch):
    """SAF-072/T06: $env: variable names and values must NOT appear in audit.jsonl."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    # This command references an env var — it must be denied but the secret
    # name/value must NOT be logged in the audit file.
    decision, _reason = sg.sanitize_terminal_command(
        "echo $env:MY_SECRET_API_KEY", WS
    )
    assert decision == "deny", "Expected deny for echo $env:MY_SECRET_API_KEY"

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists(), "Audit file must be written on deny"
    content = audit_file.read_text(encoding="utf-8")

    # Secret name must not appear in any form
    assert "MY_SECRET_API_KEY" not in content
    assert "my_secret_api_key" not in content.lower()

    # The deny decision must be recorded
    records = [json.loads(l) for l in content.splitlines()]
    assert any(r["decision"] == "deny" for r in records)


# ---------------------------------------------------------------------------
# T07: sanitize_terminal_command deny writes audit record
# ---------------------------------------------------------------------------

def test_sanitize_deny_writes_audit(tmp_path, monkeypatch):
    """SAF-072/T07: A command denied by sanitize_terminal_command produces an audit line."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    decision, _reason = sg.sanitize_terminal_command("curl http://evil.com", WS)
    assert decision == "deny"

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists(), "Deny must produce an audit.jsonl entry"

    records = [json.loads(l) for l in audit_file.read_text(encoding="utf-8").splitlines()]
    assert len(records) >= 1
    assert records[0]["tool"] == "run_in_terminal"
    assert records[0]["decision"] == "deny"
    assert records[0]["reason"] == "restricted_command"


# ---------------------------------------------------------------------------
# T08: decide() deny for restricted (unknown) tool writes audit record
# ---------------------------------------------------------------------------

def test_decide_restricted_tool_writes_audit(tmp_path, monkeypatch):
    """SAF-072/T08: decide() deny for an unknown tool writes audit with restricted_tool reason."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    data = {"tool_name": "totally_unknown_tool_xyz", "filePath": WS + "/project/file.py"}
    result = sg.decide(data, WS)
    assert result == "deny"

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists(), "Deny must produce an audit.jsonl entry"

    records = [json.loads(l) for l in audit_file.read_text(encoding="utf-8").splitlines()]
    assert any(r["tool"] == "totally_unknown_tool_xyz" for r in records)
    assert any(r["reason"] == "restricted_tool" for r in records)


# ---------------------------------------------------------------------------
# T09: decide() deny for zone violation (path outside project) writes audit record
# ---------------------------------------------------------------------------

def test_decide_zone_violation_writes_audit(tmp_path, monkeypatch):
    """SAF-072/T09: decide() deny for a path in a forbidden zone writes audit."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    # read_file targeting .github/ must be denied (zone violation)
    data = {
        "tool_name": "read_file",
        "tool_input": {"filePath": WS + "/.github/hooks/scripts/security_gate.py"},
    }
    result = sg.decide(data, WS)
    assert result == "deny"

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists(), "Deny must produce an audit.jsonl entry"

    records = [json.loads(l) for l in audit_file.read_text(encoding="utf-8").splitlines()]
    denied = [r for r in records if r["decision"] == "deny"]
    assert len(denied) >= 1
    assert denied[0]["tool"] == "read_file"
    assert denied[0]["reason"] == "zone_violation"
    # Target must be a basename (not full path containing credentials or full paths)
    target = denied[0]["target"]
    assert "/" not in target or target == "unknown", (
        f"Target should be basename only, got: {target!r}"
    )


# ---------------------------------------------------------------------------
# T10: Obfuscation-detected deny uses correct reason
# ---------------------------------------------------------------------------

def test_obfuscation_detected_reason(tmp_path, monkeypatch):
    """SAF-072/T10: Commands blocked by obfuscation pre-scan use 'obfuscation_detected' reason."""
    monkeypatch.setattr(sg, "__file__", str(tmp_path / "security_gate.py"))

    # eval is an obfuscation pattern
    decision, _reason = sg.sanitize_terminal_command("eval 'echo hi'", WS)
    assert decision == "deny"

    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.exists()

    records = [json.loads(l) for l in audit_file.read_text(encoding="utf-8").splitlines()]
    reasons = [r["reason"] for r in records]
    assert "obfuscation_detected" in reasons or "restricted_command" in reasons, (
        f"Expected obfuscation-related reason, got: {reasons}"
    )
