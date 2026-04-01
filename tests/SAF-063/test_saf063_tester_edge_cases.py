"""tests/SAF-063/test_saf063_tester_edge_cases.py

Tester-added edge-case tests for SAF-063: tool name normalization.
These supplement the developer's 22 tests with integration paths,
blocked-zone checks, fail-closed checks, and security bypass probes.

Note on architecture: zone_classifier.classify() requires a real filesystem
workspace root (calls os.listdir to detect the project folder).  Tests that
verify deny behavior use zone_classifier mocks so the test does not depend on
a real directory; tests that verify allow/deny via specific routing logic use
explicit patch.object() calls consistent with the developer's test patterns.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Make the security_gate module importable
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

WS = "c:/fake-ws"
PROJECT_PATH = f"{WS}/Project/notebook.ipynb"
GITHUB_PATH = f"{WS}/.github/hooks/scripts/security_gate.py"
DOCS_PATH = f"{WS}/docs/readme.md"
OUTSIDE_PATH = "c:/other-place/file.py"


# ---------------------------------------------------------------------------
# run_notebook_cell: decide() routing (mocked zone)
# ---------------------------------------------------------------------------
class TestRunNotebookCellDecide(unittest.TestCase):
    def test_run_notebook_cell_project_path_allowed(self) -> None:
        """run_notebook_cell targeting a Project/-zone path must be allowed."""
        with patch.object(sg.zone_classifier, "classify", return_value="allow"), \
             patch.object(sg.zone_classifier, "is_git_internals", return_value=False), \
             patch.object(sg.zone_classifier, "is_workspace_root_readable", return_value=False):
            data = {"tool_name": "run_notebook_cell", "tool_input": {"filePath": PROJECT_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "allow")

    def test_run_notebook_cell_denied_zone(self) -> None:
        """run_notebook_cell with a deny-zone path must be denied."""
        with patch.object(sg.zone_classifier, "classify", return_value="deny"):
            data = {"tool_name": "run_notebook_cell", "tool_input": {"filePath": GITHUB_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "deny")

    def test_run_notebook_cell_no_path_denied(self) -> None:
        """run_notebook_cell with no filePath must fail closed (deny)."""
        data = {"tool_name": "run_notebook_cell"}
        result = sg.decide(data, WS)
        self.assertEqual(result, "deny")

    def test_run_notebook_cell_docs_zone_denied(self) -> None:
        """run_notebook_cell with a docs/-zone path must be denied (not project)."""
        with patch.object(sg.zone_classifier, "classify", return_value="deny"), \
             patch.object(sg.zone_classifier, "is_workspace_root_readable", return_value=False):
            data = {"tool_name": "run_notebook_cell", "tool_input": {"filePath": DOCS_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# read_notebook_cell_output: decide() routing (mocked zone)
# ---------------------------------------------------------------------------
class TestReadNotebookCellOutputDecide(unittest.TestCase):
    def test_read_cell_output_project_path_allowed(self) -> None:
        """read_notebook_cell_output targeting Project/ path must be allowed."""
        with patch.object(sg.zone_classifier, "classify", return_value="allow"), \
             patch.object(sg.zone_classifier, "is_git_internals", return_value=False), \
             patch.object(sg.zone_classifier, "is_workspace_root_readable", return_value=False):
            data = {"tool_name": "read_notebook_cell_output", "tool_input": {"filePath": PROJECT_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "allow")

    def test_read_cell_output_denied_zone(self) -> None:
        """read_notebook_cell_output with a deny-zone path must be denied."""
        with patch.object(sg.zone_classifier, "classify", return_value="deny"):
            data = {"tool_name": "read_notebook_cell_output", "tool_input": {"filePath": GITHUB_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "deny")

    def test_read_cell_output_no_path_denied(self) -> None:
        """read_notebook_cell_output with no filePath must fail closed."""
        data = {"tool_name": "read_notebook_cell_output"}
        result = sg.decide(data, WS)
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# view_image: decide() routing (mocked zone)
# ---------------------------------------------------------------------------
class TestViewImageDecide(unittest.TestCase):
    def test_view_image_denied_zone(self) -> None:
        """view_image with a deny-zone path must be denied."""
        with patch.object(sg.zone_classifier, "classify", return_value="deny"):
            data = {"tool_name": "view_image", "tool_input": {"filePath": GITHUB_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "deny")

    def test_view_image_non_project_denied(self) -> None:
        """view_image with an ask-zone (docs/) path must be denied."""
        with patch.object(sg.zone_classifier, "classify", return_value="deny"), \
             patch.object(sg.zone_classifier, "is_workspace_root_readable", return_value=False):
            data = {"tool_name": "view_image", "tool_input": {"filePath": DOCS_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "deny")

    def test_view_image_no_path_denied(self) -> None:
        """view_image with no filePath must fail closed (deny)."""
        data = {"tool_name": "view_image"}
        result = sg.decide(data, WS)
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# insert_edit_into_file: write tool zone routing (mocked zone)
# ---------------------------------------------------------------------------
class TestInsertEditIntoFileZone(unittest.TestCase):
    def test_insert_edit_github_zone_denied(self) -> None:
        """insert_edit_into_file to .github zone path must be denied."""
        with patch.object(sg.zone_classifier, "classify", return_value="deny"):
            data = {"tool_name": "insert_edit_into_file", "tool_input": {"filePath": GITHUB_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "deny")

    def test_insert_edit_docs_zone_denied(self) -> None:
        """insert_edit_into_file to docs/ (non-project zone) must be denied."""
        with patch.object(sg.zone_classifier, "classify", return_value="deny"):
            data = {"tool_name": "insert_edit_into_file", "tool_input": {"filePath": DOCS_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "deny")

    def test_insert_edit_project_zone_allowed(self) -> None:
        """insert_edit_into_file to Project/ zone must be allowed."""
        with patch.object(sg.zone_classifier, "classify", return_value="allow"), \
             patch.object(sg.zone_classifier, "is_git_internals", return_value=False):
            data = {"tool_name": "insert_edit_into_file", "tool_input": {"filePath": PROJECT_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "allow")


# ---------------------------------------------------------------------------
# edit_notebook_file: fail-closed and write-tool zone routing (mocked zone)
# ---------------------------------------------------------------------------
class TestEditNotebookFileFail(unittest.TestCase):
    def test_edit_notebook_no_path_denied(self) -> None:
        """edit_notebook_file with no filePath must fail closed (deny)."""
        data = {"tool_name": "edit_notebook_file"}
        result = sg.decide(data, WS)
        self.assertEqual(result, "deny")

    def test_edit_notebook_github_zone_denied(self) -> None:
        """edit_notebook_file to .github zone must be denied."""
        with patch.object(sg.zone_classifier, "classify", return_value="deny"):
            data = {"tool_name": "edit_notebook_file", "tool_input": {"filePath": GITHUB_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "deny")

    def test_edit_notebook_project_zone_allowed(self) -> None:
        """edit_notebook_file to Project/ zone must be allowed."""
        with patch.object(sg.zone_classifier, "classify", return_value="allow"), \
             patch.object(sg.zone_classifier, "is_git_internals", return_value=False):
            data = {"tool_name": "edit_notebook_file", "tool_input": {"filePath": PROJECT_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "allow")


# ---------------------------------------------------------------------------
# create_new_jupyter_notebook: fail-closed and write-tool zone routing
# ---------------------------------------------------------------------------
class TestCreateNewJupyterNotebookFail(unittest.TestCase):
    def test_create_notebook_no_path_denied(self) -> None:
        """create_new_jupyter_notebook with no filePath must fail closed."""
        data = {"tool_name": "create_new_jupyter_notebook"}
        result = sg.decide(data, WS)
        self.assertEqual(result, "deny")

    def test_create_notebook_github_zone_denied(self) -> None:
        """create_new_jupyter_notebook to .github zone must be denied."""
        with patch.object(sg.zone_classifier, "classify", return_value="deny"):
            data = {"tool_name": "create_new_jupyter_notebook", "tool_input": {"filePath": GITHUB_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "deny")

    def test_create_notebook_project_zone_allowed(self) -> None:
        """create_new_jupyter_notebook to Project/ zone must be allowed."""
        with patch.object(sg.zone_classifier, "classify", return_value="allow"), \
             patch.object(sg.zone_classifier, "is_git_internals", return_value=False):
            data = {"tool_name": "create_new_jupyter_notebook", "tool_input": {"filePath": PROJECT_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "allow")

    def test_create_notebook_docs_zone_denied(self) -> None:
        """create_new_jupyter_notebook to docs/ (non-project zone) must be denied."""
        with patch.object(sg.zone_classifier, "classify", return_value="deny"):
            data = {"tool_name": "create_new_jupyter_notebook", "tool_input": {"filePath": DOCS_PATH}}
            result = sg.decide(data, WS)
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Security: new always-allow tools cannot be abused as write-tool proxies
# ---------------------------------------------------------------------------
class TestAlwaysAllowToolsAreSafe(unittest.TestCase):
    def test_get_terminal_output_not_in_write_tools(self) -> None:
        """get_terminal_output must NOT be in _WRITE_TOOLS (read-only introspection)."""
        self.assertNotIn("get_terminal_output", sg._WRITE_TOOLS)

    def test_terminal_last_command_not_in_write_tools(self) -> None:
        """terminal_last_command must NOT be in _WRITE_TOOLS."""
        self.assertNotIn("terminal_last_command", sg._WRITE_TOOLS)

    def test_test_failure_not_in_write_tools(self) -> None:
        """test_failure must NOT be in _WRITE_TOOLS."""
        self.assertNotIn("test_failure", sg._WRITE_TOOLS)

    def test_copilot_get_notebook_summary_not_in_write_tools(self) -> None:
        """copilot_getNotebookSummary must NOT be in _WRITE_TOOLS (read-only notebook tool)."""
        self.assertNotIn("copilot_getNotebookSummary", sg._WRITE_TOOLS)


# ---------------------------------------------------------------------------
# Security: tool name sets are mutually consistent (no accidental overlap that
# could cause a write tool to be treated as always-allow, bypassing zone checks)
# ---------------------------------------------------------------------------
class TestToolSetConsistency(unittest.TestCase):
    def test_write_tools_not_in_always_allow(self) -> None:
        """No _WRITE_TOOLS member may appear in _ALWAYS_ALLOW_TOOLS
        (write tools must always be zone-checked, never auto-allowed)."""
        overlap = sg._WRITE_TOOLS & sg._ALWAYS_ALLOW_TOOLS
        self.assertEqual(
            overlap,
            frozenset(),
            f"Write tools found in always-allow set (security risk): {overlap}",
        )

    def test_terminal_tools_not_in_always_allow(self) -> None:
        """No _TERMINAL_TOOLS member may appear in _ALWAYS_ALLOW_TOOLS
        (terminal tools require explicit zone/command checks)."""
        overlap = sg._TERMINAL_TOOLS & sg._ALWAYS_ALLOW_TOOLS
        self.assertEqual(
            overlap,
            frozenset(),
            f"Terminal tools found in always-allow set: {overlap}",
        )

    def test_insert_edit_not_in_always_allow(self) -> None:
        """insert_edit_into_file must NOT be in _ALWAYS_ALLOW_TOOLS."""
        self.assertNotIn("insert_edit_into_file", sg._ALWAYS_ALLOW_TOOLS)

    def test_run_in_terminal_not_in_always_allow(self) -> None:
        """run_in_terminal must NOT be in _ALWAYS_ALLOW_TOOLS (requires command scan)."""
        self.assertNotIn("run_in_terminal", sg._ALWAYS_ALLOW_TOOLS)


if __name__ == "__main__":
    unittest.main()
