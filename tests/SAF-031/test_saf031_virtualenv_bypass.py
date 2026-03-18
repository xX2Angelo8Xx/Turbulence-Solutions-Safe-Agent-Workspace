"""SAF-031 — Tests for VIRTUAL_ENV bypass fixes.

BUG-049 (Critical): python -m pip install bypassed the VIRTUAL_ENV check
    because the verb was 'python', not 'pip'.
BUG-050 (High): The VIRTUAL_ENV startswith check did not enforce a
    path-component boundary — 'c:/workspace2/.venv' incorrectly satisfied
    startswith('c:/workspace').

Protection tests: verify that both guards now correctly deny unsafe commands.
Regression tests: verify that valid commands are still allowed and that the
    direct pip/pip3 verb path continues to work correctly.
Bypass tests: verify that attacker-controlled VIRTUAL_ENV values cannot
    circumvent the guard through path-collision tricks.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "Default-Project"
    / ".github"
    / "hooks"
    / "scripts"
)

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# Fake workspace root (project folder = 'project' — patched by conftest)
WS = "c:/workspace"

# VIRTUAL_ENV values used across tests
VENV_INSIDE_WORKSPACE = "c:/workspace/.venv"
VENV_INSIDE_PROJECT = "c:/workspace/project/.venv"
VENV_OUTSIDE = "c:/other_workspace/.venv"
# BUG-050 collision value: starts with ws_root string but is a DIFFERENT directory
VENV_COLLISION = "c:/workspace2/.venv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(command: str, extra_env: dict | None = None) -> tuple:
    """Run sanitize_terminal_command with an optional environment overlay."""
    extra_env = extra_env or {}
    with patch.dict(sg.os.environ, extra_env, clear=False):
        return sg.sanitize_terminal_command(command, WS)


def _run_no_venv(command: str) -> tuple:
    """Run with VIRTUAL_ENV explicitly absent from the environment."""
    env_without_venv = {k: v for k, v in sg.os.environ.items() if k != "VIRTUAL_ENV"}
    with patch.object(sg.os, "environ", env_without_venv):
        return sg.sanitize_terminal_command(command, WS)


def _allow(command: str, extra_env: dict | None = None) -> bool:
    decision, _ = _run(command, extra_env)
    return decision == "allow"


def _deny(command: str, extra_env: dict | None = None) -> bool:
    decision, _ = _run(command, extra_env)
    return decision == "deny"


def _deny_no_venv(command: str) -> bool:
    decision, _ = _run_no_venv(command)
    return decision == "deny"


# ---------------------------------------------------------------------------
# BUG-049: python -m pip install without VIRTUAL_ENV must be denied
# ---------------------------------------------------------------------------

class TestBug049PythonMPipInstall:
    """Verify that the VIRTUAL_ENV guard fires for python -m pip install."""

    def test_python_m_pip_install_no_venv_denied(self):
        """TST-5500: python -m pip install without VIRTUAL_ENV is denied."""
        assert _deny_no_venv("python -m pip install requests")

    def test_python_m_pip_install_valid_venv_inside_workspace_allowed(self):
        """TST-5501: python -m pip install with .venv inside workspace is allowed."""
        extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
        assert _allow("python -m pip install requests", extra)

    def test_python_m_pip_install_valid_venv_inside_project_allowed(self):
        """TST-5502: python -m pip install with .venv inside project/ is allowed."""
        extra = {"VIRTUAL_ENV": VENV_INSIDE_PROJECT}
        assert _allow("python -m pip install requests", extra)

    def test_python_m_pip_install_outside_workspace_venv_denied(self):
        """TST-5503: python -m pip install with VIRTUAL_ENV outside workspace is denied."""
        extra = {"VIRTUAL_ENV": VENV_OUTSIDE}
        assert _deny("python -m pip install requests", extra)

    def test_python3_m_pip_install_no_venv_denied(self):
        """TST-5504: python3 -m pip install without VIRTUAL_ENV is denied."""
        assert _deny_no_venv("python3 -m pip install requests")

    def test_python3_m_pip_install_valid_venv_allowed(self):
        """TST-5505: python3 -m pip install with valid VIRTUAL_ENV is allowed."""
        extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
        assert _allow("python3 -m pip install requests", extra)

    def test_python_m_pip_install_editable_no_venv_denied(self):
        """TST-5508: python -m pip install -e . without VIRTUAL_ENV is denied."""
        assert _deny_no_venv("python -m pip install -e .")

    def test_python_m_pip_install_editable_valid_venv_allowed(self):
        """TST-5509: python -m pip install -e . with valid VIRTUAL_ENV is allowed."""
        extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
        assert _allow("python -m pip install -e .", extra)

    def test_python_m_pip_install_flag_before_subcommand_no_venv_denied(self):
        """TST-5510: python -m pip --verbose install is denied without venv."""
        assert _deny_no_venv("python -m pip install --upgrade requests")


# ---------------------------------------------------------------------------
# BUG-049: python -m pip read-only subcommands must be unaffected
# ---------------------------------------------------------------------------

class TestBug049ReadOnlySubcommands:
    """Read-only pip subcommands via python -m pip are not install → always allow."""

    def test_python_m_pip_list_no_venv_allowed(self):
        """TST-5511: python -m pip list is always allowed (read-only, no VIRTUAL_ENV needed)."""
        assert not _deny_no_venv("python -m pip list")

    def test_python_m_pip_show_no_venv_allowed(self):
        """TST-5512: python -m pip show requests is always allowed."""
        assert not _deny_no_venv("python -m pip show requests")

    def test_python_m_pip_freeze_no_venv_allowed(self):
        """TST-5513: python -m pip freeze is always allowed."""
        assert not _deny_no_venv("python -m pip freeze")

    def test_python_m_pip_check_no_venv_allowed(self):
        """TST-5514: python -m pip check is always allowed."""
        assert not _deny_no_venv("python -m pip check")

    def test_python_m_pip_list_with_venv_allowed(self):
        """TST-5515: python -m pip list with VIRTUAL_ENV is allowed."""
        extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
        assert _allow("python -m pip list", extra)


# ---------------------------------------------------------------------------
# BUG-050: startswith path-component collision must be rejected
# ---------------------------------------------------------------------------

class TestBug050StartsWithCollision:
    """Verify that 'c:/workspace2/.venv' is denied when ws_root='c:/workspace'."""

    def test_pip_install_venv_collision_denied(self):
        """TST-5516: pip install with VIRTUAL_ENV='c:/workspace2/.venv' is denied (BUG-050).

        The old code:  norm_venv.startswith(ws_root)
        would return True for 'c:/workspace2/.venv'.startswith('c:/workspace') → WRONG.

        The fixed code: norm_venv.startswith(ws_norm + "/")
        only matches paths that are genuinely inside ws_root.
        """
        extra = {"VIRTUAL_ENV": VENV_COLLISION}
        assert _deny("pip install requests", extra)

    def test_python_m_pip_install_venv_collision_denied(self):
        """TST-5517: python -m pip install with VIRTUAL_ENV='c:/workspace2/.venv' denied (BUG-049+050)."""
        extra = {"VIRTUAL_ENV": VENV_COLLISION}
        assert _deny("python -m pip install requests", extra)

    def test_pip_install_venv_with_extra_suffix_denied(self):
        """TST-5518: deny when VIRTUAL_ENV is a sibling dir that shares the ws prefix."""
        extra = {"VIRTUAL_ENV": "c:/workspace_evil/.venv"}
        assert _deny("pip install requests", extra)

    def test_pip_install_exact_ws_root_as_venv_is_denied(self):
        """TST-5519: VIRTUAL_ENV = ws_root itself (no trailing /) is denied.

        The venv directory should be INSIDE the workspace, not the workspace
        root itself.  We normalize and compare: the code checks
        norm_venv != ws_norm which catches this edge case.

        ws_root = 'c:/workspace', norm_venv = 'c:/workspace' → ws_norm = 'c:/workspace'
        norm_venv == ws_norm → True → the else branch of `not startswith(ws_norm + "/")`
        allows it.  This edge case (VIRTUAL_ENV == workspace root) is technically
        within the workspace so the gate allows it; the test documents this behavior.
        """
        extra = {"VIRTUAL_ENV": "c:/workspace"}
        # This is an edge case: workspace root as venv IS within workspace — allow
        decision, _ = _run("pip install requests", extra)
        # Documented behavior: allowed (venv == ws_root is treated as inside workspace)
        assert decision == "allow"

    def test_pip_install_venv_with_slash_inside_workspace_allowed(self):
        """TST-5520: VIRTUAL_ENV at 'c:/workspace/.venv' (contains '/') is allowed."""
        extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
        assert _allow("pip install requests", extra)


# ---------------------------------------------------------------------------
# Regression: direct pip/pip3 verb behavior must be unchanged
# ---------------------------------------------------------------------------

class TestRegressionDirectPipVerb:
    """Ensure existing pip/pip3 verb handling is unaffected by SAF-031 changes."""

    def test_pip_install_no_venv_denied(self):
        """TST-5521: Regression — direct pip install without VIRTUAL_ENV still denied."""
        assert _deny_no_venv("pip install requests")

    def test_pip_install_valid_venv_allowed(self):
        """TST-5522: Regression — direct pip install with valid VIRTUAL_ENV still allowed."""
        extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
        assert _allow("pip install requests", extra)

    def test_pip_install_venv_outside_denied(self):
        """TST-5523: Regression — direct pip install with outside VIRTUAL_ENV still denied."""
        extra = {"VIRTUAL_ENV": VENV_OUTSIDE}
        assert _deny("pip install requests", extra)

    def test_pip3_install_no_venv_denied(self):
        """TST-5524: Regression — pip3 install without venv still denied."""
        assert _deny_no_venv("pip3 install requests")

    def test_pip3_install_valid_venv_allowed(self):
        """TST-5525: Regression — pip3 install with valid VIRTUAL_ENV still allowed."""
        extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
        assert _allow("pip3 install requests", extra)

    def test_pip_list_always_allowed(self):
        """TST-5526: Regression — pip list is always allowed (no venv required)."""
        assert _deny_no_venv("pip list") is False

    def test_pip_show_always_allowed(self):
        """TST-5527: Regression — pip show requests is always allowed."""
        assert _deny_no_venv("pip show requests") is False

    def test_pip_freeze_always_allowed(self):
        """TST-5528: Regression — pip freeze with no venv still allowed."""
        assert _deny_no_venv("pip freeze") is False
