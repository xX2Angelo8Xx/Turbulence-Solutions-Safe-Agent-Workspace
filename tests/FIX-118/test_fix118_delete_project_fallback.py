"""FIX-118 — Tests for project-folder delete fallback expansion.

Verifies that Remove-Item, rm, del, erase, and rmdir are allowed when
targeting multi-segment paths inside the project folder, and that the
security boundary remains intact for deny zones and workspace root files.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "hooks"
    / "scripts"
)

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# Fake workspace root — project folder is 'project'
WS = "c:/workspace"


def _allow(command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def _deny(command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# FIX-118: Allow multi-segment delete paths inside the project folder
# ---------------------------------------------------------------------------

class TestDeleteMultiSegmentAllowed:
    """Delete commands on multi-segment paths resolving inside project folder."""

    def test_remove_item_src_file_allowed(self):
        """Remove-Item src/oldfile.py inside project folder must be allowed."""
        assert _allow("Remove-Item src/oldfile.py")

    def test_remove_item_nested_dir_allowed(self):
        """Remove-Item docs/old/file.md (2-level nested) must be allowed."""
        assert _allow("Remove-Item docs/old/file.md")

    def test_rm_src_file_allowed(self):
        """rm src/oldfile.py must be allowed (FIX-118 extends rm)."""
        assert _allow("rm src/oldfile.py")

    def test_del_src_file_allowed(self):
        """del src/oldfile.py must be allowed."""
        assert _allow("del src/oldfile.py")

    def test_erase_src_file_allowed(self):
        """erase src/oldfile.py must be allowed."""
        assert _allow("erase src/oldfile.py")

    def test_rmdir_src_subdir_allowed(self):
        """rmdir src/old_module must be allowed."""
        assert _allow("rmdir src/old_module")

    def test_ri_src_file_allowed(self):
        """ri src/oldfile.py (alias Remove-Item) must be allowed."""
        assert _allow("ri src/oldfile.py")

    def test_remove_item_with_flags_src_allowed(self):
        """Remove-Item -Recurse -Force src/old_module must be allowed."""
        assert _allow("Remove-Item -Recurse -Force src/old_module")

    def test_rm_recursive_src_dir_allowed(self):
        """rm -rf src/old_module must be allowed."""
        assert _allow("rm -rf src/old_module")

    def test_remove_item_explicit_project_path_allowed(self):
        """Remove-Item project/src/file.py (explicit project prefix) must be allowed."""
        assert _allow("Remove-Item project/src/file.py")

    def test_remove_item_absolute_project_path_allowed(self):
        """Remove-Item c:/workspace/project/src/file.py must be allowed."""
        assert _allow("Remove-Item c:/workspace/project/src/file.py")


# ---------------------------------------------------------------------------
# FIX-118: Delete dot-prefix paths for all verbs (extends SAF-029)
# ---------------------------------------------------------------------------

class TestDeleteDotPrefixAllDeleteVerbs:
    """All delete verbs (not just remove-item/ri) must allow dot-prefix project paths."""

    def test_rm_dot_venv_allowed(self):
        """rm .venv must be allowed (FIX-118: rm added to _DELETE_PROJECT_FALLBACK_VERBS)."""
        assert _allow("rm .venv")

    def test_rm_dot_env_allowed(self):
        """rm .env must be allowed inside project folder."""
        assert _allow("rm .env")

    def test_rm_dot_git_allowed(self):
        """rm .git must be allowed inside project folder."""
        assert _allow("rm .git")

    def test_del_dot_venv_allowed(self):
        """del .venv must be allowed."""
        assert _allow("del .venv")

    def test_erase_dot_cache_allowed(self):
        """erase .cache must be allowed."""
        assert _allow("erase .cache")

    def test_rmdir_dot_mypy_cache_allowed(self):
        """rmdir .mypy_cache must be allowed."""
        assert _allow("rmdir .mypy_cache")


# ---------------------------------------------------------------------------
# SECURITY: Deny zones must still be denied for all delete verbs
# ---------------------------------------------------------------------------

class TestDeleteDenyZonesProtected:
    """Delete commands targeting deny zones must remain denied for all verbs."""

    def test_rm_dot_github_denied(self):
        """rm .github must be denied."""
        assert _deny("rm .github")

    def test_rm_dot_vscode_denied(self):
        """rm .vscode must be denied."""
        assert _deny("rm .vscode")

    def test_del_dot_github_denied(self):
        """del .github must be denied."""
        assert _deny("del .github")

    def test_rm_github_subpath_denied(self):
        """rm .github/hooks/security_gate.py must be denied."""
        assert _deny("rm .github/hooks/security_gate.py")

    def test_remove_item_github_hooks_denied(self):
        """Remove-Item .github/hooks must be denied."""
        assert _deny("Remove-Item .github/hooks")

    def test_rmdir_vscode_denied(self):
        """rmdir .vscode must be denied."""
        assert _deny("rmdir .vscode")

    def test_rm_noagentzone_subpath_denied(self):
        """rm ./noagentzone/secrets.env must be denied (deny zone in path)."""
        assert _deny("rm ./noagentzone/secrets.env")

    def test_rm_noagentzone_multisegment_denied(self):
        """rm noagentzone/file.txt must be denied (deny zone as first component)."""
        assert _deny("rm noagentzone/file.txt")

    def test_remove_item_absolute_github_denied(self):
        """Remove-Item c:/workspace/.github must be denied."""
        assert _deny("Remove-Item c:/workspace/.github")


# ---------------------------------------------------------------------------
# SECURITY: Workspace root files and out-of-scope paths
# ---------------------------------------------------------------------------

class TestDeleteWorkspaceRootProtected:
    """Single-segment non-dot paths and out-of-scope paths remain protected."""

    def test_remove_item_root_file_dot_relative_denied(self):
        """Remove-Item ./root_config.json (normalizes to root_config.json) must be denied.

        normpath strips './' so norm_fb = 'root_config.json' (no dot-prefix,
        no trailing slash) — the fallback condition is not triggered.
        """
        assert _deny("Remove-Item ./root_config.json")

    def test_rm_absolute_outside_workspace_denied(self):
        """rm c:/other/path must be denied."""
        assert _deny("rm c:/other/path")

    def test_del_windows_system_denied(self):
        """del c:/windows/system32/file.dll must be denied."""
        assert _deny("del c:/windows/system32/file.dll")

    def test_rmdir_absolute_outside_workspace_denied(self):
        """rmdir c:/Users/evil must be denied."""
        assert _deny("rmdir c:/Users/evil")


# ---------------------------------------------------------------------------
# SECURITY: SAF-020 wildcard protection must remain active
# ---------------------------------------------------------------------------

class TestDeleteWildcardProtection:
    """Wildcard patterns that could target deny zones must remain denied."""

    def test_rm_dotg_star_denied(self):
        """rm .g* (could match .github) must be denied."""
        assert _deny("rm .g*")

    def test_rm_dotv_star_denied(self):
        """rm .v* (could match .vscode) must be denied."""
        assert _deny("rm .v*")

    def test_remove_item_dot_star_denied(self):
        """Remove-Item .* must be denied."""
        assert _deny("Remove-Item .*")

    def test_del_star_github_denied(self):
        """del .github/* must be denied."""
        assert _deny("del .github/*")


# ---------------------------------------------------------------------------
# REGRESSION: Existing SAF-029 allow cases must still pass
# ---------------------------------------------------------------------------

class TestSAF029RegressionAllowCasesIntact:
    """Previously-allowed cases from SAF-029 must still be allowed."""

    def test_remove_item_dot_venv_still_allowed(self):
        """Remove-Item .venv must still be allowed (SAF-029 regression)."""
        assert _allow("Remove-Item .venv")

    def test_remove_item_recurse_force_dot_venv_still_allowed(self):
        """Remove-Item -Recurse -Force .venv must still be allowed."""
        assert _allow("Remove-Item -Recurse -Force .venv")

    def test_ri_dot_venv_still_allowed(self):
        """ri .venv must still be allowed."""
        assert _allow("ri .venv")

    def test_remove_item_dot_env_still_allowed(self):
        """Remove-Item .env must still be allowed (SAF-029 regression)."""
        assert _allow("Remove-Item .env")
