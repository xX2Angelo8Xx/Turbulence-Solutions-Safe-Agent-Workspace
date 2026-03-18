"""SAF-032 — Block file tools in .git/ directories.

Tests verify that file tools (create_file, replace_string_in_file,
multi_replace_string_in_file, read_file, list_dir) are denied when targeting
paths inside .git/ within the project folder.

Normal project folder operations must remain unaffected.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Path setup — add scripts dir so zone_classifier and security_gate import
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "coding" / ".github" / "hooks" / "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import zone_classifier  # noqa: E402
import security_gate    # noqa: E402

# ---------------------------------------------------------------------------
# Workspace fixture
# ---------------------------------------------------------------------------

WS_ROOT = "c:/workspace"
PROJECT_DIR = "myproject"   # simulated project folder name


def _payload_create_file(path: str) -> dict:
    return {"tool_name": "create_file", "tool_input": {"filePath": path}}


def _payload_read_file(path: str) -> dict:
    return {"tool_name": "read_file", "tool_input": {"filePath": path}}


def _payload_list_dir(path: str) -> dict:
    return {"tool_name": "list_dir", "tool_input": {"directory": path}}


def _payload_replace(path: str) -> dict:
    return {"tool_name": "replace_string_in_file", "tool_input": {"filePath": path}}


def _payload_multi_replace(*paths: str) -> dict:
    return {
        "tool_name": "multi_replace_string_in_file",
        "replacements": [{"filePath": p} for p in paths],
    }


@pytest.fixture(autouse=True)
def patch_project_folder(tmp_path):
    """Make detect_project_folder return 'myproject' without needing real dirs."""
    with patch.object(zone_classifier, "detect_project_folder", return_value=PROJECT_DIR):
        yield


def _decide(payload: dict) -> str:
    return security_gate.decide(payload, WS_ROOT)


# ---------------------------------------------------------------------------
# is_git_internals unit tests
# ---------------------------------------------------------------------------

class TestIsGitInternals:
    def test_inside_git_hooks(self):
        assert zone_classifier.is_git_internals("c:/workspace/myproject/.git/hooks/pre-commit") is True

    def test_inside_git_config(self):
        assert zone_classifier.is_git_internals("c:/workspace/myproject/.git/config") is True

    def test_git_dir_itself_no_trailing_slash(self):
        assert zone_classifier.is_git_internals("c:/workspace/myproject/.git") is True

    def test_git_dir_with_trailing_slash(self):
        # normalize_path strips trailing slash; endswith("/.git") should match
        assert zone_classifier.is_git_internals("c:/workspace/myproject/.git/") is True

    def test_normal_project_path_not_git(self):
        assert zone_classifier.is_git_internals("c:/workspace/myproject/src/app.py") is False

    def test_workspace_root_not_git(self):
        assert zone_classifier.is_git_internals("c:/workspace/myproject") is False

    def test_upper_case_git(self):
        # normalize_path lowercases — .GIT/ must be caught
        assert zone_classifier.is_git_internals("c:/workspace/myproject/.GIT/config") is True

    def test_mixed_case_git_inner(self):
        assert zone_classifier.is_git_internals("c:/workspace/myproject/.Git/HEAD") is True

    def test_traversal_resolves_to_git(self):
        # src/../../.git after normpath becomes .git (relative), then checked
        assert zone_classifier.is_git_internals("c:/workspace/myproject/src/../.git/config") is True

    def test_path_not_starting_with_git(self):
        # A path segment like ".gitignore" must NOT be confused with ".git/"
        assert zone_classifier.is_git_internals("c:/workspace/myproject/.gitignore") is False

    def test_gitignore_inside_project(self):
        assert zone_classifier.is_git_internals("c:/workspace/myproject/src/.gitignore") is False


# ---------------------------------------------------------------------------
# SAF-032 test cases — file tools blocked for .git/ paths
# ---------------------------------------------------------------------------

class TestCreateFileGitBlocked:
    def test_create_file_git_hooks(self):
        """create_file → ProjectFolder/.git/hooks/pre-commit MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/hooks/pre-commit"
        assert _decide(_payload_create_file(path)) == "deny"

    def test_create_file_git_config(self):
        """create_file → ProjectFolder/.git/config MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/config"
        assert _decide(_payload_create_file(path)) == "deny"

    def test_create_file_git_head(self):
        """create_file → ProjectFolder/.git/HEAD MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/HEAD"
        assert _decide(_payload_create_file(path)) == "deny"


class TestReadFileGitBlocked:
    def test_read_file_git_head(self):
        """read_file → ProjectFolder/.git/HEAD MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/HEAD"
        assert _decide(_payload_read_file(path)) == "deny"

    def test_read_file_git_config(self):
        """read_file → ProjectFolder/.git/config MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/config"
        assert _decide(_payload_read_file(path)) == "deny"

    def test_read_file_git_object(self):
        """read_file → ProjectFolder/.git/objects/pack/... MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/objects/pack/pack-abc123.idx"
        assert _decide(_payload_read_file(path)) == "deny"


class TestListDirGitBlocked:
    def test_list_dir_git_root(self):
        """list_dir → ProjectFolder/.git/ MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/"
        assert _decide(_payload_list_dir(path)) == "deny"

    def test_list_dir_git_hooks(self):
        """list_dir → ProjectFolder/.git/hooks/ MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/hooks"
        assert _decide(_payload_list_dir(path)) == "deny"


class TestReplaceStringGitBlocked:
    def test_replace_string_in_file_git_config(self):
        """replace_string_in_file → ProjectFolder/.git/config MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/config"
        assert _decide(_payload_replace(path)) == "deny"

    def test_replace_string_in_file_git_hooks_script(self):
        """replace_string_in_file → ProjectFolder/.git/hooks/commit-msg MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.git/hooks/commit-msg"
        assert _decide(_payload_replace(path)) == "deny"


class TestMultiReplaceGitBlocked:
    def test_multi_replace_single_git_path(self):
        """multi_replace with a .git path MUST be denied."""
        payload = _payload_multi_replace(f"{WS_ROOT}/{PROJECT_DIR}/.git/config")
        assert _decide(payload) == "deny"

    def test_multi_replace_mixed_git_and_normal(self):
        """multi_replace with one normal + one .git path MUST be denied."""
        normal = f"{WS_ROOT}/{PROJECT_DIR}/src/app.py"
        git_path = f"{WS_ROOT}/{PROJECT_DIR}/.git/config"
        payload = _payload_multi_replace(normal, git_path)
        assert _decide(payload) == "deny"


# ---------------------------------------------------------------------------
# Normal project folder operations — MUST remain unaffected
# ---------------------------------------------------------------------------

class TestNormalProjectOpsAllowed:
    def test_create_file_normal_project_path(self):
        """create_file inside src/ MUST be allowed."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/src/app.py"
        assert _decide(_payload_create_file(path)) == "allow"

    def test_read_file_normal_project_path(self):
        """read_file inside project folder MUST be allowed."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/README.md"
        assert _decide(_payload_read_file(path)) == "allow"

    def test_list_dir_normal_project_path(self):
        """list_dir inside project src/ MUST be allowed."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/src"
        assert _decide(_payload_list_dir(path)) == "allow"

    def test_replace_string_normal_project_path(self):
        """replace_string_in_file inside project MUST be allowed."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/main.py"
        assert _decide(_payload_replace(path)) == "allow"

    def test_multi_replace_all_normal_paths(self):
        """multi_replace with only normal project paths MUST be allowed."""
        paths = [
            f"{WS_ROOT}/{PROJECT_DIR}/src/app.py",
            f"{WS_ROOT}/{PROJECT_DIR}/tests/test_app.py",
        ]
        payload = _payload_multi_replace(*paths)
        assert _decide(payload) == "allow"

    def test_gitignore_file_allowed(self):
        """create_file → .gitignore in project root MUST be allowed (not .git/)."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.gitignore"
        assert _decide(_payload_create_file(path)) == "allow"

    def test_gitkeep_file_allowed(self):
        """create_file → src/.gitkeep MUST be allowed."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/src/.gitkeep"
        assert _decide(_payload_create_file(path)) == "allow"


# ---------------------------------------------------------------------------
# Path traversal — MUST be denied
# ---------------------------------------------------------------------------

class TestPathTraversalGitBlocked:
    def test_absolute_path_traversal_to_git_config(self):
        """Absolute path traversal src/../../.git/config MUST be denied."""
        # After normpath: c:/workspace/myproject/.git/config → allow zone but .git internals
        path = f"{WS_ROOT}/{PROJECT_DIR}/src/../../{PROJECT_DIR}/.git/config"
        assert _decide(_payload_create_file(path)) == "deny"

    def test_traversal_inside_project_to_git(self):
        """Path traversal staying within project → .git still denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/src/../.git/config"
        assert _decide(_payload_create_file(path)) == "deny"

    def test_read_file_traversal_to_git_head(self):
        """read_file with path traversal to .git/HEAD MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/src/../.git/HEAD"
        assert _decide(_payload_read_file(path)) == "deny"


# ---------------------------------------------------------------------------
# Case variation (Windows) — MUST be denied
# ---------------------------------------------------------------------------

class TestCaseVariationGitBlocked:
    def test_uppercase_git_create_file(self):
        """create_file → ProjectFolder/.GIT/config MUST be denied (case-insensitive)."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.GIT/config"
        assert _decide(_payload_create_file(path)) == "deny"

    def test_mixed_case_git_read_file(self):
        """read_file → ProjectFolder/.Git/HEAD MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.Git/HEAD"
        assert _decide(_payload_read_file(path)) == "deny"

    def test_uppercase_git_hooks(self):
        """create_file → ProjectFolder/.GIT/hooks/pre-commit MUST be denied."""
        path = f"{WS_ROOT}/{PROJECT_DIR}/.GIT/hooks/pre-commit"
        assert _decide(_payload_create_file(path)) == "deny"
