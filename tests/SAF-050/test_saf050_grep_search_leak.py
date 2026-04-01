"""SAF-050: Prevent grep_search information leak — consistency with read_file.

BUG-115: grep_search surfaced workspace root content that read_file denied.
After SAF-046 enables workspace root reads, the original leak is resolved.
SAF-050 fixes the remaining inconsistency: _validate_include_pattern used
zone_classifier.classify() which denied any path outside the project folder,
making includePattern: "pyproject.toml" and includePattern: "*.py" fail even
though read_file allows those paths.

Coverage:
  includePattern — new allowed cases (SAF-050 fix):
    - "*.py"              → allow (general glob)
    - "**/*.ts"            → allow (general glob)
    - "src/**"             → allow (relative path, not a deny zone)
    - "pyproject.toml"     → allow (workspace root file — must match read_file)
    - "README.md"          → allow (workspace root file)
    - absolute workspace-root file  → allow
    - absolute project-folder path  → allow

  includePattern — deny cases (unchanged behavior):
    - ".github/**"         → deny
    - ".vscode/settings"   → deny
    - "NoAgentZone/**"     → deny
    - ".github" (bare)     → deny
    - "noagentzone" (bare lowercase) → deny
    - absolute path to .github zone  → deny
    - path traversal                 → deny

  no-includePattern default:
    - no params            → allow  (search.exclude handles denied zones)
    - query only           → allow

  includeIgnoredFiles (unchanged):
    - True                 → deny
    - "true"               → deny

  filePath field (SAF-046 consistency fix):
    - filePath = workspace root file  → allow
    - filePath = .github file         → deny

  search.exclude verification:
    - .github excluded     → True
    - .vscode excluded     → True
    - NoAgentZone excluded → True

  decide() integration:
    - "*.py" includePattern        → allow
    - "pyproject.toml" pattern     → allow
    - ".github/**" pattern         → deny
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

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

_SETTINGS_PATH = (
    Path(__file__).resolve().parents[2]
    / "templates" / "agent-workbench" / ".vscode" / "settings.json"
)

WS = "c:/workspace"


@pytest.fixture(autouse=True)
def mock_project_folder():
    """Avoid requiring the workspace directory to exist on disk."""
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ===========================================================================
# includePattern — new allow cases (SAF-050 core fix)
# ===========================================================================

def test_include_pattern_star_py_allow():
    """includePattern '*.py' is a general glob — must be allowed."""
    data = {"tool_name": "grep_search", "query": "import", "includePattern": "*.py"}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_include_pattern_double_star_ts_allow():
    """includePattern '**/*.ts' is a general glob — must be allowed."""
    data = {"tool_name": "grep_search", "query": "interface", "includePattern": "**/*.ts"}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_include_pattern_src_glob_allow():
    """includePattern 'src/**' is a relative path not targeting a deny zone — must be allowed."""
    data = {"tool_name": "grep_search", "query": "function", "includePattern": "src/**"}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_include_pattern_pyproject_toml_allow():
    """includePattern 'pyproject.toml' is a workspace root file — must be allowed (SAF-046 consistency)."""
    data = {"tool_name": "grep_search", "query": "version", "includePattern": "pyproject.toml"}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_include_pattern_readme_md_allow():
    """includePattern 'README.md' is a workspace root file — must be allowed."""
    data = {"tool_name": "grep_search", "query": "installation", "includePattern": "README.md"}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_include_pattern_absolute_workspace_root_file_allow():
    """Absolute includePattern to a workspace root file — must be allowed."""
    data = {
        "tool_name": "grep_search",
        "query": "name",
        "includePattern": "c:/workspace/pyproject.toml",
    }
    assert sg.validate_grep_search(data, WS) == "allow"


def test_include_pattern_absolute_project_folder_allow():
    """Absolute includePattern to project folder — must be allowed."""
    data = {
        "tool_name": "grep_search",
        "query": "class",
        "includePattern": "c:/workspace/project/src/app.py",
    }
    assert sg.validate_grep_search(data, WS) == "allow"


# ===========================================================================
# includePattern — deny cases (unchanged from before SAF-050)
# ===========================================================================

def test_include_pattern_github_glob_deny():
    """includePattern '.github/**' must be denied."""
    data = {"tool_name": "grep_search", "query": "hook", "includePattern": ".github/**"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_include_pattern_vscode_deny():
    """includePattern '.vscode/settings.json' must be denied."""
    data = {"tool_name": "grep_search", "query": "setting", "includePattern": ".vscode/settings.json"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_include_pattern_noagentzone_glob_deny():
    """includePattern 'NoAgentZone/**' must be denied."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": "NoAgentZone/**"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_include_pattern_github_bare_deny():
    """includePattern '.github' (bare) must be denied."""
    data = {"tool_name": "grep_search", "query": "token", "includePattern": ".github"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_include_pattern_noagentzone_bare_lower_deny():
    """includePattern 'noagentzone' (lowercase bare) must be denied."""
    data = {"tool_name": "grep_search", "query": "creds", "includePattern": "noagentzone"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_include_pattern_absolute_github_deny():
    """Absolute includePattern pointing into .github zone must be denied."""
    data = {
        "tool_name": "grep_search",
        "query": "hash",
        "includePattern": "c:/workspace/.github/hooks/scripts/security_gate.py",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_include_pattern_traversal_deny():
    """includePattern containing '..' path traversal must be denied."""
    data = {"tool_name": "grep_search", "query": "key", "includePattern": "project/../../.github/**"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_include_pattern_brace_github_deny():
    """Brace expansion containing .github must be denied."""
    data = {
        "tool_name": "grep_search",
        "query": "config",
        "includePattern": "{.github,project}/**",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


# ===========================================================================
# No includePattern — default behavior must rely on search.exclude
# ===========================================================================

def test_no_include_pattern_no_params_allow():
    """grep_search with no includePattern must be denied (SAF-066: fail-closed).

    SAF-066 supersedes the previous FIX-021 allow: VS Code search.exclude is
    not a hard security boundary, so unscoped searches must be denied.
    """
    data = {"tool_name": "grep_search", "query": "def main"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_no_include_pattern_query_only_allow():
    """grep_search with only a query (no includePattern) must be denied (SAF-066)."""
    data = {"tool_name": "grep_search", "query": "NoAgentZone"}
    assert sg.validate_grep_search(data, WS) == "deny"


# ===========================================================================
# includeIgnoredFiles — deny cases (unchanged)
# ===========================================================================

def test_include_ignored_files_bool_deny():
    """includeIgnoredFiles=True must be denied (can bypass search.exclude)."""
    data = {"tool_name": "grep_search", "query": "password", "includeIgnoredFiles": True}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_include_ignored_files_string_true_deny():
    """includeIgnoredFiles='true' (string) must be denied."""
    data = {"tool_name": "grep_search", "query": "secret", "includeIgnoredFiles": "true"}
    assert sg.validate_grep_search(data, WS) == "deny"


# ===========================================================================
# filePath field — SAF-046 consistency fix
# ===========================================================================

def test_filePath_workspace_root_file_allow():
    """filePath pointing to a workspace root file must be allowed (SAF-046 consistency)."""
    data = {
        "tool_name": "grep_search",
        "query": "version",
        "filePath": "c:/workspace/pyproject.toml",
    }
    assert sg.validate_grep_search(data, WS) == "allow"


def test_filePath_github_file_deny():
    """filePath pointing to a .github file must be denied."""
    data = {
        "tool_name": "grep_search",
        "query": "hook",
        "filePath": "c:/workspace/.github/hooks/scripts/security_gate.py",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


# ===========================================================================
# search.exclude verification — .github, .vscode, NoAgentZone excluded
# ===========================================================================

def _load_settings() -> dict:
    with open(_SETTINGS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def test_settings_search_exclude_github():
    """settings.json search.exclude must exclude .github."""
    settings = _load_settings()
    exclude = settings.get("search.exclude", {})
    assert ".github" in exclude, "search.exclude must contain .github"
    assert exclude[".github"] is True


def test_settings_search_exclude_vscode():
    """settings.json search.exclude must exclude .vscode."""
    settings = _load_settings()
    exclude = settings.get("search.exclude", {})
    assert ".vscode" in exclude, "search.exclude must contain .vscode"
    assert exclude[".vscode"] is True


def test_settings_search_exclude_noagentzone():
    """settings.json search.exclude must exclude NoAgentZone (provides defense-in-depth)."""
    settings = _load_settings()
    exclude = settings.get("search.exclude", {})
    noagentzone_keys = [k for k in exclude if "noagentzone" in k.lower()]
    assert noagentzone_keys, "search.exclude must contain a NoAgentZone entry"
    assert any(exclude[k] is True for k in noagentzone_keys)


# ===========================================================================
# decide() integration
# ===========================================================================

def test_decide_star_py_include_pattern_allow():
    """decide() with grep_search + includePattern '*.py' → allow."""
    data = {"tool_name": "grep_search", "query": "import", "includePattern": "*.py"}
    assert sg.decide(data, WS) == "allow"


def test_decide_pyproject_toml_include_pattern_allow():
    """decide() with grep_search + includePattern 'pyproject.toml' → allow."""
    data = {"tool_name": "grep_search", "query": "version", "includePattern": "pyproject.toml"}
    assert sg.decide(data, WS) == "allow"


def test_decide_github_include_pattern_deny():
    """decide() with grep_search + includePattern '.github/**' → deny."""
    data = {"tool_name": "grep_search", "query": "hook", "includePattern": ".github/**"}
    assert sg.decide(data, WS) == "deny"


def test_decide_no_include_pattern_allow():
    """decide() with grep_search + no includePattern must be denied (SAF-066)."""
    data = {"tool_name": "grep_search", "query": "TODO"}
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# SAF-046 consistency regression: read_file-allowed paths are grep-allowed
# ===========================================================================

def test_read_file_allowed_paths_are_grep_search_allowed_via_include_pattern():
    """Paths allowed by read_file (workspace root files) must also be grep-allowed.

    This is the core consistency requirement from SAF-050/BUG-115.
    """
    workspace_root_files = [
        "pyproject.toml",
        "README.md",
        "launcher.spec",
    ]
    for filename in workspace_root_files:
        data = {
            "tool_name": "grep_search",
            "query": "test",
            "includePattern": filename,
        }
        result = sg.validate_grep_search(data, WS)
        assert result == "allow", (
            f"grep_search with includePattern '{filename}' should be allowed "
            f"(read_file allows workspace root files per SAF-046), got '{result}'"
        )


def test_denied_zone_paths_are_grep_search_denied_via_include_pattern():
    """Paths denied by read_file (deny zones) must also be grep-search-denied.

    Regression guard: the fix must not inadvertently allow deny zone access.
    """
    denied_patterns = [
        ".github/**",
        ".vscode/**",
        "NoAgentZone/**",
        ".github/hooks/scripts/security_gate.py",
    ]
    for pattern in denied_patterns:
        data = {
            "tool_name": "grep_search",
            "query": "sensitive",
            "includePattern": pattern,
        }
        result = sg.validate_grep_search(data, WS)
        assert result == "deny", (
            f"grep_search with includePattern '{pattern}' should be denied "
            f"(deny zone), got '{result}'"
        )


# ===========================================================================
# _include_pattern_targets_deny_zone unit tests
# ===========================================================================

def test_helper_github_relative_deny():
    """_include_pattern_targets_deny_zone('.github/**', ws) → True."""
    assert sg._include_pattern_targets_deny_zone(".github/**", WS) is True


def test_helper_vscode_relative_deny():
    """_include_pattern_targets_deny_zone('.vscode', ws) → True."""
    assert sg._include_pattern_targets_deny_zone(".vscode", WS) is True


def test_helper_noagentzone_relative_deny():
    """_include_pattern_targets_deny_zone('noagentzone/**', ws) → True."""
    assert sg._include_pattern_targets_deny_zone("noagentzone/**", WS) is True


def test_helper_star_py_relative_allow():
    """_include_pattern_targets_deny_zone('*.py', ws) → False (general glob)."""
    assert sg._include_pattern_targets_deny_zone("*.py", WS) is False


def test_helper_double_star_glob_allow():
    """_include_pattern_targets_deny_zone('**/*.ts', ws) → False."""
    assert sg._include_pattern_targets_deny_zone("**/*.ts", WS) is False


def test_helper_project_glob_allow():
    """_include_pattern_targets_deny_zone('project/**', ws) → False (project folder)."""
    assert sg._include_pattern_targets_deny_zone("project/**", WS) is False


def test_helper_pyproject_toml_allow():
    """_include_pattern_targets_deny_zone('pyproject.toml', ws) → False (workspace root file)."""
    assert sg._include_pattern_targets_deny_zone("pyproject.toml", WS) is False


def test_helper_absolute_github_deny():
    """_include_pattern_targets_deny_zone('/c:/workspace/.github/...') → True."""
    norm = "c:/workspace/.github/hooks/scripts/security_gate.py"
    assert sg._include_pattern_targets_deny_zone(norm, WS) is True


def test_helper_absolute_project_allow():
    """_include_pattern_targets_deny_zone('c:/workspace/project/app.py') → False."""
    norm = "c:/workspace/project/app.py"
    assert sg._include_pattern_targets_deny_zone(norm, WS) is False


def test_helper_absolute_workspace_root_file_allow():
    """_include_pattern_targets_deny_zone('c:/workspace/pyproject.toml') → False (SAF-046)."""
    norm = "c:/workspace/pyproject.toml"
    assert sg._include_pattern_targets_deny_zone(norm, WS) is False


def test_helper_empty_string_allow():
    """_include_pattern_targets_deny_zone('', ws) → False (empty pattern)."""
    assert sg._include_pattern_targets_deny_zone("", WS) is False
