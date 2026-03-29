"""tests/SAF-052/test_saf052_get_changed_files.py

Tests for SAF-052: get_changed_files added to _ALWAYS_ALLOW_TOOLS in
security_gate.py.

Acceptance criteria:
  1. get_changed_files is present in _ALWAYS_ALLOW_TOOLS
  2. decide({"tool_name": "get_changed_files"}, ws_root) returns "allow"
  3. get_changed_files is NOT required to be in _EXEMPT_TOOLS (correct set)
  4. Hash verification passes after update_hashes.py ran
  5. Unknown tools still fall through to deny (regression guard)
  6. Other always-allow tools are not disturbed
"""
from __future__ import annotations

import hashlib
import re
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "hooks"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

import security_gate as sg  # noqa: E402


GATE_PATH = SCRIPTS_DIR / "security_gate.py"
WS_ROOT = str(SCRIPTS_DIR.parents[3])  # workspace root (4 levels up from scripts/)


class TestGetChangedFilesInAlwaysAllow(unittest.TestCase):
    """SAF-058: get_changed_files was moved from _ALWAYS_ALLOW_TOOLS to
    validate_get_changed_files() for conditional .git/ placement check."""

    def test_get_changed_files_in_always_allow_tools(self):
        # SAF-058: get_changed_files was moved out of _ALWAYS_ALLOW_TOOLS to
        # validate_get_changed_files() which applies a conditional .git/ check.
        self.assertNotIn(
            "get_changed_files",
            sg._ALWAYS_ALLOW_TOOLS,
            "SAF-058: get_changed_files must NOT be in _ALWAYS_ALLOW_TOOLS",
        )

    def test_always_allow_tools_is_frozenset(self):
        self.assertIsInstance(sg._ALWAYS_ALLOW_TOOLS, frozenset)

    def test_existing_always_allow_entries_preserved(self):
        expected = {
            "vscode_ask_questions",
            "ask_questions",
            "TodoWrite",
            "TodoRead",
            "todo_write",
            "manage_todo_list",
            "runSubagent",
            "Agent",
            "agent",
        }
        for name in expected:
            self.assertIn(
                name,
                sg._ALWAYS_ALLOW_TOOLS,
                f"Pre-existing always-allow tool '{name}' was accidentally removed",
            )


class TestGetChangedFilesDecision(unittest.TestCase):
    """decide() must return 'allow' for get_changed_files."""

    def test_decide_get_changed_files_returns_allow(self):
        payload = {"tool_name": "get_changed_files", "tool_input": {}}
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(
            result,
            "allow",
            "decide() must return 'allow' for get_changed_files",
        )

    def test_decide_get_changed_files_no_tool_input(self):
        payload = {"tool_name": "get_changed_files"}
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(result, "allow")

    def test_decide_get_changed_files_extra_fields_ignored(self):
        """Any extra fields in the payload must not change the allow decision."""
        payload = {
            "tool_name": "get_changed_files",
            "tool_input": {"repositoryPath": "/some/path", "sourceControlState": ["unstaged"]},
        }
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(result, "allow")


class TestSetPlacement(unittest.TestCase):
    """Verify get_changed_files placement is correct (always-allow, not exempt)."""

    def test_get_changed_files_not_in_terminal_tools(self):
        self.assertNotIn(
            "get_changed_files",
            sg._TERMINAL_TOOLS,
            "get_changed_files should not be in _TERMINAL_TOOLS",
        )

    def test_get_changed_files_not_in_write_tools(self):
        self.assertNotIn(
            "get_changed_files",
            sg._WRITE_TOOLS,
            "get_changed_files must not be in _WRITE_TOOLS",
        )


class TestHashVerification(unittest.TestCase):
    """The embedded _KNOWN_GOOD_GATE_HASH must match the actual gate file."""

    def test_gate_hash_matches_embedded_constant(self):
        """Verify the canonical hash of security_gate.py equals _KNOWN_GOOD_GATE_HASH.

        This test confirms update_hashes.py was run after adding get_changed_files.
        If the hash is stale, this test will fail — a clear signal to re-run
        update_hashes.py.
        """
        content = GATE_PATH.read_bytes()
        canonical = re.sub(
            rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}',
            b"0" * 64,
            content,
        )
        computed = hashlib.sha256(canonical).hexdigest()
        self.assertEqual(
            computed,
            sg._KNOWN_GOOD_GATE_HASH,
            "Hash mismatch — run update_hashes.py after modifying security_gate.py",
        )

    def test_known_good_gate_hash_is_64_hex_chars(self):
        self.assertRegex(
            sg._KNOWN_GOOD_GATE_HASH,
            r'^[0-9a-f]{64}$',
            "_KNOWN_GOOD_GATE_HASH must be a 64-character lowercase hex string",
        )


class TestRegressionUnknownToolDenied(unittest.TestCase):
    """Unknown tools must still be denied after SAF-052."""

    def test_completely_unknown_tool_is_denied(self):
        payload = {"tool_name": "some_unknown_nonexistent_tool", "tool_input": {}}
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(
            result,
            "deny",
            "Unknown tools must still be denied (regression guard)",
        )

    def test_empty_tool_name_is_denied(self):
        payload = {"tool_name": "", "tool_input": {}}
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(result, "deny")


if __name__ == "__main__":
    unittest.main()
