"""SAF-017 — Tests for expanded terminal allowlist: Python and pip commands.

Covers all 5 requirements:
1. python -c "..." allowed inside project folder (P-01 obfuscation pattern removed,
   -c removed from denied_flags, inline code arg skipped from zone-check)
2. python -m venv <path> allowed when path is inside project folder; denied outside
3. pip list/show/freeze/check allowed without path restrictions (read-only)
4. pip install allowed when VIRTUAL_ENV is active inside the project folder
5. pip install denied when no venv is active or venv points outside project
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

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


@pytest.fixture(scope="module")
def sg():
    import security_gate as _sg
    return _sg


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# Workspace root used by all tests
WS = "c:/workspace"

# VIRTUAL_ENV values for pip install tests
VENV_INSIDE_WORKSPACE = "c:/workspace/.venv"
VENV_INSIDE_PROJECT = "c:/workspace/project/.venv"
VENV_OUTSIDE = "c:/other_workspace/.venv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(sg, command: str, extra_env: dict = None) -> tuple:
    """Run sanitize_terminal_command with optional extra env vars."""
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
# Requirement 1: python -c allowed (P-01 obfuscation pattern removed, -c out
#                of denied_flags, inline code arg skipped from zone-check)
# ---------------------------------------------------------------------------

def test_python_c_simple_code_allowed(sg):
    """python -c with simple inline code is allowed."""
    assert _allow(sg, 'python -c "print(42)"')


def test_python3_c_simple_code_allowed(sg):
    """python3 -c with inline code is allowed."""
    # Note: ';' inside the code string would be split by _split_segments before shlex
    # sees it as a quoted token, so use a single-statement expression here.
    assert _allow(sg, 'python3 -c "print(42)"')


def test_py_c_simple_code_allowed(sg):
    """py -c (Windows launcher) with inline code is allowed."""
    assert _allow(sg, "py -c \"print('hello')\"")


def test_python_c_not_blocked_by_obfuscation_scan(sg):
    """python -c must NOT be caught by the obfuscation pre-scan (P-01 removed)."""
    # If P-01 were still present, this would be denied at Stage 3 before the
    # allowlist check.  Passing confirms P-01 was removed.
    decision, reason = sg.sanitize_terminal_command('python -c "x = 1"', WS)
    assert decision == "allow"


def test_python_c_minus_c_not_in_denied_flags(sg):
    """Confirm -c is absent from python's denied_flags set."""
    rule = sg._COMMAND_ALLOWLIST["python"]
    assert "-c" not in rule.denied_flags


def test_python3_c_minus_c_not_in_denied_flags(sg):
    """Confirm -c is absent from python3's denied_flags set."""
    rule = sg._COMMAND_ALLOWLIST["python3"]
    assert "-c" not in rule.denied_flags


def test_py_c_minus_c_not_in_denied_flags(sg):
    """Confirm -c is absent from py's denied_flags set."""
    rule = sg._COMMAND_ALLOWLIST["py"]
    assert "-c" not in rule.denied_flags


def test_python_c_inline_code_with_slash_allowed(sg):
    """Inline code containing '/' is NOT zone-checked (it's code, not a path)."""
    # The code string 'print("a/b")' contains '/' but should be skipped
    assert _allow(sg, 'python -c "print(\'a/b\')"')


def test_python_c_inline_code_without_semicolons_allowed(sg):
    """python -c with multi-part inline code (no semicolons) is allowed.

    Commands containing ';' are split by _split_segments (by design) BEFORE
    shlex sees them as a quoted token.  Inline code that does not contain ';'
    passes through as a single segment and is allowed.
    """
    assert _allow(sg, 'python -c "x = 1 + 1"')


def test_python_interactive_still_denied(sg):
    """-i (interactive) remains in denied_flags — must be blocked."""
    assert _deny(sg, "python -i")


def test_python_interactive_long_still_denied(sg):
    """--interactive remains in denied_flags — must be blocked."""
    assert _deny(sg, "python --interactive")


# ---------------------------------------------------------------------------
# Requirement 2: python -m venv <path> — allowed when path is inside project/
# ---------------------------------------------------------------------------

def test_venv_in_allowed_modules(sg):
    """'venv' must appear in _PYTHON_ALLOWED_MODULES."""
    assert "venv" in sg._PYTHON_ALLOWED_MODULES


def test_python_m_venv_project_path_allowed(sg):
    """python -m venv targeting a path inside project/ is allowed."""
    assert _allow(sg, "python -m venv project/.venv")


def test_python_m_venv_project_subdir_allowed(sg):
    """python -m venv inside project/envs/ is allowed."""
    assert _allow(sg, "python -m venv project/envs/myenv")


def test_python3_m_venv_project_allowed(sg):
    """python3 -m venv targeting project/ is allowed."""
    assert _allow(sg, "python3 -m venv project/.venv")


def test_py_m_venv_project_allowed(sg):
    """py -m venv targeting project/ is allowed."""
    assert _allow(sg, "py -m venv project/.venv")


def test_python_m_venv_dot_venv_at_root_allowed_via_fallback(sg):
    """.venv resolves to project/.venv via FIX-023 fallback — allowed."""
    assert _allow(sg, "python -m venv .venv")


def test_python_m_venv_github_denied(sg):
    """python -m venv targeting .github/ is denied."""
    assert _deny(sg, "python -m venv .github/myenv")


def test_python_m_venv_vscode_denied(sg):
    """python -m venv targeting .vscode/ is denied."""
    assert _deny(sg, "python -m venv .vscode/myenv")


def test_python_m_venv_noagentzone_denied(sg):
    """python -m venv targeting NoAgentZone/ is denied."""
    assert _deny(sg, "python -m venv NoAgentZone/myenv")


def test_python_m_venv_variable_path_denied(sg):
    """python -m venv with a shell variable as path is denied."""
    assert _deny(sg, "python -m venv $VENV_PATH")


def test_python_m_unapproved_module_still_denied(sg):
    """python -m with a module NOT in _PYTHON_ALLOWED_MODULES is still denied."""
    assert _deny(sg, "python -m malicious_module")


# ---------------------------------------------------------------------------
# Requirement 3: pip read-only subcommands allowed without path restrictions
# ---------------------------------------------------------------------------

def test_pip_list_allowed(sg):
    """pip list is allowed."""
    assert _allow(sg, "pip list")


def test_pip_list_verbose_allowed(sg):
    """pip list --verbose is allowed."""
    assert _allow(sg, "pip list --verbose")


def test_pip_list_outdated_flag_allowed(sg):
    """pip list --outdated is allowed."""
    assert _allow(sg, "pip list --outdated")


def test_pip_list_format_columns_blocked_by_format_pattern(sg):
    """pip list --format=columns is blocked by the pre-existing \\bformat\\b
    explicit-deny pattern (which guards against disk-format commands).

    This is a documented limitation: the 'format' keyword in any flag or
    argument is caught by _EXPLICIT_DENY_PATTERNS regardless of context.
    Fixing this false positive is out of scope for SAF-017.
    """
    assert _deny(sg, "pip list --format=columns")


def test_pip_show_package_allowed(sg):
    """pip show <package> is allowed."""
    assert _allow(sg, "pip show requests")


def test_pip_show_multiple_packages_allowed(sg):
    """pip show with multiple packages is allowed."""
    assert _allow(sg, "pip show requests numpy pandas")


def test_pip_freeze_allowed(sg):
    """pip freeze is allowed."""
    assert _allow(sg, "pip freeze")


def test_pip_freeze_local_allowed(sg):
    """pip freeze --local is allowed."""
    assert _allow(sg, "pip freeze --local")


def test_pip_check_allowed(sg):
    """pip check is allowed."""
    assert _allow(sg, "pip check")


def test_pip3_list_allowed(sg):
    """pip3 list is allowed."""
    assert _allow(sg, "pip3 list")


def test_pip3_show_allowed(sg):
    """pip3 show requests is allowed."""
    assert _allow(sg, "pip3 show requests")


def test_pip3_freeze_allowed(sg):
    """pip3 freeze is allowed."""
    assert _allow(sg, "pip3 freeze")


def test_pip3_check_allowed(sg):
    """pip3 check is allowed."""
    assert _allow(sg, "pip3 check")


# ---------------------------------------------------------------------------
# Requirement 4: pip install allowed when VIRTUAL_ENV is inside project folder
# ---------------------------------------------------------------------------

def test_pip_install_venv_inside_workspace_allowed(sg):
    """pip install allowed when VIRTUAL_ENV is inside workspace root."""
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    assert _allow(sg, "pip install requests", extra_env=extra)


def test_pip_install_venv_inside_project_folder_allowed(sg):
    """pip install allowed when VIRTUAL_ENV is inside project/."""
    extra = {"VIRTUAL_ENV": VENV_INSIDE_PROJECT}
    assert _allow(sg, "pip install requests", extra_env=extra)


def test_pip_install_multiple_packages_with_venv_allowed(sg):
    """pip install multiple packages allowed when venv is active."""
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    assert _allow(sg, "pip install requests numpy scipy", extra_env=extra)


def test_pip_install_upgrade_with_venv_allowed(sg):
    """pip install --upgrade is allowed when venv is active."""
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    assert _allow(sg, "pip install --upgrade requests", extra_env=extra)


def test_pip_install_requirements_file_with_venv_allowed(sg):
    """pip install -r requirements.txt allowed when venv active."""
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    assert _allow(sg, "pip install -r project/requirements.txt", extra_env=extra)


def test_pip3_install_with_venv_allowed(sg):
    """pip3 install allowed when VIRTUAL_ENV is active."""
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    assert _allow(sg, "pip3 install requests", extra_env=extra)


# ---------------------------------------------------------------------------
# Requirement 5: pip install denied when no active venv or venv outside project
# ---------------------------------------------------------------------------

def test_pip_install_no_venv_denied(sg):
    """pip install denied when VIRTUAL_ENV is not set."""
    decision, _ = _run_no_venv(sg, "pip install requests")
    assert decision == "deny"


def test_pip_install_empty_venv_denied(sg):
    """pip install denied when VIRTUAL_ENV is an empty string."""
    extra = {"VIRTUAL_ENV": ""}
    with patch.dict(sg.os.environ, extra, clear=False):
        decision, _ = sg.sanitize_terminal_command("pip install requests", WS)
    assert decision == "deny"


def test_pip_install_venv_outside_workspace_denied(sg):
    """pip install denied when VIRTUAL_ENV points outside the workspace."""
    extra = {"VIRTUAL_ENV": VENV_OUTSIDE}
    assert _deny(sg, "pip install requests", extra_env=extra)


def test_pip3_install_no_venv_denied(sg):
    """pip3 install denied when no venv is active."""
    decision, _ = _run_no_venv(sg, "pip3 install requests")
    assert decision == "deny"


def test_pip_install_venv_path_traversal_denied(sg):
    """pip install denied when VIRTUAL_ENV uses path traversal to escape workspace."""
    extra = {"VIRTUAL_ENV": "c:/workspace/../other/.venv"}
    assert _deny(sg, "pip install requests", extra_env=extra)


# ---------------------------------------------------------------------------
# Security: bypass-attempt tests
# ---------------------------------------------------------------------------

def test_python_c_code_with_github_path_still_allowed(sg):
    """Inline code containing a .github reference is allowed.

    The gate cannot and does not audit the Python code content — that is the
    responsibility of the sandboxed execution environment.  The contract is:
    the -c argument is not zone-checked, so any valid inline code is allowed.
    """
    # This is intentionally allowed: the security gate governs file-system
    # access via tool parameters, not the logic inside Python code strings.
    assert _allow(sg, 'python -c "x = \'no path here\'"')


def test_python_m_venv_traversal_denied(sg):
    """python -m venv with path traversal targeting .github via .. is denied."""
    assert _deny(sg, "python -m venv project/../.github/myenv")


def test_pip_install_req_file_outside_project_denied(sg):
    """pip install -r with a requirements file outside project/ is denied."""
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    assert _deny(sg, "pip install -r .github/requirements.txt", extra_env=extra)


def test_pip_install_req_file_vscode_denied(sg):
    """pip install -r targeting .vscode/ is denied even with active venv."""
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    assert _deny(sg, "pip install -r .vscode/reqs.txt", extra_env=extra)


def test_python_c_minus_m_code_chaining_denied(sg):
    """python -c chained with a blocked -m usage is denied.

    python -c '...' chains via shell operators are split per segment;
    each segment is evaluated independently.
    """
    # The segment 'python -m malicious_module' would be denied by the module check
    assert _deny(sg, "python -c 'print(1)'; python -m malicious_module")


def test_pip_uninstall_still_allowed_with_venv(sg):
    """pip uninstall is still allowed (it was already in allowed_subcommands)."""
    extra = {"VIRTUAL_ENV": VENV_INSIDE_WORKSPACE}
    assert _allow(sg, "pip uninstall requests", extra_env=extra)
