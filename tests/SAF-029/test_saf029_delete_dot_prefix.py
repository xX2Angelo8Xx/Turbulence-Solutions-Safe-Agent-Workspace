"""SAF-029 — Tests for dot-prefix path matching fix for delete operations.

Verifies that delete commands (Remove-Item, rm, del, etc.) targeting
dot-prefix paths like .venv, .git, .pytest_cache, .env inside the project
folder are correctly allowed, while .github, .vscode, and wildcards like
.g*, .v* remain denied (SAF-020 protection intact).

Regression: exact deny-zone names must not be allowed.
Protection: wildcard prefix matching (SAF-020) must still work.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "coding"
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
# SAF-029: Delete commands — dot-prefix non-deny-zone paths allowed
# ---------------------------------------------------------------------------

class TestRemoveItemDotPrefixAllowed:
    """Delete commands on dot-prefix paths that are NOT deny zones must be allowed."""

    def test_remove_item_dot_venv_allowed(self):
        """TST-5300: Remove-Item .venv inside project folder must be allowed."""
        assert _allow("Remove-Item .venv")

    def test_remove_item_dot_git_allowed(self):
        """TST-5301: Remove-Item .git inside project folder must be allowed."""
        assert _allow("Remove-Item .git")

    def test_remove_item_dot_pytest_cache_allowed(self):
        """TST-5302: Remove-Item .pytest_cache inside project folder must be allowed."""
        assert _allow("Remove-Item .pytest_cache")

    def test_remove_item_dot_env_allowed(self):
        """TST-5303: Remove-Item .env inside project folder must be allowed."""
        assert _allow("Remove-Item .env")

    def test_ri_dot_venv_allowed(self):
        """TST-5308: ri (alias for Remove-Item) .venv must be allowed."""
        assert _allow("ri .venv")

    def test_remove_item_dot_gitignore_allowed(self):
        """TST-5309: Remove-Item .gitignore inside project folder must be allowed."""
        assert _allow("Remove-Item .gitignore")

    def test_remove_item_dot_editorconfig_allowed(self):
        """TST-5310: Remove-Item .editorconfig inside project folder must be allowed."""
        assert _allow("Remove-Item .editorconfig")

    def test_remove_item_recursive_dot_venv_allowed(self):
        """TST-5311: Remove-Item -Recurse .venv must be allowed."""
        assert _allow("Remove-Item -Recurse .venv")

    def test_remove_item_force_dot_venv_allowed(self):
        """TST-5312: Remove-Item -Force .venv must be allowed."""
        assert _allow("Remove-Item -Force .venv")

    def test_remove_item_recurse_force_dot_venv_allowed(self):
        """TST-5313: Remove-Item -Recurse -Force .venv must be allowed."""
        assert _allow("Remove-Item -Recurse -Force .venv")


# ---------------------------------------------------------------------------
# SAF-029 regression: deny zones must STILL be denied for delete commands
# ---------------------------------------------------------------------------

class TestRemoveItemDenyZonesStillDenied:
    """Delete commands on exact deny-zone names must remain denied."""

    def test_remove_item_dot_github_denied(self):
        """TST-5320: Remove-Item .github must be denied."""
        assert _deny("Remove-Item .github")

    def test_remove_item_dot_vscode_denied(self):
        """TST-5321: Remove-Item .vscode must be denied."""
        assert _deny("Remove-Item .vscode")

    def test_rm_dot_github_denied(self):
        """TST-5322: rm .github must be denied."""
        assert _deny("rm .github")

    def test_rm_dot_vscode_denied(self):
        """TST-5323: rm .vscode must be denied."""
        assert _deny("rm .vscode")

    def test_remove_item_noagentzone_path_denied(self):
        """TST-5324: Remove-Item c:/workspace/noagentzone (absolute path) must be denied."""
        assert _deny("Remove-Item c:/workspace/noagentzone")

    def test_rm_slash_noagentzone_denied(self):
        """TST-5325: rm ./noagentzone (dot-relative path) must be denied."""
        assert _deny("rm ./noagentzone")


# ---------------------------------------------------------------------------
# SAF-020 regression: wildcard prefix matching must still be active
# ---------------------------------------------------------------------------

class TestSAF020WildcardProtectionIntact:
    """Wildcard patterns .g* and .v* must remain denied (SAF-020 protection)."""

    def test_remove_item_dotg_star_denied(self):
        """TST-5330: Remove-Item .g* (wildcard matching .github) must be denied."""
        assert _deny("Remove-Item .g*")

    def test_remove_item_dotv_star_denied(self):
        """TST-5331: Remove-Item .v* (wildcard matching .vscode) must be denied."""
        assert _deny("Remove-Item .v*")

    def test_rm_dotg_star_denied(self):
        """TST-5332: rm .g* must be denied."""
        assert _deny("rm .g*")

    def test_rm_dotv_star_denied(self):
        """TST-5333: rm .v* must be denied."""
        assert _deny("rm .v*")

    def test_remove_item_dot_star_denied(self):
        """TST-5334: Remove-Item .* (matches all dot dirs including deny zones) must be denied."""
        assert _deny("Remove-Item .*")

    def test_rm_dot_star_denied(self):
        """TST-5335: rm .* must be denied."""
        assert _deny("rm .*")


# ---------------------------------------------------------------------------
# Safety boundary: non-project paths must still be denied for delete commands
# ---------------------------------------------------------------------------

class TestDeleteCommandsBoundary:
    """Delete commands targeting paths outside the project folder remain denied."""

    def test_remove_item_dot_slash_root_file_denied(self):
        """TST-5340: Remove-Item ./root_config.json at workspace root must be denied.

        normpath strips './' so norm_fb = 'root_config.json' (no leading dot).
        The project-folder fallback is not tried for single-segment non-dot names.
        """
        assert _deny("Remove-Item ./root_config.json")

    def test_rm_absolute_path_outside_project_denied(self):
        """TST-5341: rm c:/other/path must be denied (outside workspace)."""
        assert _deny("rm c:/other/path")

    def test_del_absolute_forward_slash_denied(self):
        """TST-5342: del c:/windows/system32/file.dll must be denied (outside workspace)."""
        assert _deny("del c:/windows/system32/file.dll")

    def test_rm_dot_venv_denied(self):
        """TST-5343: rm .venv must be denied.

        Unix rm is intentionally excluded from _DELETE_DOT_FALLBACK_VERBS.
        FIX-033 requires `rm .env` to be denied; rm family gets no dot-prefix fallback.
        """
        assert _deny("rm .venv")

    def test_rm_dot_git_denied(self):
        """TST-5344: rm .git must be denied (rm excluded from dot-prefix fallback)."""
        assert _deny("rm .git")

    def test_rm_dot_pytest_cache_denied(self):
        """TST-5345: rm .pytest_cache must be denied (rm excluded from dot-prefix fallback)."""
        assert _deny("rm .pytest_cache")

    def test_rm_dot_env_denied(self):
        """TST-5346: rm .env must be denied.

        Explicit regression: rm .env must be denied (FIX-033 requirement).
        rm is not in _DELETE_DOT_FALLBACK_VERBS.
        """
        assert _deny("rm .env")

    def test_remove_item_multisegment_denied(self):
        """TST-5347: Remove-Item src/app.py must be denied (multi-segment, FIX-022)."""
        assert _deny("Remove-Item src/app.py")
