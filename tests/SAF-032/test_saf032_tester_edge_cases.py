"""SAF-032 Tester Edge Cases — Additional tests beyond the Developer's suite.

Edge cases focused on:
1. list_dir targeting .git (no trailing slash) via decide()
2. .gitmodules in project root must be allowed (not .git/)
3. .github/ paths still denied by deny-zone (not by SAF-032 .git check)
4. Deep traversal sequences resolving into .git/
5. edit_notebook_file targeting .git/ path
6. .git blocking is path-based, not tool-name-based
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Path setup — add scripts dir so zone_classifier and security_gate import
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import zone_classifier  # noqa: E402
import security_gate    # noqa: E402

# ---------------------------------------------------------------------------
# Workspace fixture
# ---------------------------------------------------------------------------

WS_ROOT = "c:/workspace"
PROJECT_DIR = "myproject"


@pytest.fixture(autouse=True)
def patch_project_folder():
    """Make detect_project_folder return 'myproject' without needing real dirs."""
    with patch.object(zone_classifier, "detect_project_folder", return_value=PROJECT_DIR):
        yield


def _decide(payload: dict) -> str:
    return security_gate.decide(payload, WS_ROOT)


# ---------------------------------------------------------------------------
# EC-1: list_dir targeting .git (no trailing slash) — end-to-end via decide()
# Developer tests is_git_internals() in isolation but does not test list_dir
# with a bare .git path (no trailing slash) through decide().
# ---------------------------------------------------------------------------

class TestListDirGitBareNoTrailingSlash:
    """list_dir with '.git' (no trailing slash) must be blocked end-to-end."""

    def test_list_dir_bare_git_via_decide(self):
        """`list_dir` targeting `.git` (no slash) MUST be denied via decide()."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git"
        payload = {"tool_name": "list_dir", "tool_input": {"directory": path}}
        assert _decide(payload) == "deny"

    def test_is_git_internals_bare_git_is_true(self):
        """`is_git_internals` for bare `.git` (no slash) MUST return True."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git"
        assert zone_classifier.is_git_internals(path) is True

    def test_list_dir_git_subdir_no_trailing_slash_via_decide(self):
        """`list_dir` targeting `.git/objects` (no trailing slash) MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/objects"
        payload = {"tool_name": "list_dir", "tool_input": {"directory": path}}
        assert _decide(payload) == "deny"


# ---------------------------------------------------------------------------
# EC-2: .gitmodules in project root — must be ALLOWED (not inside .git/)
# Developer tests .gitignore and .gitkeep, but not .gitmodules.
# ---------------------------------------------------------------------------

class TestGitmodulesAllowed:
    """.gitmodules is a project-root file, not inside .git/ — must be allowed."""

    def test_create_file_gitmodules_allowed(self):
        """`create_file` → .gitmodules in project root MUST be allowed."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.gitmodules"
        payload = {"tool_name": "create_file", "tool_input": {"filePath": path}}
        assert _decide(payload) == "allow"

    def test_read_file_gitmodules_allowed(self):
        """`read_file` → .gitmodules in project root MUST be allowed."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.gitmodules"
        payload = {"tool_name": "read_file", "tool_input": {"filePath": path}}
        assert _decide(payload) == "allow"

    def test_is_git_internals_gitmodules_is_false(self):
        """`is_git_internals('.gitmodules')` MUST return False."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.gitmodules"
        assert zone_classifier.is_git_internals(path) is False

    def test_gitattributes_in_root_allowed(self):
        """`create_file` → .gitattributes in project root MUST be allowed."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.gitattributes"
        payload = {"tool_name": "create_file", "tool_input": {"filePath": path}}
        assert _decide(payload) == "allow"


# ---------------------------------------------------------------------------
# EC-3: .github/ denied by the deny-zone, NOT by SAF-032's .git check
# The deny-zone check fires before is_git_internals(), so .github/ paths
# are denied by the existing zone mechanism and must NOT mislead is_git_internals().
# ---------------------------------------------------------------------------

class TestGithubDeniedByZoneNotBySaf032:
    """.github/ at workspace-root level is denied by deny-zone; is_git_internals False.

    The zone classifier denies paths whose FIRST segment (relative to the
    workspace root) is a deny-zone dir (.github, .vscode, noagentzone).
    Paths at *workspace root level* like `c:/workspace/.github/...` ARE denied.
    Paths inside the project folder like `c:/workspace/myproject/.github/...`
    are in the allow zone (project folder is first segment) — governed by the
    security_gate integrity check (SAF-008), not the zone classifier.
    The SAF-032 .git check must NOT fire for .github paths (is_git_internals=False).
    """

    def test_create_file_workspace_root_github_denied(self):
        """`create_file` → workspace-root .github/ path MUST be denied by zone."""
        # c:/workspace/.github/... — first segment IS .github → deny zone
        path = f"{WS_ROOT}/.github/workflows/ci.yml"
        payload = {"tool_name": "create_file", "tool_input": {"filePath": path}}
        assert _decide(payload) == "deny"

    def test_read_file_workspace_root_github_denied(self):
        """`read_file` → workspace-root .github/ path MUST be denied by zone."""
        path = f"{WS_ROOT}/.github/CODEOWNERS"
        payload = {"tool_name": "read_file", "tool_input": {"filePath": path}}
        assert _decide(payload) == "deny"

    def test_is_git_internals_github_is_false(self):
        """`is_git_internals('.github/...')` MUST return False — it is not .git."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.github/hooks/pre-commit"
        assert zone_classifier.is_git_internals(path) is False

    def test_is_git_internals_github_root_is_false(self):
        """`is_git_internals('.github')` (no trailing slash) MUST return False."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.github"
        assert zone_classifier.is_git_internals(path) is False


# ---------------------------------------------------------------------------
# EC-4: Deep traversal sequences resolving into .git/
# Developer tests 1-level and 2-level traversal; these test deeper nesting.
# ---------------------------------------------------------------------------

class TestDeepTraversalToGit:
    """Path traversal with many ../ segments that ultimately resolve to .git/."""

    def test_six_level_traversal_create_file(self):
        """Six-level deep traversal resolving to .git/config MUST be denied."""
        # a/b/c/d/e/f/../../../../../../.git/config normalises to
        # c:/workspace/myproject/.git/config
        path = (
            f"{WS_ROOT}/{PROJECT_DIR}"
            "/a/b/c/d/e/f/../../../../../../.git/config"
        )
        payload = {"tool_name": "create_file", "tool_input": {"filePath": path}}
        assert _decide(payload) == "deny"

    def test_six_level_traversal_is_git_internals(self):
        """is_git_internals with six-level traversal MUST return True after normpath."""
        path = (
            f"{WS_ROOT}/{PROJECT_DIR}"
            "/a/b/c/d/e/f/../../../../../../.git/HEAD"
        )
        assert zone_classifier.is_git_internals(path) is True

    def test_four_level_traversal_read_file(self):
        """Four-level traversal to .git/objects MUST be denied for read_file."""
        path = (
            f"{WS_ROOT}/{PROJECT_DIR}"
            "/components/src/utils/helpers/../../../../.git/objects/pack/abc.idx"
        )
        payload = {"tool_name": "read_file", "tool_input": {"filePath": path}}
        assert _decide(payload) == "deny"

    def test_backslash_traversal_to_git(self):
        """Backslash-based traversal to .git/ MUST be denied (Windows paths)."""
        path = f"{WS_ROOT}\\{PROJECT_DIR}\\src\\..\\.git\\config"
        payload = {"tool_name": "read_file", "tool_input": {"filePath": path}}
        assert _decide(payload) == "deny"


# ---------------------------------------------------------------------------
# EC-5: edit_notebook_file targeting .git/ path
# edit_notebook_file is not in _WRITE_TOOLS and would reach the unknown-tool
# deny branch if not in _EXEMPT_TOOLS. Either way, it MUST be denied.
# ---------------------------------------------------------------------------

class TestEditNotebookFileGitBlocked:
    """`edit_notebook_file` on .git/ paths must result in deny."""

    def test_edit_notebook_file_git_config_denied(self):
        """`edit_notebook_file` targeting .git/config MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/config"
        payload = {"tool_name": "edit_notebook_file", "tool_input": {"filePath": path}}
        assert _decide(payload) == "deny"

    def test_edit_notebook_file_git_hooks_denied(self):
        """`edit_notebook_file` targeting .git/hooks/ MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/hooks/pre-commit"
        payload = {"tool_name": "edit_notebook_file", "tool_input": {"filePath": path}}
        assert _decide(payload) == "deny"

    def test_edit_notebook_file_git_head_denied(self):
        """`edit_notebook_file` targeting .git/HEAD MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/HEAD"
        payload = {"tool_name": "edit_notebook_file", "tool_input": {"filePath": path}}
        assert _decide(payload) == "deny"


# ---------------------------------------------------------------------------
# EC-6: .git blocking is path-based — multiple exempt tools must all deny
# The SAF-032 check in decide() applies to all exempt tools reaching the
# zone path — the tool name itself does not grant access to .git/.
# ---------------------------------------------------------------------------

class TestGitBlockingIsPathBasedNotToolBased:
    """All exempt file tools must be denied when targeting .git/."""

    def test_all_exempt_read_write_tools_denied_on_git(self):
        """Every exempt file tool targeting .git/ must return deny."""
        git_path = f"{WS_ROOT}/{PROJECT_DIR}/.git/config"
        cases = [
            ("read_file",              {"filePath": git_path}),
            ("create_file",            {"filePath": git_path}),
            ("replace_string_in_file", {"filePath": git_path}),
            ("edit_file",              {"filePath": git_path}),
            ("write_file",             {"filePath": git_path}),
            ("list_dir",               {"directory": git_path}),
        ]
        for tool_name, tool_input in cases:
            payload = {"tool_name": tool_name, "tool_input": tool_input}
            result = _decide(payload)
            assert result == "deny", (
                f"Tool '{tool_name}' targeting .git/ should be denied, got '{result}'"
            )

    def test_multi_replace_with_only_git_paths_denied(self):
        """multi_replace_string_in_file with all .git/ paths MUST be denied."""
        git_paths = [
            f"{WS_ROOT}/{PROJECT_DIR}/.git/config",
            f"{WS_ROOT}/{PROJECT_DIR}/.git/hooks/pre-commit",
        ]
        payload = {
            "tool_name": "multi_replace_string_in_file",
            "replacements": [{"filePath": p} for p in git_paths],
        }
        assert _decide(payload) == "deny"

    def test_normal_paths_still_allowed_after_git_check(self):
        """Normal project paths must remain allowed — gate is .git/-specific."""
        normal_path = f"{WS_ROOT}/{PROJECT_DIR}/src/app.py"
        cases = [
            ("read_file",              {"filePath": normal_path}),
            ("create_file",            {"filePath": normal_path}),
            ("replace_string_in_file", {"filePath": normal_path}),
            ("list_dir",               {"directory": f"{WS_ROOT}/{PROJECT_DIR}/src"}),
        ]
        for tool_name, tool_input in cases:
            payload = {"tool_name": tool_name, "tool_input": tool_input}
            result = _decide(payload)
            assert result == "allow", (
                f"Tool '{tool_name}' on normal path should be allowed, got '{result}'"
            )
