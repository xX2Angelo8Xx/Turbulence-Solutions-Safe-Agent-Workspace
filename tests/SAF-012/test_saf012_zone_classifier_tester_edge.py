"""SAF-012 — Tester Edge-Case Tests for Zone Classifier

Additional edge-case tests added by the Tester Agent, beyond the Developer's 51 tests.

Covers scenarios not tested by the Developer:
 - Empty workspace root (no subdirectories at all)
 - Workspace root with only files, no directories
 - Project folder name containing spaces
 - Project folder name with hyphens, underscores, dots
 - Workspace root path itself contains spaces
 - Empty string path (no crash, returns deny)
 - Path exactly equals workspace root (returns deny)
 - Relative path that IS inside the project folder (returns allow)
 - WSL /mnt/c/... prefix path inside project folder
 - Git Bash /c/... prefix path inside project folder
 - URL-encoded characters attempting to bypass .github deny
 - JSON double-escaped backslash path to .github
 - Double slash path normalization
 - Unicode in project folder name
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Fixture: import zone_classifier from Default-Project scripts directory
# ---------------------------------------------------------------------------

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "Default-Project"
    / ".github"
    / "hooks"
    / "scripts"
)


@pytest.fixture(scope="module")
def zc():
    """Import zone_classifier from the Default-Project scripts directory."""
    if SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, SCRIPTS_DIR)
    import zone_classifier as _zc
    return _zc


WS_ROOT = "c:/workspace"


# ---------------------------------------------------------------------------
# Tests: empty / files-only workspace
# ---------------------------------------------------------------------------

class TestEmptyWorkspace:
    """Workspace root has no subdirectories at all or only regular files."""

    def test_empty_workspace_detect_raises_runtime_error(self, zc):
        """detect_project_folder() raises RuntimeError when workspace has no entries."""
        with patch("os.listdir", return_value=[]):
            with patch("os.path.isdir", return_value=False):
                with pytest.raises(RuntimeError, match="No project folder detected"):
                    zc.detect_project_folder(Path("/workspace"))

    def test_empty_workspace_classify_returns_deny(self, zc):
        """classify() returns deny (fail-closed) when workspace has no subdirectories."""
        with patch("os.listdir", return_value=[]):
            with patch("os.path.isdir", return_value=False):
                result = zc.classify("c:/workspace/project/file.py", WS_ROOT)
        assert result == "deny"

    def test_files_only_workspace_detect_raises_runtime_error(self, zc):
        """detect_project_folder() raises RuntimeError when workspace has only files (no dirs)."""
        with patch("os.listdir", return_value=["README.md", "pyproject.toml", "launcher.spec"]):
            with patch("os.path.isdir", return_value=False):
                with pytest.raises(RuntimeError, match="No project folder detected"):
                    zc.detect_project_folder(Path("/workspace"))

    def test_files_only_workspace_classify_returns_deny(self, zc):
        """classify() returns deny when workspace has only files and no project folder."""
        with patch("os.listdir", return_value=["README.md", "pyproject.toml"]):
            with patch("os.path.isdir", return_value=False):
                result = zc.classify("c:/workspace/README.md", WS_ROOT)
        assert result == "deny"

    def test_mix_files_and_system_dirs_only_returns_deny(self, zc):
        """classify() returns deny when workspace has files + system dirs but no project dir."""
        # isdir returns True only for system dirs
        def _isdir(p):
            import os
            return os.path.basename(p) in {".github", ".vscode", "NoAgentZone"}

        with patch("os.listdir", return_value=["README.md", ".github", "pyproject.toml", ".vscode", "NoAgentZone"]):
            with patch("os.path.isdir", side_effect=_isdir):
                result = zc.classify("c:/workspace/project/app.py", WS_ROOT)
        assert result == "deny"


# ---------------------------------------------------------------------------
# Tests: project folder names with special characters
# ---------------------------------------------------------------------------

class TestSpecialProjectFolderNames:
    """Project folder names containing spaces, hyphens, underscores, dots, Unicode."""

    def _classify(self, zc, raw_path: str, project_dir: str, ws_root: str = WS_ROOT) -> str:
        with patch("os.listdir", return_value=[project_dir, ".github", ".vscode"]):
            with patch("os.path.isdir", return_value=True):
                return zc.classify(raw_path, ws_root)

    def _detect(self, zc, dirs: list, project_dir: str) -> str:
        def _isdir(p):
            import os
            return os.path.basename(p) in dirs
        with patch("os.listdir", return_value=dirs):
            with patch("os.path.isdir", side_effect=_isdir):
                return zc.detect_project_folder(Path("/workspace"))

    # --- spaces ---

    def test_project_folder_spaces_detected(self, zc):
        """detect_project_folder() returns 'my project' for folder named 'My Project'."""
        result = self._detect(zc, ["My Project", ".github", ".vscode"], "My Project")
        assert result == "my project"

    def test_project_folder_with_spaces_allow(self, zc):
        """Path inside a folder named 'My Project' (with a space) returns allow."""
        result = self._classify(zc, "c:/workspace/my project/src/app.py", "My Project")
        assert result == "allow"

    def test_project_folder_with_spaces_deny_outside_project(self, zc):
        """Path outside the project folder (workspace with spaces) returns deny."""
        result = self._classify(zc, "c:/workspace/.github/hooks/test.py", "My Project")
        assert result == "deny"

    def test_project_folder_with_spaces_sibling_denied(self, zc):
        """Sibling folder 'my projectevil' next to 'my project' is denied."""
        result = self._classify(zc, "c:/workspace/my projectevil/file.txt", "My Project")
        assert result == "deny"

    # --- hyphens ---

    def test_project_folder_with_hyphens_detected(self, zc):
        """detect_project_folder() returns 'my-project' for folder 'my-project'."""
        result = self._detect(zc, ["my-project", ".github"], "my-project")
        assert result == "my-project"

    def test_project_folder_with_hyphens_allow(self, zc):
        """Path inside a hyphenated project folder (e.g. 'my-project') returns allow."""
        result = self._classify(zc, "c:/workspace/my-project/src/main.py", "my-project")
        assert result == "allow"

    def test_project_folder_partial_hyphen_denied(self, zc):
        """'my-project-evil' is NOT the project folder and is denied."""
        result = self._classify(zc, "c:/workspace/my-project-evil/file.txt", "my-project")
        assert result == "deny"

    # --- underscores ---

    def test_project_folder_with_underscores_allow(self, zc):
        """Path inside 'my_project' (underscore) returns allow."""
        result = self._classify(zc, "c:/workspace/my_project/app.py", "my_project")
        assert result == "allow"

    # --- dots ---

    def test_project_folder_with_dots_allow(self, zc):
        """Path inside 'my.project.v2' (dots) returns allow."""
        result = self._classify(zc, "c:/workspace/my.project.v2/file.py", "my.project.v2")
        assert result == "allow"

    # --- unicode ---

    def test_project_folder_unicode_detected(self, zc):
        """detect_project_folder() returns unicode name correctly (e.g. 'café')."""
        result = self._detect(zc, ["café", ".github"], "café")
        assert result == "café"

    def test_project_folder_unicode_allow(self, zc):
        """Path inside a Unicode-named project folder returns allow."""
        result = self._classify(zc, "c:/workspace/café/app.py", "café")
        assert result == "allow"

    def test_project_folder_unicode_deny_outside(self, zc):
        """Non-project path in a Unicode-named workspace is denied."""
        result = self._classify(zc, "c:/workspace/docs/readme.txt", "café")
        assert result == "deny"


# ---------------------------------------------------------------------------
# Tests: workspace root path contains spaces
# ---------------------------------------------------------------------------

class TestWorkspaceRootWithSpaces:
    """Workspace root path itself contains spaces."""

    def _classify(self, zc, raw_path: str, ws_root: str, project_dir: str = "project") -> str:
        with patch("os.listdir", return_value=[project_dir, ".github", ".vscode"]):
            with patch("os.path.isdir", return_value=True):
                return zc.classify(raw_path, ws_root)

    def test_workspace_root_with_spaces_project_allow(self, zc):
        """Path inside project folder when workspace root has spaces → allow."""
        ws = "c:/my workspace folder"
        result = self._classify(zc, "c:/my workspace folder/project/src/app.py", ws)
        assert result == "allow"

    def test_workspace_root_with_spaces_github_deny(self, zc):
        """.github path in workspace with spaces → deny."""
        ws = "c:/my workspace folder"
        result = self._classify(zc, "c:/my workspace folder/.github/hooks/test.py", ws)
        assert result == "deny"

    def test_workspace_root_with_spaces_root_file_deny(self, zc):
        """Root-level file in workspace with spaces → deny."""
        ws = "c:/my workspace folder"
        result = self._classify(zc, "c:/my workspace folder/README.md", ws)
        assert result == "deny"

    def test_workspace_root_with_spaces_noagentzone_deny(self, zc):
        """NoAgentZone in workspace with spaces → deny."""
        ws = "c:/my workspace folder"
        result = self._classify(zc, "c:/my workspace folder/noagentzone/secret.txt", ws)
        assert result == "deny"


# ---------------------------------------------------------------------------
# Tests: path edge cases (empty, equals root, relative)
# ---------------------------------------------------------------------------

class TestPathEdgeCases:
    """Empty path, path equals workspace root, relative paths."""

    def _classify(self, zc, raw_path: str) -> str:
        with patch("os.listdir", return_value=["project", ".github", ".vscode"]):
            with patch("os.path.isdir", return_value=True):
                return zc.classify(raw_path, WS_ROOT)

    def test_empty_string_path_returns_deny_no_crash(self, zc):
        """Empty string path must return deny without raising an exception."""
        result = self._classify(zc, "")
        assert result == "deny"

    def test_empty_string_path_never_returns_ask(self, zc):
        """Empty string path must not return 'ask'."""
        result = self._classify(zc, "")
        assert result != "ask"

    def test_path_equals_workspace_root_returns_deny(self, zc):
        """Path exactly equal to workspace root must return deny (not inside any folder)."""
        result = self._classify(zc, "c:/workspace")
        assert result == "deny"

    def test_path_equals_workspace_root_with_trailing_slash_returns_deny(self, zc):
        """Workspace root path with trailing slash → deny."""
        result = self._classify(zc, "c:/workspace/")
        assert result == "deny"

    def test_relative_path_inside_project_returns_allow(self, zc):
        """Relative path 'project/src/app.py' resolves against workspace root → allow."""
        result = self._classify(zc, "project/src/app.py")
        assert result == "allow"

    def test_relative_path_to_github_returns_deny(self, zc):
        """Relative path '.github/secret' resolves to deny zone → deny."""
        result = self._classify(zc, ".github/secret")
        assert result == "deny"

    def test_double_slash_project_path_allow(self, zc):
        """Double forward slashes inside a project path are normalized away → allow."""
        result = self._classify(zc, "c:/workspace//project//src/file.py")
        assert result == "allow"

    def test_double_slash_github_path_deny(self, zc):
        """Double slashes in .github path are normalized; result is still deny."""
        result = self._classify(zc, "c:/workspace//.github//hooks/test.py")
        assert result == "deny"

    def test_whitespace_only_path_returns_deny(self, zc):
        """Path of just spaces/whitespace (after control-char stripping) → deny."""
        # Spaces are not C0 control chars so they survive stripping;
        # the path resolves to an innocuous name that is outside the project folder.
        result = self._classify(zc, "   ")
        assert result == "deny"


# ---------------------------------------------------------------------------
# Tests: WSL and Git Bash path prefixes
# ---------------------------------------------------------------------------

class TestUnixPrefixPaths:
    """WSL /mnt/c/... and Git Bash /c/... path prefixes."""

    def _classify(self, zc, raw_path: str) -> str:
        with patch("os.listdir", return_value=["project", ".github", ".vscode"]):
            with patch("os.path.isdir", return_value=True):
                return zc.classify(raw_path, WS_ROOT)

    def test_wsl_path_inside_project_allows(self, zc):
        """/mnt/c/workspace/project/file.py (WSL) maps to allow zone."""
        result = self._classify(zc, "/mnt/c/workspace/project/file.py")
        assert result == "allow"

    def test_wsl_path_github_denies(self, zc):
        """/mnt/c/workspace/.github/secret (WSL) maps to deny zone."""
        result = self._classify(zc, "/mnt/c/workspace/.github/secret")
        assert result == "deny"

    def test_wsl_path_noagentzone_denies(self, zc):
        """/mnt/c/workspace/NoAgentZone/secret (WSL) maps to deny zone."""
        result = self._classify(zc, "/mnt/c/workspace/NoAgentZone/secret")
        assert result == "deny"

    def test_gitbash_path_inside_project_allows(self, zc):
        """/c/workspace/project/file.py (Git Bash) maps to allow zone."""
        result = self._classify(zc, "/c/workspace/project/file.py")
        assert result == "allow"

    def test_gitbash_path_github_denies(self, zc):
        """/c/workspace/.github/hooks/test.py (Git Bash) maps to deny zone."""
        result = self._classify(zc, "/c/workspace/.github/hooks/test.py")
        assert result == "deny"

    def test_wsl_root_file_denies(self, zc):
        """/mnt/c/workspace/README.md (WSL, root-level file) → deny."""
        result = self._classify(zc, "/mnt/c/workspace/README.md")
        assert result == "deny"


# ---------------------------------------------------------------------------
# Tests: URL-encoded path bypass attempts
# ---------------------------------------------------------------------------

class TestUrlEncodingBypassAttempts:
    """Attempt to defeat deny zones using URL-encoded characters.

    normalize_path() does NOT decode URL percent-encoding. Any percent-encoded
    path that is NOT the literal project folder name therefore falls through to
    deny (neither matching a deny-zone pattern nor matching the project allow pattern).
    The important property is: no URL-encoded path should return 'allow' when it
    is not genuinely the project folder.
    """

    def _classify(self, zc, raw_path: str) -> str:
        with patch("os.listdir", return_value=["project", ".github", ".vscode"]):
            with patch("os.path.isdir", return_value=True):
                return zc.classify(raw_path, WS_ROOT)

    def test_url_encoded_dot_github_is_denied(self, zc):
        """'%2egithub' (URL-encoded dot) path is denied — not in project folder."""
        result = self._classify(zc, "c:/workspace/%2egithub/hooks/script.py")
        assert result == "deny"

    def test_url_encoded_github_letter_is_denied(self, zc):
        """'.githu%62' (URL-encoded 'b') path is denied — not in project folder."""
        result = self._classify(zc, "c:/workspace/.githu%62/hooks/secret.py")
        assert result == "deny"

    def test_url_encoded_uppercase_dot_github_is_denied(self, zc):
        """'%2Egithub' (uppercase URL-encoded dot) is denied — not in project folder."""
        result = self._classify(zc, "c:/workspace/%2Egithub/secret")
        assert result == "deny"

    def test_url_encoded_noagentzone_is_denied(self, zc):
        """'%4eoagentzone' (URL-encoded 'N') path is denied."""
        result = self._classify(zc, "c:/workspace/%4eoagentzone/secret.txt")
        assert result == "deny"

    def test_url_encoded_path_never_returns_allow_for_deny_zone(self, zc):
        """No URL-encoded variant of a deny-zone folder name should return allow."""
        bypass_attempts = [
            "c:/workspace/%2egithub/x",
            "c:/workspace/%2Egithub/x",
            "c:/workspace/.githu%62/x",
            "c:/workspace/%2evscode/x",
            "c:/workspace/noagentzon%65/x",
        ]
        for path in bypass_attempts:
            result = self._classify(zc, path)
            assert result != "allow", f"URL-encoded bypass succeeded for {path!r}"


# ---------------------------------------------------------------------------
# Tests: JSON double-escaped backslash paths
# ---------------------------------------------------------------------------

class TestJsonDoubleEscapedPaths:
    """Paths with JSON-style double-escaped backslashes (\\\\) as sent in hook payloads."""

    def _classify(self, zc, raw_path: str) -> str:
        with patch("os.listdir", return_value=["project", ".github", ".vscode"]):
            with patch("os.path.isdir", return_value=True):
                return zc.classify(raw_path, WS_ROOT)

    def test_json_double_backslash_github_is_denied(self, zc):
        """JSON double-escaped path to .github (c:\\\\workspace\\\\.github) → deny.

        JSON payload: "c:\\\\workspace\\\\.github\\\\hooks\\\\test.py"
        After JSON decode: "c:\\\\workspace\\\\.github\\\\hooks\\\\test.py" (Python raw)
        normalize_path replaces '\\\\' → '/': c:/workspace/.github/hooks/test.py → deny.
        """
        # Python string: c:\\workspace\\.github\\hooks\\test.py
        # (each \\\\ in Python source = \\ in the string = one JSON layer of escaping)
        raw = "c:\\\\workspace\\\\.github\\\\hooks\\\\test.py"
        result = self._classify(zc, raw)
        assert result == "deny"

    def test_json_double_backslash_project_is_allowed(self, zc):
        """JSON double-escaped path inside project (c:\\\\workspace\\\\project\\\\...) → allow."""
        raw = "c:\\\\workspace\\\\project\\\\src\\\\main.py"
        result = self._classify(zc, raw)
        assert result == "allow"

    def test_json_double_backslash_noagentzone_is_denied(self, zc):
        """JSON double-escaped path to NoAgentZone → deny."""
        raw = "c:\\\\workspace\\\\noagentzone\\\\secret.txt"
        result = self._classify(zc, raw)
        assert result == "deny"
