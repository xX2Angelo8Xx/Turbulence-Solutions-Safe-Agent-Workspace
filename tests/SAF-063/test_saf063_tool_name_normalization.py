"""tests/SAF-063/test_saf063_tool_name_normalization.py

Tests for SAF-063: tool name normalization in the security gate.
Validates:
  1. vscode_askQuestions (camelCase) is always allowed
  2. vscode_ask_questions (snake_case) is still allowed (backward compat)
  3. All newly added always-allow tool names return "allow"
  4. insert_edit_into_file to a project-zone path is allowed
  5. insert_edit_into_file to a path outside project is denied
  6. insert_edit_into_file is in _WRITE_TOOLS
  7. view_image is in _EXEMPT_TOOLS (path-checked)
  8. edit_notebook_file is in _WRITE_TOOLS and _EXEMPT_TOOLS (write-checked)
  9. create_new_jupyter_notebook is in _WRITE_TOOLS and _EXEMPT_TOOLS
  10. read_notebook_cell_output is in _EXEMPT_TOOLS (read-only, path-checked)
  11. run_notebook_cell is in _EXEMPT_TOOLS (path-checked)
  12. Unknown tools are still denied
  13. Security bypass: unknown camelCase tool rejected
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


# Fake workspace root / project path used throughout tests.
# These do not need to exist on disk because decide() is called without
# integrity verification here (we bypass main() and call decide() directly).
WS_ROOT = "c:/fake-workspace"
PROJECT_PATH = f"{WS_ROOT}/Project/src/app.py"
OUTSIDE_PATH = "c:/other-place/file.py"


def _allow_payload(tool_name: str, file_path: str = "") -> dict:
    """Build a minimal tool-call payload."""
    payload: dict = {"tool_name": tool_name}
    if file_path:
        payload["tool_input"] = {"filePath": file_path}
    return payload


# ---------------------------------------------------------------------------
# Test 1 — vscode_askQuestions (camelCase) is allowed
# ---------------------------------------------------------------------------
class TestVscodeAskQuestionsCamelCase(unittest.TestCase):
    def test_vscode_ask_questions_camel_case_allowed(self) -> None:
        """vscode_askQuestions (camelCase) must be in _ALWAYS_ALLOW_TOOLS and allowed."""
        self.assertIn("vscode_askQuestions", sg._ALWAYS_ALLOW_TOOLS)
        data = {"tool_name": "vscode_askQuestions"}
        result = sg.decide(data, WS_ROOT)
        self.assertEqual(result, "allow")

    def test_vscode_ask_questions_camel_case_security_bypass(self) -> None:
        """Confirm the decision is truly "allow", not a coincidental allow from fallback."""
        # The name is in _ALWAYS_ALLOW_TOOLS, so it returns before any path check.
        self.assertIn("vscode_askQuestions", sg._ALWAYS_ALLOW_TOOLS)


# ---------------------------------------------------------------------------
# Test 2 — vscode_ask_questions (snake_case) backward compatibility
# ---------------------------------------------------------------------------
class TestVscodeAskQuestionsSnakeCase(unittest.TestCase):
    def test_vscode_ask_questions_snake_case_allowed(self) -> None:
        """vscode_ask_questions (snake_case) must remain in _ALWAYS_ALLOW_TOOLS."""
        self.assertIn("vscode_ask_questions", sg._ALWAYS_ALLOW_TOOLS)
        data = {"tool_name": "vscode_ask_questions"}
        result = sg.decide(data, WS_ROOT)
        self.assertEqual(result, "allow")


# ---------------------------------------------------------------------------
# Test 3 — All newly added always-allow tools return "allow"
# ---------------------------------------------------------------------------
NEW_ALWAYS_ALLOW = [
    "get_terminal_output",
    "terminal_last_command",
    "terminal_selection",
    "test_failure",
    "tool_search",
    "get_vscode_api",
    "switch_agent",
    "copilot_getNotebookSummary",
    "get_search_view_results",
    "install_extension",
    "create_and_run_task",
    "get_task_output",
    "runTests",
]


class TestNewAlwaysAllowTools(unittest.TestCase):
    def test_new_tools_in_frozenset(self) -> None:
        """All new tool names must be present in _ALWAYS_ALLOW_TOOLS."""
        for tool in NEW_ALWAYS_ALLOW:
            with self.subTest(tool=tool):
                self.assertIn(tool, sg._ALWAYS_ALLOW_TOOLS)

    def test_new_tools_decide_allow(self) -> None:
        """decide() must return 'allow' for each newly added always-allow tool."""
        for tool in NEW_ALWAYS_ALLOW:
            with self.subTest(tool=tool):
                data = {"tool_name": tool}
                result = sg.decide(data, WS_ROOT)
                self.assertEqual(result, "allow", f"{tool!r} returned {result!r}")


# ---------------------------------------------------------------------------
# Test 4 — insert_edit_into_file allowed when path is in project zone
# ---------------------------------------------------------------------------
class TestInsertEditIntoFileAllow(unittest.TestCase):
    def test_insert_edit_allowed_in_project(self) -> None:
        """insert_edit_into_file to a project-zone path must be allowed."""
        with patch.object(
            sg.zone_classifier, "classify", return_value="allow"
        ), patch.object(
            sg.zone_classifier, "is_git_internals", return_value=False
        ):
            data = _allow_payload("insert_edit_into_file", PROJECT_PATH)
            result = sg.decide(data, WS_ROOT)
            self.assertEqual(result, "allow")


# ---------------------------------------------------------------------------
# Test 5 — insert_edit_into_file denied when path is outside project
# ---------------------------------------------------------------------------
class TestInsertEditIntoFileDeny(unittest.TestCase):
    def test_insert_edit_denied_outside_project(self) -> None:
        """insert_edit_into_file to a path outside the project zone must be denied."""
        with patch.object(
            sg.zone_classifier, "classify", return_value="deny"
        ):
            data = _allow_payload("insert_edit_into_file", OUTSIDE_PATH)
            result = sg.decide(data, WS_ROOT)
            self.assertEqual(result, "deny")

    def test_insert_edit_denied_no_path(self) -> None:
        """insert_edit_into_file with no filePath fails closed (deny)."""
        data = {"tool_name": "insert_edit_into_file"}
        with patch.object(sg.zone_classifier, "classify", return_value="deny"):
            result = sg.decide(data, WS_ROOT)
            self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Test 6 — insert_edit_into_file is in _WRITE_TOOLS
# ---------------------------------------------------------------------------
class TestInsertEditInWriteTools(unittest.TestCase):
    def test_insert_edit_in_write_tools(self) -> None:
        """insert_edit_into_file must be in _WRITE_TOOLS frozenset."""
        self.assertIn("insert_edit_into_file", sg._WRITE_TOOLS)


# ---------------------------------------------------------------------------
# Test 7 — view_image is in _EXEMPT_TOOLS
# ---------------------------------------------------------------------------
class TestViewImageExempt(unittest.TestCase):
    def test_view_image_in_exempt_tools(self) -> None:
        """view_image must be in _EXEMPT_TOOLS (path-checked per zone)."""
        self.assertIn("view_image", sg._EXEMPT_TOOLS)

    def test_view_image_allowed_in_project(self) -> None:
        """view_image to a project-zone path must be allowed."""
        with patch.object(
            sg.zone_classifier, "classify", return_value="allow"
        ), patch.object(
            sg.zone_classifier, "is_git_internals", return_value=False
        ), patch.object(
            sg.zone_classifier, "is_workspace_root_readable", return_value=False
        ):
            data = _allow_payload("view_image", PROJECT_PATH)
            result = sg.decide(data, WS_ROOT)
            self.assertEqual(result, "allow")


# ---------------------------------------------------------------------------
# Test 8 — edit_notebook_file is in _WRITE_TOOLS and _EXEMPT_TOOLS
# ---------------------------------------------------------------------------
class TestEditNotebookFile(unittest.TestCase):
    def test_edit_notebook_in_write_tools(self) -> None:
        """edit_notebook_file must be in _WRITE_TOOLS."""
        self.assertIn("edit_notebook_file", sg._WRITE_TOOLS)

    def test_edit_notebook_in_exempt_tools(self) -> None:
        """edit_notebook_file must be in _EXEMPT_TOOLS."""
        self.assertIn("edit_notebook_file", sg._EXEMPT_TOOLS)

    def test_edit_notebook_denied_outside_project(self) -> None:
        """edit_notebook_file outside project is denied via _WRITE_TOOLS path."""
        with patch.object(sg.zone_classifier, "classify", return_value="deny"):
            data = _allow_payload("edit_notebook_file", OUTSIDE_PATH)
            result = sg.decide(data, WS_ROOT)
            self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Test 9 — create_new_jupyter_notebook is in _WRITE_TOOLS and _EXEMPT_TOOLS
# ---------------------------------------------------------------------------
class TestCreateNewJupyterNotebook(unittest.TestCase):
    def test_create_notebook_in_write_tools(self) -> None:
        """create_new_jupyter_notebook must be in _WRITE_TOOLS."""
        self.assertIn("create_new_jupyter_notebook", sg._WRITE_TOOLS)

    def test_create_notebook_in_exempt_tools(self) -> None:
        """create_new_jupyter_notebook must be in _EXEMPT_TOOLS."""
        self.assertIn("create_new_jupyter_notebook", sg._EXEMPT_TOOLS)


# ---------------------------------------------------------------------------
# Test 10 — read_notebook_cell_output is in _EXEMPT_TOOLS
# ---------------------------------------------------------------------------
class TestReadNotebookCellOutput(unittest.TestCase):
    def test_read_cell_output_in_exempt_tools(self) -> None:
        """read_notebook_cell_output must be in _EXEMPT_TOOLS."""
        self.assertIn("read_notebook_cell_output", sg._EXEMPT_TOOLS)


# ---------------------------------------------------------------------------
# Test 11 — run_notebook_cell is in _EXEMPT_TOOLS
# ---------------------------------------------------------------------------
class TestRunNotebookCell(unittest.TestCase):
    def test_run_notebook_cell_in_exempt_tools(self) -> None:
        """run_notebook_cell must be in _EXEMPT_TOOLS."""
        self.assertIn("run_notebook_cell", sg._EXEMPT_TOOLS)


# ---------------------------------------------------------------------------
# Test 12 — Unknown tools are still denied
# ---------------------------------------------------------------------------
class TestUnknownToolDenied(unittest.TestCase):
    def test_completely_unknown_tool_denied(self) -> None:
        """A tool name not in any set must be denied."""
        data = {"tool_name": "totally_unknown_tool_xyz"}
        result = sg.decide(data, WS_ROOT)
        self.assertEqual(result, "deny")

    def test_empty_tool_name_denied(self) -> None:
        """An empty tool name falls through to path-check path and is denied (no path)."""
        data = {"tool_name": ""}
        result = sg.decide(data, WS_ROOT)
        self.assertEqual(result, "deny")


# ---------------------------------------------------------------------------
# Test 13 — Security bypass: unknown camelCase tool name rejected
# ---------------------------------------------------------------------------
class TestSecurityBypassPrevented(unittest.TestCase):
    def test_malicious_camel_case_tool_denied(self) -> None:
        """An arbitrary camelCase tool not in any allowlist must be denied."""
        data = {"tool_name": "dangerousToolXyz"}
        result = sg.decide(data, WS_ROOT)
        self.assertEqual(result, "deny")

    def test_camel_case_variant_of_terminal_tool_denied(self) -> None:
        """A camelCase variant of run_in_terminal not in any set must be denied."""
        # "runInTerminal" is NOT in _TERMINAL_TOOLS, so it must be denied.
        data = {"tool_name": "runInTerminal", "tool_input": {"command": "ls"}}
        result = sg.decide(data, WS_ROOT)
        self.assertEqual(result, "deny")


if __name__ == "__main__":
    unittest.main()
