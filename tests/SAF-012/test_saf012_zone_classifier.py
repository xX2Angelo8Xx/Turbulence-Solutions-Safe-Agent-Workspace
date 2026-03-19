"""SAF-012 — Tests for 2-Tier Deny-by-Default Zone Classifier

Tests for zone_classifier.py after the SAF-012 rewrite:
  - detect_project_folder() auto-detection
  - classify() returns only "allow" or "deny" (never "ask")
  - Explicit deny for .github/, .vscode/, NoAgentZone/
  - Deny for root-level files and non-project subdirectories
  - Security: path traversal, sibling-prefix, case variation
  - Edge cases: no project folder, multiple non-system folders
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Fixture: import zone_classifier from templates/coding scripts directory
# ---------------------------------------------------------------------------

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "coding"
    / ".github"
    / "hooks"
    / "scripts"
)


@pytest.fixture(scope="module")
def zc():
    """Import zone_classifier from the templates/coding scripts directory."""
    if SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, SCRIPTS_DIR)
    import zone_classifier as _zc
    return _zc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WS_ROOT = "c:/workspace"


def make_listdir(dirs: list[str]):
    """Return a side_effect for os.listdir that yields the given dir names."""
    def _listdir(path):
        return list(dirs)
    return _listdir


def make_isdir(dirs: list[str]):
    """Return a side_effect for os.path.isdir that is True only for listed dirs."""
    def _isdir(path):
        return os.path.basename(path) in dirs
    return _isdir


# ---------------------------------------------------------------------------
# Tests: detect_project_folder
# ---------------------------------------------------------------------------

class TestDetectProjectFolder:
    def test_detect_project_folder_named_project(self, zc):
        """Auto-detects the project folder when it is named 'Project'."""
        with patch("os.listdir", return_value=["Project", ".github", ".vscode"]):
            with patch("os.path.isdir", side_effect=lambda p: os.path.basename(p) in ["Project", ".github", ".vscode"]):
                result = zc.detect_project_folder(Path("/workspace"))
        assert result == "project"

    def test_detect_project_folder_named_matlabdemo(self, zc):
        """Auto-detects a project folder named 'MatlabDemo'."""
        with patch("os.listdir", return_value=["MatlabDemo", ".github", ".vscode", "NoAgentZone"]):
            with patch("os.path.isdir", side_effect=lambda p: os.path.basename(p) in ["MatlabDemo", ".github", ".vscode", "NoAgentZone"]):
                result = zc.detect_project_folder(Path("/workspace"))
        assert result == "matlabdemo"

    def test_detect_project_folder_named_myapp(self, zc):
        """Auto-detects a project folder named 'MyApp'."""
        with patch("os.listdir", return_value=[".github", "MyApp", ".vscode"]):
            with patch("os.path.isdir", side_effect=lambda p: os.path.basename(p) in [".github", "MyApp", ".vscode"]):
                result = zc.detect_project_folder(Path("/workspace"))
        assert result == "myapp"

    def test_detect_project_folder_first_alphabetically(self, zc):
        """When multiple non-system folders exist, the first alphabetically is chosen."""
        with patch("os.listdir", return_value=["Zebra", "Alpha", ".github"]):
            with patch("os.path.isdir", side_effect=lambda p: os.path.basename(p) in ["Zebra", "Alpha", ".github"]):
                result = zc.detect_project_folder(Path("/workspace"))
        assert result == "alpha"

    def test_detect_project_folder_no_project_raises(self, zc):
        """RuntimeError is raised when all subdirectories are system folders."""
        with patch("os.listdir", return_value=[".github", ".vscode", "NoAgentZone"]):
            with patch("os.path.isdir", side_effect=lambda p: os.path.basename(p) in [".github", ".vscode", "NoAgentZone"]):
                with pytest.raises(RuntimeError, match="No project folder detected"):
                    zc.detect_project_folder(Path("/workspace"))

    def test_detect_ignores_system_folders_case_insensitive(self, zc):
        """System folder names are excluded case-insensitively (e.g. NOAGENTZONE)."""
        with patch("os.listdir", return_value=["NOAGENTZONE", ".GITHUB", "MyProject"]):
            with patch("os.path.isdir", side_effect=lambda p: os.path.basename(p) in ["NOAGENTZONE", ".GITHUB", "MyProject"]):
                result = zc.detect_project_folder(Path("/workspace"))
        assert result == "myproject"

    def test_detect_only_considers_directories(self, zc):
        """Files at workspace root are ignored — only directories are candidates."""
        with patch("os.listdir", return_value=["README.md", "MyApp", ".github"]):
            with patch("os.path.isdir", side_effect=lambda p: os.path.basename(p) in ["MyApp", ".github"]):
                result = zc.detect_project_folder(Path("/workspace"))
        assert result == "myapp"


# ---------------------------------------------------------------------------
# Tests: classify — allow paths
# ---------------------------------------------------------------------------

class TestClassifyAllow:
    def _classify_with_project(self, zc, raw_path: str, project_dir: str = "project") -> str:
        """Call classify() with a mocked filesystem that has the given project dir."""
        with patch("os.listdir", return_value=[project_dir, ".github", ".vscode", "NoAgentZone"]):
            with patch("os.path.isdir", return_value=True):
                return zc.classify(raw_path, WS_ROOT)

    def test_classify_allow_project_root(self, zc):
        """Path at the project folder root returns allow."""
        result = self._classify_with_project(zc, "c:/workspace/project")
        assert result == "allow"

    def test_classify_allow_project_nested(self, zc):
        """Nested path inside the project folder returns allow."""
        result = self._classify_with_project(zc, "c:/workspace/project/src/main.py")
        assert result == "allow"

    def test_classify_allow_deep_nested(self, zc):
        """Deeply nested path inside the project folder returns allow."""
        result = self._classify_with_project(zc, "c:/workspace/project/a/b/c/d/file.txt")
        assert result == "allow"

    def test_classify_allow_matlabdemo_folder(self, zc):
        """Path inside a project folder named 'MatlabDemo' returns allow."""
        result = self._classify_with_project(zc, "c:/workspace/matlabdemo/src/main.py", project_dir="MatlabDemo")
        assert result == "allow"

    def test_classify_allow_myapp_folder(self, zc):
        """Path inside a project folder named 'MyApp' returns allow."""
        result = self._classify_with_project(zc, "c:/workspace/myapp/app.py", project_dir="MyApp")
        assert result == "allow"


# ---------------------------------------------------------------------------
# Tests: classify — deny paths
# ---------------------------------------------------------------------------

class TestClassifyDeny:
    def _classify_with_project(self, zc, raw_path: str, project_dir: str = "project") -> str:
        with patch("os.listdir", return_value=[project_dir, ".github", ".vscode", "NoAgentZone"]):
            with patch("os.path.isdir", return_value=True):
                return zc.classify(raw_path, WS_ROOT)

    def test_classify_deny_github(self, zc):
        """.github/ path returns deny (explicit defense-in-depth)."""
        result = self._classify_with_project(zc, "c:/workspace/.github/hooks/scripts/security_gate.py")
        assert result == "deny"

    def test_classify_deny_vscode(self, zc):
        """.vscode/ path returns deny (explicit defense-in-depth)."""
        result = self._classify_with_project(zc, "c:/workspace/.vscode/settings.json")
        assert result == "deny"

    def test_classify_deny_noagentzone(self, zc):
        """NoAgentZone/ path returns deny (explicit defense-in-depth)."""
        result = self._classify_with_project(zc, "c:/workspace/NoAgentZone/secret.txt")
        assert result == "deny"

    def test_classify_deny_root_file(self, zc):
        """Root-level workspace file (e.g. README.md) returns deny."""
        result = self._classify_with_project(zc, "c:/workspace/README.md")
        assert result == "deny"

    def test_classify_deny_root_file_pyproject(self, zc):
        """pyproject.toml at workspace root returns deny."""
        result = self._classify_with_project(zc, "c:/workspace/pyproject.toml")
        assert result == "deny"

    def test_classify_deny_non_project_subdir(self, zc):
        """A subdirectory that is not the project folder returns deny."""
        result = self._classify_with_project(zc, "c:/workspace/src/launcher/main.py")
        assert result == "deny"

    def test_classify_deny_docs_subdir(self, zc):
        """docs/ subdirectory returns deny."""
        result = self._classify_with_project(zc, "c:/workspace/docs/architecture.md")
        assert result == "deny"

    def test_classify_deny_tests_subdir(self, zc):
        """tests/ subdirectory returns deny."""
        result = self._classify_with_project(zc, "c:/workspace/tests/conftest.py")
        assert result == "deny"


# ---------------------------------------------------------------------------
# Tests: classify — never returns "ask"
# ---------------------------------------------------------------------------

class TestClassifyNeverReturnsAsk:
    def _classify_with_project(self, zc, raw_path: str, project_dir: str = "project") -> str:
        with patch("os.listdir", return_value=[project_dir, ".github", ".vscode", "NoAgentZone"]):
            with patch("os.path.isdir", return_value=True):
                return zc.classify(raw_path, WS_ROOT)

    @pytest.mark.parametrize("raw_path", [
        "c:/workspace/README.md",
        "c:/workspace/src/launcher/main.py",
        "c:/workspace/docs/architecture.md",
        "c:/workspace/tests/conftest.py",
        "c:/workspace/.github/secret",
        "c:/workspace/.vscode/settings.json",
        "c:/workspace/NoAgentZone/private.txt",
        "c:/workspace/project/src/app.py",
        "c:/workspace",
        "c:/other/path/README.md",
        "c:/workspace/anyrandomfolder/file.txt",
    ])
    def test_classify_never_returns_ask(self, zc, raw_path):
        """classify() must never return 'ask' for any input."""
        result = self._classify_with_project(zc, raw_path)
        assert result in ("allow", "deny"), f"Got {result!r} for {raw_path!r}"
        assert result != "ask"

    def test_classify_no_project_folder_is_deny_not_ask(self, zc):
        """When no project folder is detected, classify() returns deny (not ask)."""
        with patch("os.listdir", return_value=[".github", ".vscode", "NoAgentZone"]):
            with patch("os.path.isdir", return_value=True):
                result = zc.classify("c:/workspace/README.md", WS_ROOT)
        assert result == "deny"
        assert result != "ask"


# ---------------------------------------------------------------------------
# Tests: edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def _classify_with_project(self, zc, raw_path: str, project_dir: str = "project") -> str:
        with patch("os.listdir", return_value=[project_dir, ".github", ".vscode", "NoAgentZone"]):
            with patch("os.path.isdir", return_value=True):
                return zc.classify(raw_path, WS_ROOT)

    def test_classify_deny_when_no_project_folder(self, zc):
        """Fail-closed: deny when no project folder is found."""
        with patch("os.listdir", return_value=[".github", ".vscode", "NoAgentZone"]):
            with patch("os.path.isdir", return_value=True):
                result = zc.classify("c:/workspace/project/file.py", WS_ROOT)
        assert result == "deny"

    def test_classify_deny_when_detection_raises_oserror(self, zc):
        """Fail-closed: deny when filesystem detection raises OSError."""
        with patch("os.listdir", side_effect=OSError("permission denied")):
            result = zc.classify("c:/workspace/project/file.py", WS_ROOT)
        assert result == "deny"

    def test_detect_multiple_non_system_first_alphabetically(self, zc):
        """With multiple non-system dirs, the first alphabetically is the allow zone."""
        with patch("os.listdir", return_value=["Zapp", "Alpha", ".github"]):
            with patch("os.path.isdir", return_value=True):
                # "alpha" is first alphabetically — only alpha/ should be allow
                result_alpha = zc.classify("c:/workspace/alpha/file.py", WS_ROOT)
                result_zapp = zc.classify("c:/workspace/zapp/file.py", WS_ROOT)
        assert result_alpha == "allow"
        assert result_zapp == "deny"

    def test_classify_case_insensitive_deny_github(self, zc):
        """GitHub directory with mixed case returns deny."""
        result = self._classify_with_project(zc, "c:/workspace/.GITHUB/hooks/scripts/test.py")
        assert result == "deny"

    def test_classify_case_insensitive_deny_vscode(self, zc):
        """.VSCODE with mixed case returns deny."""
        result = self._classify_with_project(zc, "c:/workspace/.VSCODE/settings.json")
        assert result == "deny"

    def test_classify_case_insensitive_deny_noagentzone(self, zc):
        """NOAGENTZONE with mixed case returns deny."""
        result = self._classify_with_project(zc, "c:/workspace/NOAGENTZONE/secret.txt")
        assert result == "deny"


# ---------------------------------------------------------------------------
# Tests: security — bypass attempts
# ---------------------------------------------------------------------------

class TestBypassAttempts:
    def _classify_with_project(self, zc, raw_path: str, project_dir: str = "project") -> str:
        with patch("os.listdir", return_value=[project_dir, ".github", ".vscode", "NoAgentZone"]):
            with patch("os.path.isdir", return_value=True):
                return zc.classify(raw_path, WS_ROOT)

    def test_bypass_path_traversal_dotdot(self, zc):
        """project/../.github/secret resolves to .github/ and is denied."""
        result = self._classify_with_project(zc, "c:/workspace/project/../.github/secret")
        assert result == "deny"

    def test_bypass_deep_traversal(self, zc):
        """project/../../../../.github/x resolves outside workspace and is denied."""
        result = self._classify_with_project(zc, "c:/workspace/project/../../../../.github/x")
        assert result == "deny"

    def test_bypass_sibling_prefix(self, zc):
        """project-evil/ does not match the project/ allow zone — is denied."""
        result = self._classify_with_project(zc, "c:/workspace/project-evil/file.txt")
        assert result == "deny"

    def test_bypass_sibling_prefix_github(self, zc):
        """project-evil/.github/ path is denied."""
        result = self._classify_with_project(zc, "c:/workspace/project-evil/.github/secret")
        assert result == "deny"

    def test_bypass_relative_dotdot_into_github(self, zc):
        """Relative path using .. to reach .github/ is denied."""
        result = self._classify_with_project(zc, "../.github/hooks/scripts/security_gate.py")
        assert result == "deny"

    def test_bypass_unc_path_with_project_name(self, zc):
        """UNC path \\server\\share\\project is not allowed (not in workspace root)."""
        result = self._classify_with_project(zc, "//server/share/project/file.py")
        assert result == "deny"

    def test_bypass_null_byte_injection(self, zc):
        """Null byte before .github is stripped; the path is still denied."""
        result = self._classify_with_project(zc, "c:/workspace/\x00.github/secret")
        assert result == "deny"

    def test_bypass_control_char_injection(self, zc):
        """Control character before .github is stripped; the path is still denied."""
        result = self._classify_with_project(zc, "c:/workspace/\x01.github/secret")
        assert result == "deny"

    def test_bypass_backslash_path(self, zc):
        """Windows backslash path to .github is denied."""
        result = self._classify_with_project(zc, "c:\\workspace\\.github\\hooks\\test.py")
        assert result == "deny"

    def test_bypass_backslash_allow_path(self, zc):
        """Windows backslash path inside project folder is allowed."""
        result = self._classify_with_project(zc, "c:\\workspace\\project\\src\\main.py")
        assert result == "allow"


# ---------------------------------------------------------------------------
# Tests: ZoneDecision type is Literal["allow", "deny"]
# ---------------------------------------------------------------------------

class TestZoneDecisionType:
    def test_zonedecision_does_not_include_ask(self, zc):
        """ZoneDecision type hint must not include 'ask'."""
        # Access the __args__ of the Literal type
        args = zc.ZoneDecision.__args__
        assert "ask" not in args, f"ZoneDecision must not include 'ask', got {args}"

    def test_zonedecision_includes_allow_and_deny(self, zc):
        """ZoneDecision type hint must include 'allow' and 'deny'."""
        args = zc.ZoneDecision.__args__
        assert "allow" in args
        assert "deny" in args

    def test_zonedecision_has_exactly_two_values(self, zc):
        """ZoneDecision must have exactly 2 values: allow and deny."""
        args = zc.ZoneDecision.__args__
        assert len(args) == 2, f"ZoneDecision should have 2 values, got {args}"
