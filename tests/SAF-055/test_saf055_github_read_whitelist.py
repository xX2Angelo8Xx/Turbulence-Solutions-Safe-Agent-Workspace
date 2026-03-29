"""tests/SAF-055/test_saf055_github_read_whitelist.py

Tests for SAF-055: Whitelist .github/ agent-facing subdirectories read-only.

Coverage:
  - read_file / Read / list_dir targeting .github/agents/ → allow
  - read_file / Read / list_dir targeting .github/skills/ → allow
  - read_file / Read / list_dir targeting .github/prompts/ → allow
  - read_file / Read / list_dir targeting .github/instructions/ → allow
  - Nested file paths inside allowed subdirectories → allow
  - Absolute paths to allowed subdirectories → allow
  - Write operations (create_file, replace_string_in_file) targeting allowed paths → deny
  - .github/hooks/ fully denied for read and write
  - .github/ root denied for read
  - Unknown .github/ subdirectory denied for read
  - Path traversal attempt (.github/agents/../hooks/) → deny
  - edit_notebook_file (non-READ_ONLY_TOOLS member) targeting .github/agents/ → deny
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WS_ROOT = "c:/workspace"
PROJECT_DIR = "c:/workspace/project"


def _payload(tool_name: str, file_path: str) -> dict:
    """Build a minimal decide() data payload for file-path tools."""
    return {
        "tool_name": tool_name,
        "tool_input": {"filePath": file_path},
    }


def _decide(tool_name: str, file_path: str) -> str:
    """Run decide() with integrity check bypassed."""
    data = _payload(tool_name, file_path)
    with patch.object(sg, "verify_file_integrity", return_value=True):
        with patch.object(
            sg.zone_classifier,
            "detect_project_folder",
            return_value="project",
        ):
            return sg.decide(data, WS_ROOT)


# ---------------------------------------------------------------------------
# Tests: read_file → allowed subdirectories
# ---------------------------------------------------------------------------


class TestReadFileAllowedSubdirs(unittest.TestCase):

    def test_read_file_agents_allowed(self):
        result = _decide("read_file", ".github/agents/some-agent.md")
        self.assertEqual(result, "allow")

    def test_read_file_skills_allowed(self):
        result = _decide("read_file", ".github/skills/SKILL.md")
        self.assertEqual(result, "allow")

    def test_read_file_prompts_allowed(self):
        result = _decide("read_file", ".github/prompts/my-prompt.prompt.md")
        self.assertEqual(result, "allow")

    def test_read_file_instructions_allowed(self):
        result = _decide("read_file", ".github/instructions/copilot-instructions.md")
        self.assertEqual(result, "allow")

    def test_read_alias_agents_allowed(self):
        """'Read' is the Anthropic alias for read_file — must also be allowed."""
        result = _decide("Read", ".github/agents/some-agent.md")
        self.assertEqual(result, "allow")

    def test_read_file_deep_nested_allowed(self):
        """Files nested multiple levels inside an allowed subdir are allowed."""
        result = _decide("read_file", ".github/skills/subfolder/deep-skill.md")
        self.assertEqual(result, "allow")

    def test_read_file_agents_dir_itself_allowed(self):
        """Reading the directory entry itself (no trailing slash) is allowed."""
        result = _decide("read_file", ".github/agents")
        self.assertEqual(result, "allow")


# ---------------------------------------------------------------------------
# Tests: list_dir → allowed subdirectories
# ---------------------------------------------------------------------------


class TestListDirAllowedSubdirs(unittest.TestCase):

    def test_list_dir_agents_allowed(self):
        result = _decide("list_dir", ".github/agents/")
        self.assertEqual(result, "allow")

    def test_list_dir_skills_allowed(self):
        result = _decide("list_dir", ".github/skills/")
        self.assertEqual(result, "allow")

    def test_list_dir_prompts_allowed(self):
        result = _decide("list_dir", ".github/prompts/")
        self.assertEqual(result, "allow")

    def test_list_dir_instructions_allowed(self):
        result = _decide("list_dir", ".github/instructions/")
        self.assertEqual(result, "allow")


# ---------------------------------------------------------------------------
# Tests: absolute path variants
# ---------------------------------------------------------------------------


class TestAbsolutePathVariants(unittest.TestCase):

    def test_absolute_path_agents_allowed(self):
        """Absolute path to allowed subdirectory is allowed."""
        result = _decide("read_file", f"{WS_ROOT}/.github/agents/skill.md")
        self.assertEqual(result, "allow")

    def test_absolute_path_instructions_allowed(self):
        result = _decide(
            "read_file", f"{WS_ROOT}/.github/instructions/copilot-instructions.md"
        )
        self.assertEqual(result, "allow")

    def test_absolute_path_hooks_denied(self):
        """Absolute path to .github/hooks/ is always denied."""
        result = _decide("read_file", f"{WS_ROOT}/.github/hooks/security_gate.py")
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Tests: write operations remain denied
# ---------------------------------------------------------------------------


class TestWriteOperationsDenied(unittest.TestCase):

    def test_create_file_agents_denied(self):
        """Write tools must NOT gain access via the SAF-055 whitelist."""
        result = _decide("create_file", ".github/agents/evil.md")
        self.assertEqual(result, "deny")

    def test_replace_string_in_agents_denied(self):
        result = _decide("replace_string_in_file", ".github/agents/tamper.md")
        self.assertEqual(result, "deny")

    def test_write_file_skills_denied(self):
        result = _decide("write_file", ".github/skills/SKILL.md")
        self.assertEqual(result, "deny")

    def test_edit_file_prompts_denied(self):
        result = _decide("edit_file", ".github/prompts/prompt.md")
        self.assertEqual(result, "deny")

    def test_edit_notebook_instructions_denied(self):
        """edit_notebook_file is not in _READ_ONLY_TOOLS — must be denied."""
        result = _decide("edit_notebook_file", ".github/instructions/copilot-instructions.md")
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Tests: .github/hooks/ fully denied (read AND write)
# ---------------------------------------------------------------------------


class TestHooksFullyDenied(unittest.TestCase):

    def test_read_file_hooks_denied(self):
        result = _decide("read_file", ".github/hooks/security_gate.py")
        self.assertEqual(result, "deny")

    def test_read_hooks_dir_denied(self):
        result = _decide("read_file", ".github/hooks/")
        self.assertEqual(result, "deny")

    def test_list_dir_hooks_denied(self):
        result = _decide("list_dir", ".github/hooks/")
        self.assertEqual(result, "deny")

    def test_create_file_hooks_denied(self):
        result = _decide("create_file", ".github/hooks/evil.py")
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Tests: .github/ root denied
# ---------------------------------------------------------------------------


class TestGithubRootDenied(unittest.TestCase):

    def test_read_file_github_root_denied(self):
        """Reading the .github/ root directory itself is denied."""
        result = _decide("read_file", ".github/")
        self.assertEqual(result, "deny")

    def test_list_dir_github_root_denied(self):
        result = _decide("list_dir", ".github/")
        self.assertEqual(result, "deny")

    def test_read_file_github_no_trailing_slash_denied(self):
        result = _decide("read_file", ".github")
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Tests: unknown .github/ subdirectory denied
# ---------------------------------------------------------------------------


class TestUnknownSubdirDenied(unittest.TestCase):

    def test_read_unknown_subdir_denied(self):
        result = _decide("read_file", ".github/other/foo.md")
        self.assertEqual(result, "deny")

    def test_read_workflows_denied(self):
        """Workflow files are not in the whitelist."""
        result = _decide("read_file", ".github/workflows/ci.yml")
        self.assertEqual(result, "deny")

    def test_list_dir_other_denied(self):
        result = _decide("list_dir", ".github/other/")
        self.assertEqual(result, "deny")

    def test_agents_extra_prefix_not_matched(self):
        """'.github/agents-extra' must NOT match '.github/agents' prefix."""
        result = _decide("read_file", ".github/agents-extra/foo.md")
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Tests: path traversal attempts are denied
# ---------------------------------------------------------------------------


class TestPathTraversalDenied(unittest.TestCase):

    def test_traversal_via_agents_to_hooks(self):
        """Path traversal .github/agents/../hooks/ resolves to .github/hooks/ — deny."""
        result = _decide("read_file", ".github/agents/../hooks/security_gate.py")
        self.assertEqual(result, "deny")

    def test_traversal_via_skills_to_hooks(self):
        result = _decide("read_file", ".github/skills/../../.github/hooks/evil.py")
        self.assertEqual(result, "deny")

    def test_double_traversal_denied(self):
        result = _decide("read_file", ".github/instructions/../../.vscode/settings.json")
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Tests: constants structure validation
# ---------------------------------------------------------------------------


class TestConstants(unittest.TestCase):

    def test_github_read_allowed_is_frozenset(self):
        self.assertIsInstance(sg._GITHUB_READ_ALLOWED, frozenset)

    def test_github_read_allowed_contains_expected_entries(self):
        expected = {".github/agents", ".github/skills", ".github/prompts", ".github/instructions"}
        self.assertEqual(sg._GITHUB_READ_ALLOWED, expected)

    def test_read_only_tools_is_frozenset(self):
        self.assertIsInstance(sg._READ_ONLY_TOOLS, frozenset)

    def test_read_only_tools_contains_expected_tools(self):
        self.assertIn("read_file", sg._READ_ONLY_TOOLS)
        self.assertIn("Read", sg._READ_ONLY_TOOLS)
        self.assertIn("list_dir", sg._READ_ONLY_TOOLS)

    def test_hooks_not_in_read_allowed(self):
        """Security gate code directory must NOT be in the whitelist."""
        self.assertNotIn(".github/hooks", sg._GITHUB_READ_ALLOWED)

    def test_github_read_allowed_re_matches_agents(self):
        self.assertIsNotNone(sg._GITHUB_READ_ALLOWED_RE.search(".github/agents/foo.md"))

    def test_github_read_allowed_re_does_not_match_hooks(self):
        self.assertIsNone(sg._GITHUB_READ_ALLOWED_RE.search(".github/hooks/security_gate.py"))

    def test_github_read_allowed_re_does_not_match_agents_extra(self):
        """Prefix 'agents-extra' must not match 'agents'."""
        self.assertIsNone(sg._GITHUB_READ_ALLOWED_RE.search(".github/agents-extra/foo.md"))


if __name__ == "__main__":
    unittest.main()
