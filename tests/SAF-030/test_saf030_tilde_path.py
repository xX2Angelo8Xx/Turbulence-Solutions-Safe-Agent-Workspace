"""SAF-030 — Tests for bare tilde recognition as a path-like token.

Verifies that `rm ~`, `rm ~/Documents`, `remove-item ~`, `del ~`, `cat ~/secret.txt`,
and `ls ~` are all denied because `~` resolves to the user's HOME directory which
is outside the project folder.

Also verifies regression: normal project-relative paths are still allowed.

Protection test: tilde paths are recognized as path-like and zone-checked.
Bypass test: attempting to use `~` to bypass the zone check is prevented.
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
# Unit tests for _is_path_like
# ---------------------------------------------------------------------------

class TestIsPathLikeTilde:
    """Unit tests for _is_path_like() recognizing tilde tokens."""

    def test_bare_tilde_is_path_like(self):
        """TST-5400: Bare ~ must be recognized as path-like."""
        assert sg._is_path_like("~") is True

    def test_tilde_slash_prefix_is_path_like(self):
        """TST-5401: ~/Documents must be recognized as path-like."""
        assert sg._is_path_like("~/Documents") is True

    def test_tilde_backslash_prefix_is_path_like(self):
        """TST-5402: ~\\Documents must be recognized as path-like."""
        assert sg._is_path_like("~\\Documents") is True

    def test_tilde_nested_path_is_path_like(self):
        """TST-5403: ~/foo/bar must be recognized as path-like."""
        assert sg._is_path_like("~/foo/bar") is True

    def test_regular_token_not_path_like(self):
        """TST-5404: A plain word like 'requests' must NOT be path-like."""
        assert sg._is_path_like("requests") is False

    def test_tilde_middle_of_word_not_path_like(self):
        """TST-5405: A tilde in the middle of a word (e.g. foo~bar) is not path-like."""
        assert sg._is_path_like("foo~bar") is False


# ---------------------------------------------------------------------------
# Protection tests: delete commands with tilde must be denied
# ---------------------------------------------------------------------------

class TestDeleteTildeDenied:
    """Delete commands targeting ~ must be denied (SAF-030 protection)."""

    def test_rm_bare_tilde_denied(self):
        """TST-5410: rm ~ must be denied."""
        assert _deny("rm ~")

    def test_rm_tilde_documents_denied(self):
        """TST-5411: rm ~/Documents must be denied."""
        assert _deny("rm ~/Documents")

    def test_remove_item_bare_tilde_denied(self):
        """TST-5412: remove-item ~ must be denied."""
        assert _deny("remove-item ~")

    def test_remove_item_tilde_desktop_denied(self):
        """TST-5413: remove-item ~/Desktop must be denied."""
        assert _deny("remove-item ~/Desktop")

    def test_del_bare_tilde_denied(self):
        """TST-5414: del ~ must be denied."""
        assert _deny("del ~")

    def test_erase_bare_tilde_denied(self):
        """TST-5415: erase ~ must be denied."""
        assert _deny("erase ~")

    def test_rmdir_bare_tilde_denied(self):
        """TST-5416: rmdir ~ must be denied."""
        assert _deny("rmdir ~")


# ---------------------------------------------------------------------------
# Protection tests: read commands with tilde must be denied
# ---------------------------------------------------------------------------

class TestReadTildeDenied:
    """Read commands targeting ~ must also be denied (outside project folder)."""

    def test_cat_tilde_secret_txt_denied(self):
        """TST-5420: cat ~/secret.txt must be denied."""
        assert _deny("cat ~/secret.txt")

    def test_ls_bare_tilde_denied(self):
        """TST-5421: ls ~ must be denied."""
        assert _deny("ls ~")

    def test_get_content_tilde_denied(self):
        """TST-5422: Get-Content ~ must be denied."""
        assert _deny("Get-Content ~")

    def test_get_childitem_tilde_denied(self):
        """TST-5423: Get-ChildItem ~ must be denied."""
        assert _deny("Get-ChildItem ~")


# ---------------------------------------------------------------------------
# Bypass tests: various tilde-related bypass attempts must be denied
# ---------------------------------------------------------------------------

class TestTildeBypassAttempts:
    """Attempts to use tilde to reach outside the project must be denied."""

    def test_rm_tilde_backslash_path_denied(self):
        """TST-5430: rm ~\\Documents (double-backslash, preserved through shlex) must be denied."""
        # Two backslashes in the literal → shlex preserves one → token is ~\Documents
        assert _deny("rm ~\\\\Documents")

    def test_cd_tilde_denied(self):
        """TST-5431: cd ~ must be denied (navigating to HOME)."""
        assert _deny("cd ~")

    def test_python_tilde_script_denied(self):
        """TST-5432: python ~/script.py must be denied."""
        assert _deny("python ~/script.py")

    def test_cat_tilde_etc_denied(self):
        """TST-5433: cat ~/../../etc/passwd must be denied."""
        assert _deny("cat ~/../../etc/passwd")


# ---------------------------------------------------------------------------
# Regression tests: normal project paths still work
# ---------------------------------------------------------------------------

class TestRegressionProjectPaths:
    """Normal project-relative paths must not regress (SAF-030 regression)."""

    def test_rm_project_file_allowed(self):
        """TST-5440: rm of a file inside the project folder must still be allowed."""
        # project/src/app.py is inside the project folder → allow
        assert _allow("rm c:/workspace/project/src/app.py")

    def test_ls_project_folder_allowed(self):
        """TST-5441: ls of the project folder must still be allowed."""
        assert _allow("ls c:/workspace/project")

    def test_cat_project_file_allowed(self):
        """TST-5442: cat of a project file must still be allowed."""
        assert _allow("cat c:/workspace/project/README.md")

    def test_remove_item_project_file_allowed(self):
        """TST-5443: remove-item of a project file must still be allowed."""
        assert _allow("remove-item c:/workspace/project/src/app.py")

    def test_del_project_file_allowed(self):
        """TST-5444: del of a project file must still be allowed."""
        assert _allow("del c:/workspace/project/src/app.py")
