"""SAF-057 — Tester edge-case tests for VCS directory deny set.

Additional edge cases beyond the developer's test suite:
- .GIT (uppercase) on case-insensitive file systems
- .git/objects/ and .git/HEAD deeply nested paths
- User-created dot-prefixed folder (.myproject) is skipped
- Workspace with ONLY dot-prefixed directories → RuntimeError
- .gitignore / .gitmodules files at workspace root don't affect detect_project_folder
- .gitignore files are not granted allow by classify() (files not in project dir are denied)
- is_workspace_root_readable() returns False for .git
- is_workspace_root_readable() returns True for .gitignore (file, not in _DENY_DIRS)
- Multiple VCS systems co-existing with a project folder
- noagentzone (mixed case) stays in deny dirs
- Regression: normal workspace layout works correctly
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"),
)

import zone_classifier as zc


# ---------------------------------------------------------------------------
# Case-insensitivity edge cases
# ---------------------------------------------------------------------------

class TestCaseInsensitivity:
    def test_uppercase_GIT_skipped_by_detect_project_folder(self, tmp_path):
        """.GIT (uppercase) must be skipped: startswith('.') is unambiguous."""
        # On Windows, os.mkdir('.GIT') and os.mkdir('.git') may refer to same dir.
        # Either way, the dot-prefix guard catches it.
        (tmp_path / ".GIT").mkdir()
        (tmp_path / "project").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "project"

    def test_uppercase_GIT_path_denied_by_classify(self, tmp_path):
        """Path containing .GIT (uppercase) is normalized to lowercase and denied."""
        (tmp_path / "project").mkdir()
        ws = zc.normalize_path(str(tmp_path))
        # Uppercase .GIT path — normalize_path lowercases it
        path = str(tmp_path).replace("\\", "/") + "/.GIT/config"
        assert zc.classify(path, ws) == "deny"

    def test_uppercase_HG_skipped_by_detect_project_folder(self, tmp_path):
        """.HG (uppercase) must be skipped by detect_project_folder."""
        (tmp_path / ".HG").mkdir()
        (tmp_path / "project").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "project"


# ---------------------------------------------------------------------------
# Deeply nested .git paths
# ---------------------------------------------------------------------------

class TestGitNestedPaths:
    def test_git_objects_dir_denied(self, tmp_path):
        """Paths like .git/objects/pack/... must be denied."""
        (tmp_path / "project").mkdir()
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / ".git" / "objects" / "pack" / "pack-abc.idx")
        assert zc.classify(path, ws) == "deny"

    def test_git_refs_heads_denied(self, tmp_path):
        """Path .git/refs/heads/main must be denied."""
        (tmp_path / "project").mkdir()
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / ".git" / "refs" / "heads" / "main")
        assert zc.classify(path, ws) == "deny"

    def test_git_HEAD_file_denied(self, tmp_path):
        """.git/HEAD file must be denied."""
        (tmp_path / "project").mkdir()
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / ".git" / "HEAD")
        assert zc.classify(path, ws) == "deny"

    def test_svn_wc_db_denied(self, tmp_path):
        """.svn/wc.db (SVN working copy database) must be denied."""
        (tmp_path / "project").mkdir()
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / ".svn" / "wc.db")
        assert zc.classify(path, ws) == "deny"


# ---------------------------------------------------------------------------
# User-created dot-prefixed project folder
# ---------------------------------------------------------------------------

class TestDotPrefixedUserFolder:
    def test_dot_myproject_is_skipped(self, tmp_path):
        """.myproject (user-created) must be skipped; real project below it is used."""
        (tmp_path / ".myproject").mkdir()
        (tmp_path / "realproject").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "realproject"

    def test_only_dot_myproject_raises(self, tmp_path):
        """If only .myproject exists (no normal folder), RuntimeError is raised."""
        (tmp_path / ".myproject").mkdir()
        with pytest.raises(RuntimeError, match="No project folder detected"):
            zc.detect_project_folder(tmp_path)

    def test_dot_env_skipped(self, tmp_path):
        """.env directory (common in repos) is skipped."""
        (tmp_path / ".env").mkdir()
        (tmp_path / "project").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "project"


# ---------------------------------------------------------------------------
# Workspace with ONLY dot-prefixed and deny directories
# ---------------------------------------------------------------------------

class TestAllDotOrDenyWorkspace:
    def test_only_vcs_and_dot_dirs_raises(self, tmp_path):
        """Workspace with only VCS dirs + other dot dirs raises RuntimeError."""
        (tmp_path / ".git").mkdir()
        (tmp_path / ".hg").mkdir()
        (tmp_path / ".svn").mkdir()
        (tmp_path / ".vscode").mkdir()
        (tmp_path / ".github").mkdir()
        with pytest.raises(RuntimeError):
            zc.detect_project_folder(tmp_path)

    def test_only_noagentzone_raises(self, tmp_path):
        """Workspace with only NoAgentZone (case-insensitive deny) raises RuntimeError."""
        (tmp_path / "NoAgentZone").mkdir()
        with pytest.raises(RuntimeError):
            zc.detect_project_folder(tmp_path)

    def test_classify_fails_closed_when_no_project_dir(self, tmp_path):
        """classify() returns 'deny' when no project folder can be detected."""
        (tmp_path / ".git").mkdir()
        # No real project dir
        ws = zc.normalize_path(str(tmp_path))
        result = zc.classify(str(tmp_path / "something" / "file.py"), ws)
        assert result == "deny"


# ---------------------------------------------------------------------------
# .gitignore and .gitmodules files at workspace root
# ---------------------------------------------------------------------------

class TestDotFilesAtRoot:
    def test_gitignore_file_not_a_dir_does_not_affect_detection(self, tmp_path):
        """.gitignore is a file — detect_project_folder must not be confused by it."""
        (tmp_path / ".gitignore").write_text("*.pyc\n")
        (tmp_path / "project").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "project"

    def test_gitmodules_file_not_a_dir_does_not_affect_detection(self, tmp_path):
        """.gitmodules is a file — must not affect detect_project_folder."""
        (tmp_path / ".gitmodules").write_text("[submodule \"lib\"]\n")
        (tmp_path / "project").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "project"

    def test_classify_gitignore_at_root_is_denied(self, tmp_path):
        """.gitignore at workspace root is not inside project folder — denied."""
        (tmp_path / "project").mkdir()
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / ".gitignore")
        # .gitignore is a direct child of workspace root but NOT inside project dir
        # classify() returns deny for everything outside the project folder
        assert zc.classify(path, ws) == "deny"

    def test_classify_gitmodules_at_root_is_denied(self, tmp_path):
        """.gitmodules at workspace root is not inside project folder — denied."""
        (tmp_path / "project").mkdir()
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / ".gitmodules")
        assert zc.classify(path, ws) == "deny"


# ---------------------------------------------------------------------------
# is_workspace_root_readable() with VCS paths
# ---------------------------------------------------------------------------

class TestWorkspaceRootReadableVCS:
    def test_git_dir_not_readable_from_root(self, tmp_path):
        """.git directory must NOT be readable via is_workspace_root_readable."""
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / ".git")
        assert zc.is_workspace_root_readable(path, ws) is False

    def test_hg_dir_not_readable_from_root(self, tmp_path):
        """.hg directory must NOT be readable via is_workspace_root_readable."""
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / ".hg")
        assert zc.is_workspace_root_readable(path, ws) is False

    def test_svn_dir_not_readable_from_root(self, tmp_path):
        """.svn directory must NOT be readable via is_workspace_root_readable."""
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / ".svn")
        assert zc.is_workspace_root_readable(path, ws) is False

    def test_gitignore_file_is_readable_from_root(self, tmp_path):
        """.gitignore is a root-level file, NOT in _DENY_DIRS → readable."""
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / ".gitignore")
        # .gitignore is not in _DENY_DIRS — root-level non-denied child
        assert zc.is_workspace_root_readable(path, ws) is True

    def test_git_internal_path_not_readable_from_root(self, tmp_path):
        """.git/config depth > 1 — not readable from root."""
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / ".git" / "config")
        assert zc.is_workspace_root_readable(path, ws) is False


# ---------------------------------------------------------------------------
# Multiple VCS systems co-existing
# ---------------------------------------------------------------------------

class TestMultipleVCSSystems:
    def test_git_and_hg_both_present(self, tmp_path):
        """Repo with both .git and .hg — project folder still detected."""
        (tmp_path / ".git").mkdir()
        (tmp_path / ".hg").mkdir()
        (tmp_path / "project").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "project"

    def test_all_three_vcs_dirs_present(self, tmp_path):
        """Repo with .git, .hg, .svn — project folder still detected."""
        (tmp_path / ".git").mkdir()
        (tmp_path / ".hg").mkdir()
        (tmp_path / ".svn").mkdir()
        (tmp_path / "myapp").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "myapp"

    def test_alphabetically_first_vcs_does_not_win(self, tmp_path):
        """.git sorts before 'alpha' — but .git must be skipped."""
        (tmp_path / ".git").mkdir()
        (tmp_path / "alpha").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "alpha"


# ---------------------------------------------------------------------------
# Regression: normal workspace still works
# ---------------------------------------------------------------------------

class TestNormalWorkspaceRegression:
    def test_project_folder_detected_no_vcs_dirs(self, tmp_path):
        """Normal workspace without any VCS dirs — project detected correctly."""
        (tmp_path / "MyProject").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "myproject"

    def test_project_folder_with_multiple_non_dot_dirs_picks_first_alpha(self, tmp_path):
        """Multiple non-dot dirs — alphabetically first (case-insensitive) is picked."""
        (tmp_path / "zoo").mkdir()
        (tmp_path / "alpha").mkdir()
        (tmp_path / "middle").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "alpha"

    def test_files_inside_project_remain_allowed(self, tmp_path):
        """Files inside the project folder stay classified as 'allow'."""
        (tmp_path / ".git").mkdir()
        (tmp_path / "project").mkdir()
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / "project" / "src" / "main.py")
        assert zc.classify(path, ws) == "allow"
