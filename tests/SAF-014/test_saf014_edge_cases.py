"""SAF-014 Tester edge-case tests.

Edge cases not covered by the developer suite:
  - NoAgentZone as a target
  - Path traversal via ../ from inside the project folder
  - Dollar-sign variable injection ($HOME, $env:VAR)
  - Absolute paths outside the workspace (Unix /etc and Windows C:/Users)
  - grep -r recursive flag behaviour (allow for project, deny for .github)
  - grep -r . (workspace root — deny in 2-tier model)
  - Multiple project paths in a single command (allow)
  - findstr /S Windows-style flag (known limitation: misidentified as path → deny)
  - wc with no path arguments (allow — nothing to zone-check)
  - Deeply nested project path (allow)
"""

import sys
from pathlib import Path
from unittest.mock import patch

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


@pytest.fixture(scope="module")
def sg():
    import security_gate as _sg
    return _sg


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


WS = "c:/workspace"


def allow(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def deny(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# 1. NoAgentZone as a target (TST-1283 – TST-1285)
# ---------------------------------------------------------------------------

def test_get_content_noagentzone_denied(sg):
    """get-content targeting NoAgentZone/ must be denied."""
    assert deny(sg, "get-content NoAgentZone/readme.md")


def test_gc_noagentzone_denied(sg):
    """gc (PowerShell alias) targeting NoAgentZone/ must be denied."""
    assert deny(sg, "gc NoAgentZone/secret.txt")


def test_grep_noagentzone_denied(sg):
    """grep targeting NoAgentZone/ must be denied."""
    assert deny(sg, "grep pattern NoAgentZone/config.json")


# ---------------------------------------------------------------------------
# 2. Path traversal via ../ (TST-1286 – TST-1287)
# ---------------------------------------------------------------------------

def test_path_traversal_project_to_github_denied(sg):
    """get-content traversing from project/ to .github/ must be denied.

    project/../.github/secret normalises to .github/secret which is deny zone.
    """
    assert deny(sg, "get-content project/../.github/secret")


def test_path_traversal_stat_project_to_vscode_denied(sg):
    """stat traversing from project/ to .vscode/ must be denied.

    project/../.vscode/settings.json normalises to .vscode/settings.json → deny.
    """
    assert deny(sg, "stat project/../.vscode/settings.json")


# ---------------------------------------------------------------------------
# 3. Dollar-sign variable injection (TST-1288 – TST-1289)
# ---------------------------------------------------------------------------

def test_dollar_sign_unix_variable_denied(sg):
    """stat with $HOME variable in path must be denied.

    _validate_args returns False immediately when '$' appears in any argument.
    """
    assert deny(sg, "stat $HOME/secret")


def test_dollar_sign_powershell_env_variable_denied(sg):
    """get-content with PowerShell $env:APPDATA variable must be denied."""
    assert deny(sg, "get-content $env:APPDATA/file.txt")


# ---------------------------------------------------------------------------
# 4. Absolute paths outside the workspace (TST-1290 – TST-1291)
# ---------------------------------------------------------------------------

def test_stat_absolute_unix_path_outside_workspace_denied(sg):
    """stat targeting /etc/passwd (absolute Unix path) must be denied.

    /etc/passwd is outside the workspace root c:/workspace → deny zone.
    """
    assert deny(sg, "stat /etc/passwd")


def test_get_content_absolute_windows_path_outside_workspace_denied(sg):
    """get-content targeting C:/Users/secret.txt (Windows absolute path) must be denied.

    C:/Users/ is outside the workspace root c:/workspace → deny zone.
    """
    assert deny(sg, "get-content C:/Users/Administrator/secret.txt")


# ---------------------------------------------------------------------------
# 5. grep recursive flag behaviour (TST-1292 – TST-1294)
# ---------------------------------------------------------------------------

def test_grep_recursive_flag_project_allowed(sg):
    """grep -r targeting the project folder must be allowed.

    The -r flag is recognised as a dash-prefixed flag and skipped by
    _validate_args; project/ is in the allow zone.
    """
    assert allow(sg, "grep -r pattern project/")


def test_grep_recursive_flag_github_denied(sg):
    """grep -r targeting .github/ must be denied.

    -r is skipped; .github/ is in the deny zone.
    """
    assert deny(sg, "grep -r pattern .github/")


def test_grep_recursive_dot_workspace_root_denied(sg):
    """grep -r . (workspace root via dot) must be denied.

    '.' starts with '.' so _is_path_like returns True.  In the 2-tier zone
    model the workspace root itself is not the project folder → deny.
    """
    assert deny(sg, "grep -r . pattern")


# ---------------------------------------------------------------------------
# 6. Multiple project paths in one command (TST-1295 – TST-1296)
# ---------------------------------------------------------------------------

def test_grep_multiple_project_paths_allowed(sg):
    """grep with two project paths must be allowed.

    Both tokens zone-check to 'allow' so the overall decision is allow.
    """
    assert allow(sg, "grep pattern project/file1.py project/file2.py")


def test_wc_multiple_project_paths_allowed(sg):
    """wc counting two project files must be allowed."""
    assert allow(sg, "wc project/module_a.py project/module_b.py")


# ---------------------------------------------------------------------------
# 7. findstr /S Windows-style flag — known limitation (TST-1297)
# ---------------------------------------------------------------------------

def test_findstr_slash_flag_is_denied_known_limitation(sg):
    """findstr /S is denied because _validate_args does not skip /- prefixed flags.

    KNOWN LIMITATION (BUG-048): _validate_args only skips tokens starting
    with '-'.  The Windows-style flag '/S' starts with '/', which makes
    _is_path_like return True.  It is then zone-checked as the absolute path
    '/s', which is outside the workspace → deny.

    This is fail-safe (over-restrictive) but prevents recursive findstr usage.
    A separate FIX workpackage should extend _validate_args to recognise
    single-character /FLAG tokens on Windows.
    """
    assert deny(sg, "findstr /S pattern project/file.py")


# ---------------------------------------------------------------------------
# 8. wc with flag-only arguments (no path) (TST-1298)
# ---------------------------------------------------------------------------

def test_wc_flag_only_no_path_allowed(sg):
    """wc -l with no path argument must be allowed.

    When all arguments are flags, _validate_args finds no path-like tokens to
    zone-check and returns True, so the command is allowed.
    """
    assert allow(sg, "wc -l")
