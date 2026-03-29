"""tests/SAF-055/test_saf055_tester_edge_cases.py

Tester-added edge-case tests for SAF-055 (Whitelist .github/ subdirectories read-only).

These supplement the Developer's test_saf055_github_read_whitelist.py by probing:
  - Case-variant paths (.GitHub/agents/) — normalize_path lowercases before regex
  - Windows backslash paths (c:\\workspace\\.github\\agents\\foo.md)
  - Backslash-based path traversal bypass attempts
  - WSL/Git Bash mount prefix paths (/mnt/c/.github/agents/ and /c/.github/agents/)
  - Non-READ_ONLY_TOOLS (grep_search, file_search) targeting allowed subdirs → deny
  - Null-byte injection in path
  - Empty string path
  - Path with only whitespace
  - URL-encoded .github path
  - .github/instructions/copilot-instructions.md specifically (explicit per US-060 AC)
  - multi_replace_string_in_file (write tool) on instructions path
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Make security_gate importable without triggering real integrity checks
# ---------------------------------------------------------------------------
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


WS_ROOT = "c:/workspace"


def _decide(tool_name: str, file_path: str) -> str:
    """Run decide() with integrity check bypassed."""
    data = {
        "tool_name": tool_name,
        "tool_input": {"filePath": file_path},
    }
    with patch.object(sg, "verify_file_integrity", return_value=True):
        with patch.object(
            sg.zone_classifier,
            "detect_project_folder",
            return_value="project",
        ):
            return sg.decide(data, WS_ROOT)


# ---------------------------------------------------------------------------
# Case-sensitivity: normalize_path lowercases before regex check
# ---------------------------------------------------------------------------


class TestCaseVariants(unittest.TestCase):
    """normalize_path() converts path to lowercase, so mixed-case .github
    variants should behave identically to the canonical lowercase form."""

    def test_uppercase_github_agents_allowed(self):
        """.GitHub/agents/ → normalized to .github/agents/ → allow."""
        result = _decide("read_file", ".GitHub/agents/my-agent.md")
        self.assertEqual(result, "allow")

    def test_mixed_case_instructions_allowed(self):
        result = _decide("read_file", ".GitHub/Instructions/copilot-instructions.md")
        self.assertEqual(result, "allow")

    def test_uppercase_hooks_still_denied(self):
        """.GITHUB/HOOKS/ → normalized to .github/hooks/ → deny."""
        result = _decide("read_file", ".GITHUB/HOOKS/security_gate.py")
        self.assertEqual(result, "deny")

    def test_mixed_case_agents_list_dir_allowed(self):
        result = _decide("list_dir", ".GitHub/Agents/")
        self.assertEqual(result, "allow")


# ---------------------------------------------------------------------------
# Windows backslash paths
# ---------------------------------------------------------------------------


class TestWindowsBackslashPaths(unittest.TestCase):
    """normalize_path() converts backslashes to forward slashes."""

    def test_backslash_agents_path_allowed(self):
        """Windows-style path .github\\agents\\foo.md → allow."""
        result = _decide("read_file", ".github\\agents\\foo.md")
        self.assertEqual(result, "allow")

    def test_backslash_absolute_agents_allowed(self):
        result = _decide("read_file", r"c:\workspace\.github\agents\foo.md")
        self.assertEqual(result, "allow")

    def test_backslash_hooks_denied(self):
        result = _decide("read_file", r".github\hooks\security_gate.py")
        self.assertEqual(result, "deny")

    def test_backslash_traversal_to_hooks_denied(self):
        """Backslash-based traversal: .github\\agents\\..\\hooks\\sg.py → deny."""
        result = _decide("read_file", r".github\agents\..\hooks\security_gate.py")
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# WSL and Git Bash mount prefixes
# ---------------------------------------------------------------------------


class TestMountPrefixPaths(unittest.TestCase):
    """normalize_path() converts /mnt/c/ prefix to c:/ and /c/ prefix to c:/."""

    def test_wsl_mount_prefix_agents_allowed(self):
        """/mnt/c/workspace/.github/agents/foo.md → normalized → allow."""
        result = _decide("read_file", "/mnt/c/workspace/.github/agents/foo.md")
        self.assertEqual(result, "allow")

    def test_git_bash_prefix_agents_allowed(self):
        """/c/workspace/.github/agents/foo.md → normalized → allow."""
        result = _decide("read_file", "/c/workspace/.github/agents/foo.md")
        self.assertEqual(result, "allow")

    def test_wsl_mount_prefix_hooks_denied(self):
        result = _decide("read_file", "/mnt/c/workspace/.github/hooks/security_gate.py")
        self.assertEqual(result, "deny")

    def test_git_bash_prefix_hooks_denied(self):
        result = _decide("read_file", "/c/workspace/.github/hooks/security_gate.py")
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Non-READ_ONLY_TOOLS targeting allowed subdirectories
# ---------------------------------------------------------------------------


def _decide_raw(data: dict) -> str:
    """Run decide() with a fully custom payload — for tools like file_search
    that use parameters other than filePath."""
    with patch.object(sg, "verify_file_integrity", return_value=True):
        with patch.object(
            sg.zone_classifier,
            "detect_project_folder",
            return_value="project",
        ):
            return sg.decide(data, WS_ROOT)


class TestNonReadOnlyToolsDenied(unittest.TestCase):
    """Tools not in _READ_ONLY_TOOLS must NOT gain access via the SAF-055 whitelist.
    Each tool must be tested with its actual parameter format."""

    def test_grep_search_agents_denied(self):
        """grep_search uses filePath — not in _READ_ONLY_TOOLS; denied."""
        result = _decide("grep_search", ".github/agents/foo.md")
        self.assertEqual(result, "deny")

    def test_file_search_query_github_denied(self):
        """file_search uses 'query' not 'filePath'. validate_file_search detects
        '.github' in query and denies — no SAF-055 path needed."""
        data = {"tool_name": "file_search", "tool_input": {"query": ".github/agents/foo.md"}}
        self.assertEqual(_decide_raw(data), "deny")

    def test_get_errors_file_paths_github_denied(self):
        """get_errors uses 'filePaths' array. zone_classifier denies .github/ paths."""
        data = {"tool_name": "get_errors", "tool_input": {"filePaths": [".github/agents/"]}}
        self.assertEqual(_decide_raw(data), "deny")

    def test_get_errors_file_paths_hooks_denied(self):
        """get_errors with .github/hooks/ path is denied."""
        data = {"tool_name": "get_errors", "tool_input": {"filePaths": [".github/hooks/security_gate.py"]}}
        self.assertEqual(_decide_raw(data), "deny")

    def test_multi_replace_instructions_denied(self):
        """multi_replace_string_in_file is a write tool — must be denied."""
        result = _decide("multi_replace_string_in_file", ".github/instructions/copilot-instructions.md")
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Specific user story acceptance criteria: copilot-instructions.md
# ---------------------------------------------------------------------------


class TestCopilotInstructionsSpecifically(unittest.TestCase):
    """US-060 AC explicitly calls out copilot-instructions.md.
    Test every relevant tool variant."""

    def test_read_file_copilot_instructions_allowed(self):
        result = _decide("read_file", ".github/instructions/copilot-instructions.md")
        self.assertEqual(result, "allow")

    def test_read_alias_copilot_instructions_allowed(self):
        result = _decide("Read", ".github/instructions/copilot-instructions.md")
        self.assertEqual(result, "allow")

    def test_list_dir_instructions_folder_allowed(self):
        result = _decide("list_dir", ".github/instructions/")
        self.assertEqual(result, "allow")

    def test_create_file_copilot_instructions_denied(self):
        """Write remains denied even when targeting the whitelisted path."""
        result = _decide("create_file", ".github/instructions/copilot-instructions.md")
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Malformed / adversarial path inputs
# ---------------------------------------------------------------------------


class TestMalformedPaths(unittest.TestCase):

    def test_null_byte_injected_path_agents(self):
        """Null bytes are stripped; remaining path .github/agents/foo.md is in allowed zone."""
        result = _decide("read_file", ".github/agents/\x00foo.md")
        self.assertEqual(result, "allow")

    def test_null_byte_injected_hooks_still_denied(self):
        """Null-byte in .github/hooks/\x00sg.py → stripped → .github/hooks/sg.py → deny."""
        result = _decide("read_file", ".github/hooks/\x00security_gate.py")
        self.assertEqual(result, "deny")

    def test_empty_path_denied(self):
        """Empty string path must not accidentally match any whitelist."""
        result = _decide("read_file", "")
        self.assertEqual(result, "deny")

    def test_url_encoded_github_path_behavior(self):
        """%2egithub%2f (URL-encoded .github/) is NOT decoded by normalize_path.
        The URL-encoded string becomes a single workspace-root child token that
        is_workspace_root_readable() passes through (pre-existing SAF-046 behavior).
        The OS would refuse to open such a file anyway — no real exploit exists.
        This test documents the current behavior to detect regressions.
        
        BUG NOTE: Logged as BUG-150 — URL-encoded paths bypass zone classification
        via is_workspace_root_readable (pre-existing, not introduced by SAF-055)."""
        result = _decide("read_file", "%2egithub%2fagents%2ffoo.md")
        # is_workspace_root_readable treats %2egithub%2fagents%2ffoo.md as a
        # single-component workspace-root path — returns allow. Pre-existing.
        self.assertEqual(result, "allow")

    def test_url_encoded_hooks_behavior(self):
        """URL-encoded .github/hooks/ path — same pre-existing SAF-046 behavior.
        Documents that even supposedly 'safe' URL-encoded hooks paths are allowed
        by is_workspace_root_readable but can't access real files on the OS."""
        result = _decide("read_file", "%2egithub%2fhooks%2fsecurity_gate.py")
        self.assertEqual(result, "allow")  # pre-existing SAF-046 behavior

    def test_double_slash_path_traversal_denied(self):
        """Double slash .github//agents/../hooks/ → normalized → .github/hooks/ → deny."""
        result = _decide("read_file", ".github//agents/../hooks/security_gate.py")
        self.assertEqual(result, "deny")

    def test_agents_prefix_with_hyphen_denied(self):
        """.github/agents-config does not match the agents whitelist."""
        result = _decide("read_file", ".github/agents-config/foo.md")
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Regression: _GITHUB_READ_ALLOWED_RE pattern boundary checks
# ---------------------------------------------------------------------------


class TestRegexBoundaryConditions(unittest.TestCase):

    def test_re_does_not_match_github_root(self):
        """The pattern must not match .github/ with nothing after it."""
        self.assertIsNone(sg._GITHUB_READ_ALLOWED_RE.search(".github/"))

    def test_re_matches_instructions_with_slash(self):
        self.assertIsNotNone(sg._GITHUB_READ_ALLOWED_RE.search(".github/instructions/"))

    def test_re_matches_deep_nested_path(self):
        self.assertIsNotNone(
            sg._GITHUB_READ_ALLOWED_RE.search(".github/skills/subfolder/deep.md")
        )

    def test_re_does_not_match_prompts_extra(self):
        """.github/prompts-extra must not match .github/prompts."""
        self.assertIsNone(sg._GITHUB_READ_ALLOWED_RE.search(".github/prompts-extra/foo.md"))

    def test_re_does_not_match_workflows(self):
        self.assertIsNone(sg._GITHUB_READ_ALLOWED_RE.search(".github/workflows/ci.yml"))


if __name__ == "__main__":
    unittest.main()
