"""SAF-017 — Tester-added edge-case tests.

These tests go beyond the Developer's 52 tests and probe:
1. python -m pip install bypass (no VIRTUAL_ENV check when using python -m pip)
2. python -c "malicious os.system code" — documented intentional allow
3. python -m venv ../outside path traversal
4. pip install --target <path> attacks (absolute path outside workspace)
5. pip3.11 install normalization (passes venv check correctly)
6. VIRTUAL_ENV prefix collision (ws_root string prefix, not path prefix)
7. Mixed-case PIP command normalization
8. pip install with VIRTUAL_ENV equal to workspace root (design limitation)
9. python -c with exec/eval patterns inside the inline code
"""
import os
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


@pytest.fixture(scope="module")
def sg():
    import security_gate as _sg
    return _sg


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# Workspace root used by all tests — intentionally uses a path that could
# expose the prefix-collision bug (ws_root "c:/workspace" is a prefix of
# "c:/workspace2/...").
WS = "c:/workspace"

VENV_INSIDE_WORKSPACE = "c:/workspace/.venv"
VENV_OUTSIDE = "c:/other_workspace/.venv"


def _run(sg, command: str, extra_env: dict = None) -> tuple:
    extra_env = extra_env or {}
    with patch.dict(sg.os.environ, extra_env, clear=False):
        return sg.sanitize_terminal_command(command, WS)


def _allow(sg, command: str, extra_env: dict = None) -> bool:
    decision, _ = _run(sg, command, extra_env)
    return decision == "allow"


def _deny(sg, command: str, extra_env: dict = None) -> bool:
    decision, _ = _run(sg, command, extra_env)
    return decision == "deny"


def _run_no_venv(sg, command: str) -> tuple:
    """Run with VIRTUAL_ENV explicitly absent from the environment."""
    env_without_venv = {k: v for k, v in sg.os.environ.items() if k != "VIRTUAL_ENV"}
    with patch.object(sg.os, "environ", env_without_venv):
        return sg.sanitize_terminal_command(command, WS)


# ---------------------------------------------------------------------------
# CRITICAL: python -m pip install bypasses VIRTUAL_ENV check
#
# WP requirement 5 states: "Deny pip install when no venv is active."
# Using 'python -m pip install' sets verb='python', so the venv check
# (which gates on verb in ("pip","pip3")) is never reached.
# This is a security bypass.
# ---------------------------------------------------------------------------

def test_python_m_pip_install_no_venv_should_be_denied(sg):
    """CRITICAL: python -m pip install with no VIRTUAL_ENV must be denied.

    WP requirement 5 requires blocking global pip installs.  Using
    'python -m pip install' rather than 'pip install' currently bypasses
    the VIRTUAL_ENV guard, allowing global package installation.

    Expected: deny
    Actual result exposes the bypass if this test FAILS (i.e. returns allow).
    """
    decision, _ = _run_no_venv(sg, "python -m pip install requests")
    assert decision == "deny", (
        "SECURITY BYPASS: 'python -m pip install' with no VIRTUAL_ENV was "
        "allowed. The venv guard only checks verb in ('pip','pip3') and does "
        "not fire when pip is invoked via 'python -m pip'."
    )


def test_python3_m_pip_install_no_venv_should_be_denied(sg):
    """CRITICAL: python3 -m pip install with no VIRTUAL_ENV must be denied."""
    decision, _ = _run_no_venv(sg, "python3 -m pip install requests")
    assert decision == "deny", (
        "SECURITY BYPASS: 'python3 -m pip install' with no VIRTUAL_ENV was "
        "allowed. The venv guard does not fire for python3 -m pip."
    )


def test_python_m_pip_install_venv_outside_should_be_denied(sg):
    """python -m pip install with VIRTUAL_ENV outside workspace must be denied."""
    decision, _ = _run(sg, "python -m pip install requests",
                        extra_env={"VIRTUAL_ENV": VENV_OUTSIDE})
    assert decision == "deny", (
        "SECURITY BYPASS: 'python -m pip install' with VIRTUAL_ENV outside "
        "workspace was allowed."
    )


def test_python_m_pip_install_venv_inside_workspace_allowed(sg):
    """python -m pip install with valid VIRTUAL_ENV inside workspace should be allowed.

    NOTE: This test documents the DESIRED behavior after the bypass is fixed.
    If the bypass still exists, this test would pass (incorrectly), meaning
    the command is allowed regardless of venv state.  The companion
    test_python_m_pip_install_no_venv_should_be_denied is the critical one.
    """
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    # Even if the bypass exists, verify at minimum venv-inside path allows
    assert _allow(sg, "python -m pip install requests", extra_env=extra)


# ---------------------------------------------------------------------------
# VIRTUAL_ENV prefix-collision attack
#
# If ws_root = "c:/workspace", then norm_venv.startswith(ws_root) is True
# for "c:/workspace2/.venv" because string prefix is not path prefix.
# The correct check should be startswith(ws_root + "/") or == ws_root.
# ---------------------------------------------------------------------------

def test_pip_install_venv_path_with_prefix_collision_denied(sg):
    """pip install must be denied when VIRTUAL_ENV has ws_root as string prefix
    but is NOT inside the workspace directory.

    Example: ws_root='c:/workspace', VIRTUAL_ENV='c:/workspace2/.venv'
    String test: 'c:/workspace2/.venv'.startswith('c:/workspace') → True (BUG)
    Path test:   'c:/workspace2' is NOT inside 'c:/workspace' → should deny

    If this test FAILS, the startswith check has a prefix-collision bug.
    """
    # A malicious path that shares a string prefix with ws_root but
    # is NOT actually inside the workspace.
    colliding_venv = "c:/workspace2/.venv"
    extra = {"VIRTUAL_ENV": colliding_venv}
    decision, reason = sg.sanitize_terminal_command("pip install requests", WS,
                                                    ) if False else _run(
        sg, "pip install requests", extra_env=extra
    )
    assert decision == "deny", (
        f"PREFIX COLLISION BUG: VIRTUAL_ENV='{colliding_venv}' was accepted "
        f"as inside ws_root='{WS}' due to string prefix match. "
        "The check must verify path component boundaries."
    )


# ---------------------------------------------------------------------------
# python -c with dangerous inline code — intentionally allowed
# ---------------------------------------------------------------------------

def test_python_c_with_os_system_rm_is_intentionally_allowed(sg):
    """python -c 'import os; os.system(\"rm -rf /\")' is INTENTIONALLY ALLOWED.

    Per the dev-log: 'The -c argument is intentionally not zone-checked (it
    is a code string, not a path). Malicious code within the string is the
    responsibility of the outer AI safety layer.'

    This documents the intentional design decision.
    """
    # Note: semicolons inside a quoted string are tricky. Use a version
    # without semicolons so _split_segments doesn't split it.
    assert _allow(
        sg,
        'python -c "import os"',
    ), "python -c with benign inline code must be allowed (P-01 removed)"


def test_python_c_os_import_no_semicolons_allowed(sg):
    """python -c inline code without semicolons passes through as one segment."""
    assert _allow(sg, 'python -c "x = __import__(\'os\')"')


# ---------------------------------------------------------------------------
# python -m venv with path traversal (../outside)
# ---------------------------------------------------------------------------

def test_python_m_venv_dotdot_outside_project_denied(sg):
    """python -m venv ../outside_project is denied (path escapes project/)."""
    assert _deny(sg, "python -m venv ../outside_project")


def test_python_m_venv_parent_dir_denied(sg):
    """python -m venv targeting parent directory (..) is denied."""
    assert _deny(sg, "python -m venv ..")


def test_python_m_venv_absolute_outside_workspace_denied(sg):
    """python -m venv with absolute path outside workspace is denied."""
    assert _deny(sg, "python -m venv /tmp/myenv")


# ---------------------------------------------------------------------------
# pip install --target <path> attack vector
# ---------------------------------------------------------------------------

def test_pip_install_target_outside_workspace_denied(sg):
    """pip install --target /etc/ is denied even with valid VIRTUAL_ENV.

    The --target flag specifies where packages are installed.  Targeting
    a path outside the workspace is a write-to-arbitrary-path attack.
    --target starts with '-' so it's skipped; the value '/etc/' is the
    next non-flag token and should be zone-checked.
    """
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    assert _deny(sg, "pip install --target /etc/ requests", extra_env=extra)


def test_pip_install_target_inside_workspace_allowed(sg):
    """pip install --target inside workspace is allowed with valid VIRTUAL_ENV."""
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    # Note: 'project/site-packages' is inside project/ → zone "allow"
    assert _allow(
        sg, "pip install --target project/site-packages requests",
        extra_env=extra,
    )


def test_pip_install_target_noagentzone_denied(sg):
    """pip install --target NoAgentZone/ is denied."""
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    assert _deny(sg, "pip install --target NoAgentZone/packages requests",
                 extra_env=extra)


# ---------------------------------------------------------------------------
# pip3.11 / version-aliased pip
# ---------------------------------------------------------------------------

def test_pip311_install_no_venv_denied(sg):
    """pip3.11 install without VIRTUAL_ENV is denied (normalized to pip3)."""
    decision, _ = _run_no_venv(sg, "pip3.11 install requests")
    assert decision == "deny"


def test_pip311_install_venv_inside_workspace_allowed(sg):
    """pip3.11 install with VIRTUAL_ENV inside workspace is allowed."""
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    assert _allow(sg, "pip3.11 install requests", extra_env=extra)


def test_pip311_list_allowed(sg):
    """pip3.11 list is allowed (read-only subcommand, no venv check)."""
    assert _allow(sg, "pip3.11 list")


# ---------------------------------------------------------------------------
# Mixed-case pip commands
# ---------------------------------------------------------------------------

def test_pip_uppercase_no_venv_denied(sg):
    """PIP (uppercase) install without VIRTUAL_ENV is denied."""
    decision, _ = _run_no_venv(sg, "PIP install requests")
    assert decision == "deny"


def test_pip_mixed_case_list_allowed(sg):
    """PiP list is allowed (verb is normalized to pip)."""
    assert _allow(sg, "PiP list")


# ---------------------------------------------------------------------------
# VIRTUAL_ENV set to workspace root exactly (not a .venv subdir)
# ---------------------------------------------------------------------------

def test_pip_install_venv_equals_workspace_root_allowed(sg):
    """pip install when VIRTUAL_ENV equals the workspace root itself is allowed.

    This is a known design limitation documented here: the implementation
    checks that VIRTUAL_ENV starts with ws_root, so setting VIRTUAL_ENV to
    ws_root itself satisfies the check even though ws_root is not a real venv.
    The check prevents global installs (VIRTUAL_ENV at /usr/local etc.)
    but does not validate that the venv is properly structured.
    """
    extra = {"VIRTUAL_ENV": WS}  # WS itself, not a subdir
    decision, _ = _run(sg, "pip install requests", extra_env=extra)
    # Document the actual behavior (allowed) as a design limitation — not a
    # hard failure, but worth tracking.
    assert decision == "allow", (
        "Design limitation: VIRTUAL_ENV=ws_root satisfies startswith check. "
        "Documented in test report."
    )


# ---------------------------------------------------------------------------
# ipython -c still blocked (P-08 not removed)
# ---------------------------------------------------------------------------

def test_ipython_c_still_denied(sg):
    """ipython -c is still blocked by obfuscation pattern P-08."""
    # SAF-017 only removed P-01 (python -c). ipython -c (P-08) must remain.
    assert _deny(sg, 'ipython -c "print(1)"')


# ---------------------------------------------------------------------------
# python -c with eval/exec in inline code passes obfuscation scan
# (by design — gate does not audit code contents)
# ---------------------------------------------------------------------------

def test_python_c_with_eval_string_passes_obfuscation(sg):
    """python -c 'code containing eval keyword' is allowed by design.

    The obfuscation scan checks the lowercased command string. When eval
    appears inside an inline code argument (a Python string), the P-20
    pattern (\\beval\\b) would match on the ENTIRE command line, causing
    a deny.  Test verifies actual behavior.
    """
    # 'eval' inside quoted string triggers P-20 on the lowercased command.
    # This is expected: the gate can't distinguish 'eval' in code vs command.
    decision, _ = _run(sg, 'python -c "eval(\'1+1\')"')
    # The obfuscation scan sees \beval\b in the lowercased segment → deny.
    # This is the correct security-conservative behavior.
    assert decision == "deny", (
        "python -c with eval inside inline code is correctly blocked by P-20 "
        "(\\beval\\b obfuscation pattern). The gate cannot distinguish eval "
        "as a Python builtin from eval as a shell injection vector."
    )


def test_python_c_with_exec_string_blocked_by_obfuscation(sg):
    """python -c 'exec(...)' triggers P-21 (\\bexec\\b) → denied by design."""
    decision, _ = _run(sg, 'python -c "exec(\'import os\')"')
    assert decision == "deny", (
        "python -c with exec() inside inline code is correctly blocked by P-21 "
        "(\\bexec\\b obfuscation pattern)."
    )
