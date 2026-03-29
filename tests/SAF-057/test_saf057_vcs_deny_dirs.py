"""SAF-057 — Tests for VCS directories in zone classifier deny set.

Covers:
- .git, .hg, .svn are in _DENY_DIRS
- detect_project_folder() skips .git even when it exists
- detect_project_folder() skips all dot-prefixed directories
- classify() returns "deny" for paths inside .git/
- After git init at workspace root, real project folder is still detected
- No regression on normal project folder detection
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the scripts directory is importable
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"),
)

import zone_classifier as zc


# ---------------------------------------------------------------------------
# _DENY_DIRS membership
# ---------------------------------------------------------------------------

class TestDenyDirsMembership:
    def test_git_in_deny_dirs(self):
        assert ".git" in zc._DENY_DIRS

    def test_hg_in_deny_dirs(self):
        assert ".hg" in zc._DENY_DIRS

    def test_svn_in_deny_dirs(self):
        assert ".svn" in zc._DENY_DIRS

    def test_github_still_in_deny_dirs(self):
        assert ".github" in zc._DENY_DIRS

    def test_vscode_still_in_deny_dirs(self):
        assert ".vscode" in zc._DENY_DIRS

    def test_noagentzone_still_in_deny_dirs(self):
        assert "noagentzone" in zc._DENY_DIRS


# ---------------------------------------------------------------------------
# _BLOCKED_PATTERN covers VCS directories
# ---------------------------------------------------------------------------

class TestBlockedPattern:
    def test_pattern_matches_git(self):
        assert zc._BLOCKED_PATTERN.search("/.git/config")

    def test_pattern_matches_git_at_end(self):
        assert zc._BLOCKED_PATTERN.search("/c:/workspace/.git")

    def test_pattern_matches_hg(self):
        assert zc._BLOCKED_PATTERN.search("/.hg/store")

    def test_pattern_matches_svn(self):
        assert zc._BLOCKED_PATTERN.search("/.svn/entries")

    def test_pattern_still_matches_github(self):
        assert zc._BLOCKED_PATTERN.search("/.github/hooks")

    def test_pattern_does_not_match_unrelated(self):
        assert not zc._BLOCKED_PATTERN.search("/myproject/src/main.py")


# ---------------------------------------------------------------------------
# detect_project_folder() — dot-prefixed directory skipping
# ---------------------------------------------------------------------------

class TestDetectProjectFolderDotSkipping:
    def test_skips_git_directory(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / "myproject").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "myproject"

    def test_skips_hg_directory(self, tmp_path):
        (tmp_path / ".hg").mkdir()
        (tmp_path / "myproject").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "myproject"

    def test_skips_svn_directory(self, tmp_path):
        (tmp_path / ".svn").mkdir()
        (tmp_path / "myproject").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "myproject"

    def test_skips_all_dot_prefixed_dirs(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".hidden").mkdir()
        (tmp_path / ".vscode").mkdir()
        (tmp_path / ".github").mkdir()
        (tmp_path / "project").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "project"

    def test_git_sorts_before_project_but_is_skipped(self, tmp_path):
        # .git sorts alphabetically before 'aproject' — must be skipped
        (tmp_path / ".git").mkdir()
        (tmp_path / "aproject").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "aproject"

    def test_only_dot_dirs_raises_runtime_error(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".hg").mkdir()
        (tmp_path / ".hidden").mkdir()
        with pytest.raises(RuntimeError):
            zc.detect_project_folder(tmp_path)

    def test_normal_project_detection_unchanged(self, tmp_path):
        (tmp_path / ".github").mkdir()
        (tmp_path / ".vscode").mkdir()
        (tmp_path / "myapp").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "myapp"


# ---------------------------------------------------------------------------
# classify() — .git paths return "deny"
# ---------------------------------------------------------------------------

class TestClassifyGitPaths:
    def _ws_root(self, tmp_path: Path, project_name: str = "project") -> str:
        (tmp_path / project_name).mkdir(exist_ok=True)
        return zc.normalize_path(str(tmp_path))

    def test_classify_git_config_denied(self, tmp_path):
        ws = self._ws_root(tmp_path)
        path = str(tmp_path / ".git" / "config")
        assert zc.classify(path, ws) == "deny"

    def test_classify_git_head_denied(self, tmp_path):
        ws = self._ws_root(tmp_path)
        path = str(tmp_path / ".git" / "HEAD")
        assert zc.classify(path, ws) == "deny"

    def test_classify_git_dir_itself_denied(self, tmp_path):
        ws = self._ws_root(tmp_path)
        path = str(tmp_path / ".git")
        assert zc.classify(path, ws) == "deny"

    def test_classify_hg_path_denied(self, tmp_path):
        ws = self._ws_root(tmp_path)
        path = str(tmp_path / ".hg" / "store")
        assert zc.classify(path, ws) == "deny"

    def test_classify_svn_path_denied(self, tmp_path):
        ws = self._ws_root(tmp_path)
        path = str(tmp_path / ".svn" / "entries")
        assert zc.classify(path, ws) == "deny"

    def test_classify_project_file_still_allowed(self, tmp_path):
        (tmp_path / "project").mkdir()
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / "project" / "main.py")
        assert zc.classify(path, ws) == "allow"


# ---------------------------------------------------------------------------
# After git init at workspace root — real project folder still detected
# ---------------------------------------------------------------------------

class TestGitInitScenario:
    def test_git_init_does_not_break_detection(self, tmp_path):
        # Simulate git init: creates .git at workspace root
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("[core]\n\trepositoryformatversion = 0\n")
        (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        # The actual project folder also exists
        (tmp_path / "MyProject").mkdir()
        result = zc.detect_project_folder(tmp_path)
        assert result == "myproject"

    def test_git_init_does_not_break_classify(self, tmp_path):
        # .git exists at workspace root — project file must still be "allow"
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("[core]\n\trepositoryformatversion = 0\n")
        (tmp_path / "project").mkdir()
        ws = zc.normalize_path(str(tmp_path))
        path = str(tmp_path / "project" / "README.md")
        assert zc.classify(path, ws) == "allow"

    def test_git_subdir_denied_after_git_init(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / "project").mkdir()
        ws = zc.normalize_path(str(tmp_path))
        git_path = str(tmp_path / ".git" / "COMMIT_EDITMSG")
        assert zc.classify(git_path, ws) == "deny"
