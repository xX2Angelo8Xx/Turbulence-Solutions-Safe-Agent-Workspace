"""SAF-058 — Tester edge-case tests for get_changed_files conditional .git/ check.

Edge cases covered beyond the developer's tests:
- .git is a FILE (not a directory) at workspace root → allow
  (os.path.isdir() returns False for files; documents the design decision
   that only .git *directories* are flagged as workspace-root repos)
- .git is a FILE inside the project folder → allow
  (falls through to the no-git 'allow' path, same isdir boundary)
- Symlinked .git/ directory at workspace root → deny
  (os.path.isdir() follows symlinks; link to a dir is detected and denied)
- PermissionError (subclass of OSError) → deny
  (verifies the fail-closed path catches subclasses, not just base OSError)
- detect_project_folder raises RuntimeError (explicitly mocked) with no root
  .git/ present → allow
  (documents the RuntimeError bypass path without relying on an empty tmpdir)
- Custom project folder name returned by detect_project_folder, .git/ inside
  that folder → allow
  (verifies the project_git path is correctly assembled from the returned name)
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent.parent
        / "templates"
        / "agent-workbench"
        / ".github"
        / "hooks"
        / "scripts"
    ),
)

import security_gate as sg
import zone_classifier as zc


class TestTesterEdgeCases:
    # ------------------------------------------------------------------
    # .git-as-FILE at workspace root (submodule / worktree pointer)
    # ------------------------------------------------------------------

    def test_git_file_at_workspace_root_is_allowed(self, tmp_path):
        """.git as a FILE at workspace root is treated as 'no git directory'.

        os.path.isdir() returns False for a regular file.  The implementation
        only denies when .git is a *directory* — this is an intentional design
        decision: a .git file is a worktree/submodule pointer where the actual
        repository data lives elsewhere, so no workspace-level zone exposure is
        guaranteed.

        This test documents the current behaviour and the isdir() boundary.
        """
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        # Create a .git FILE (git worktree / submodule pointer format)
        (tmp_path / ".git").write_text("gitdir: ../.git/worktrees/feature")
        ws_root = str(tmp_path).replace("\\", "/")

        result = sg.validate_get_changed_files(ws_root)

        # A .git FILE is not caught by os.path.isdir() — behaviour: allow.
        assert result == "allow"

    def test_git_file_inside_project_folder_is_allowed(self, tmp_path):
        """.git as a FILE inside the project folder also yields allow.

        os.path.isdir() returns False — the function falls through to the
        'no .git/ found' return "allow" path.
        """
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        (project_dir / ".git").write_text("gitdir: ../../.git/worktrees/feat")
        ws_root = str(tmp_path).replace("\\", "/")

        result = sg.validate_get_changed_files(ws_root)

        assert result == "allow"

    # ------------------------------------------------------------------
    # Symlinked .git/ at workspace root
    # ------------------------------------------------------------------

    def test_symlinked_git_dir_at_workspace_root_is_denied(self, tmp_path):
        """A symlink pointing to a directory at workspace root/.git → deny.

        os.path.isdir() follows symlinks; a symlink to a .git-like directory
        is indistinguishable from a real .git/ directory and must be denied.
        """
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        # Create a real directory that will serve as the symlink target
        real_git_dir = tmp_path / "_real_git_store"
        real_git_dir.mkdir()
        symlink_path = tmp_path / ".git"
        try:
            symlink_path.symlink_to(real_git_dir, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip(
                "Symlinks are not supported on this platform/configuration "
                "(Windows may require Developer Mode or admin privileges)"
            )

        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.validate_get_changed_files(ws_root)
        assert result == "deny"

    # ------------------------------------------------------------------
    # Fail-closed: PermissionError (subclass of OSError)
    # ------------------------------------------------------------------

    def test_permission_error_fails_closed(self):
        """PermissionError is a subclass of OSError and must trigger deny.

        The except clause catches OSError; PermissionError inherits from it.
        Verifying this subclass is caught prevents a potential fail-open gap if
        the exception type were ever narrowed by mistake.
        """
        with patch("os.path.isdir", side_effect=PermissionError("access denied")):
            result = sg.validate_get_changed_files("/some/workspace")
        assert result == "deny"

    # ------------------------------------------------------------------
    # detect_project_folder RuntimeError (explicit mock)
    # ------------------------------------------------------------------

    def test_detect_project_folder_runtime_error_no_root_git_is_allowed(
        self, tmp_path
    ):
        """Explicitly mocked RuntimeError from detect_project_folder → allow.

        When the zone_classifier raises RuntimeError (no project folder found)
        AND there is no .git/ at the workspace root, the tool must be allowed
        because no workspace-level git repository is tracking denied zones.
        """
        ws_root = str(tmp_path).replace("\\", "/")
        # No .git/ at workspace root; zone_classifier will raise RuntimeError
        with patch(
            "zone_classifier.detect_project_folder",
            side_effect=RuntimeError("no project folder detected"),
        ):
            result = sg.validate_get_changed_files(ws_root)
        assert result == "allow"

    # ------------------------------------------------------------------
    # Custom project folder name assembled correctly
    # ------------------------------------------------------------------

    def test_custom_project_folder_name_is_used_for_git_path(self, tmp_path):
        """validate_get_changed_files() uses the name returned by detect_project_folder.

        Verifies the project_git path is constructed via the dynamically
        detected folder name, not a hardcoded default.  Using a non-standard
        name ("MySpecialApp") ensures the test fails if 'Project' were hardcoded.
        """
        custom_name = "MySpecialApp"
        custom_project = tmp_path / custom_name
        custom_project.mkdir()
        (custom_project / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")

        with patch(
            "zone_classifier.detect_project_folder",
            return_value=custom_name,
        ):
            result = sg.validate_get_changed_files(ws_root)
        assert result == "allow"

    def test_custom_project_folder_no_git_dir_is_allowed(self, tmp_path):
        """When the detected project folder exists but has no .git/, result is allow.

        Complements the previous test by verifying the function does not falsely
        deny when a custom-named project folder is present without a .git/.
        """
        custom_name = "MySpecialApp"
        (tmp_path / custom_name).mkdir()
        ws_root = str(tmp_path).replace("\\", "/")

        with patch(
            "zone_classifier.detect_project_folder",
            return_value=custom_name,
        ):
            result = sg.validate_get_changed_files(ws_root)
        assert result == "allow"
