"""
DOC-066: Tests for persistent documentation inversion fixes.

Verifies:
1. isBackground:true row removed from Known Tool Limitations in both templates
2. Navigation wording updated to mention within-workspace allowance
3. file_search not conflated with grep_search includePattern requirement
4. MANIFEST.json files are valid JSON
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

AW_COPILOT = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "instructions" / "copilot-instructions.md"
CW_COPILOT = REPO_ROOT / "templates" / "clean-workspace" / ".github" / "instructions" / "copilot-instructions.md"
AW_RULES = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs" / "AGENT-RULES.md"
CW_RULES = REPO_ROOT / "templates" / "clean-workspace" / "Project" / "AGENT-RULES.md"
AW_MANIFEST = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "MANIFEST.json"
CW_MANIFEST = REPO_ROOT / "templates" / "clean-workspace" / ".github" / "hooks" / "scripts" / "MANIFEST.json"


# ---------------------------------------------------------------------------
# Change 1: isBackground:true must NOT appear in Known Tool Limitations
# ---------------------------------------------------------------------------

class TestIsBackgroundRemoved:
    def test_aw_copilot_no_isbackground_limitation(self):
        """agent-workbench copilot-instructions.md must not list isBackground:true as a limitation."""
        content = AW_COPILOT.read_text(encoding="utf-8")
        # The row that was wrong listed isBackground:true under "Known Tool Limitations"
        assert "isBackground:true`) | Security gate cannot validate" not in content

    def test_cw_copilot_no_isbackground_limitation(self):
        """clean-workspace copilot-instructions.md must not list isBackground:true as a limitation."""
        content = CW_COPILOT.read_text(encoding="utf-8")
        assert "isBackground:true`) | Security gate cannot validate" not in content

    def test_cw_rules_no_isbackground_row(self):
        """clean-workspace AGENT-RULES.md Known Tool Workarounds must not have isBackground:true row."""
        content = CW_RULES.read_text(encoding="utf-8")
        assert "isBackground:true`) | Security gate cannot validate" not in content

    def test_aw_rules_isbackground_positive_workaround_retained(self):
        """agent-workbench AGENT-RULES.md Known Workarounds must still reference isBackground=true positively."""
        content = AW_RULES.read_text(encoding="utf-8")
        # The positive workaround row for long-running commands must still be present
        assert "isBackground=true" in content
        assert "Long-running commands time out" in content


# ---------------------------------------------------------------------------
# Change 2: Navigation wording — within-workspace navigation is now allowed
# ---------------------------------------------------------------------------

class TestNavigationWording:
    def test_aw_copilot_navigation_wording_updated(self):
        """agent-workbench copilot-instructions.md navigation row must mention 'above workspace root'."""
        content = AW_COPILOT.read_text(encoding="utf-8")
        assert "above workspace root" in content

    def test_aw_copilot_navigation_no_blanket_deny(self):
        """agent-workbench copilot-instructions.md must not use misleading 'outward navigation' label."""
        content = AW_COPILOT.read_text(encoding="utf-8")
        assert "(outward navigation)" not in content

    def test_cw_copilot_navigation_wording_updated(self):
        """clean-workspace copilot-instructions.md navigation row must mention 'above workspace root'."""
        content = CW_COPILOT.read_text(encoding="utf-8")
        assert "above workspace root" in content

    def test_cw_copilot_navigation_no_blanket_deny(self):
        """clean-workspace copilot-instructions.md must not use misleading 'outward navigation' label."""
        content = CW_COPILOT.read_text(encoding="utf-8")
        assert "(outward navigation)" not in content

    def test_aw_rules_navigation_row_updated(self):
        """agent-workbench AGENT-RULES.md Blocked Commands row must reflect within-workspace allowance."""
        content = AW_RULES.read_text(encoding="utf-8")
        assert "above workspace root" in content
        # Old misleading label must be gone
        assert "(outward navigation)" not in content

    def test_cw_rules_navigation_wording_updated(self):
        """clean-workspace AGENT-RULES.md Security Rules must mention within-workspace allowance."""
        content = CW_RULES.read_text(encoding="utf-8")
        assert "above the workspace root are blocked" in content
        assert "navigation within" in content

    def test_aw_copilot_mentions_within_workspace_allowed(self):
        """agent-workbench copilot-instructions.md must positively state navigation within workspace is allowed."""
        content = AW_COPILOT.read_text(encoding="utf-8")
        assert "directories is allowed" in content

    def test_cw_copilot_mentions_within_workspace_allowed(self):
        """clean-workspace copilot-instructions.md must positively state navigation within workspace is allowed."""
        content = CW_COPILOT.read_text(encoding="utf-8")
        assert "directories is allowed" in content


# ---------------------------------------------------------------------------
# Change 3: file_search must not be conflated with grep_search includePattern
# ---------------------------------------------------------------------------

class TestFileSearchNotConflated:
    def test_aw_rules_file_search_clarification_exists(self):
        """agent-workbench AGENT-RULES.md must have a clarifying note that file_search uses query not includePattern."""
        content = AW_RULES.read_text(encoding="utf-8")
        assert "file_search" in content
        # Must clarify that includePattern does NOT apply to file_search
        assert "includePattern` requirement applies only to `grep_search`" in content

    def test_cw_rules_file_search_does_not_require_include_pattern(self):
        """clean-workspace AGENT-RULES.md Tool Permission Matrix must not say file_search requires includePattern."""
        content = CW_RULES.read_text(encoding="utf-8")
        # The old incorrect text said: "`includePattern` is required" for file_search
        # The new text must say file_search uses query parameter (permission may be Allowed or Zone-checked)
        assert "file_search" in content
        assert "Uses the `query` parameter" in content

    def test_cw_rules_file_search_clarifies_no_include_pattern(self):
        """clean-workspace AGENT-RULES.md must explicitly state file_search does not require includePattern."""
        content = CW_RULES.read_text(encoding="utf-8")
        assert "does **not** require `includePattern`" in content

    def test_aw_rules_grep_search_still_requires_include_pattern(self):
        """agent-workbench AGENT-RULES.md must still state grep_search requires includePattern."""
        content = AW_RULES.read_text(encoding="utf-8")
        assert "grep_search` denied with" in content
        assert "Always provide `includePattern`" in content

    def test_cw_rules_grep_search_still_requires_include_pattern(self):
        """clean-workspace AGENT-RULES.md must still state grep_search requires includePattern."""
        content = CW_RULES.read_text(encoding="utf-8")
        assert "`includePattern` is required" in content


# ---------------------------------------------------------------------------
# MANIFEST.json validity
# ---------------------------------------------------------------------------

class TestManifestValid:
    def test_aw_manifest_is_valid_json(self):
        """agent-workbench MANIFEST.json must be valid JSON."""
        data = json.loads(AW_MANIFEST.read_text(encoding="utf-8"))
        assert "files" in data
        assert "file_count" in data

    def test_cw_manifest_is_valid_json(self):
        """clean-workspace MANIFEST.json must be valid JSON."""
        data = json.loads(CW_MANIFEST.read_text(encoding="utf-8"))
        assert "files" in data
        assert "file_count" in data

    def test_aw_manifest_tracks_copilot_instructions(self):
        """agent-workbench MANIFEST.json must track copilot-instructions.md as security-critical."""
        data = json.loads(AW_MANIFEST.read_text(encoding="utf-8"))
        key = ".github/instructions/copilot-instructions.md"
        assert key in data["files"]
        assert data["files"][key]["security_critical"] is True

    def test_cw_manifest_tracks_copilot_instructions(self):
        """clean-workspace MANIFEST.json must track copilot-instructions.md as security-critical."""
        data = json.loads(CW_MANIFEST.read_text(encoding="utf-8"))
        key = ".github/instructions/copilot-instructions.md"
        assert key in data["files"]
        assert data["files"][key]["security_critical"] is True

    def test_aw_manifest_file_count_matches_files(self):
        """agent-workbench MANIFEST.json file_count must match actual files tracked."""
        data = json.loads(AW_MANIFEST.read_text(encoding="utf-8"))
        assert data["file_count"] == len(data["files"])

    def test_cw_manifest_file_count_matches_files(self):
        """clean-workspace MANIFEST.json file_count must match actual files tracked."""
        data = json.loads(CW_MANIFEST.read_text(encoding="utf-8"))
        assert data["file_count"] == len(data["files"])
