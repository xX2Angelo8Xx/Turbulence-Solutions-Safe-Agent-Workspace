"""FIX-116 — Regression and security tests for file_search .github/ allowlist.

BUG-195: file_search over-blocks .github/ paths.  validate_file_search()
previously denied any query containing '.github', even when the target
subdirectory (.github/agents/, .github/skills/, .github/prompts/,
.github/instructions/) was explicitly whitelisted for read_file/list_dir.

FIX-116 makes file_search behaviour consistent with read_file by applying the
same _GITHUB_READ_ALLOWED_RE check that SAF-055 introduced for read-only tools.

Test categories:
- Regression: the originally reported paths now return allow
- Security: non-whitelisted .github/ paths remain denied
- Security: other deny zones (.vscode, noagentzone) still blocked
- Edge cases: wildcards, absolute paths, mixed case
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Make security_gate importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "hooks"
    / "scripts"
)

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg       # noqa: E402
import zone_classifier as zc    # noqa: E402

WS = "/workspace"
WS_WIN = "c:/workspace"


@pytest.fixture(autouse=True)
def _patch_detect_project_folder():
    """Use a fallback project folder for the fake workspace root."""
    original = zc.detect_project_folder

    def _detect_with_fallback(workspace_root: Path) -> str:
        try:
            return original(workspace_root)
        except (RuntimeError, OSError):
            return "project"

    with patch.object(zc, "detect_project_folder", side_effect=_detect_with_fallback):
        yield


# ===========================================================================
# Regression tests — BUG-195: queries that were wrongly denied must now allow
# ===========================================================================

class TestRegressionBug195:
    """These queries were denied before FIX-116. They must now return allow."""

    def test_agents_readme_allowed(self):
        """BUG-195 original report: .github/agents/README.md must be allowed."""
        data = {"query": ".github/agents/README.md"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_agents_directory_glob_allowed(self):
        """.github/agents/ glob — allowed."""
        data = {"query": ".github/agents/**"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_instructions_allowed(self):
        """.github/instructions/ — allowed."""
        data = {"query": ".github/instructions/copilot-instructions.md"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_skills_allowed(self):
        """.github/skills/ — allowed."""
        data = {"query": ".github/skills/agent-customization/SKILL.md"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_prompts_allowed(self):
        """.github/prompts/ — allowed."""
        data = {"query": ".github/prompts/example.prompt.md"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_nested_tool_input_agents_allowed(self):
        """VS Code hook nested format with .github/agents/ — allowed."""
        data = {"tool_input": {"query": ".github/agents/foo.md"}}
        assert sg.validate_file_search(data, WS) == "allow"


# ===========================================================================
# Security tests — non-whitelisted .github/ paths must remain denied
# ===========================================================================

class TestGithubNonWhitelistedRemainsDenied:
    """Paths outside the four whitelisted subdirectories must still be denied."""

    def test_hooks_directory_denied(self):
        """.github/hooks/ (security gate) — must remain denied."""
        data = {"query": ".github/hooks/scripts/security_gate.py"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_hooks_wildcard_denied(self):
        """.github/hooks/** wildcard — denied."""
        data = {"query": ".github/hooks/**"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_workflows_denied(self):
        """.github/workflows/ (CI configuration) — denied."""
        data = {"query": ".github/workflows/ci.yml"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_github_root_denied(self):
        """.github root query — denied (not whitelisted)."""
        data = {"query": ".github/copilot-instructions.md"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_github_bare_name_denied(self):
        """Query containing only '.github' — denied."""
        data = {"query": ".github"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_embedded_github_non_whitelisted_denied(self):
        """Glob with .github/ targeting non-whitelisted subdir — denied."""
        data = {"query": "**/.github/workflows/*.yml"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_agents_extra_prefix_denied(self):
        """.github/agents-extra/ must NOT be treated as whitelisted (prefix attack)."""
        data = {"query": ".github/agents-extra/foo.md"}
        assert sg.validate_file_search(data, WS) == "deny"


# ===========================================================================
# Security tests — other deny zones unaffected by FIX-116
# ===========================================================================

class TestOtherDenyZonesUnchanged:
    """.vscode and NoAgentZone must still be denied unconditionally."""

    def test_vscode_still_denied(self):
        """.vscode queries remain denied."""
        data = {"query": ".vscode/settings.json"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_vscode_uppercase_denied(self):
        """.VSCODE queries remain denied (case-insensitive)."""
        data = {"query": ".VSCODE/extensions.json"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_noagentzone_denied(self):
        """NoAgentZone queries remain denied."""
        data = {"query": "NoAgentZone/secret.txt"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_noagentzone_lowercase_denied(self):
        """noagentzone (all lowercase) remains denied."""
        data = {"query": "noagentzone/**"}
        assert sg.validate_file_search(data, WS) == "deny"


# ===========================================================================
# Edge cases: wildcards, absolute paths, mixed case
# ===========================================================================

class TestEdgeCases:
    """Edge cases for FIX-116 — wildcards, absolute paths, casing."""

    def test_agents_wildcard_md_allowed(self):
        """.github/agents/**/*.md — allowed."""
        data = {"query": ".github/agents/**/*.md"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_mixed_case_github_agents_allowed(self):
        """.GitHub/agents/ (capital G) — allowed via normalize_path lowercasing."""
        data = {"query": ".GitHub/agents/README.md"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_mixed_case_github_hooks_denied(self):
        """.GitHub/hooks/ (capital G) — denied (non-whitelisted)."""
        data = {"query": ".GitHub/hooks/scripts/security_gate.py"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_absolute_path_agents_unix_allowed(self):
        """Absolute Unix path to .github/agents/ — allowed."""
        data = {"query": f"{WS}/.github/agents/README.md"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_absolute_path_agents_windows_allowed(self):
        """Absolute Windows path to .github/agents/ — allowed."""
        data = {"query": f"{WS_WIN}/.github/agents/README.md"}
        assert sg.validate_file_search(data, WS_WIN) == "allow"

    def test_absolute_path_hooks_denied(self):
        """Absolute path to .github/hooks/ — denied."""
        data = {"query": f"{WS}/.github/hooks/security_gate.py"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_traversal_in_whitelisted_subdir_denied(self):
        """Path traversal inside whitelisted subdir — denied by .. check."""
        data = {"query": ".github/agents/../hooks/security_gate.py"}
        assert sg.validate_file_search(data, WS) == "deny"
