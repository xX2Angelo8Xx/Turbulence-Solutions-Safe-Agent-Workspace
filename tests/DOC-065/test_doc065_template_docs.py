"""
DOC-065: Batch template documentation fixes for v3.4.0

Tests verify all 5 documentation changes across both templates:
1. isBackground:true removed from Blocked Commands (agent-workbench AGENT-RULES only)
2. grep_search includePattern is required (both AGENT-RULES)
3. Terminal navigation lock-in documented (both AGENT-RULES + copilot-instructions)
4. includeIgnoredFiles:true restriction documented (both templates)
5. list_dir scope clarified for .github/ (both AGENT-RULES)
"""

import os
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

AGENT_WORKBENCH_RULES = os.path.join(
    REPO_ROOT, "templates", "agent-workbench", "Project", "AgentDocs", "AGENT-RULES.md"
)
CLEAN_WORKSPACE_RULES = os.path.join(
    REPO_ROOT, "templates", "clean-workspace", "Project", "AGENT-RULES.md"
)
AGENT_WORKBENCH_COPILOT = os.path.join(
    REPO_ROOT, "templates", "agent-workbench", ".github", "instructions", "copilot-instructions.md"
)
CLEAN_WORKSPACE_COPILOT = os.path.join(
    REPO_ROOT, "templates", "clean-workspace", ".github", "instructions", "copilot-instructions.md"
)
AGENT_WORKBENCH_MANIFEST = os.path.join(
    REPO_ROOT, "templates", "agent-workbench", ".github", "hooks", "scripts", "MANIFEST.json"
)
CLEAN_WORKSPACE_MANIFEST = os.path.join(
    REPO_ROOT, "templates", "clean-workspace", ".github", "hooks", "scripts", "MANIFEST.json"
)


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─── Change 1: isBackground:true removed from Blocked Commands (agent-workbench only) ───

class TestIsBackgroundRemoved:
    def test_isBackground_not_in_blocked_commands_table_agent_workbench(self):
        """isBackground:true must NOT appear in the Blocked Commands table in agent-workbench AGENT-RULES."""
        content = _read(AGENT_WORKBENCH_RULES)
        # Find the Blocked Commands section
        assert "### Blocked Commands" in content, "Blocked Commands section missing"
        blocked_start = content.index("### Blocked Commands")
        # Find the end of the Blocked Commands table (next --- or ## heading)
        blocked_section = content[blocked_start:blocked_start + 2000]
        # The row that used to say "isBackground:true | Security gate cannot validate"
        # should no longer appear in this section
        assert "isBackground:true` | Security gate" not in blocked_section, \
            "isBackground:true block row still present in Blocked Commands table (should be removed)"

    def test_isBackground_not_blocked_in_clean_workspace_agent_rules(self):
        """clean-workspace AGENT-RULES should still have isBackground:true in Known Tool Workarounds (unchanged)."""
        content = _read(CLEAN_WORKSPACE_RULES)
        # clean-workspace keeps this in Known Tool Workarounds — not changed by this WP
        assert "isBackground:true" in content, \
            "clean-workspace AGENT-RULES should still document isBackground:true workaround"


# ─── Change 2: grep_search includePattern required ───

class TestGrepSearchIncludePatternRequired:
    def test_agent_workbench_grep_search_includePattern_required(self):
        """agent-workbench AGENT-RULES must state includePattern is required for grep_search."""
        content = _read(AGENT_WORKBENCH_RULES)
        assert "includePattern` is required" in content, \
            "agent-workbench AGENT-RULES: grep_search includePattern required not documented"

    def test_clean_workspace_grep_search_includePattern_required(self):
        """clean-workspace AGENT-RULES must state includePattern is required (not auto-scoped)."""
        content = _read(CLEAN_WORKSPACE_RULES)
        assert "includePattern` is required" in content, \
            "clean-workspace AGENT-RULES: grep_search includePattern required not documented"

    def test_clean_workspace_no_auto_scoped_claim(self):
        """clean-workspace AGENT-RULES must NOT claim grep_search is auto-scoped to project folder."""
        content = _read(CLEAN_WORKSPACE_RULES)
        assert "Scoped to `{{PROJECT_NAME}}/` by default" not in content, \
            "clean-workspace AGENT-RULES still incorrectly claims grep_search auto-scopes to project folder"


# ─── Change 3: Terminal navigation lock-in ───

class TestTerminalNavigationLockIn:
    def test_agent_workbench_rules_documents_cd_blocked(self):
        """agent-workbench AGENT-RULES Blocked Commands must document outward cd/Set-Location."""
        content = _read(AGENT_WORKBENCH_RULES)
        assert "outward navigation" in content or "Set-Location .." in content, \
            "agent-workbench AGENT-RULES does not document terminal navigation restriction"

    def test_clean_workspace_rules_documents_navigation_restriction(self):
        """clean-workspace AGENT-RULES Security Rules must document terminal navigation restriction."""
        content = _read(CLEAN_WORKSPACE_RULES)
        assert "Terminal navigation is restricted" in content, \
            "clean-workspace AGENT-RULES does not document terminal navigation restriction"

    def test_agent_workbench_copilot_documents_navigation_blocked(self):
        """agent-workbench copilot-instructions Known Tool Limitations must include outward navigation blocked."""
        content = _read(AGENT_WORKBENCH_COPILOT)
        assert "outward navigation" in content or "Push-Location" in content, \
            "agent-workbench copilot-instructions does not document navigation lock-in"

    def test_clean_workspace_copilot_documents_navigation_blocked(self):
        """clean-workspace copilot-instructions Known Tool Limitations must include outward navigation blocked."""
        content = _read(CLEAN_WORKSPACE_COPILOT)
        assert "outward navigation" in content or "Push-Location" in content, \
            "clean-workspace copilot-instructions does not document navigation lock-in"


# ─── Change 4: includeIgnoredFiles:true restriction ───

class TestIncludeIgnoredFilesRestriction:
    def test_agent_workbench_rules_documents_includeIgnoredFiles_blocked(self):
        """agent-workbench AGENT-RULES must document includeIgnoredFiles:true restriction."""
        content = _read(AGENT_WORKBENCH_RULES)
        assert "includeIgnoredFiles" in content, \
            "agent-workbench AGENT-RULES does not mention includeIgnoredFiles restriction"

    def test_clean_workspace_rules_documents_includeIgnoredFiles_blocked(self):
        """clean-workspace AGENT-RULES must document includeIgnoredFiles:true restriction."""
        content = _read(CLEAN_WORKSPACE_RULES)
        assert "includeIgnoredFiles" in content, \
            "clean-workspace AGENT-RULES does not mention includeIgnoredFiles restriction"

    def test_clean_workspace_rules_workarounds_includeIgnoredFiles(self):
        """clean-workspace AGENT-RULES Known Tool Workarounds must explicitly warn against includeIgnoredFiles:true."""
        content = _read(CLEAN_WORKSPACE_RULES)
        assert "includeIgnoredFiles: true` in `grep_search" in content or \
               "includeIgnoredFiles: true` in" in content, \
            "clean-workspace AGENT-RULES Known Tool Workarounds missing includeIgnoredFiles warning"


# ─── Change 5: list_dir .github/ scope clarification ───

class TestListDirGithubScopeClarification:
    def test_agent_workbench_rules_list_dir_subdirs_allowed(self):
        """agent-workbench AGENT-RULES must clarify that .github/ subdirectory listings are allowed."""
        content = _read(AGENT_WORKBENCH_RULES)
        assert "subdirectory listings" in content and ".github/instructions/" in content, \
            "agent-workbench AGENT-RULES does not clarify that .github/ subdirectory listings are allowed"

    def test_clean_workspace_rules_list_dir_subdirs_allowed(self):
        """clean-workspace AGENT-RULES must clarify that .github/ subdirectory listings are allowed."""
        content = _read(CLEAN_WORKSPACE_RULES)
        assert "subdirectory listings" in content and ".github/instructions/" in content, \
            "clean-workspace AGENT-RULES does not clarify that .github/ subdirectory listings are allowed"

    def test_agent_workbench_rules_list_dir_top_level_denied(self):
        """agent-workbench AGENT-RULES must clarify that top-level .github/ listing is denied."""
        content = _read(AGENT_WORKBENCH_RULES)
        assert "top-level `.github/` listing is denied" in content, \
            "agent-workbench AGENT-RULES does not clarify top-level .github/ listing is denied"

    def test_clean_workspace_rules_list_dir_top_level_denied(self):
        """clean-workspace AGENT-RULES must clarify that top-level .github/ listing is denied."""
        content = _read(CLEAN_WORKSPACE_RULES)
        assert "top-level `.github/` listing is denied" in content, \
            "clean-workspace AGENT-RULES does not clarify top-level .github/ listing is denied"


# ─── MANIFEST regenerated ───

class TestManifestRegenerated:
    def test_agent_workbench_manifest_exists(self):
        """MANIFEST.json must exist for agent-workbench."""
        assert os.path.exists(AGENT_WORKBENCH_MANIFEST), \
            f"agent-workbench MANIFEST.json missing at {AGENT_WORKBENCH_MANIFEST}"

    def test_clean_workspace_manifest_exists(self):
        """MANIFEST.json must exist for clean-workspace."""
        assert os.path.exists(CLEAN_WORKSPACE_MANIFEST), \
            f"clean-workspace MANIFEST.json missing at {CLEAN_WORKSPACE_MANIFEST}"

    def test_agent_workbench_manifest_tracks_agent_rules(self):
        """agent-workbench MANIFEST.json must reference AGENT-RULES.md."""
        import json
        with open(AGENT_WORKBENCH_MANIFEST, encoding="utf-8") as f:
            manifest = json.load(f)
        files = manifest.get("files", {})
        # AGENT-RULES.md should appear in the manifest (under AgentDocs/)
        keys = list(files.keys())
        assert any("AGENT-RULES.md" in k for k in keys), \
            "AGENT-RULES.md not tracked in agent-workbench MANIFEST.json"

    def test_clean_workspace_manifest_tracks_agent_rules(self):
        """clean-workspace MANIFEST.json must reference AGENT-RULES.md."""
        import json
        with open(CLEAN_WORKSPACE_MANIFEST, encoding="utf-8") as f:
            manifest = json.load(f)
        files = manifest.get("files", {})
        keys = list(files.keys())
        assert any("AGENT-RULES.md" in k for k in keys), \
            "AGENT-RULES.md not tracked in clean-workspace MANIFEST.json"
