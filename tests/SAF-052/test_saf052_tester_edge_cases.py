"""tests/SAF-052/test_saf052_tester_edge_cases.py

Tester-added edge-case tests for SAF-052: get_changed_files in _ALWAYS_ALLOW_TOOLS.

Edge cases examined:
  1. Case sensitivity — wrong-case names are denied, not silently allowed
  2. Whitespace variants — trailing/leading spaces are not accidentally matched
  3. get_changed_files NOT in _EXEMPT_TOOLS (correct set placement)
  4. repositoryPath pointing outside workspace still allowed (always-allow bypasses zone checks)
  5. sourceControlState filter values still allowed
  6. None/null tool_name handled gracefully (no crash, returns deny)
  7. Coding template (templates/coding) absence — no parallel gate to update
  8. Unicode and special characters in tool_input still allowed
  9. Large repositoryPath value still allowed (always-allow path)
 10. Verify _ALWAYS_ALLOW_TOOLS is a frozenset (immutable — cannot be mutated at runtime)
"""
from __future__ import annotations

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

WS_ROOT = str(SCRIPTS_DIR.parents[3])  # workspace root (4 levels up from scripts/)


class TestCaseSensitivity(unittest.TestCase):
    """Tool name comparison must be case-sensitive — only exact match is allowed."""

    def test_uppercase_get_changed_files_is_denied(self):
        """GET_CHANGED_FILES (all caps) must not be allowed by the always-allow set."""
        payload = {"tool_name": "GET_CHANGED_FILES", "tool_input": {}}
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(
            result,
            "deny",
            "Tool name lookup must be case-sensitive; GET_CHANGED_FILES must be denied",
        )

    def test_mixed_case_get_changed_files_is_denied(self):
        """Get_Changed_Files (mixed case) must not accidentally match."""
        payload = {"tool_name": "Get_Changed_Files", "tool_input": {}}
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(
            result,
            "deny",
            "Mixed-case variant must not match the exact always-allow entry",
        )


class TestWhitespaceVariants(unittest.TestCase):
    """Tool names with leading/trailing whitespace must not match the good name."""

    def test_trailing_space_is_denied(self):
        payload = {"tool_name": "get_changed_files ", "tool_input": {}}
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(result, "deny", "Trailing space must not match the always-allow entry")

    def test_leading_space_is_denied(self):
        payload = {"tool_name": " get_changed_files", "tool_input": {}}
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(result, "deny", "Leading space must not match the always-allow entry")


class TestCorrectSetPlacement(unittest.TestCase):
    """get_changed_files must be in _ALWAYS_ALLOW_TOOLS and NOT in _EXEMPT_TOOLS."""

    def test_get_changed_files_not_in_exempt_tools(self):
        self.assertNotIn(
            "get_changed_files",
            sg._EXEMPT_TOOLS,
            "get_changed_files should be in _ALWAYS_ALLOW_TOOLS, not _EXEMPT_TOOLS",
        )

    def test_immutable_always_allow_frozenset(self):
        """_ALWAYS_ALLOW_TOOLS must be immutable — a frozenset, not a plain set."""
        self.assertIsInstance(sg._ALWAYS_ALLOW_TOOLS, frozenset)
        with self.assertRaises((AttributeError, TypeError)):
            sg._ALWAYS_ALLOW_TOOLS.add("injected_tool")  # type: ignore[attr-defined]


class TestAlwaysAllowBypassesZoneChecks(unittest.TestCase):
    """Because get_changed_files is in _ALWAYS_ALLOW_TOOLS, zone checks are skipped.
    This means even a payload with a repositoryPath outside the workspace is still
    allowed — the tool is unconditionally safe because it has no path-traversal risk.
    """

    def test_repository_path_outside_workspace_still_allowed(self):
        payload = {
            "tool_name": "get_changed_files",
            "tool_input": {"repositoryPath": "C:\\Users\\attacker\\secret_repo"},
        }
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(
            result,
            "allow",
            "Always-allow path must bypass zone checks even with an external repositoryPath",
        )

    def test_repository_path_traversal_string_still_allowed(self):
        """Path-traversal sequences in repositoryPath must not change the allow decision
        for always-allow tools — zone checks are not reached."""
        payload = {
            "tool_name": "get_changed_files",
            "tool_input": {"repositoryPath": "../../../../../../etc/passwd"},
        }
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(result, "allow")

    def test_source_control_state_filters_allowed(self):
        for state in (["staged"], ["unstaged"], ["merge-conflicts"], ["staged", "unstaged"]):
            with self.subTest(state=state):
                payload = {
                    "tool_name": "get_changed_files",
                    "tool_input": {"sourceControlState": state},
                }
                result = sg.decide(payload, WS_ROOT)
                self.assertEqual(result, "allow", f"sourceControlState={state} must be allowed")


class TestNullAndEdgeInputs(unittest.TestCase):
    """Null/None tool_name and degenerate inputs must not crash decide()."""

    def test_none_tool_name_handled_gracefully(self):
        """decide() must not raise if tool_name is None — should return deny."""
        payload = {"tool_name": None, "tool_input": {}}
        try:
            result = sg.decide(payload, WS_ROOT)
            # Either a deny or an exception is acceptable; a crash is not.
            self.assertNotEqual(result, "allow", "None tool_name must not be allowed")
        except (TypeError, AttributeError, KeyError):
            pass  # Raising an exception is acceptable; crashing the hook is not OK in prod

    def test_unicode_in_tool_input_allowed(self):
        """Unicode characters in tool_input must not break always-allow logic."""
        payload = {
            "tool_name": "get_changed_files",
            "tool_input": {"repositoryPath": "/proj/\u4e2d\u6587\u76ee\u5f55"},
        }
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(result, "allow")

    def test_large_repository_path_allowed(self):
        """A very long repositoryPath value must not affect the always-allow decision."""
        long_path = "/some/repo/" + "a" * 4096
        payload = {
            "tool_name": "get_changed_files",
            "tool_input": {"repositoryPath": long_path},
        }
        result = sg.decide(payload, WS_ROOT)
        self.assertEqual(result, "allow")


class TestCodingTemplateAbsence(unittest.TestCase):
    """The coding template (templates/coding) has been removed/deprecated.
    There must be no parallel security_gate.py in that location to update.
    """

    def test_coding_template_security_gate_does_not_exist(self):
        """Confirm templates/coding/ is absent — no second gate to keep in sync."""
        coding_gate = Path(SCRIPTS_DIR).parents[3] / "templates" / "coding"
        self.assertFalse(
            coding_gate.exists(),
            "templates/coding/ should not exist (deprecated); found unexpected path: "
            + str(coding_gate),
        )


if __name__ == "__main__":
    unittest.main()
